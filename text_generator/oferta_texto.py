def gerar_texto_oferta(produto, preco_anterior, preco_historico=False):

    
    nome = produto["nome"]
    preco_atual = produto["preco"]
    link = produto["link"]

    if produto.get("preco_antigo"):
        preco_anterior = produto["preco_antigo"]
    desconto_percentual = int(
        ((preco_anterior - preco_atual) / preco_anterior) * 100
    )

    selo = "🔥 PREÇO HISTÓRICO\n\n" if preco_historico else ""

    texto = f"""{selo}🔥 OFERTA NO RADAR


🖱 {nome}

💸 De R$ {preco_anterior:.2f}
🔥 Por R$ {preco_atual:.2f}
📉 {desconto_percentual}% OFF

🧾 Desconto aplicado automaticamente

🛒 Mercado Livre
🔗 {link}

⏰ Monitorado pelo Radar Tech
"""
    
    

    return texto


