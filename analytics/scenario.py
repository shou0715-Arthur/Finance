from __future__ import annotations

from dataclasses import dataclass

from analytics.dcf import DCFInputs, DCFResult, build_dcf_model


@dataclass(frozen=True)
class ScenarioAssumption:
    name: str
    growth_rates: list[float]
    discount_rate: float
    terminal_growth_rate: float
    probability: float


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    probability: float
    dcf_result: DCFResult


def run_dcf_scenarios(base_inputs: DCFInputs, scenarios: list[ScenarioAssumption]) -> list[ScenarioResult]:
    results: list[ScenarioResult] = []
    for scenario in scenarios:
        scenario_inputs = DCFInputs(
            initial_free_cash_flow=base_inputs.initial_free_cash_flow,
            growth_rates=scenario.growth_rates,
            discount_rate=scenario.discount_rate,
            terminal_growth_rate=scenario.terminal_growth_rate,
            net_debt=base_inputs.net_debt,
            shares_outstanding=base_inputs.shares_outstanding,
        )
        results.append(ScenarioResult(scenario.name, scenario.probability, build_dcf_model(scenario_inputs)))
    return results


def probability_weighted_value(results: list[ScenarioResult]) -> float:
    total_probability = sum(result.probability for result in results)
    if total_probability <= 0:
        raise ValueError("Total probability must be positive.")
    return sum(result.probability * result.dcf_result.value_per_share for result in results) / total_probability


def run_sensitivity_table(base_inputs: DCFInputs, discount_rates: list[float], terminal_growth_rates: list[float]) -> dict[tuple[float, float], float]:
    table: dict[tuple[float, float], float] = {}
    for discount_rate in discount_rates:
        for terminal_growth_rate in terminal_growth_rates:
            adjusted = DCFInputs(
                initial_free_cash_flow=base_inputs.initial_free_cash_flow,
                growth_rates=base_inputs.growth_rates,
                discount_rate=discount_rate,
                terminal_growth_rate=terminal_growth_rate,
                net_debt=base_inputs.net_debt,
                shares_outstanding=base_inputs.shares_outstanding,
            )
            table[(discount_rate, terminal_growth_rate)] = build_dcf_model(adjusted).value_per_share
    return table

