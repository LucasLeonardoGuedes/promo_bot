import csv
import random
import time
from datetime import datetime, timedelta
from scraper.selenium_busca import iniciar_driver

from scraper.selenium_busca import (
    buscar_mercadolivre_selenium,
    buscar_amazon_selenium
)

# -------------------------------------------------
# CONTROLE DE COOLDOWN POR MARKETPLACE
# -------------------------------------------------
falhas_marketplace = {
    "mercadolivre": 0,
    "amazon": 0
}

cooldown_ate = {
    "mercadolivre": None,
    "amazon": None
}

# -------------------------------------------------
# VERIFICA SE PODE EXECUTAR MARKETPLACE
# -------------------------------------------------
def pode_executar(marketplace):
    agora = datetime.now()

    if cooldown_ate[marketplace] is None:
        return True

    if agora >= cooldown_ate[marketplace]:
        print(f"🔓 Cooldown encerrado para {marketplace}")
        falhas_marketplace[marketplace] = 0
        cooldown_ate[marketplace] = None
        return True

    print(f"⏸ {marketplace} em cooldown até {cooldown_ate[marketplace].strftime('%H:%M:%S')}")
    return False


# -------------------------------------------------
# REGISTRA FALHA
# -------------------------------------------------
def registrar_falha(marketplace):
    falhas_marketplace[marketplace] += 1

    print(f"⚠ Falha {marketplace}: {falhas_marketplace[marketplace]}")

    if falhas_marketplace[marketplace] >= 3:
        cooldown_ate[marketplace] = datetime.now() + timedelta(minutes=30)
        print(f"🚨 {marketplace} entrou em cooldown por 30 minutos")


# -------------------------------------------------
# CARREGAR LISTA DE BUSCA (60/30/10)
# -------------------------------------------------
def carregar_lista_busca():
    grupos = {
        "baixo": [],
        "medio": [],
        "alto": []
    }

    with open("config/lista_busca.txt", encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue

            try:
                grupo, termo = linha.split(";")
                grupo = grupo.strip().lower()
                termo = termo.strip()

                if grupo in grupos:
                    grupos[grupo].append(termo)

            except ValueError:
                continue

    return grupos


# -------------------------------------------------
# SALVAR NO CSV (ANTI-DUPLICAÇÃO + LIMITE)
# -------------------------------------------------
def salvar_no_csv(nome_base, links, limite_total=800):
    arquivo = "config/produtos.csv"

    existentes = set()

    try:
        with open(arquivo, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # pula header
            for row in reader:
                if len(row) >= 2:
                    existentes.add(row[1])
    except FileNotFoundError:
        pass

    novos = []

    for link in links:
        if link not in existentes:
            novos.append([nome_base, link])

    total_atual = len(existentes)
    espaco_restante = limite_total - total_atual

    if espaco_restante <= 0:
        print("⚠ Limite máximo de produtos atingido.")
        return

    novos = novos[:espaco_restante]

    if not novos:
        print("🔁 Nenhum produto novo para adicionar.")
        return

    with open(arquivo, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(novos)

    print(f"✅ {len(novos)} novos produtos adicionados ao CSV")


# -------------------------------------------------
# EXECUÇÃO PRINCIPAL
# -------------------------------------------------
if __name__ == "__main__":

    # 🔒 Controle de horário
    agora = datetime.now().hour
    if agora < 7 or agora > 23:
        print("⛔ Fora do horário operacional (07h–23h)")
        exit()

    grupos = carregar_lista_busca()

    # 🎯 Rotação 60/30/10
    total_por_ciclo = 3

    qtd_baixo = int(total_por_ciclo * 0.6)
    qtd_medio = int(total_por_ciclo * 0.3)
    qtd_alto = total_por_ciclo - qtd_baixo - qtd_medio

    termos_escolhidos = []

    if grupos["baixo"]:
        termos_escolhidos += random.sample(
            grupos["baixo"],
            min(qtd_baixo, len(grupos["baixo"]))
        )

    if grupos["medio"]:
        termos_escolhidos += random.sample(
            grupos["medio"],
            min(qtd_medio, len(grupos["medio"]))
        )

    if grupos["alto"]:
        termos_escolhidos += random.sample(
            grupos["alto"],
            min(qtd_alto, len(grupos["alto"]))
        )

    random.shuffle(termos_escolhidos)

    driver_ml = None
    driver_amz = None

    try:
        # 🔥 Driver persistente (aberto uma vez só)
        driver_ml = iniciar_driver()
        driver_amz = iniciar_driver()

        driver_ml.get("https://www.google.com")
        driver_amz.get("https://www.google.com")
        time.sleep(2)

        # --------------------------------------------------
        # LOOP DE BUSCA
        # -------------------------------------------------- 
        for termo in termos_escolhidos:

            print(f"\n🔎 Buscando: {termo}")

            ml_links = []
            amz_links = []

            marketplaces = ["mercadolivre", "amazon"]
            random.shuffle(marketplaces)

            for marketplace in marketplaces:

                if not pode_executar(marketplace):
                    continue

                # 🎲 Limite variável
                if marketplace == "mercadolivre":
                    limite = random.randint(6, 8)
                else:
                    limite = random.randint(5,7)

                try:
                    if marketplace == "mercadolivre":
                        print(f"🔎 ML (limite {limite})")
                        ml_links = buscar_mercadolivre_selenium(driver_ml, termo, limite=limite)
                        falhas_marketplace["mercadolivre"] = 0

                    elif marketplace == "amazon":
                        print(f"🔎 Amazon (limite {limite})")
                        amz_links = buscar_amazon_selenium(driver_amz, termo, limite=limite)
                        falhas_marketplace["amazon"] = 0

                except Exception as e:
                    print(f"Erro {marketplace}:", e)
                    registrar_falha(marketplace)

            print(f"ML encontrados: {len(ml_links)}")
            print(f"Amazon encontrados: {len(amz_links)}")

            todos_links = ml_links + amz_links
            salvar_no_csv(termo, todos_links)

            # 🔥 Delay adaptativo
            total_encontrados = len(todos_links)

            if total_encontrados == 0:
                delay = random.uniform(70, 110)
                print("⚠ Nenhum produto encontrado — delay maior")
            elif total_encontrados < 5:
                delay = random.uniform(45, 75)
            else:
                delay = random.uniform(30, 55)

            print(f"⏳ Aguardando {round(delay,1)} segundos...")
            time.sleep(delay)

        print("🚀 Ciclo finalizado.")

    finally:
        # 🔥 Fecha drivers no final do ciclo
        if driver_ml:
            driver_ml.quit()

        if driver_amz:
            driver_amz.quit()

