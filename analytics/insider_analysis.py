from __future__ import annotations

from collections import Counter

from data_sources.insider_client import InsiderTransaction


BUY_CODES = {"P", "BUY", "PURCHASE"}
SELL_CODES = {"S", "SALE", "SELL"}
OPTION_CODES = {"M", "OPTION", "EXERCISE"}
GIFT_CODES = {"G", "GIFT"}


def classify_insider_transaction(transaction: InsiderTransaction) -> str:
    code = transaction.transaction_type.strip().upper()
    if code in BUY_CODES:
        return "open_market_buy"
    if code in SELL_CODES:
        return "sale_10b5_1" if transaction.is_10b5_1 else "sale"
    if code in OPTION_CODES:
        return "option_exercise"
    if code in GIFT_CODES:
        return "gift"
    return "other"


def detect_cluster_buying(transactions: list[InsiderTransaction], minimum_buyers: int = 2) -> bool:
    buyers = {tx.insider_name for tx in transactions if classify_insider_transaction(tx) == "open_market_buy"}
    return len(buyers) >= minimum_buyers


def detect_unusual_selling(transactions: list[InsiderTransaction], share_threshold: float) -> bool:
    sale_shares = sum(tx.shares for tx in transactions if classify_insider_transaction(tx).startswith("sale"))
    return sale_shares >= share_threshold


def summarize_insider_activity(transactions: list[InsiderTransaction]) -> dict[str, int]:
    counter = Counter(classify_insider_transaction(tx) for tx in transactions)
    return dict(counter)

