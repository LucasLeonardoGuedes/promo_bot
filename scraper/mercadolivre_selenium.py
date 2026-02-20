from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import random


def coletar_produto_ml_selenium(url, driver):
    try:
        driver.get(url)

        time.sleep(random.uniform(3, 5))

        # pequeno scroll humano
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(random.uniform(2, 4))

        # espera título carregar
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.ui-pdp-title"))
        )

        html = driver.page_source
        soup = BeautifulSoup(html, "lxml")

        # -----------------------------
        # 🔥 NOME
        # -----------------------------
        nome_elemento = soup.select_one("h1.ui-pdp-title")
        if not nome_elemento:
            print("ML: nome não encontrado")
            return None

        nome = nome_elemento.text.strip()

        # -----------------------------
        # 🔥 PREÇO ATUAL (CORRETO)
        # -----------------------------
        preco_atual_elemento = soup.select_one(
            "div.ui-pdp-price__second-line span.andes-money-amount__fraction"
        )

        if not preco_atual_elemento:
            print("ML: preço atual não encontrado")
            return None

        preco_atual = preco_atual_elemento.text.strip().replace(".", "")

        # -----------------------------
        # 🔥 PREÇO ANTIGO (SE EXISTIR)
        # -----------------------------
        preco_antigo = None
        preco_antigo_elemento = soup.select_one(
            "s.andes-money-amount span.andes-money-amount__fraction"
        )

        if preco_antigo_elemento:
            preco_antigo = preco_antigo_elemento.text.strip().replace(".", "")

        # -----------------------------
        # 🔥 IMAGEM
        # -----------------------------
        imagem_elemento = soup.select_one(
            "figure.ui-pdp-gallery__figure img"
        )
        imagem = imagem_elemento["src"] if imagem_elemento else None

        # -----------------------------
        # 🔒 DISPONIBILIDADE
        # -----------------------------
        page_text = html.lower()

        if "produto pausado" in page_text:
            print("Produto pausado")
            return None

        if "publicação pausada" in page_text:
            print("Publicação pausada")
            return None

        if "no momento não está disponível" in page_text:
            print("Produto indisponível")
            return None
        # -----------------------------
        # 🔒 VALIDAÇÃO REAL DE COMPRA
        # -----------------------------
        try:
            driver.find_element(By.CSS_SELECTOR, "button.andes-button--loud")
        except:
            print("ML: Produto não comprável")
            return None

        return {
            "nome": nome,
            "preco": float(preco_atual),
            "preco_antigo": float(preco_antigo) if preco_antigo else None,
            "link": url,
            "imagem": imagem
        }

    except Exception as e:
        print(f"ML Selenium erro: {e}")
        return None

