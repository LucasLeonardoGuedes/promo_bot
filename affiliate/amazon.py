def gerar_link_afiliado_amazon(url):
    tag = "radartech0b-20"
    if "tag=" in url:
        return url
    separador = "&" if "?" in url else "?"
    return f"{url}{separador}tag={tag}"
