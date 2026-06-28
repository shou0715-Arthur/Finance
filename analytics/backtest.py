from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class BacktestResult:
    returns: list[float]
    cumulative_return: float
    win_rate: float
    max_drawdown: float
    sharpe: float


def calculate_win_rate(returns: list[float]) -> float:
    if not returns:
        return 0.0
    return sum(1 for ret in returns if ret > 0) / len(returns)


def calculate_max_drawdown(returns: list[float]) -> float:
    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    for ret in returns:
        equity *= 1 + ret
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, equity / peak - 1)
    return max_drawdown


def calculate_sharpe(returns: list[float], periods_per_year: int = 252) -> float:
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    variance = sum((ret - mean) ** 2 for ret in returns) / (len(returns) - 1)
    stdev = math.sqrt(variance)
    if stdev == 0:
        return 0.0
    return mean / stdev * math.sqrt(periods_per_year)


def run_backtest(prices: list[float], signals: list[int]) -> BacktestResult:
    if len(prices) != len(signals):
        raise ValueError("Prices and signals must have equal length.")
    returns: list[float] = []
    for idx in range(1, len(prices)):
        daily_return = prices[idx] / prices[idx - 1] - 1
        returns.append(daily_return * signals[idx - 1])
    cumulative = math.prod([1 + ret for ret in returns]) - 1 if returns else 0.0
    return BacktestResult(returns, cumulative, calculate_win_rate(returns), calculate_max_drawdown(returns), calculate_sharpe(returns))

