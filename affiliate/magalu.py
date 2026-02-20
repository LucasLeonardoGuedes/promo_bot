from urllib.parse import urlparse

MAGALU_STORE = "magazineradart3ch"

def gerar_link_afiliado_magalu(url):
    parsed = urlparse(url)

    # pega só o caminho do produto
    caminho_produto = parsed.path

    return f"https://www.magazinevoce.com.br/{MAGALU_STORE}{caminho_produto}"
