from __future__ import annotations


def calculate_position_weights(values: dict[str, float]) -> dict[str, float]:
    total = sum(values.values())
    if total <= 0:
        raise ValueError("Portfolio value must be positive.")
    return {symbol: value / total for symbol, value in values.items()}


def calculate_concentration(weights: dict[str, float]) -> float:
    return sum(weight**2 for weight in weights.values())


def largest_position(weights: dict[str, float]) -> tuple[str, float] | None:
    if not weights:
        return None
    return max(weights.items(), key=lambda item: item[1])

