from __future__ import annotations

import unittest

from analytics.diversification import calculate_concentration, calculate_position_weights, largest_position
from analytics.portfolio_risk import calculate_beta, calculate_cvar, calculate_var, calculate_volatility
from analytics.stress_test import run_fx_shock, run_macro_shock, run_rate_shock, run_sector_shock
from research.risk_prompt import build_risk_prompt_context
from workflow.portfolio_risk_workflow import build_portfolio_risk_workflow


class Batch7PortfolioRiskTests(unittest.TestCase):
    def test_diversification(self) -> None:
        weights = calculate_position_weights({"A": 60, "B": 40})
        self.assertAlmostEqual(weights["A"], 0.6)
        self.assertAlmostEqual(calculate_concentration(weights), 0.52)
        self.assertEqual(largest_position(weights), ("A", 0.6))

    def test_portfolio_risk_metrics(self) -> None:
        returns = [0.01, -0.02, 0.03, -0.04]
        self.assertGreater(calculate_volatility(returns), 0)
        self.assertAlmostEqual(calculate_beta([0.02, 0.04, 0.06], [0.01, 0.02, 0.03]), 2.0)
        self.assertLessEqual(calculate_var(returns), 0)
        self.assertLessEqual(calculate_cvar(returns), 0)

    def test_stress_tests(self) -> None:
        weights = {"A": 0.6, "B": 0.4}
        self.assertEqual(run_macro_shock(weights, -0.1), -0.1)
        self.assertEqual(run_sector_shock(weights, {"A": "Tech"}, "Tech", -0.2), -0.12)
        self.assertEqual(run_rate_shock(5, 0.01), -0.05)
        self.assertEqual(run_fx_shock({"USD": 0.5}, "USD", -0.1), -0.05)

    def test_risk_prompt_context(self) -> None:
        context = build_risk_prompt_context({"A": 1.0}, 1.0, 0.2, -0.1, -0.15, {"macro": -0.1})
        self.assertEqual(context.stress_losses["macro"], -0.1)

    def test_portfolio_risk_workflow(self) -> None:
        workflow = build_portfolio_risk_workflow()
        result = workflow.run({"position_values": {"A": 60, "B": 40}, "portfolio_returns": [0.01, -0.02], "macro_shock": -0.1})
        self.assertTrue(result.ok)
        self.assertIn("risk_prompt_context", result.context.data)


if __name__ == "__main__":
    unittest.main()

