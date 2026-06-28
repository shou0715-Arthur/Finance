from __future__ import annotations

import json
from pathlib import Path
import shutil
import unittest

from analytics.etf_exposure import calculate_group_exposure, calculate_top_holdings_summary, detect_ptp_exposure
from analytics.etf_overlap import Holding
from data_sources.etf_files import load_etf_holdings_file, load_json_holdings, load_ptp_symbols
from research.etf_prompt import build_etf_prompt_context, render_etf_prompt_summary
from workflow.etf_analysis_workflow import build_etf_analysis_workflow


TMP = Path("tmp_tests_batch3")


class Batch3ETFCompleteTests(unittest.TestCase):
    def setUp(self) -> None:
        TMP.mkdir(exist_ok=True)

    def tearDown(self) -> None:
        if TMP.exists():
            shutil.rmtree(TMP)

    def test_load_json_holdings_and_dispatcher(self) -> None:
        path = TMP / "holdings.json"
        path.write_text(json.dumps([{"isin": "A", "name": "A Corp", "weight": 20}], ensure_ascii=False), encoding="utf-8")
        self.assertEqual(load_json_holdings(path)[0].identifier, "A")
        self.assertEqual(load_etf_holdings_file(path)[0].weight, 0.2)

    def test_load_ptp_symbols(self) -> None:
        path = TMP / "ptp.txt"
        path.write_text("ABC, DEF\n", encoding="utf-8")
        self.assertIn("ABC", load_ptp_symbols(path))

    def test_exposure_top_holdings_and_ptp(self) -> None:
        holdings = [Holding("A", "A Corp", 0.2), Holding("B", "B Corp", 0.1)]
        exposure = calculate_group_exposure(holdings, {"A": "Taiwan"})
        self.assertEqual(exposure.exposure["Taiwan"], 0.2)
        self.assertEqual(exposure.missing_identifiers, ["B"])
        self.assertEqual(calculate_top_holdings_summary(holdings, 1)[0]["identifier"], "A")
        self.assertEqual(detect_ptp_exposure(holdings, {"B"})[0].identifier, "B")

    def test_etf_prompt_context_and_render(self) -> None:
        holdings = [Holding("A", "A Corp", 0.2)]
        context = build_etf_prompt_context("vwo", holdings, [{"identifier": "A", "name": "A Corp", "weight": 0.2}], ptp_holdings=holdings)
        text = render_etf_prompt_summary(context)
        self.assertIn("ETF：VWO", text)
        self.assertIn("PTP", text)

    def test_etf_analysis_workflow(self) -> None:
        path = TMP / "holdings.json"
        path.write_text(json.dumps([{"isin": "A", "name": "A Corp", "weight": 20}], ensure_ascii=False), encoding="utf-8")
        workflow = build_etf_analysis_workflow()
        result = workflow.run({"symbol": "VWO", "holdings_path": path, "country_mapping": {"A": "Taiwan"}, "sector_mapping": {"A": "Tech"}, "ptp_symbols": {"A"}})
        self.assertTrue(result.ok)
        context = result.context.data["etf_prompt_context"]
        self.assertEqual(context.symbol, "VWO")
        self.assertEqual(context.holdings_count, 1)
        self.assertEqual(context.ptp_warnings, ["A"])


if __name__ == "__main__":
    unittest.main()

