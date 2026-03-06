import requests
from bs4 import BeautifulSoup
import time
import random

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC




def coletar_produto_amazon(url):
    time.sleep(random.uniform(2.5, 4.5))

    headers = {
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (X11; Linux x86_64)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        ]),
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print("Amazon: status diferente de 200")
            return None
    except Exception as e:
        print(f"Amazon: erro de conexão {e}")
        return None

    # Detectar possível bloqueio
    if "captcha" in response.text.lower():
        print("Amazon: possível bloqueio detectado")
        return None

    soup = BeautifulSoup(response.text, "lxml")

    # Nome
    nome = soup.select_one("#productTitle")
    if not nome:
        print("Amazon: nome não encontrado (possível bloqueio)")
        return None

    nome_produto = nome.text.strip()

    # Preço
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
            preco = _converter_preco(preco_texto)
            if preco:
                break

    if preco is None:
        print("Amazon: preço não encontrado")
        return None

    # Imagem
    imagem = soup.select_one("#landingImage")
    imagem_url = imagem["src"] if imagem else None

    return {
        "nome": nome_produto,
        "preco": preco,
        "link": url,
        "imagem": imagem_url
    }

def coletar_produto_amazon_selenium(url, driver):
    try:
        driver.get(url)

        time.sleep(random.uniform(6, 10))
        if "validateCaptcha" in driver.page_source:
            print("🚨 Amazon bloqueou com captcha")
            return None
         
        time.sleep(random.uniform(3, 6))

        page_lower = driver.page_source.lower()

        # Detectar bloqueio
        if "clique aqui para continuar" in page_lower or "captcha" in page_lower:
            print("⚠ Amazon solicitando validação humana")
            return None

        # Scroll 
        driver.execute_script("window.scrollBy(0, 400);")
        time.sleep(random.uniform(2, 4))

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "productTitle"))
        )

        nome = driver.find_element(By.ID, "productTitle").text.strip()

        
        preco = None

        seletores = [
            "span.a-price span.a-offscreen",
            "#priceblock_dealprice",
            "#priceblock_saleprice",
            "#priceblock_ourprice"
        ]

        for seletor in seletores:
            try:
                elemento = driver.find_element(By.CSS_SELECTOR, seletor)
                preco = _converter_preco(elemento.text)
                if preco:
                    break
            except:
                continue

        
        if not preco:
            try:
                inteiro = driver.find_element(By.CLASS_NAME, "a-price-whole").text
                fracao = driver.find_element(By.CLASS_NAME, "a-price-fraction").text
                preco = float(
                    inteiro.replace(".", "") + "." + fracao
                )
            except:
                pass

        if not preco:
            print("Amazon Selenium: preço não encontrado")
            print("------ DEBUG HTML AMAZON ------")
            print(driver.page_source[:2000])
            print("------ FIM DEBUG ------")
            return None

       
        try:
            imagem = driver.find_element(By.ID, "landingImage").get_attribute("src")
        except:
            imagem = None

        
        try:
            driver.find_element(By.ID, "add-to-cart-button")
        except:
            print("Amazon: Produto indisponível")
            return None

        return {
            "nome": nome,
            "preco": preco,
            "link": url,
            "imagem": imagem
        }

    except Exception as e:
        print(f"Amazon Selenium erro: {e}")
        return None



def _converter_preco(preco_texto):
    """
    Converte preço brasileiro:
    'R$ 1.299,90' -> 1299.90
    """
    try:
        preco_texto = preco_texto.replace("R$", "").strip()
        preco_texto = preco_texto.replace(".", "").replace(",", ".")
        return float(preco_texto)
    except:
        return None
