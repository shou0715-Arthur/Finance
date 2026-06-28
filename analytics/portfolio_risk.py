from __future__ import annotations

import math


def calculate_volatility(returns: list[float]) -> float:
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    variance = sum((ret - mean) ** 2 for ret in returns) / (len(returns) - 1)
    return math.sqrt(variance)


def calculate_beta(asset_returns: list[float], benchmark_returns: list[float]) -> float:
    if len(asset_returns) != len(benchmark_returns) or len(asset_returns) < 2:
        raise ValueError("Asset and benchmark returns must have equal length >= 2.")
    mean_asset = sum(asset_returns) / len(asset_returns)
    mean_benchmark = sum(benchmark_returns) / len(benchmark_returns)
    covariance = sum((a - mean_asset) * (b - mean_benchmark) for a, b in zip(asset_returns, benchmark_returns)) / (len(asset_returns) - 1)
    benchmark_variance = sum((b - mean_benchmark) ** 2 for b in benchmark_returns) / (len(benchmark_returns) - 1)
    if benchmark_variance == 0:
        raise ValueError("Benchmark variance is zero.")
    return covariance / benchmark_variance


def calculate_var(returns: list[float], confidence: float = 0.95) -> float:
    if not returns:
        return 0.0
    sorted_returns = sorted(returns)
    index = max(int((1 - confidence) * len(sorted_returns)), 0)
    return sorted_returns[index]


def calculate_cvar(returns: list[float], confidence: float = 0.95) -> float:
    var = calculate_var(returns, confidence)
    tail = [ret for ret in returns if ret <= var]
    return sum(tail) / len(tail) if tail else var

