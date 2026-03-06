from src.models import ValidationResult


def _preco_basico_valido(preco):
    return preco is not None and preco > 0 and preco < 50000


def validate_ml_snapshot(snapshot):
    flags = snapshot.scraper_flags or {}
    indisponivel = bool(flags.get("encontrou_texto_indisponivel"))
    sinal_compra = bool(flags.get("encontrou_sinal_compra"))

    if indisponivel:
        termos = flags.get("termos_indisponibilidade_detectados") or []
        motivo = "texto de indisponibilidade detectado"
        if termos:
            motivo = f"{motivo}: {', '.join(termos)}"
        return ValidationResult(
            is_valid=False,
            reason=motivo,
            normalized_price=snapshot.preco,
            status="INVALID",
        )

    if not sinal_compra:
        return ValidationResult(
            is_valid=False,
            reason="sem sinal forte de compra",
            normalized_price=snapshot.preco,
            status="INVALID",
        )

    if not _preco_basico_valido(snapshot.preco):
        return ValidationResult(
            is_valid=False,
            reason="preco fora da faixa valida",
            normalized_price=snapshot.preco,
            status="INVALID",
        )

    preco_extraido = flags.get("preco_extraido_html")
    if preco_extraido is not None:
        diferenca = abs(float(preco_extraido) - float(snapshot.preco))
        if diferenca > 0.05:
            return ValidationResult(
                is_valid=False,
                reason="preco inconsistente entre scraper e html",
                normalized_price=snapshot.preco,
                status="INVALID",
            )

    return ValidationResult(
        is_valid=True,
        reason="ml valido: preco consistente e compravel",
        normalized_price=snapshot.preco,
        status="VALID",
    )

