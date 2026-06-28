from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WACCInputs:
    risk_free_rate: float
    equity_risk_premium: float
    beta: float
    pre_tax_cost_of_debt: float
    tax_rate: float
    market_value_equity: float
    market_value_debt: float


def calculate_wacc(inputs: WACCInputs) -> float:
    total_capital = inputs.market_value_equity + inputs.market_value_debt
    if total_capital <= 0:
        raise ValueError("Total capital must be positive.")
    cost_of_equity = inputs.risk_free_rate + inputs.beta * inputs.equity_risk_premium
    after_tax_debt = inputs.pre_tax_cost_of_debt * (1 - inputs.tax_rate)
    return (inputs.market_value_equity / total_capital) * cost_of_equity + (inputs.market_value_debt / total_capital) * after_tax_debt


@dataclass(frozen=True)
class DCFInputs:
    initial_free_cash_flow: float
    growth_rates: list[float]
    discount_rate: float
    terminal_growth_rate: float
    net_debt: float
    shares_outstanding: float


@dataclass(frozen=True)
class DCFResult:
    enterprise_value: float
    equity_value: float
    value_per_share: float
    projected_cash_flows: list[float]
    warnings: list[str]


def build_dcf_model(inputs: DCFInputs) -> DCFResult:
    if inputs.discount_rate <= inputs.terminal_growth_rate:
        raise ValueError("Discount rate must exceed terminal growth rate.")
    if inputs.shares_outstanding <= 0:
        raise ValueError("Shares outstanding must be positive.")
    projected: list[float] = []
    fcf = inputs.initial_free_cash_flow
    for growth in inputs.growth_rates:
        fcf *= 1 + growth
        projected.append(fcf)
    discounted = [cash_flow / ((1 + inputs.discount_rate) ** (idx + 1)) for idx, cash_flow in enumerate(projected)]
    terminal_cash_flow = projected[-1] * (1 + inputs.terminal_growth_rate)
    terminal_value = terminal_cash_flow / (inputs.discount_rate - inputs.terminal_growth_rate)
    discounted_terminal = terminal_value / ((1 + inputs.discount_rate) ** len(projected))
    enterprise_value = sum(discounted) + discounted_terminal
    equity_value = enterprise_value - inputs.net_debt
    return DCFResult(
        enterprise_value=enterprise_value,
        equity_value=equity_value,
        value_per_share=equity_value / inputs.shares_outstanding,
        projected_cash_flows=projected,
        warnings=[],
    )

