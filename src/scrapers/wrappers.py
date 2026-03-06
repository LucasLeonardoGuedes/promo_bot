import re
from urllib.request import Request, urlopen


def _baixar_html(url):
    try:
        req = Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        with urlopen(req, timeout=20) as response:
            return response.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _extrair_preco_texto_ml(raw_text):
    match = re.search(r"R\$\s*([\d\.]+,\d{2})", raw_text or "")
    if not match:
        return None
    preco_texto = match.group(1).replace(".", "").replace(",", ".")
    try:
        return float(preco_texto)
    except Exception:
        return None


def _extrair_primeiro_preco_brl(texto):
    match = re.search(r"R\$\s*([\d\.]+,\d{2})", texto or "")
    if not match:
        return None
    bruto = match.group(1).replace(".", "").replace(",", ".")
    try:
        return float(bruto)
    except Exception:
        return None


def _extrair_preco_amazon_principal(html):
    padroes_principais = [
        (r'id="corePrice_feature_div"[\s\S]{0,1800}?R\$\s*([\d\.]+,\d{2})', 0.95),
        (r'id="priceblock_ourprice"[\s\S]{0,300}?R\$\s*([\d\.]+,\d{2})', 0.95),
        (r'id="priceblock_dealprice"[\s\S]{0,300}?R\$\s*([\d\.]+,\d{2})', 0.95),
        (r'id="price_inside_buybox"[\s\S]{0,300}?R\$\s*([\d\.]+,\d{2})', 0.90),
        (r'class="a-price aok-align-center[^"]*"[\s\S]{0,400}?R\$\s*([\d\.]+,\d{2})', 0.80),
    ]

    for pattern, confidence in padroes_principais:
        m = re.search(pattern, html or "", flags=re.IGNORECASE)
        if not m:
            continue
        try:
            value = float(m.group(1).replace(".", "").replace(",", "."))
            return value, confidence
        except Exception:
            continue
    return None, 0.0


def _extrair_preco_amazon_alternativo(html):
    # Parcelado 
    alternativos = [
        r"(\d{1,2})x\s+de\s+R\$\s*([\d\.]+,\d{2})",
        r"R\$\s*([\d\.]+,\d{2})\s*/\s*m[êe]s",
        r"assinatura[\s\S]{0,120}?R\$\s*([\d\.]+,\d{2})",
    ]

    for pattern in alternativos:
        m = re.search(pattern, html or "", flags=re.IGNORECASE)
        if not m:
            continue
        # padrão de parcelado
        group = 2 if len(m.groups()) >= 2 else 1
        try:
            return float(m.group(group).replace(".", "").replace(",", "."))
        except Exception:
            continue
    return None


def coletar_produto_amazon_v2(url):
    html = _baixar_html(url)
    texto = (html or "").lower()

    termos_indisponivel = [
        "currently unavailable",
        "indisponível",
        "indisponivel",
        "temporarily out of stock",
        "out of stock",
    ]
    encontrou_indisponivel = any(t in texto for t in termos_indisponivel)

    sinais_disponibilidade = {
        "tem_add_to_cart_button": ("add-to-cart-button" in texto),
        "tem_buy_now_button": ("buy-now-button" in texto),
        "tem_buybox": ("buybox" in texto or "desktop_buybox" in texto),
    }
    encontrou_sinal_compra = any(sinais_disponibilidade.values())

    preco_principal, confianca = _extrair_preco_amazon_principal(html)
    preco_alternativo = _extrair_preco_amazon_alternativo(html)

    flags = {
        "preco_principal": preco_principal,
        "preco_alternativo": preco_alternativo,
        "confianca_preco_principal": confianca,
        "encontrou_indisponivel_texto": encontrou_indisponivel,
        "encontrou_sinal_compra": encontrou_sinal_compra,
        "sinais_disponibilidade": sinais_disponibilidade,
        "preco_extraido_html": _extrair_primeiro_preco_brl(html),
        "html_len": len(html),
    }

    produto = None
    try:
        from scraper.amazon_scraper import coletar_produto_amazon as _coletar_produto_amazon

        produto = _coletar_produto_amazon(url)
    except Exception:
        produto = None

    return {
        "produto": produto,
        "html": html,
        "texto": texto,
        "preco_principal": preco_principal,
        "preco_alternativo": preco_alternativo,
        "sinais_disponibilidade": sinais_disponibilidade,
        "flags": flags,
    }


def coletar_produto_ml_v2(url, driver=None):
    html = _baixar_html(url)
    texto = (html or "").lower()

    termos_indisponiveis = [
        "publicação pausada",
        "publicacao pausada",
        "produto indisponível",
        "produto indisponivel",
        "sem estoque",
        "no momento não está disponível",
        "no momento nao esta disponivel",
    ]
    detectados = [t for t in termos_indisponiveis if t in texto]

    sinais_compra = [
        "comprar agora",
        "adicionar ao carrinho",
        "quantity__available",
        "ui-pdp-buybox",
    ]
    encontrou_sinal_compra = any(s in texto for s in sinais_compra)

    preco_html = _extrair_preco_texto_ml(html)

    flags = {
        "encontrou_texto_indisponivel": len(detectados) > 0,
        "encontrou_sinal_compra": encontrou_sinal_compra,
        "termos_indisponibilidade_detectados": detectados,
        "sinais_compra_detectados": [s for s in sinais_compra if s in texto],
        "preco_extraido_html": preco_html,
        "html_len": len(html),
    }

    produto = None
    if driver is not None:
        try:
            from scraper.mercadolivre_selenium import (
                coletar_produto_ml_selenium as _coletar_produto_ml_selenium,
            )
            produto = _coletar_produto_ml_selenium(url, driver)
        except Exception:
            produto = None

    return {
        "produto": produto,
        "html": html,
        "texto": texto,
        "flags": flags,
    }


def coletar_produto_ml_selenium(url, driver):
    try:
        from scraper.mercadolivre_selenium import (
            coletar_produto_ml_selenium as _coletar_produto_ml_selenium,
        )
    except Exception:
        return None
    return _coletar_produto_ml_selenium(url, driver)


def coletar_produto_amazon(url):
    try:
        from scraper.amazon_scraper import coletar_produto_amazon as _coletar_produto_amazon
    except Exception:
        return None
    return _coletar_produto_amazon(url)


def coletar_produto_amazon_selenium(url, driver):
    try:
        from scraper.amazon_scraper import (
            coletar_produto_amazon_selenium as _coletar_produto_amazon_selenium,
        )
    except Exception:
        return None
    return _coletar_produto_amazon_selenium(url, driver)


def coletar_produto_magalu(url):
    try:
        from scraper.magalu_scraper import coletar_produto_magalu as _coletar_produto_magalu
    except Exception:
        return None
    return _coletar_produto_magalu(url)
