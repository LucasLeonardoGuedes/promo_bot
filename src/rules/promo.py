from dataclasses import dataclass
from typing import Optional

from src.storage import connect_db


@dataclass
class PromoDecision:
    status: str
    reason: str
    baseline_price: Optional[float] = None
    baseline_source: Optional[str] = None
    drop_pct: Optional[float] = None


def _round_price(value, decimals=2):
    return round(float(value), decimals)


def _within_tolerance_pct(a, b, tolerance_pct=0.5):
    if a is None or b is None:
        return False
    a2 = _round_price(a, 2)
    b2 = _round_price(b, 2)
    base = max(abs(b2), 0.01)
    diff_pct = abs(a2 - b2) / base * 100
    return diff_pct <= tolerance_pct


def _get_produto_id(conn, link):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id FROM produtos WHERE link = ?
        """,
        (link,),
    )
    row = cur.fetchone()
    return row[0] if row else None


def _get_recent_valid_prices(conn, produto_id, n=5):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT preco
        FROM historico_precos
        WHERE produto_id = ?
        ORDER BY data_coleta DESC
        LIMIT ?
        """,
        (produto_id, n),
    )
    return [float(r[0]) for r in cur.fetchall() if r[0] is not None]


def _has_double_confirmation(conn, produto_id, current_price, tolerance_pct=0.5):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT preco
        FROM price_checks
        WHERE produto_id = ?
          AND status_validacao = 'SUSPECT'
          AND preco IS NOT NULL
        ORDER BY data_coleta DESC
        LIMIT 1
        """,
        (produto_id,),
    )
    row = cur.fetchone()
    if not row:
        return False
    previous_suspect_price = float(row[0])
    return _within_tolerance_pct(current_price, previous_suspect_price, tolerance_pct=tolerance_pct)


def apply_promo_rules(
    snapshot,
    validation,
    min_drop_pct=10.0,
    outlier_drop_pct=45.0,
    dedupe_tolerance_pct=0.5,
    baseline_n=5,
):
    if validation.status != "VALID":
        return PromoDecision(
            status="SKIP",
            reason="validacao nao-VALID",
        )

    if snapshot.preco is None:
        return PromoDecision(
            status="SKIP",
            reason="sem preco no snapshot",
        )

    conn = connect_db()
    try:
        produto_id = _get_produto_id(conn, snapshot.link)
        if not produto_id:
            return PromoDecision(
                status="NO_BASELINE",
                reason="produto sem historico valido",
            )

        history = _get_recent_valid_prices(conn, produto_id, n=baseline_n)
        if not history:
            return PromoDecision(
                status="NO_BASELINE",
                reason="sem precos validos no historico",
            )

        last_valid = history[0]
        avg_valid = sum(history) / len(history)

        baseline_price = last_valid if last_valid is not None else avg_valid
        baseline_source = "last_valid" if last_valid is not None else f"avg_last_{len(history)}"

        if _within_tolerance_pct(snapshot.preco, baseline_price, tolerance_pct=dedupe_tolerance_pct):
            return PromoDecision(
                status="DEDUPE",
                reason="preco equivalente ao baseline dentro da tolerancia",
                baseline_price=baseline_price,
                baseline_source=baseline_source,
                drop_pct=0.0,
            )

        drop_pct = ((baseline_price - snapshot.preco) / baseline_price) * 100

        if drop_pct < min_drop_pct:
            return PromoDecision(
                status="NO_PROMO",
                reason="queda abaixo do minimo",
                baseline_price=baseline_price,
                baseline_source=baseline_source,
                drop_pct=round(drop_pct, 2),
            )

        if drop_pct > outlier_drop_pct:
            if _has_double_confirmation(
                conn,
                produto_id,
                snapshot.preco,
                tolerance_pct=dedupe_tolerance_pct,
            ):
                return PromoDecision(
                    status="PROMO",
                    reason="outlier confirmado em dupla coleta",
                    baseline_price=baseline_price,
                    baseline_source=baseline_source,
                    drop_pct=round(drop_pct, 2),
                )

            return PromoDecision(
                status="SUSPECT",
                reason="OUTLIER_GUARD: queda > 45% sem confirmacao dupla",
                baseline_price=baseline_price,
                baseline_source=baseline_source,
                drop_pct=round(drop_pct, 2),
            )

        return PromoDecision(
            status="PROMO",
            reason="queda valida conforme regra de promocao",
            baseline_price=baseline_price,
            baseline_source=baseline_source,
            drop_pct=round(drop_pct, 2),
        )
    finally:
        conn.close()

