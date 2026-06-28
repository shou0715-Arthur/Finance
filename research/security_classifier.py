from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class SecurityClassification:
    symbol: str
    security_type: str
    confidence: float
    reasons: list[str] = field(default_factory=list)


KNOWN_ETF_SYMBOLS = {"ARKK", "IEMG", "VWO", "SPY", "QQQ", "VOO", "VT", "0050", "0056", "00878", "00919"}


def normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper().replace(".TW", "").replace(".TWO", "")


def is_likely_taiwan_etf_symbol(symbol: str) -> bool:
    clean_symbol = normalize_symbol(symbol)
    return clean_symbol.isdigit() and clean_symbol.startswith("00")


def classify_security(
    symbol: str,
    name: str = "",
    metadata: Mapping[str, str] | None = None,
) -> SecurityClassification:
    clean_symbol = normalize_symbol(symbol)
    clean_name = name.strip().lower()
    metadata = metadata or {}
    declared_type = str(metadata.get("security_type") or metadata.get("type") or "").strip().lower()
    reasons: list[str] = []

    if declared_type in {"etf", "fund"}:
        return SecurityClassification(clean_symbol, "etf", 0.98, ["metadata declares ETF/fund"])
    if declared_type in {"stock", "equity"}:
        return SecurityClassification(clean_symbol, "stock", 0.98, ["metadata declares stock/equity"])

    if clean_symbol in KNOWN_ETF_SYMBOLS:
        reasons.append("known ETF symbol")
        return SecurityClassification(clean_symbol, "etf", 0.92, reasons)

    if is_likely_taiwan_etf_symbol(clean_symbol):
        reasons.append("Taiwan ETF-like numeric prefix 00")
        return SecurityClassification(clean_symbol, "etf", 0.8, reasons)

    if any(keyword in clean_name for keyword in ["etf", "基金", "指數", "高股息", "台灣50"]):
        reasons.append("name contains ETF/fund-like keyword")
        return SecurityClassification(clean_symbol, "etf", 0.72, reasons)

    if clean_symbol.isdigit() and len(clean_symbol) == 4:
        reasons.append("four-digit Taiwan equity-like symbol")
        return SecurityClassification(clean_symbol, "stock", 0.68, reasons)

    if clean_symbol:
        reasons.append("symbol present but type not identified")
        return SecurityClassification(clean_symbol, "unknown", 0.35, reasons)

    return SecurityClassification(clean_symbol, "unknown", 0.0, ["empty symbol"])

