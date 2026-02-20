from urllib.parse import urlparse


def limpar_link_mercadolivre(link: str) -> str:
    if "/p/" in link:
        return link.split("?")[0]
    return link


def limpar_link_amazon(link: str) -> str:
    if "/dp/" in link:
        asin = link.split("/dp/")[1].split("/")[0]
        return f"https://www.amazon.com.br/dp/{asin}"
    return link


def limpar_link_magalu(link: str) -> str:
    return link.split("?")[0]


def limpar_link(link: str, marketplace: str) -> str:
    if marketplace == "mercadolivre":
        return limpar_link_mercadolivre(link)

    elif marketplace == "amazon":
        return limpar_link_amazon(link)

    elif marketplace == "magalu":
        return limpar_link_magalu(link)

    return link
