from urllib.parse import urlparse, urlunparse




def limpar_link_mercadolivre(link: str) -> str:
    """
    Remove parâmetros de tracking do Mercado Livre.
    Mantém apenas a URL base.
    """
    if not link:
        return link

    parsed = urlparse(link)

   
    clean = parsed._replace(query="")
    return urlunparse(clean)




def limpar_link_amazon(link: str) -> str:
    """
    Extrai ASIN corretamente e gera link limpo:
    https://www.amazon.com.br/dp/ASIN
    """
    if not link:
        return link

    parsed = urlparse(link)

    # procura padrão /dp/ASIN
    if "/dp/" in parsed.path:
        try:
            asin = parsed.path.split("/dp/")[1].split("/")[0]
            return f"https://www.amazon.com.br/dp/{asin}"
        except:
            return link

    # fallback: remove parâmetros
    clean = parsed._replace(query="")
    return urlunparse(clean)




def limpar_link_magalu(link: str) -> str:
    """
    Remove parâmetros da URL do Magalu.
    """
    if not link:
        return link

    parsed = urlparse(link)
    clean = parsed._replace(query="")
    return urlunparse(clean)




def limpar_link(link: str, marketplace: str) -> str:
    """
    Aplica limpeza conforme marketplace.
    """
    if not link or not isinstance(link, str):
        return link

    marketplace = marketplace.lower()

    if marketplace == "mercadolivre":
        return limpar_link_mercadolivre(link)

    elif marketplace == "amazon":
        return limpar_link_amazon(link)

    elif marketplace == "magalu":
        return limpar_link_magalu(link)

    return link