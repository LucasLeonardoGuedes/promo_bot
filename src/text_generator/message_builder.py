def _fmt_price(value):
    if value is None:
        return "N/A"
    return f"R$ {float(value):.2f}"


def _fmt_drop(value):
    if value is None:
        return "N/A"
    return f"{float(value):.2f}%"


def build_offer_message(snapshot, promo_decision):
    status = promo_decision.status
    prefix = "⚠️ " if status == "SUSPECT" else ""

    return (
        f"{prefix}<b>Status:</b> {status}\n"
        f"<b>Produto:</b> {snapshot.nome}\n"
        f"<b>Preço atual:</b> {_fmt_price(snapshot.preco)}\n"
        f"<b>Baseline:</b> {_fmt_price(promo_decision.baseline_price)}"
        f" ({promo_decision.baseline_source or 'N/A'})\n"
        f"<b>Queda:</b> {_fmt_drop(promo_decision.drop_pct)}\n"
        f"<b>Marketplace:</b> {snapshot.marketplace or 'desconhecido'}\n"
        f"<b>Link:</b> {snapshot.link}\n"
        f"<b>Motivo:</b> {promo_decision.reason}"
    )

