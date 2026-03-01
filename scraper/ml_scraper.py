import random
import time
import requests
from bs4 import BeautifulSoup

from scraper.amazon_scraper import coletar_produto_amazon_selenium
from scraper.selenium_busca import iniciar_driver
from scraper.mercadolivre_selenium import coletar_produto_ml_selenium
from scraper.magalu_scraper import coletar_produto_magalu

from affiliate.amazon import gerar_link_afiliado_amazon
from affiliate.magalu import gerar_link_afiliado_magalu
from affiliate.mercadolivre import gerar_link_afiliado

from config.produtos import carregar_produtos, identificar_marketplace
from database.db import conectar, criar_tabelas
from database.metricas import registrar_promocao
from rules.promo_rules import PromoRules
from text_generator.oferta_texto import gerar_texto_oferta
from poster.telegram_bot import enviar_telegram_foto_com_texto, enviar_telegram
from poster.whatsapp_channel import enviar_imagem_canal, preparar_whatsapp_canal, enviar_mensagem_canal
from scraper.selenium_busca import iniciar_driver_whatsapp



if __name__ == "__main__":

    criar_tabelas()
    conn = conectar()
    rules = PromoRules(conn)

    PRODUTOS = carregar_produtos()
    random.shuffle(PRODUTOS)
    PRODUTOS = PRODUTOS[:80]

    print(f"🔎 {len(PRODUTOS)} produtos selecionados para este ciclo.")

    driver_amazon = iniciar_driver()
    driver_ml = iniciar_driver()

    driver_whatsapp = iniciar_driver_whatsapp()
    preparar_whatsapp_canal(driver_whatsapp, "Radar Tech")

    sucessos_total = 0
    contador_produtos = 0

    for item in PRODUTOS:
        contador_produtos += 1

        categoria = item["categoria"]
        url = item["url"]

        print(f"\n🔍 Verificando {categoria}")

        try:
            marketplace = identificar_marketplace(url)

            if marketplace == "mercadolivre":
                produto = coletar_produto_ml_selenium(url, driver_ml)
            elif marketplace == "amazon":
                produto = coletar_produto_amazon_selenium(url, driver_amazon)
            elif marketplace == "magalu":
                produto = coletar_produto_magalu(url)
            else:
                continue

        except Exception as e:
            print(f"💥 Erro no scraping → {e}")
            continue

        if not produto:
            print("Falha ao coletar produto")
            continue

        # 🔒 PROTEÇÃO 1 — preço absurdo
        if produto["preco"] <= 0 or produto["preco"] > 50000:
            print("⚠ Preço atual inválido — ignorando")
            continue

        # -----------------------------
        # SALVAR PRODUTO
        # -----------------------------
        try:
            cursor = conn.cursor()

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

        except Exception as e:
            print(f"Erro ao salvar no banco: {e}")
            continue

        produto["id"] = produto_id
        produto["categoria"] = categoria

        link_original = produto["link"]

        if marketplace == "mercadolivre":
            produto["link"] = gerar_link_afiliado(link_original)
        elif marketplace == "amazon":
            produto["link"] = gerar_link_afiliado_amazon(link_original)
        elif marketplace == "magalu":
            produto["link"] = gerar_link_afiliado_magalu(link_original)

        produto_regra = produto.copy()
        produto_regra["link"] = link_original

        # -----------------------------
        # REGRAS DE PROMOÇÃO
        # -----------------------------
        preco_anterior = rules.obter_preco_anterior(produto_regra)

        if not preco_anterior:
            print("Sem histórico suficiente")
            continue

        # 🔒 PROTEÇÃO 2 — histórico absurdo
        if preco_anterior <= 0 or preco_anterior > 50000:
            print("⚠ Histórico inválido — ignorando")
            continue

        # 🔒 PROTEÇÃO 3 — preço maior que anterior (não é promoção)
        if produto["preco"] >= preco_anterior:
            print("Preço maior ou igual ao anterior — ignorando")
            continue

        variacao = abs(produto["preco"] - preco_anterior) / preco_anterior
        if variacao > 0.60:
            print("⚠ Variação suspeita (>60%)")
            continue

        if not rules.verificar_promocao(produto_regra):
            print("Preço normal")
            continue

        if rules.promocao_ja_postada(produto, produto["preco"]):
            if not rules.pode_repostar(produto, horas=6):
                print("Promoção recente — ignorando")
                continue
            else:
                print("Repostando após cooldown")

        desconto = (preco_anterior - produto["preco"]) / preco_anterior

        # 🔒 PROTEÇÃO 4 — desconto absurdo
        if desconto > 0.80:
            print("Desconto suspeito (>80%)")
            continue

        eh_preco_historico = rules.preco_historico(produto_regra)

        # -----------------------------
        # MÉTRICAS
        # -----------------------------
        try:
            registrar_promocao(produto, preco_anterior, conn)
            sucessos_total += 1
        except Exception as e:
            print(f"Erro ao registrar métrica: {e}")

        # -----------------------------
        # TEXTO
        # -----------------------------
        texto = gerar_texto_oferta(
            produto,
            preco_anterior,
            preco_historico=eh_preco_historico
        )

        # -----------------------------
        # TELEGRAM
        # -----------------------------
        try:
            if produto.get("imagem"):
                enviar_telegram_foto_com_texto(texto, produto["imagem"])
            else:
                enviar_telegram(texto)
        except Exception as e:
            print(f"Erro ao enviar Telegram: {e}")

        # -----------------------------
        # WHATSAPP
        # -----------------------------
        sucesso_whatsapp = False

        if produto.get("imagem"):
            try:
                enviar_imagem_canal(driver_whatsapp, texto, produto["imagem"])
                sucesso_whatsapp = True
            except Exception as e:
                print("Erro ao enviar imagem WhatsApp:", e)
        else:
            sucesso_whatsapp = enviar_mensagem_canal(driver_whatsapp, texto)

        if not sucesso_whatsapp:
            print("⚠ Tentando re-preparar canal...")
            preparar_whatsapp_canal(driver_whatsapp, "Radar Tech")
            enviar_mensagem_canal(driver_whatsapp, texto)

        time.sleep(random.uniform(6, 12))

    print(f"\n📊 Taxa de sucesso: {round((sucessos_total / contador_produtos)*100,1)}%")

    driver_amazon.quit()
    driver_ml.quit()
    driver_whatsapp.quit()
    conn.close()

    print("\n✅ Ciclo finalizado com estabilidade.")