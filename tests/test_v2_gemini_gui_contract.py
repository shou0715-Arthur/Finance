from __future__ import annotations

import unittest
import sys
import types
from unittest.mock import patch

import pandas as pd

if "requests" not in sys.modules:
    requests_stub = types.ModuleType("requests")
    exceptions_stub = types.SimpleNamespace(
        Timeout=TimeoutError,
        RequestException=Exception,
    )
    requests_stub.exceptions = exceptions_stub
    requests_stub.get = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("requests is stubbed in tests"))
    sys.modules["requests"] = requests_stub

from app.ai_stock_gui import (
    FundamentalInfo,
    MLSignal,
    NewsItem,
    build_ref_data_status_packet,
    generate_ai_insights,
)
from data_sources.gemini_client import GeminiGenerationResult


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


class V2GeminiGuiContractTests(unittest.TestCase):
    def test_ref_data_packet_is_attached_to_gemini_prompt(self) -> None:
        df = make_price_frame()
        packet = build_ref_data_status_packet(
            "0050",
            df,
            14,
            [NewsItem(title="ETF rebalancing", source="Test", published="2026-06-24", link="")],
            MLSignal(status="not_run", message="no model"),
            FundamentalInfo(status="not_loaded", message="no fundamentals"),
        )

        self.assertIn("Version: v2.0", packet)
        self.assertIn("Security type: etf", packet)
        self.assertIn("Ref-data modules converted to Python", packet)
        self.assertIn("Display rule", packet)

    def test_gemini_key_is_required_in_v2(self) -> None:
        with self.assertRaises(RuntimeError):
            generate_ai_insights(
                "2330",
                make_price_frame(),
                "",
                14,
                [],
                MLSignal(status="not_run", message="no model"),
                FundamentalInfo(status="not_loaded", message="no fundamentals"),
            )

    def test_generate_ai_insights_returns_a_gui_ready_gemini_result(self) -> None:
        captured_prompt: dict[str, str] = {}

        def fake_generate(*, api_key: str, prompt: str):
            captured_prompt["api_key"] = api_key
            captured_prompt["prompt"] = prompt
            return GeminiGenerationResult(
                text="Gemini investment memo",
                model_name="gemini-test",
                attempts=["gemini-test: ok via mock"],
            )

        with patch("app.ai_stock_gui.generate_content_with_fallback", side_effect=fake_generate):
            result = generate_ai_insights(
                "2330",
                make_price_frame(),
                "fake-key",
                14,
                [NewsItem(title="Revenue growth", source="Test", published="2026-06-24", link="")],
                MLSignal(status="not_run", message="no model"),
                FundamentalInfo(status="not_loaded", message="no fundamentals"),
            )

        self.assertEqual(result.report, "Gemini investment memo")
        self.assertEqual(result.model_name, "gemini-test")
        self.assertIn("gemini-test: ok via mock", result.attempts)
        self.assertIn("Ref-data / Python workflow status packet", captured_prompt["prompt"])
        self.assertIn("Version: v2.0", result.ref_data_status)
        self.assertIn("Display rule", result.source_packet)


if __name__ == "__main__":
    unittest.main()
