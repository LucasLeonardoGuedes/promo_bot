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

        # Scroll humano leve
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(random.uniform(2, 4))

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.ui-pdp-title"))
        )

        html = driver.page_source
        soup = BeautifulSoup(html, "lxml")

        page_lower = html.lower()

       
        bloqueios = [
            "produto pausado",
            "publicação pausada",
            "no momento não está disponível",
            "captcha"
        ]

        for termo in bloqueios:
            if termo in page_lower:
                print(f"ML bloqueio detectado: {termo}")
                return None

       
        nome_elemento = soup.select_one("h1.ui-pdp-title")
        if not nome_elemento:
            print("ML: nome não encontrado")
            return None

        nome = nome_elemento.text.strip()

       
        preco_atual = _extrair_preco_ml(soup)

        if preco_atual is None:
            print("ML: preço atual não encontrado")
            return None

        
        preco_antigo = _extrair_preco_antigo_ml(soup)

        
        imagem_elemento = soup.select_one(
            "figure.ui-pdp-gallery__figure img"
        )

        imagem = None
        if imagem_elemento:
            imagem = imagem_elemento.get("src")

        
        try:
            driver.find_element(By.CSS_SELECTOR, "button.andes-button--loud")
        except:
            print("ML: Produto não comprável")
            return None

        return {
            "nome": nome,
            "preco": preco_atual,
            "preco_antigo": preco_antigo,
            "link": url,
            "imagem": imagem
        }

    except Exception as e:
        print(f"ML Selenium erro: {e}")
        return None




def _extrair_preco_ml(soup):
    """
    Extrai preço atual corretamente.
    ML separa parte inteira e centavos.
    """

    inteiro = soup.select_one(
        "div.ui-pdp-price__second-line span.andes-money-amount__fraction"
    )

    centavos = soup.select_one(
        "div.ui-pdp-price__second-line span.andes-money-amount__cents"
    )

    if not inteiro:
        return None

    inteiro = inteiro.text.strip().replace(".", "")

    if centavos:
        preco_str = f"{inteiro}.{centavos.text.strip()}"
    else:
        preco_str = inteiro

    try:
        return float(preco_str)
    except:
        return None


def _extrair_preco_antigo_ml(soup):
    """
    Extrai preço antigo (se houver).
    """

    inteiro = soup.select_one(
        "s.andes-money-amount span.andes-money-amount__fraction"
    )

    centavos = soup.select_one(
        "s.andes-money-amount span.andes-money-amount__cents"
    )

    if not inteiro:
        return None

    inteiro = inteiro.text.strip().replace(".", "")

    if centavos:
        preco_str = f"{inteiro}.{centavos.text.strip()}"
    else:
        preco_str = inteiro

    try:
        return float(preco_str)
    except:
        return None