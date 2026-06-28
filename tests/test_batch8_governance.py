from __future__ import annotations

import unittest

from analytics.insider_analysis import classify_insider_transaction, detect_cluster_buying, detect_unusual_selling, summarize_insider_activity
from data_sources.insider_client import InsiderTransaction, normalize_insider_transactions
from research.governance_prompt import build_governance_prompt_context
from workflow.governance_workflow import build_governance_workflow


class Batch8GovernanceTests(unittest.TestCase):
    def test_normalize_and_classify_transactions(self) -> None:
        tx = normalize_insider_transactions("AAPL", [{"reportingName": "Insider", "transactionDate": "2026-01-01", "transactionType": "P", "shares": 100, "price": 10}])[0]
        self.assertEqual(tx.symbol, "AAPL")
        self.assertEqual(classify_insider_transaction(tx), "open_market_buy")
        self.assertEqual(classify_insider_transaction(InsiderTransaction("A", "B", "D", "S", 1, is_10b5_1=True)), "sale_10b5_1")

    def test_cluster_and_unusual_selling(self) -> None:
        transactions = [
            InsiderTransaction("A", "One", "D", "P", 10),
            InsiderTransaction("A", "Two", "D", "P", 20),
            InsiderTransaction("A", "Three", "D", "S", 200),
        ]
        self.assertTrue(detect_cluster_buying(transactions))
        self.assertTrue(detect_unusual_selling(transactions, 100))
        self.assertEqual(summarize_insider_activity(transactions)["open_market_buy"], 2)

    def test_governance_prompt_context(self) -> None:
        context = build_governance_prompt_context({"sale": 1}, cluster_buying=False, unusual_selling=True)
        self.assertTrue(context.warnings)

    def test_governance_workflow(self) -> None:
        workflow = build_governance_workflow()
        rows = [
            {"reportingName": "One", "transactionDate": "D", "transactionType": "P", "shares": 10},
            {"reportingName": "Two", "transactionDate": "D", "transactionType": "P", "shares": 20},
        ]
        result = workflow.run({"symbol": "AAPL", "insider_rows": rows})
        self.assertTrue(result.ok)
        self.assertTrue(result.context.data["governance_prompt_context"].cluster_buying)


if __name__ == "__main__":
    unittest.main()

