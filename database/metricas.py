from database.db import conectar


def registrar_promocao(produto, preco_anterior, conn=None):
    """
    Registra evento de promoção na tabela metricas_promocoes.
    Usa produto_id para integridade de dados.
    """

    if not produto or "id" not in produto:
        print("Erro: produto inválido para registrar métrica.")
        return False

    produto_id = produto["id"]
    nome = produto.get("nome")
    categoria = produto.get("categoria")
    preco_atual = produto.get("preco")

    # -----------------------------
    # Cálculo seguro de desconto
    # -----------------------------
    if not preco_anterior or preco_anterior == 0:
        desconto = 0
    else:
        desconto = ((preco_anterior - preco_atual) / preco_anterior) * 100

    desconto = round(desconto, 2)

    # -----------------------------
    # Conexão reutilizável
    # -----------------------------
    fechar_conexao = False

    if conn is None:
        conn = conectar()
        fechar_conexao = True

    try:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO metricas_promocoes
            (produto_id, produto_nome, categoria,
             preco_anterior, preco_atual, desconto)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            produto_id,
            nome,
            categoria,
            preco_anterior,
            preco_atual,
            desconto
        ))

        conn.commit()
        return True

    except Exception as e:
        print(f"Erro ao registrar promoção: {e}")
        return False

    finally:
        if fechar_conexao:
            conn.close()