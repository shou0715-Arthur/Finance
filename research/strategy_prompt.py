from __future__ import annotations

from dataclasses import dataclass

from analytics.backtest import BacktestResult
from analytics.technical_strategy import StrategySignal


@dataclass(frozen=True)
class StrategyPromptContext:
    signal: StrategySignal
    backtest: BacktestResult
    controls: dict[str, bool | float]


def build_strategy_prompt_context(signal: StrategySignal, backtest: BacktestResult, controls: dict[str, bool | float]) -> StrategyPromptContext:
    return StrategyPromptContext(signal=signal, backtest=backtest, controls=controls)

