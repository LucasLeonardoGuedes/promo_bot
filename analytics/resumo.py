import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "database" / "produtos.db"


def conectar():
    return sqlite3.connect(DB_PATH)


def total_produtos():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM produtos")
    total = cursor.fetchone()[0]

    conn.close()
    return total


def promocoes_hoje():
    conn = conectar()
    cursor = conn.cursor()

    hoje = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT COUNT(*) FROM metricas_promocoes
        WHERE DATE(data_evento) = ?
    """, (hoje,))

    total = cursor.fetchone()[0]
    conn.close()
    return total


def promocoes_semana():
    conn = conectar()
    cursor = conn.cursor()

    sete_dias = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT COUNT(*) FROM metricas_promocoes
        WHERE DATE(data_evento) >= ?
    """, (sete_dias,))

    total = cursor.fetchone()[0]
    conn.close()
    return total


def media_desconto():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT AVG(desconto) FROM metricas_promocoes
    """)

    resultado = cursor.fetchone()[0]
    conn.close()

    return round(resultado, 2) if resultado else 0


def precos_historicos():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM metricas_promocoes
        WHERE desconto >= 20
    """)

    total = cursor.fetchone()[0]
    conn.close()
    return total


def resumo_geral():
    print("\n📊 ===== RADAR TECH ANALYTICS =====\n")

    print(f"📦 Produtos monitorados: {total_produtos()}")
    print(f"🔥 Promoções hoje: {promocoes_hoje()}")
    print(f"📅 Promoções últimos 7 dias: {promocoes_semana()}")
    print(f"💎 Possíveis preços históricos (≥20%): {precos_historicos()}")
    print(f"📉 Média de desconto: {media_desconto()}%")

    print("\n===================================\n")


if __name__ == "__main__":
    resumo_geral()
