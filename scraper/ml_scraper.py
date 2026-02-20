import random
import requests
import time 
from bs4 import BeautifulSoup
from scraper.amazon_scraper import coletar_produto_amazon_selenium
from scraper.selenium_busca import iniciar_driver
from scraper.mercadolivre_selenium import coletar_produto_ml_selenium



HEADERS_POOL = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "pt-BR,pt;q=0.9"
    },
    {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)",
        "Accept-Language": "pt-BR,pt;q=0.9"
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Accept-Language": "pt-BR,pt;q=0.9"
    }
]

from scraper.amazon_scraper import coletar_produto_amazon
from affiliate.amazon import gerar_link_afiliado_amazon
from config.produtos import identificar_marketplace
from scraper.magalu_scraper import coletar_produto_magalu
from affiliate.magalu import gerar_link_afiliado_magalu



from database.db import conectar, criar_tabelas
from config.produtos import carregar_produtos

from rules.promo_rules import (
    verificar_promocao,
    obter_preco_anterior,
    promocao_ja_postada,
    pode_repostar,
    preco_historico
)

from database.metricas import registrar_promocao
from text_generator.oferta_texto import gerar_texto_oferta
from affiliate.mercadolivre import gerar_link_afiliado
from poster.telegram_bot import enviar_telegram_foto_com_texto, enviar_telegram


# --------------------------------------------------
# COLETA DO PRODUTO
# --------------------------------------------------
def coletar_produto(url):

    # 🔥 micro delay humano
    time.sleep(random.uniform(1.5, 3.5))

    headers = random.choice(HEADERS_POOL)

    # 🔥 session persistente
    session = requests.Session()

    for tentativa in range(3):
        try:
            response = session.get(
                url,
                headers=headers,
                timeout=15
            )

            # 🔥 detectar bloqueio / captcha
            if "captcha" in response.text.lower():
                print("🚨 Possível bloqueio detectado")
                return None

            if response.status_code == 200:
                break

        except requests.exceptions.RequestException:
            time.sleep(2)
    else:
        print("Falha de conexão após tentativas")
        return None


    soup = BeautifulSoup(response.text, "lxml")

    nome = soup.select_one("h1.ui-pdp-title")

    # 🔥 tentativa 1 — preço padrão
    preco_elemento = soup.select_one("span.andes-money-amount__fraction")

    preco_valor = None

    if preco_elemento:
        preco_valor = preco_elemento.text.strip().replace(".", "")

    # 🔥 tentativa 2 — fallback meta price
    if not preco_valor:
        meta_price = soup.select_one("meta[itemprop='price']")
        if meta_price:
            preco_valor = meta_price.get("content")

    imagem = soup.select_one('meta[property="og:image"]')

    if not nome or not preco_valor:
        print("Não foi possível encontrar nome ou preço")
        return None

    return {
        "nome": nome.text.strip(),
        "preco": float(preco_valor),
        "link": url,
        "imagem": imagem["content"] if imagem else None
    }



# --------------------------------------------------
# SALVA PRODUTO + HISTÓRICO
# --------------------------------------------------
def salvar_produto(produto):
    conn = conectar()
    cursor = conn.cursor()
    criar_tabelas()

    cursor.execute("""
        INSERT OR IGNORE INTO produtos (nome, link)
        VALUES (?, ?)
    """, (produto["nome"], produto["link"]))

    cursor.execute("""
        SELECT id FROM produtos WHERE link = ?
    """, (produto["link"],))
    produto_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO historico_precos (produto_id, preco)
        VALUES (?, ?)
    """, (produto_id, produto["preco"]))

    conn.commit()
    conn.close()
    return produto_id


# --------------------------------------------------
# EXECUÇÃO PRINCIPAL
# --------------------------------------------------
# --------------------------------------------------
# EXECUÇÃO PRINCIPAL
# --------------------------------------------------
if __name__ == "__main__":

    PRODUTOS = carregar_produtos()

# 🔥 Embaralha lista inteira a cada ciclo
    random.shuffle(PRODUTOS)

# 🎯 Limite por ciclo (máquina fraca)
    limite_por_ciclo = 80

    PRODUTOS = PRODUTOS[:limite_por_ciclo]

    print(f"🔎 {len(PRODUTOS)} produtos selecionados para este ciclo.")

    driver_amazon = iniciar_driver()
    driver_ml = iniciar_driver()


    falhas_consecutivas = 0
    falhas_total = 0
    sucessos_total = 0
    contador_produtos = 0

    for item in PRODUTOS:
        contador_produtos += 1

        if contador_produtos % 20 == 0:
            print("♻ Reiniciando drivers preventivamente")

        try:
            driver_ml.quit()
        except:
            pass

        try:
            driver_amazon.quit()
        except:
            pass

        driver_amazon = iniciar_driver()
        driver_ml = iniciar_driver()

        # 🔥 CAMADA 3 — simular navegação humana
        print("🌎 Aquecendo sessão Amazon...")
        driver_amazon.get("https://www.amazon.com.br/")
        time.sleep(random.uniform(4, 7))


        try:
            categoria = item["categoria"]
            url = item["url"]

            print(f"\nVerificando {categoria}")

            marketplace = identificar_marketplace(url)

            if marketplace == "mercadolivre":
                try:
                    produto = coletar_produto_ml_selenium(url, driver_ml)
                except Exception as e:
                    print("💥 Crash ML — reiniciando driver")
                    try:
                        driver_ml.quit()
                    except:
                        pass
                    driver_ml = iniciar_driver()
                    continue
            elif marketplace == "amazon":
                produto = coletar_produto_amazon_selenium(url, driver_amazon)


            elif marketplace == "magalu":
                produto = coletar_produto_magalu(url)

            else:
                print("Marketplace não suportado")
                continue

        except Exception as e:
            print(f"Erro geral no produto {item.get('categoria')} → {e}")
            falhas_consecutivas += 1
            falhas_total += 1
            continue

        # -----------------------------
        # FALHA DE COLETA
        # -----------------------------
        if not produto:
            print(f"Falha ao coletar produto: {categoria}")

            falhas_consecutivas += 1
            falhas_total += 1

            if falhas_consecutivas >= 8:
                pausa = random.uniform(180, 300)
                print(f"🚨 Muitas falhas consecutivas — pausando {round(pausa/60,1)} minutos")
                time.sleep(pausa)
                falhas_consecutivas = 0

            continue

        # Reset falhas se coletou com sucesso
        falhas_consecutivas = 0

        # -----------------------------
        # SALVA NO BANCO
        # -----------------------------
        link_canonico = produto["link"]
        produto["link"] = link_canonico

        try:
            produto_id = salvar_produto(produto)
        except Exception as e:
            print(f"Erro ao salvar no banco: {e}")
            continue

        produto["id"] = produto_id
        produto["categoria"] = categoria

        # -----------------------------
        # LINK AFILIADO
        # -----------------------------
        if marketplace == "mercadolivre":
            produto["link"] = gerar_link_afiliado(link_canonico)

        elif marketplace == "amazon":
            produto["link"] = gerar_link_afiliado_amazon(link_canonico)

        elif marketplace == "magalu":
            produto["link"] = gerar_link_afiliado_magalu(link_canonico)

        produto_regra = produto.copy()
        produto_regra["link"] = link_canonico

        # -----------------------------
        # REGRAS DE PROMOÇÃO
        preco_anterior = obter_preco_anterior(produto_regra)

        if preco_anterior:
            variacao = abs(produto["preco"] - preco_anterior) / preco_anterior

            if variacao > 0.60:  # maior que 60%
                print("⚠ Variação suspeita — ignorando")
                continue
        if not verificar_promocao(produto_regra):
            print(f"{produto['nome']} → Preço normal")
            continue

        if promocao_ja_postada(produto, produto["preco"]):
            if not pode_repostar(produto, horas=6):
                print(f"{produto['nome']} → Promoção recente, ignorando")
                continue
            else:
                print(f"{produto['nome']} → Repostando após cooldown")
        if not preco_anterior:
            print("Sem histórico suficiente — ignorando")
            continue

        preco_anterior = obter_preco_anterior(produto_regra)
        # -----------------------------------------
        # 🔒 Filtro anti-histórico distorcido
        # -----------------------------------------

        if preco_anterior:

            if preco_anterior > produto["preco"] * 3:
                print("Histórico distorcido detectado — ignorando")
                continue

        # -----------------------------------------
        # 🔒 FILTRO 3 — Desconto suspeito
        # -----------------------------------------
        desconto = (preco_anterior - produto["preco"]) / preco_anterior

        if desconto > 0.80:
            print("Desconto suspeito (>80%) — ignorando")
            continue

        if preco_anterior is None:
            print(f"{produto['nome']} → Sem histórico suficiente")
            continue

        eh_preco_historico = preco_historico(produto_regra)

        if eh_preco_historico:
            print(f"{produto['nome']} → 🔥 PREÇO HISTÓRICO")
        else:
            print(f"{produto['nome']} → Promoção normal")

        # -----------------------------
        # MÉTRICAS
        # -----------------------------
        try:
            registrar_promocao(produto, preco_anterior)
            sucessos_total += 1
        except Exception as e:
            print(f"Erro ao registrar métrica: {e}")

        # -----------------------------
        # ENVIO TELEGRAM
        # -----------------------------
        texto = gerar_texto_oferta(
            produto,
            preco_anterior,
            preco_historico=eh_preco_historico
        )

        try:
            if produto.get("imagem"):
                enviar_telegram_foto_com_texto(texto, produto["imagem"])
            else:
                enviar_telegram(texto)
        except Exception as e:
            print(f"Erro ao enviar Telegram: {e}")

        # Delay humano entre produtos
        time.sleep(random.uniform(6, 12))

        # -----------------------------
        # PAUSA PREVENTIVA A CADA 40
        # -----------------------------
        if contador_produtos % random.randint(35, 50) == 0:
            pausa = random.uniform(120, 240)
            print(f"⏸ Pausa estratégica após {contador_produtos} produtos — {round(pausa/60,1)} min")
            time.sleep(pausa)

    # -----------------------------
    # ANÁLISE FINAL DO CICLO
    # -----------------------------
    if contador_produtos > 0:
        taxa_sucesso = sucessos_total / contador_produtos
        print(f"\n📊 Taxa de sucesso do ciclo: {round(taxa_sucesso*100,1)}%")

        if taxa_sucesso < 0.5:
            pausa = random.uniform(300, 600)
            print("📉 Sistema instável — pausa longa")
            time.sleep(pausa)

        elif taxa_sucesso > 0.8:
            print("🚀 Sistema saudável — desempenho ideal")
    
    driver_amazon.quit()
    driver_ml.quit()

    print("\n✅ Ciclo finalizado com estabilidade.")