from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskPromptContext:
    weights: dict[str, float]
    concentration: float
    volatility: float
    var: float
    cvar: float
    stress_losses: dict[str, float]


def build_risk_prompt_context(weights: dict[str, float], concentration: float, volatility: float, var: float, cvar: float, stress_losses: dict[str, float]) -> RiskPromptContext:
    return RiskPromptContext(weights, concentration, volatility, var, cvar, stress_losses)

