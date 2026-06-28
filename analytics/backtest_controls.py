from __future__ import annotations


def check_sample_size(sample_count: int, minimum: int = 60) -> bool:
    return sample_count >= minimum


def check_lookahead_bias(signal_dates: list[str], trade_dates: list[str]) -> bool:
    return all(signal <= trade for signal, trade in zip(signal_dates, trade_dates))


def apply_transaction_costs(gross_returns: list[float], cost_per_trade: float) -> list[float]:
    return [ret - cost_per_trade for ret in gross_returns]


def calculate_turnover(trade_count: int, periods: int) -> float:
    if periods <= 0:
        raise ValueError("Periods must be positive.")
    return trade_count / periods

