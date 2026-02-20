import requests
import time
import random
from bs4 import BeautifulSoup


def coletar_produto_magalu(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9"
    }

    for tentativa in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                break
        except requests.RequestException:
            time.sleep(random.uniform(2, 4))
    else:
        return None

    soup = BeautifulSoup(r.text, "lxml")

    # Nome
    nome = soup.select_one("h1[data-testid='heading-product-title']") \
        or soup.select_one("h1")

    # Preço
    preco = soup.select_one("p[data-testid='price-value']") \
        or soup.select_one("span[data-testid='price-value']")

    # Imagem
    imagem = soup.select_one("img[data-testid='image-selected']")

    if not nome or not preco:
        return None

    nome_produto = nome.text.strip()
    preco_texto = (
        preco.text.replace("R$", "")
        .replace(".", "")
        .replace(",", ".")
        .strip()
    )

    preco_produto = float(preco_texto)
    imagem_url = imagem["src"] if imagem else None

    return {
        "nome": nome_produto,
        "preco": preco_produto,
        "link": url,
        "imagem": imagem_url,
        "marketplace": "magalu"
    }
