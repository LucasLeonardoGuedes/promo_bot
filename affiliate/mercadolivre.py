from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

TRACKING_ID = "8c17cb98-d081-4d2c-a41a-99de065a7177"  

def gerar_link_afiliado(url_produto):
    parsed = urlparse(url_produto)
    query = parse_qs(parsed.query)

    
    query["tracking_id"] = [TRACKING_ID]

    nova_query = urlencode(query, doseq=True)

    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        nova_query,
        parsed.fragment
    ))


