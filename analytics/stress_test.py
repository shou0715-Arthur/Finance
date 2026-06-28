from __future__ import annotations


def run_macro_shock(weights: dict[str, float], shock_return: float) -> float:
    return sum(weights.values()) * shock_return


def run_sector_shock(weights: dict[str, float], sector_map: dict[str, str], shocked_sector: str, shock_return: float) -> float:
    return sum(weight for symbol, weight in weights.items() if sector_map.get(symbol) == shocked_sector) * shock_return


def run_rate_shock(duration_exposure: float, rate_change: float) -> float:
    return -duration_exposure * rate_change


def run_fx_shock(currency_weights: dict[str, float], shocked_currency: str, shock_return: float) -> float:
    return currency_weights.get(shocked_currency, 0.0) * shock_return

