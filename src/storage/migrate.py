import sqlite3
from pathlib import Path

from database.db import criar_tabelas

DB_PATH = Path(__file__).resolve().parents[2] / "database" / "produtos.db"


def migrate():
    criar_tabelas()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS price_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            data_coleta DATETIME DEFAULT CURRENT_TIMESTAMP,
            marketplace TEXT,
            preco REAL,
            disponivel INTEGER,
            status_validacao TEXT,
            motivo_validacao TEXT,
            raw_meta_json TEXT,
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_price_checks_produto_data
        ON price_checks(produto_id, data_coleta DESC)
        """
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    migrate()
    print("Migration OK: price_checks")

