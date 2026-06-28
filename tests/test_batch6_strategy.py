from __future__ import annotations

import unittest

from analytics.backtest import calculate_max_drawdown, calculate_sharpe, calculate_win_rate, run_backtest
from analytics.backtest_controls import apply_transaction_costs, calculate_turnover, check_lookahead_bias, check_sample_size
from analytics.technical_strategy import calculate_ema, calculate_supertrend_direction, generate_strategy_signal
from research.strategy_agent_prompt import build_strategy_agent_guardrails
from research.strategy_prompt import build_strategy_prompt_context
from workflow.strategy_analysis_workflow import build_strategy_analysis_workflow


class Batch6StrategyTests(unittest.TestCase):
    def test_backtest_controls(self) -> None:
        self.assertTrue(check_sample_size(60))
        self.assertTrue(check_lookahead_bias(["2026-01-01"], ["2026-01-02"]))
        self.assertEqual(apply_transaction_costs([0.02], 0.01), [0.01])
        self.assertEqual(calculate_turnover(2, 10), 0.2)

    def test_technical_strategy(self) -> None:
        ema = calculate_ema([1, 2, 3], 2)
        self.assertEqual(len(ema), 3)
        self.assertEqual(len(calculate_supertrend_direction([1, 2, 3], 2)), 3)
        signal = generate_strategy_signal([1, 2, 3, 4, 5], ema_period=3)
        self.assertIn(signal.trigger, {"bullish", "bearish"})

    def test_backtest_metrics(self) -> None:
        result = run_backtest([100, 110, 99], [1, 1, 1])
        self.assertEqual(len(result.returns), 2)
        self.assertGreaterEqual(calculate_win_rate(result.returns), 0)
        self.assertLessEqual(calculate_max_drawdown(result.returns), 0)
        self.assertIsInstance(calculate_sharpe(result.returns), float)

    def test_strategy_prompt_and_guardrails(self) -> None:
        signal = generate_strategy_signal([1, 2, 3, 4, 5], ema_period=3)
        backtest = run_backtest([1, 2, 3, 4, 5], [1, 1, 1, 1, 1])
        context = build_strategy_prompt_context(signal, backtest, {"sample_size_ok": False})
        self.assertFalse(context.controls["sample_size_ok"])
        self.assertIn("must not invent signals", build_strategy_agent_guardrails())

    def test_strategy_workflow(self) -> None:
        workflow = build_strategy_analysis_workflow()
        result = workflow.run({"prices": [1, 2, 3, 4, 5], "ema_period": 3})
        self.assertTrue(result.ok)
        self.assertIn("strategy_prompt_context", result.context.data)


if __name__ == "__main__":
    unittest.main()

