from src.models import ValidationResult


def _preco_basico_valido(preco):
    return preco is not None and preco > 0 and preco < 50000


def validate_amazon_snapshot(snapshot):
    flags = snapshot.scraper_flags or {}
    texto = (snapshot.raw_text or "").lower()

    termos_indisponivel = [
        "currently unavailable",
        "indisponível",
        "indisponivel",
        "temporarily out of stock",
        "out of stock",
    ]
    if any(t in texto for t in termos_indisponivel) or flags.get("encontrou_indisponivel_texto"):
        return ValidationResult(
            is_valid=False,
            reason="produto indisponivel",
            normalized_price=snapshot.preco,
            status="INVALID",
        )

    preco_principal = flags.get("preco_principal")
    confianca = flags.get("confianca_preco_principal", 0.0)
    preco_alternativo = flags.get("preco_alternativo")

    # Se não há confiança no preço principal, bloquear para evitar preço de bloco errado.
    if preco_principal is None or confianca < 0.8:
        return ValidationResult(
            is_valid=False,
            reason="PRICE_UNCERTAIN",
            normalized_price=preco_principal,
            status="INVALID",
        )

    if not _preco_basico_valido(preco_principal):
        return ValidationResult(
            is_valid=False,
            reason="preco principal fora da faixa valida",
            normalized_price=preco_principal,
            status="INVALID",
        )

    if preco_alternativo is not None and preco_alternativo > preco_principal * 2.5:
        return ValidationResult(
            is_valid=False,
            reason="PRICE_UNCERTAIN",
            normalized_price=preco_principal,
            status="INVALID",
        )

    if not flags.get("encontrou_sinal_compra", False):
        return ValidationResult(
            is_valid=False,
            reason="sem sinal de compra",
            normalized_price=preco_principal,
            status="INVALID",
        )

    return ValidationResult(
        is_valid=True,
        reason="amazon valido: preco principal confiavel",
        normalized_price=preco_principal,
        status="VALID",
    )

