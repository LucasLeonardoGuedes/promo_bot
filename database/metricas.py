from database.db import conectar

def registrar_promocao(produto, preco_anterior):
    preco_atual = produto["preco"]
    # 🚨 trava de segurança
    if preco_anterior is None:
        desconto = 0
    else:
        desconto = ((preco_anterior - preco_atual) / preco_anterior) * 100

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO metricas_promocoes
        (produto_nome, categoria, preco_anterior, preco_atual, desconto)
        VALUES (?, ?, ?, ?, ?)
    """, (
        produto["nome"],
        produto["categoria"],
        preco_anterior,
        preco_atual,
        round(desconto, 2)
    ))

    conn.commit()
    conn.close()
