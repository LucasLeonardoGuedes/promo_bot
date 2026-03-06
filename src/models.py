from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ProductSnapshot:
    nome: str
    link: str
    marketplace: Optional[str]
    preco: Optional[float] = None
    imagem: Optional[str] = None
    categoria: Optional[str] = None
    disponivel: Optional[bool] = None
    raw_html: Optional[str] = None
    raw_text: Optional[str] = None
    scraper_flags: Optional[Dict[str, Any]] = None


@dataclass
class ValidationResult:
    is_valid: bool
    reason: str = ""
    normalized_price: Optional[float] = None
    status: str = "INVALID"
