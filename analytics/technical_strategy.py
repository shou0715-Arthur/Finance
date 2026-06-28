from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StrategySignal:
    signal_name: str
    trigger: str
    evidence: dict[str, float]
    invalidation: str
    confidence: float


def calculate_ema(values: list[float], period: int) -> list[float]:
    if period <= 0:
        raise ValueError("Period must be positive.")
    if not values:
        return []
    alpha = 2 / (period + 1)
    ema = [values[0]]
    for value in values[1:]:
        ema.append(alpha * value + (1 - alpha) * ema[-1])
    return ema


def calculate_supertrend_direction(close: list[float], period: int = 10) -> list[int]:
    ema = calculate_ema(close, period)
    return [1 if price >= trend else -1 for price, trend in zip(close, ema)]


def generate_strategy_signal(close: list[float], *, ema_period: int = 10) -> StrategySignal:
    if len(close) < max(ema_period, 2):
        return StrategySignal("ema_momentum", "insufficient_data", {}, "collect more data", 0.0)
    ema = calculate_ema(close, ema_period)
    direction = calculate_supertrend_direction(close, ema_period)
    trigger = "bullish" if close[-1] > ema[-1] and direction[-1] == 1 else "bearish"
    confidence = min(abs(close[-1] / ema[-1] - 1) * 10, 1.0) if ema[-1] else 0.0
    return StrategySignal("ema_momentum", trigger, {"close": close[-1], "ema": ema[-1]}, "close crosses EMA in opposite direction", confidence)

