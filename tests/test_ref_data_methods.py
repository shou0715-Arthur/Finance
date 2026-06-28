from __future__ import annotations

import unittest

from analytics.etf_overlap import (
    Holding,
    calculate_holdings_overlap,
    holdings_to_weight_map,
    make_holding,
    normalize_identifier,
    normalize_weight,
    top_holdings,
)
from analytics.financial_quality import (
    AltmanInputs,
    DuPontInputs,
    PiotroskiInputs,
    calculate_altman_z_score,
    calculate_dupont,
    calculate_piotroski_f_score,
    safe_divide,
)
from research.security_classifier import classify_security, is_likely_taiwan_etf_symbol, normalize_symbol


class SecurityClassifierTests(unittest.TestCase):
    def test_normalize_symbol(self) -> None:
        self.assertEqual(normalize_symbol(" 2330.tw "), "2330")

    def test_is_likely_taiwan_etf_symbol(self) -> None:
        self.assertTrue(is_likely_taiwan_etf_symbol("0050"))
        self.assertFalse(is_likely_taiwan_etf_symbol("2330"))

    def test_classify_security_uses_metadata(self) -> None:
        result = classify_security("ABC", metadata={"security_type": "stock"})
        self.assertEqual(result.security_type, "stock")
        self.assertGreater(result.confidence, 0.9)

    def test_classify_security_detects_etf_and_stock(self) -> None:
        self.assertEqual(classify_security("0050").security_type, "etf")
        self.assertEqual(classify_security("2330").security_type, "stock")
        self.assertEqual(classify_security("ARKK").security_type, "etf")


class FinancialQualityTests(unittest.TestCase):
    def test_safe_divide(self) -> None:
        self.assertEqual(safe_divide(6, 3), 2)
        self.assertIsNone(safe_divide(1, 0))

    def test_calculate_piotroski_f_score(self) -> None:
        inputs = PiotroskiInputs(
            net_income=10,
            operating_cash_flow=12,
            roa=0.12,
            prior_roa=0.10,
            long_term_debt=20,
            prior_long_term_debt=25,
            current_ratio=1.5,
            prior_current_ratio=1.2,
            shares_outstanding=100,
            prior_shares_outstanding=100,
            gross_margin=0.4,
            prior_gross_margin=0.35,
            asset_turnover=0.8,
            prior_asset_turnover=0.7,
        )
        result = calculate_piotroski_f_score(inputs)
        self.assertEqual(result.score, 9)
        self.assertTrue(result.components["positive_net_income"])

    def test_calculate_altman_z_score(self) -> None:
        result = calculate_altman_z_score(
            AltmanInputs(
                working_capital=20,
                total_assets=100,
                retained_earnings=30,
                ebit=15,
                market_value_equity=80,
                total_liabilities=40,
                sales=120,
            )
        )
        self.assertAlmostEqual(result.score, 3.555)
        self.assertFalse(result.warnings)

    def test_calculate_altman_z_score_handles_zero_denominator(self) -> None:
        result = calculate_altman_z_score(
            AltmanInputs(0, 0, 0, 0, 0, 0, 0)
        )
        self.assertTrue(result.warnings)

    def test_calculate_dupont(self) -> None:
        result = calculate_dupont(DuPontInputs(net_income=10, revenue=100, total_assets=50, equity=25))
        self.assertAlmostEqual(result.score, 0.4)
        self.assertAlmostEqual(result.components["net_margin"], 0.1)

    def test_calculate_dupont_handles_zero_denominator(self) -> None:
        result = calculate_dupont(DuPontInputs(net_income=10, revenue=0, total_assets=0, equity=0))
        self.assertTrue(result.warnings)


class ETFOverlapTests(unittest.TestCase):
    def test_normalize_identifier_and_weight(self) -> None:
        self.assertEqual(normalize_identifier(" tw0001 "), "TW0001")
        self.assertEqual(normalize_weight(25), 0.25)
        self.assertEqual(normalize_weight(0.25), 0.25)

    def test_make_holding(self) -> None:
        holding = make_holding({"isin": "abc", "name": "ABC Corp", "weight": 10})
        self.assertEqual(holding.identifier, "ABC")
        self.assertEqual(holding.name, "ABC Corp")
        self.assertEqual(holding.weight, 0.10)

    def test_holdings_to_weight_map_merges_duplicates(self) -> None:
        weights = holdings_to_weight_map([Holding("A", "A", 0.1), Holding("A", "A", 0.2)])
        self.assertAlmostEqual(weights["A"], 0.3)

    def test_calculate_holdings_overlap(self) -> None:
        left = [Holding("A", "A", 0.2), Holding("B", "B", 0.3)]
        right = [Holding("A", "A", 0.1), Holding("C", "C", 0.4)]
        result = calculate_holdings_overlap(left, right)
        self.assertEqual(result.common_identifiers, {"A"})
        self.assertEqual(result.common_count, 1)
        self.assertAlmostEqual(result.left_common_weight, 0.2)
        self.assertAlmostEqual(result.right_common_weight, 0.1)
        self.assertAlmostEqual(result.overlap_weight, 0.1)

    def test_top_holdings(self) -> None:
        holdings = [Holding("A", "A", 0.1), Holding("B", "B", 0.3), Holding("C", "C", 0.2)]
        self.assertEqual([holding.identifier for holding in top_holdings(holdings, limit=2)], ["B", "C"])


if __name__ == "__main__":
    unittest.main()
