from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValuationMethodRecommendation:
    preferred_methods: list[str]
    rejected_methods: list[str]
    rationale: list[str]


def select_valuation_methods(security_type: str, *, has_cash_flow: bool, is_financial_company: bool = False) -> ValuationMethodRecommendation:
    if security_type == "etf":
        return ValuationMethodRecommendation(["look-through NAV", "holdings multiple"], ["single-company DCF"], ["ETF should be valued through holdings and mandate."])
    if is_financial_company:
        return ValuationMethodRecommendation(["P/B", "ROE spread", "DDM"], ["standard industrial DCF"], ["Financial companies require balance-sheet-centric valuation."])
    if has_cash_flow:
        return ValuationMethodRecommendation(["DCF", "EV/EBITDA", "P/E"], [], ["Cash flow data supports intrinsic valuation and comps."])
    return ValuationMethodRecommendation(["P/E", "P/S", "EV/Sales"], ["DCF"], ["Cash flow data is insufficient for a reliable DCF."])

