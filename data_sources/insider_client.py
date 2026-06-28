from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class InsiderTransaction:
    symbol: str
    insider_name: str
    transaction_date: str
    transaction_type: str
    shares: float
    price: float | None = None
    is_10b5_1: bool = False


def normalize_insider_transactions(symbol: str, rows: list[dict[str, Any]]) -> list[InsiderTransaction]:
    transactions: list[InsiderTransaction] = []
    for row in rows:
        shares = float(row.get("securitiesTransacted") or row.get("shares") or row.get("transactionShares") or 0)
        price_value = row.get("price") or row.get("transactionPrice")
        price = float(price_value) if price_value not in {None, ""} else None
        transactions.append(
            InsiderTransaction(
                symbol=symbol.upper(),
                insider_name=str(row.get("reportingName") or row.get("insiderName") or ""),
                transaction_date=str(row.get("transactionDate") or row.get("date") or ""),
                transaction_type=str(row.get("transactionType") or row.get("type") or ""),
                shares=shares,
                price=price,
                is_10b5_1=bool(row.get("is10b5_1") or row.get("tenBFiveOne")),
            )
        )
    return transactions

