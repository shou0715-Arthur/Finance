from __future__ import annotations

from pathlib import Path
import shutil
import unittest

from analytics.market_regime import build_market_regime_summary
from analytics.sentiment import score_news_relevance, score_sentiment
from data_sources.market_sentiment_client import MarketSentimentSnapshot, classify_market_regime
from data_sources.news_client import NewsRecord, deduplicate_news, normalize_news_records
from research.catalyst_calendar import build_catalyst_calendar
from research.event_extractor import classify_event_type, extract_events
from storage.event_store import load_events, save_events
from workflow.event_monitoring_workflow import build_event_monitoring_workflow


TMP = Path("tmp_tests_batch4")


class Batch4EventsTests(unittest.TestCase):
    def setUp(self) -> None:
        TMP.mkdir(exist_ok=True)

    def tearDown(self) -> None:
        if TMP.exists():
            shutil.rmtree(TMP)

    def test_news_normalize_and_deduplicate(self) -> None:
        records = normalize_news_records([{"title": "A", "source": "S"}, {"title": "A", "source": "S"}])
        self.assertEqual(len(records), 2)
        self.assertEqual(len(deduplicate_news(records)), 1)

    def test_market_regime(self) -> None:
        self.assertEqual(classify_market_regime(MarketSentimentSnapshot(vix=35)), "risk_off")
        self.assertEqual(build_market_regime_summary(MarketSentimentSnapshot(fear_greed=80))["regime"], "euphoric")

    def test_sentiment_and_relevance(self) -> None:
        self.assertGreater(score_sentiment("strong growth upgrade"), 0)
        self.assertLess(score_sentiment("weak decline risk"), 0)
        self.assertEqual(score_news_relevance("TSMC AI demand", ["TSMC", "AI"]), 1.0)

    def test_event_extraction_and_calendar(self) -> None:
        self.assertEqual(classify_event_type("earnings beat"), "earnings")
        events = extract_events([NewsRecord("earnings strong growth", "Test", "2026-06-24")])
        calendar = build_catalyst_calendar("2330", events)
        self.assertEqual(calendar[0].ticker, "2330")
        self.assertEqual(calendar[0].event_type, "earnings")

    def test_event_store(self) -> None:
        events = build_catalyst_calendar("2330", extract_events([NewsRecord("earnings strong growth", "Test")]))
        path = TMP / "events.json"
        save_events(path, events)
        self.assertEqual(load_events(path)[0].ticker, "2330")

    def test_event_monitoring_workflow(self) -> None:
        workflow = build_event_monitoring_workflow()
        result = workflow.run({"ticker": "2330", "news_rows": [{"title": "earnings strong growth", "source": "Test"}]})
        self.assertTrue(result.ok)
        self.assertEqual(result.context.data["catalyst_calendar"][0].event_type, "earnings")


if __name__ == "__main__":
    unittest.main()

