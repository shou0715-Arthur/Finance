from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SourceItem:
    name: str
    source_type: str
    as_of_date: str = ""
    retrieved_at: str = ""
    confidence: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SourcePacket:
    ticker: str
    items: list[SourceItem]
    missing_items: list[str] = field(default_factory=list)

    @property
    def readiness(self) -> str:
        if self.missing_items:
            return "screen-grade"
        if len(self.items) >= 3 and all(item.confidence >= 0.7 for item in self.items):
            return "decision-grade-candidate"
        return "screen-grade"


REQUIRED_PUBLIC_EQUITY_SOURCES = [
    "price_history",
    "income_statement",
    "balance_sheet",
    "cash_flow",
    "valuation_inputs",
    "consensus_or_guidance",
]


def build_source_packet(ticker: str, items: list[SourceItem]) -> SourcePacket:
    present = {item.source_type for item in items}
    missing = [source for source in REQUIRED_PUBLIC_EQUITY_SOURCES if source not in present]
    return SourcePacket(ticker=ticker.upper(), items=items, missing_items=missing)

