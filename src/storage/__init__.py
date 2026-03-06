import json
import sqlite3
from pathlib import Path
from typing import Optional

from database.db import criar_tabelas

DB_PATH = Path(__file__).resolve().parents[2] / "database" / "produtos.db"


def connect_db():
    return sqlite3.connect(DB_PATH)


def _get_or_create_produto_id(conn, snapshot) -> int:
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR IGNORE INTO produtos (nome, link)
        VALUES (?, ?)
        """,
        (snapshot.nome, snapshot.link),
    )
    cursor.execute(
        """
        SELECT id FROM produtos WHERE link = ?
        """,
        (snapshot.link,),
    )
    row = cursor.fetchone()
    return row[0]


def save_check_and_maybe_history(snapshot, validation, raw_meta: Optional[dict] = None):
    criar_tabelas()

    conn = connect_db()
    cursor = conn.cursor()

    try:
        produto_id = _get_or_create_produto_id(conn, snapshot)

        cursor.execute(
            """
            INSERT INTO price_checks (
                produto_id,
                marketplace,
                preco,
                disponivel,
                status_validacao,
                motivo_validacao,
                raw_meta_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                produto_id,
                snapshot.marketplace,
                snapshot.preco,
                1 if snapshot.disponivel else 0,
                validation.status,
                validation.reason,
                json.dumps(raw_meta or {}, ensure_ascii=False),
            ),
        )

        historico_inserido = False
        if validation.status == "VALID":
            cursor.execute(
                """
                INSERT INTO historico_precos (produto_id, preco)
                VALUES (?, ?)
                """,
                (produto_id, validation.normalized_price),
            )
            historico_inserido = True

        conn.commit()
        return {
            "produto_id": produto_id,
            "status_validacao": validation.status,
            "historico_inserido": historico_inserido,
        }
    finally:
        conn.close()
