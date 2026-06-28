from __future__ import annotations

import unittest

import pandas as pd

from research.public_equity_prompt import build_local_public_equity_note, build_public_equity_prompt


class NewsItem:
    title = "測試新聞"
    source = "Test"
    published = "2026-06-24"


def make_price_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-06-20", "2026-06-21", "2026-06-22"]),
            "open": [100, 101, 102],
            "high": [102, 103, 104],
            "low": [99, 100, 101],
            "close": [101, 102, 103],
            "volume": [1000, 1100, 1200],
            "MA5": [101, 101.5, 102],
            "MA10": [101, 101.3, 101.8],
            "MA20": [101, 101.2, 101.6],
            "MA60": [101, 101.1, 101.4],
            "RSI": [55, 58, 60],
        }
    )


class PromptIntegrationTests(unittest.TestCase):
    def test_local_note_contains_security_type(self) -> None:
        note = build_local_public_equity_note(
            symbol="0050",
            df=make_price_frame(),
            rsi_period=14,
            news_items=[NewsItem()],
            ml_summary="ML",
            fundamental_summary="Fundamental",
            rsi_status_func=lambda _: "中性",
        )
        self.assertIn("資產類型：etf", note)
        self.assertIn("Source Posture", note)

    def test_public_equity_prompt_contains_security_type_and_contract(self) -> None:
        prompt = build_public_equity_prompt(
            symbol="2330",
            df=make_price_frame(),
            rsi_period=14,
            news_items=[NewsItem()],
            ml_summary="ML",
            fundamental_summary="Fundamental",
            rsi_status_func=lambda _: "中性",
        )
        self.assertIn("資產類型：stock", prompt)
        self.assertIn("必須輸出的 memo 契約", prompt)


if __name__ == "__main__":
    unittest.main()

