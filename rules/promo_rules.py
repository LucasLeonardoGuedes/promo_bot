from database.db import conectar
from datetime import datetime, timedelta


def verificar_promocao(produto, percentual_minimo=10):
    conn = conectar()
    cursor = conn.cursor()

    produto_id = produto["id"]

    cursor.execute("""
        SELECT preco
        FROM historico_precos
        WHERE produto_id = ?
        ORDER BY data_coleta DESC
    """, (produto_id,))

    precos = [row[0] for row in cursor.fetchall()]
    conn.close()

    if len(precos) < 2:
        return False

    preco_atual = precos[0]

    preco_anterior = None
    for p in precos[1:]:
        if p != preco_atual:
            preco_anterior = p
            break

    if not preco_anterior:
        return False

    queda_percentual = ((preco_anterior - preco_atual) / preco_anterior) * 100

    return queda_percentual >= percentual_minimo



def obter_preco_anterior(produto):
    conn = conectar()
    cursor = conn.cursor()

    produto_id = produto["id"]

    cursor.execute("""
        SELECT preco
        FROM historico_precos
        WHERE produto_id = ?
        ORDER BY data_coleta DESC
    """, (produto_id,))

    precos = [row[0] for row in cursor.fetchall()]
    conn.close()

    if len(precos) < 2:
        return None

    preco_atual = precos[0]

    for p in precos[1:]:
        if p != preco_atual:
            return p

    return None

def promocao_ja_postada(produto, preco_atual):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT preco_atual
        FROM metricas_promocoes
        WHERE produto_nome = ?
        ORDER BY data_evento DESC
        LIMIT 1
    """, (produto["nome"],))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return False  # nunca postou

    ultimo_preco_postado = row[0]

    # se o preço é IGUAL, não repostar
    return ultimo_preco_postado == preco_atual

def pode_repostar(produto, horas=6):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT data_evento
        FROM metricas_promocoes
        WHERE produto_nome = ?
        ORDER BY data_evento DESC
        LIMIT 1
    """, (produto["nome"],))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return True  # nunca postado

    ultima_data = datetime.fromisoformat(row[0])
    return datetime.now() - ultima_data >= timedelta(hours=horas)

def preco_historico(produto, minimo_registros=5):
    conn = conectar()
    cursor = conn.cursor()

    # pega ID do produto
    cursor.execute("""
        SELECT id
        FROM produtos
        WHERE link = ?
    """, (produto["link"],))

    row = cursor.fetchone()
    if not row:
        conn.close()
        return False

    produto_id = row[0]

    # pega TODOS os preços, exceto o mais recente
    cursor.execute("""
        SELECT preco
        FROM historico_precos
        WHERE produto_id = ?
        ORDER BY data_coleta DESC
    """, (produto_id,))

    precos = [p[0] for p in cursor.fetchall()]
    conn.close()

    # precisa de histórico suficiente (SEM contar o atual)
    if len(precos) - 1 < minimo_registros:
        return False

    preco_atual = precos[0]
    menor_preco_anterior = min(precos[1:])

    return preco_atual < menor_preco_anterior





