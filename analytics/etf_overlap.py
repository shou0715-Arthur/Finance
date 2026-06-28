from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class Holding:
    identifier: str
    name: str
    weight: float


@dataclass(frozen=True)
class ETFOverlapResult:
    common_identifiers: set[str]
    left_common_weight: float
    right_common_weight: float
    overlap_weight: float
    common_count: int


def normalize_identifier(value: str) -> str:
    return value.strip().upper()


def normalize_weight(value: Any) -> float:
    weight = float(value)
    if weight > 1:
        return weight / 100
    return weight


def make_holding(raw: Mapping[str, Any]) -> Holding:
    identifier = (
        raw.get("isin")
        or raw.get("ISIN")
        or raw.get("symbol")
        or raw.get("ticker")
        or raw.get("Ticker")
        or raw.get("name")
        or raw.get("Name")
        or ""
    )
    name = str(raw.get("name") or raw.get("Name") or identifier)
    weight = raw.get("weight") or raw.get("Weight") or raw.get("weight_pct") or raw.get("% Weight") or 0
    return Holding(identifier=normalize_identifier(str(identifier)), name=name.strip(), weight=normalize_weight(weight))


def holdings_to_weight_map(holdings: Iterable[Holding]) -> dict[str, float]:
    weights: dict[str, float] = {}
    for holding in holdings:
        if not holding.identifier:
            continue
        weights[holding.identifier] = weights.get(holding.identifier, 0.0) + holding.weight
    return weights


def calculate_holdings_overlap(left: Iterable[Holding], right: Iterable[Holding]) -> ETFOverlapResult:
    left_weights = holdings_to_weight_map(left)
    right_weights = holdings_to_weight_map(right)
    common = set(left_weights).intersection(right_weights)
    left_common_weight = sum(left_weights[key] for key in common)
    right_common_weight = sum(right_weights[key] for key in common)
    overlap_weight = sum(min(left_weights[key], right_weights[key]) for key in common)
    return ETFOverlapResult(
        common_identifiers=common,
        left_common_weight=left_common_weight,
        right_common_weight=right_common_weight,
        overlap_weight=overlap_weight,
        common_count=len(common),
    )


def top_holdings(holdings: Iterable[Holding], limit: int = 10) -> list[Holding]:
    return sorted(list(holdings), key=lambda holding: holding.weight, reverse=True)[:limit]

