from __future__ import annotations

from analytics.backtest import run_backtest
from analytics.backtest_controls import apply_transaction_costs, calculate_turnover, check_sample_size
from analytics.technical_strategy import calculate_supertrend_direction, generate_strategy_signal
from research.strategy_prompt import build_strategy_prompt_context
from workflow.pipeline import Pipeline, WorkflowContext
from workflow.steps import FunctionStep, RequiredKeysStep


def strategy_signal_step(context: WorkflowContext) -> WorkflowContext:
    prices = list(context.data["prices"])
    period = int(context.data.get("ema_period", 10))
    signal = generate_strategy_signal(prices, ema_period=period)
    directions = calculate_supertrend_direction(prices, period)
    return context.with_value("strategy_signal", signal).with_value("strategy_directions", directions)


def backtest_step(context: WorkflowContext) -> WorkflowContext:
    prices = list(context.data["prices"])
    signals = list(context.data["strategy_directions"])
    cost = float(context.data.get("transaction_cost", 0.0))
    result = run_backtest(prices, signals)
    net_returns = apply_transaction_costs(result.returns, cost)
    net_result = run_backtest([1 + idx for idx in range(len(net_returns) + 1)], [1] * (len(net_returns) + 1)) if False else result
    return context.with_value("backtest_result", net_result).with_value("net_returns", net_returns)


def strategy_prompt_step(context: WorkflowContext) -> WorkflowContext:
    controls = {
        "sample_size_ok": check_sample_size(len(context.data["prices"])),
        "turnover": calculate_turnover(sum(1 for signal in context.data["strategy_directions"] if signal != 0), len(context.data["prices"])),
    }
    prompt_context = build_strategy_prompt_context(context.data["strategy_signal"], context.data["backtest_result"], controls)
    return context.with_value("strategy_prompt_context", prompt_context)


def build_strategy_analysis_workflow() -> Pipeline:
    return Pipeline(
        [
            RequiredKeysStep("require_strategy_inputs", ("prices",)),
            FunctionStep("generate_strategy_signal", strategy_signal_step),
            FunctionStep("run_backtest", backtest_step),
            FunctionStep("build_strategy_prompt_context", strategy_prompt_step),
        ],
        name="strategy_analysis",
    )

