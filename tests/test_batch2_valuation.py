from __future__ import annotations

import unittest

from analytics.dcf import DCFInputs, WACCInputs, build_dcf_model, calculate_wacc
from analytics.scenario import ScenarioAssumption, probability_weighted_value, run_dcf_scenarios, run_sensitivity_table
from analytics.valuation_methods import select_valuation_methods
from research.valuation_prompt import build_valuation_prompt_context
from workflow.valuation_workflow import build_valuation_workflow


class Batch2ValuationTests(unittest.TestCase):
    def test_select_valuation_methods(self) -> None:
        self.assertIn("look-through NAV", select_valuation_methods("etf", has_cash_flow=True).preferred_methods)
        self.assertIn("DCF", select_valuation_methods("stock", has_cash_flow=True).preferred_methods)
        self.assertIn("P/B", select_valuation_methods("stock", has_cash_flow=True, is_financial_company=True).preferred_methods)

    def test_calculate_wacc(self) -> None:
        wacc = calculate_wacc(WACCInputs(0.02, 0.05, 1.2, 0.04, 0.2, 80, 20))
        self.assertAlmostEqual(wacc, 0.0704)

    def test_build_dcf_model(self) -> None:
        result = build_dcf_model(DCFInputs(100, [0.05, 0.04], 0.10, 0.02, 50, 10))
        self.assertGreater(result.value_per_share, 0)
        self.assertEqual(len(result.projected_cash_flows), 2)

    def test_dcf_validation(self) -> None:
        with self.assertRaises(ValueError):
            build_dcf_model(DCFInputs(100, [0.05], 0.02, 0.02, 0, 10))

    def test_scenarios_probability_and_sensitivity(self) -> None:
        base = DCFInputs(100, [0.05], 0.10, 0.02, 0, 10)
        scenarios = [
            ScenarioAssumption("Downside", [0.00], 0.11, 0.01, 0.25),
            ScenarioAssumption("Base", [0.05], 0.10, 0.02, 0.50),
            ScenarioAssumption("Upside", [0.08], 0.09, 0.03, 0.25),
        ]
        results = run_dcf_scenarios(base, scenarios)
        self.assertEqual(len(results), 3)
        self.assertGreater(probability_weighted_value(results), 0)
        table = run_sensitivity_table(base, [0.09, 0.10], [0.01, 0.02])
        self.assertEqual(len(table), 4)

    def test_valuation_prompt_context(self) -> None:
        context = build_valuation_prompt_context(["DCF"], {"base": 100}, {"discount_rate": 0.1})
        self.assertEqual(context.base_value, 100)

    def test_valuation_workflow(self) -> None:
        workflow = build_valuation_workflow()
        result = workflow.run({"dcf_inputs": DCFInputs(100, [0.05], 0.10, 0.02, 0, 10), "scenarios": [ScenarioAssumption("Base", [0.05], 0.10, 0.02, 1.0)]})
        self.assertTrue(result.ok)
        self.assertIsNotNone(result.context.data["valuation_prompt_context"].base_value)


if __name__ == "__main__":
    unittest.main()
