from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValuationPromptContext:
    preferred_methods: list[str]
    downside_value: float | None
    base_value: float | None
    upside_value: float | None
    key_assumptions: dict[str, float | str]
    warnings: list[str]


def build_valuation_prompt_context(
    preferred_methods: list[str],
    scenario_values: dict[str, float],
    key_assumptions: dict[str, float | str],
    warnings: list[str] | None = None,
) -> ValuationPromptContext:
    return ValuationPromptContext(
        preferred_methods=preferred_methods,
        downside_value=scenario_values.get("downside"),
        base_value=scenario_values.get("base"),
        upside_value=scenario_values.get("upside"),
        key_assumptions=key_assumptions,
        warnings=warnings or [],
    )

