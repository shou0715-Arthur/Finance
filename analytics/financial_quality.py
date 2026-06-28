from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def safe_divide(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


@dataclass(frozen=True)
class PiotroskiInputs:
    net_income: float
    operating_cash_flow: float
    roa: float
    prior_roa: float
    long_term_debt: float
    prior_long_term_debt: float
    current_ratio: float
    prior_current_ratio: float
    shares_outstanding: float
    prior_shares_outstanding: float
    gross_margin: float
    prior_gross_margin: float
    asset_turnover: float
    prior_asset_turnover: float


@dataclass(frozen=True)
class FinancialScoreResult:
    score: float
    components: dict[str, Any]
    warnings: list[str]


def calculate_piotroski_f_score(inputs: PiotroskiInputs) -> FinancialScoreResult:
    components = {
        "positive_net_income": inputs.net_income > 0,
        "positive_operating_cash_flow": inputs.operating_cash_flow > 0,
        "roa_improved": inputs.roa > inputs.prior_roa,
        "cash_flow_exceeds_net_income": inputs.operating_cash_flow > inputs.net_income,
        "lower_leverage": inputs.long_term_debt < inputs.prior_long_term_debt,
        "higher_current_ratio": inputs.current_ratio > inputs.prior_current_ratio,
        "no_new_shares": inputs.shares_outstanding <= inputs.prior_shares_outstanding,
        "higher_gross_margin": inputs.gross_margin > inputs.prior_gross_margin,
        "higher_asset_turnover": inputs.asset_turnover > inputs.prior_asset_turnover,
    }
    return FinancialScoreResult(score=float(sum(components.values())), components=components, warnings=[])


@dataclass(frozen=True)
class AltmanInputs:
    working_capital: float
    total_assets: float
    retained_earnings: float
    ebit: float
    market_value_equity: float
    total_liabilities: float
    sales: float


def calculate_altman_z_score(inputs: AltmanInputs) -> FinancialScoreResult:
    warnings: list[str] = []
    ratios = {
        "working_capital_to_assets": safe_divide(inputs.working_capital, inputs.total_assets),
        "retained_earnings_to_assets": safe_divide(inputs.retained_earnings, inputs.total_assets),
        "ebit_to_assets": safe_divide(inputs.ebit, inputs.total_assets),
        "market_value_equity_to_liabilities": safe_divide(inputs.market_value_equity, inputs.total_liabilities),
        "sales_to_assets": safe_divide(inputs.sales, inputs.total_assets),
    }
    if any(value is None for value in ratios.values()):
        warnings.append("One or more Altman ratios could not be calculated because a denominator was zero.")
        return FinancialScoreResult(score=0.0, components=ratios, warnings=warnings)

    score = (
        1.2 * ratios["working_capital_to_assets"]
        + 1.4 * ratios["retained_earnings_to_assets"]
        + 3.3 * ratios["ebit_to_assets"]
        + 0.6 * ratios["market_value_equity_to_liabilities"]
        + 1.0 * ratios["sales_to_assets"]
    )
    return FinancialScoreResult(score=float(score), components=ratios, warnings=warnings)


@dataclass(frozen=True)
class DuPontInputs:
    net_income: float
    revenue: float
    total_assets: float
    equity: float


def calculate_dupont(inputs: DuPontInputs) -> FinancialScoreResult:
    warnings: list[str] = []
    net_margin = safe_divide(inputs.net_income, inputs.revenue)
    asset_turnover = safe_divide(inputs.revenue, inputs.total_assets)
    equity_multiplier = safe_divide(inputs.total_assets, inputs.equity)

    components = {
        "net_margin": net_margin,
        "asset_turnover": asset_turnover,
        "equity_multiplier": equity_multiplier,
    }
    if any(value is None for value in components.values()):
        warnings.append("One or more DuPont components could not be calculated because a denominator was zero.")
        return FinancialScoreResult(score=0.0, components=components, warnings=warnings)

    roe = net_margin * asset_turnover * equity_multiplier
    return FinancialScoreResult(score=float(roe), components=components, warnings=warnings)

