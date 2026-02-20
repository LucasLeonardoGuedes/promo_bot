from urllib import response
import requests
from bs4 import BeautifulSoup
import time
import random


from webdriver_manager import drivers

def coletar_produto_amazon(url):
    time.sleep(random.uniform(2.5, 4.5))
    headers = {
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (X11; Linux x86_64)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        ]),
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print("Amazon: status diferente de 200")
            return None
    except Exception as e:
        print(f"Amazon: erro de conexão {e}")
        return None

    soup = BeautifulSoup(response.text, "lxml")

    # 🔹 Nome
    nome = soup.select_one("#productTitle")
    if not nome:
        print("Amazon: nome não encontrado (possível bloqueio)")
        return None

    nome_produto = nome.text.strip()

    # 🔹 Preço (Amazon tem vários formatos)
    preco = None

    seletores_preco = [
        "span.a-price span.a-offscreen",
        "#priceblock_ourprice",
        "#priceblock_dealprice",
        "#priceblock_saleprice"
    ]

    for seletor in seletores_preco:
        tag = soup.select_one(seletor)
        if tag:
            preco_texto = tag.text.strip()
            preco = preco_texto.replace("R$", "").replace(".", "").replace(",", ".")
            try:
                preco = float(preco)
                break
            except:
                preco = None

    if preco is None:
        print("Amazon: preço não encontrado")
        return None

    

    # 🔹 Imagem
    imagem = soup.select_one("#landingImage")
    imagem_url = imagem["src"] if imagem else None

    

    return {
        "nome": nome_produto,
        "preco": preco,
        "link": url,
        "imagem": imagem_url
    }

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random


def coletar_produto_amazon_selenium(url, driver):
    try:
        driver.get(url)
        time.sleep(random.uniform(3, 6))

        # 🔥 Detectar bloqueio Amazon
        if "clique aqui para continuar" in driver.page_source.lower():
            print("⚠ Amazon solicitando validação humana")
            time.sleep(60)
            return None

        # pequeno scroll humano
        driver.execute_script("window.scrollBy(0, 400);")
        time.sleep(random.uniform(2, 4))

        # espera o título carregar
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "productTitle"))
        )

        nome = driver.find_element(By.ID, "productTitle").text.strip()

        # -----------------------------------------
        # PREÇO
        # -----------------------------------------
        try:
            preco = driver.find_element(By.CLASS_NAME, "a-price-whole").text
        except:
            print("Amazon: preço não encontrado")
            return None

        # -----------------------------------------
        # IMAGEM
        # -----------------------------------------
        try:
            imagem = driver.find_element(By.ID, "landingImage").get_attribute("src")
        except:
            imagem = None

        # -----------------------------------------
        # 🔒 FILTRO 1 — Disponibilidade
        # -----------------------------------------
        try:
            driver.find_element(By.ID, "add-to-cart-button")
        except:
            print("Amazon: Produto indisponível")
            return None

        # -----------------------------------------
        # 🔒 FILTRO 2 — Seller confiável (via Selenium)
        # -----------------------------------------
        seller_text = ""

        try:
            seller_element = driver.find_element(By.ID, "sellerProfileTriggerId")
            seller_text = seller_element.text.strip()
        except:
            # fallback: vendido e entregue por Amazon
            page_lower = driver.page_source.lower()
            if "vendido e entregue por amazon.com.br" in page_lower:
                seller_text = "Amazon Oficial"

        if not seller_text:
            print("Seller não identificado — produto pode ser marketplace")
        # -----------------------------
        # 🔒 VALIDAÇÃO REAL AMAZON
        # -----------------------------
        try:
            driver.find_element(By.ID, "add-to-cart-button")
        except:
            print("Amazon: Produto indisponível")
            return None

        return {
            "nome": nome,
            "preco": float(preco.replace(".", "").replace(",", "")),
            "link": url,
            "imagem": imagem
        }

    except Exception as e:
        print(f"Amazon Selenium erro: {e}")
        return None
