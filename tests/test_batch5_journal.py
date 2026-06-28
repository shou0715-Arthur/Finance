from __future__ import annotations

from pathlib import Path
import shutil
import unittest

from research.behavioral_checklist import build_behavioral_checklist
from research.decision_journal import create_decision_journal_entry, evaluate_decision_quality
from research.thesis_tracker import update_thesis_status
from storage.journal_store import load_journal_entries, save_journal_entries
from workflow.journal_workflow import build_journal_workflow


TMP = Path("tmp_tests_batch5")


class Batch5JournalTests(unittest.TestCase):
    def setUp(self) -> None:
        TMP.mkdir(exist_ok=True)

    def tearDown(self) -> None:
        if TMP.exists():
            shutil.rmtree(TMP)

    def test_behavioral_checklist(self) -> None:
        checklist = build_behavioral_checklist(has_disconfirmers=False, has_position_limit=True, has_base_rate=False, has_exit_rule=True)
        self.assertTrue(checklist.confirmation_bias)
        self.assertTrue(checklist.overconfidence)

    def test_decision_journal(self) -> None:
        entry = create_decision_journal_entry("2330", "AI demand", "Watchlist", 0.6, "earnings", "margin decline")
        self.assertEqual(entry.ticker, "2330")
        self.assertEqual(evaluate_decision_quality(entry), "pending")
        with self.assertRaises(ValueError):
            create_decision_journal_entry("2330", "x", "y", 2, "", "")

    def test_thesis_tracker(self) -> None:
        self.assertEqual(update_thesis_status("2330", "t1", ["revenue up"], []).status, "active")
        self.assertEqual(update_thesis_status("2330", "t1", [], ["margin down"]).status, "challenged")

    def test_journal_store(self) -> None:
        path = TMP / "journal.json"
        entry = create_decision_journal_entry("2330", "AI demand", "Watchlist", 0.6, "earnings", "margin decline")
        save_journal_entries(path, [entry])
        self.assertEqual(load_journal_entries(path)[0].ticker, "2330")

    def test_journal_workflow(self) -> None:
        workflow = build_journal_workflow()
        result = workflow.run({"ticker": "2330", "thesis": "AI demand", "action": "Watchlist", "confidence": 0.6, "invalidation": "margin decline", "evidence": ["revenue up"]})
        self.assertTrue(result.ok)
        self.assertEqual(result.context.data["journal_entry"].ticker, "2330")
        self.assertEqual(result.context.data["thesis_status"].status, "active")


if __name__ == "__main__":
    unittest.main()

