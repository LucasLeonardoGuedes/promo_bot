import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "produtos.db"

def conectar():
    return sqlite3.connect(DB_PATH)

def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        link TEXT UNIQUE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historico_precos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto_id INTEGER,
        preco REAL,
        data_coleta DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (produto_id) REFERENCES produtos(id)
    )
    """)
    cursor.execute("""
CREATE TABLE IF NOT EXISTS metricas_promocoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_nome TEXT,
    categoria TEXT,
    preco_anterior REAL,
    preco_atual REAL,
    desconto REAL,
    data_evento DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")


    conn.commit()
    conn.close()


# Teste rápido
if __name__ == "__main__":
    criar_tabelas()
    print("Banco criado com sucesso")
