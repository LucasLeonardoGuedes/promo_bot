"""Placeholder de validação V2."""

from src.models import ValidationResult
from src.validator.amazon import validate_amazon_snapshot
from src.validator.ml import validate_ml_snapshot


def validate_snapshot(snapshot):
    if snapshot.marketplace == "mercadolivre":
        return validate_ml_snapshot(snapshot)
    if snapshot.marketplace == "amazon":
        return validate_amazon_snapshot(snapshot)

    preco = snapshot.preco
    if preco is None:
        return ValidationResult(
            is_valid=False,
            reason="preco ausente",
            normalized_price=None,
            status="INVALID",
        )

    if preco <= 0:
        return ValidationResult(
            is_valid=False,
            reason="preco <= 0",
            normalized_price=preco,
            status="INVALID",
        )

    if preco >= 50000:
        return ValidationResult(
            is_valid=False,
            reason="preco >= 50000",
            normalized_price=preco,
            status="INVALID",
        )

    return ValidationResult(
        is_valid=True,
        reason="ok",
        normalized_price=preco,
        status="VALID",
    )
