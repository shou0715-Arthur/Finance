from __future__ import annotations

import json
from pathlib import Path
import shutil
import unittest

from analytics.financial_normalizer import normalize_financial_row, pick_field, to_float
from analytics.financial_statement_parser import parse_csv_statement_file, parse_json_statement_file, parse_statement_file
from data_sources.finmind_client import extract_latest_finmind_record, normalize_finmind_records
from data_sources.fmp_client import latest_fmp_statement, normalize_fmp_statement_rows
from research.source_packet import SourceItem, build_source_packet
from workflow.financial_analysis_workflow import build_financial_analysis_workflow


TMP = Path("tmp_tests_batch1")


class Batch1FinancialFoundationTests(unittest.TestCase):
    def setUp(self) -> None:
        TMP.mkdir(exist_ok=True)

    def tearDown(self) -> None:
        if TMP.exists():
            shutil.rmtree(TMP)

    def test_finmind_records_normalize_and_latest(self) -> None:
        records = normalize_finmind_records("TaiwanStockFinancialStatements", "2330", [{"date": "2026-01-01", "EPS": "1"}, {"date": "2026-03-01", "EPS": "2"}])
        self.assertEqual(records[0].dataset, "TaiwanStockFinancialStatements")
        self.assertEqual(extract_latest_finmind_record(records).fields["EPS"], "2")

    def test_fmp_rows_normalize_and_latest(self) -> None:
        records = normalize_fmp_statement_rows("nvda", [{"calendarYear": "2025", "period": "Q1", "reportedCurrency": "USD"}, {"calendarYear": "2025", "period": "Q2", "reportedCurrency": "USD"}])
        self.assertEqual(records[0].symbol, "NVDA")
        self.assertEqual(latest_fmp_statement(records).period, "Q2")

    def test_statement_file_parsers(self) -> None:
        json_path = TMP / "statement.json"
        json_path.write_text(json.dumps([{"revenue": 1}], ensure_ascii=False), encoding="utf-8")
        self.assertEqual(parse_json_statement_file(json_path).records[0]["revenue"], 1)
        self.assertEqual(parse_statement_file(json_path).source_type, "json")

        csv_path = TMP / "statement.csv"
        csv_path.write_text("revenue\n2\n", encoding="utf-8")
        self.assertEqual(parse_csv_statement_file(csv_path).records[0]["revenue"], "2")

    def test_financial_normalizer(self) -> None:
        self.assertEqual(to_float("1,234"), 1234)
        row = {"revenue": "100", "netIncome": "10", "totalAssets": "50", "totalLiabilities": "20", "totalStockholdersEquity": "30"}
        self.assertEqual(pick_field(row, "revenue"), 100)
        normalized = normalize_financial_row("2330", row, source="unit")
        self.assertEqual(normalized.ticker, "2330")
        self.assertEqual(normalized.income_statement["net_income"], 10)
        self.assertIn("missing:gross_profit", normalized.warnings)

    def test_source_packet_readiness(self) -> None:
        packet = build_source_packet("2330", [SourceItem("price", "price_history", confidence=0.9)])
        self.assertEqual(packet.readiness, "screen-grade")
        self.assertIn("income_statement", packet.missing_items)

    def test_financial_analysis_workflow(self) -> None:
        workflow = build_financial_analysis_workflow()
        result = workflow.run({"ticker": "2330", "financial_row": {"revenue": 100, "netIncome": 10, "totalAssets": 50, "totalLiabilities": 20, "totalStockholdersEquity": 30}})
        self.assertTrue(result.ok)
        self.assertEqual(result.context.data["normalized_financials"].ticker, "2330")
        self.assertEqual(result.context.data["source_packet"].ticker, "2330")


if __name__ == "__main__":
    unittest.main()

