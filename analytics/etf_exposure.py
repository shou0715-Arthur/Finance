from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Mapping

from analytics.etf_overlap import Holding


@dataclass(frozen=True)
class ExposureResult:
    exposure: dict[str, float]
    missing_identifiers: list[str]


def calculate_group_exposure(holdings: Iterable[Holding], mapping: Mapping[str, str]) -> ExposureResult:
    exposure: dict[str, float] = defaultdict(float)
    missing: list[str] = []
    for holding in holdings:
        group = mapping.get(holding.identifier)
        if not group:
            missing.append(holding.identifier)
            continue
        exposure[group] += holding.weight
    return ExposureResult(exposure=dict(sorted(exposure.items())), missing_identifiers=missing)


def calculate_top_holdings_summary(holdings: Iterable[Holding], limit: int = 10) -> list[dict[str, float | str]]:
    sorted_holdings = sorted(list(holdings), key=lambda holding: holding.weight, reverse=True)[:limit]
    return [{"identifier": holding.identifier, "name": holding.name, "weight": holding.weight} for holding in sorted_holdings]


def detect_ptp_exposure(holdings: Iterable[Holding], ptp_symbols: set[str]) -> list[Holding]:
    return [holding for holding in holdings if holding.identifier in ptp_symbols or holding.name.upper() in ptp_symbols]

