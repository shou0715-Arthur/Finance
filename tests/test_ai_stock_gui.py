from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from ai_stock_gui import (
    DEFAULT_GEMINI_MODEL,
    FundamentalInfo,
    MLSignal,
    NewsItem,
    PotentialSignal,
    RevenueInfo,
    add_indicators,
    build_ai_prompt,
    build_industry_basket,
    build_ml_feature_frame,
    industry_profiles_for_symbol,
    load_industry_data,
    parse_monthly_revenue_info,
    train_ml_signal,
    train_potential_signal,
)


class IndustryDataTests(unittest.TestCase):
    def test_industry_file_contains_all_requested_themes(self) -> None:
        themes, candidates = load_industry_data(Path("industry_chain.json"))
        self.assertEqual(DEFAULT_GEMINI_MODEL, "gemini-3.5-flash")
        self.assertTrue(
            {"CPO與高速光通訊", "ABF載板", "Glass載板", "被動元件", "矽電容"}.issubset(themes)
        )
        self.assertGreaterEqual(len(candidates), 20)
        self.assertTrue(industry_profiles_for_symbol(candidates, "3037"))
        self.assertFalse([item for item in candidates if item.theme == "矽電容"])

    def test_monthly_revenue_growth(self) -> None:
        rows = [
            {"date": "2025-05-01", "revenue": 100, "revenue_year": 2025, "revenue_month": 5},
            {"date": "2026-04-01", "revenue": 110, "revenue_year": 2026, "revenue_month": 4},
            {"date": "2026-05-01", "revenue": 120, "revenue_year": 2026, "revenue_month": 5},
        ]
        info = parse_monthly_revenue_info(rows)
        self.assertEqual(info.status, "ok")
        self.assertAlmostEqual(info.month_over_month or 0, 120 / 110 - 1)
        self.assertAlmostEqual(info.year_over_year or 0, 0.2)


class MachineLearningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rng = np.random.default_rng(42)
        dates = pd.bdate_range("2023-01-02", periods=460)
        stock_returns = rng.normal(0.0005, 0.016, len(dates))
        benchmark_returns = rng.normal(0.0003, 0.011, len(dates))
        industry_returns = 0.45 * stock_returns + rng.normal(0.0002, 0.009, len(dates))
        close = 100 * np.exp(np.cumsum(stock_returns))
        benchmark_close = 100 * np.exp(np.cumsum(benchmark_returns))
        industry_close = 100 * np.exp(np.cumsum(industry_returns))
        open_price = close * (1 + rng.normal(0, 0.004, len(dates)))

        raw = pd.DataFrame(
            {
                "date": dates,
                "stock_id": "TEST",
                "open": open_price,
                "high": np.maximum(open_price, close) * 1.01,
                "low": np.minimum(open_price, close) * 0.99,
                "close": close,
                "volume": rng.integers(1_000_000, 5_000_000, len(dates)),
            }
        )
        cls.stock = add_indicators(raw, 14)
        cls.benchmark = pd.DataFrame({"date": dates, "close": benchmark_close})
        cls.industry = pd.DataFrame({"date": dates, "close": industry_close})

    def test_reference_features_do_not_create_future_target(self) -> None:
        features = build_ml_feature_frame(self.stock, self.benchmark, self.industry)
        self.assertIn("relative_return_20d", features)
        self.assertIn("industry_relative_20d", features)
        self.assertTrue(pd.isna(features.iloc[-1]["target_up_next_day"]))

    def test_short_and_medium_models_run(self) -> None:
        short_signal = train_ml_signal(self.stock, self.benchmark, self.industry)
        potential_signal = train_potential_signal(self.stock, self.benchmark, self.industry)
        self.assertEqual(short_signal.status, "ok", short_signal.message)
        self.assertEqual(potential_signal.status, "ok", potential_signal.message)
        self.assertGreater(short_signal.feature_count, 11)
        self.assertGreater(potential_signal.feature_count, 15)
        self.assertIsNotNone(potential_signal.outperform_probability)

    def test_industry_basket_is_normalized(self) -> None:
        frame_a = self.benchmark.iloc[:30]
        frame_b = self.industry.iloc[:30]
        basket = build_industry_basket([frame_a, frame_b])
        self.assertFalse(basket.empty)
        self.assertAlmostEqual(float(basket.iloc[0]["close"]), 100.0)

    def test_ai_prompt_contains_new_research_inputs(self) -> None:
        themes, candidates = load_industry_data(Path("industry_chain.json"))
        del themes
        prompt = build_ai_prompt(
            "3037",
            self.stock.tail(180).reset_index(drop=True),
            14,
            [NewsItem("測試新聞", "Test", "2026-06-20", "https://example.com")],
            MLSignal(
                status="ok",
                model_name="Random Forest",
                prediction_label="偏多",
                up_probability=0.6,
                down_probability=0.4,
                train_accuracy=0.7,
                test_accuracy=0.55,
                sample_count=300,
                feature_count=19,
            ),
            FundamentalInfo(status="ok", eps=8.0, eps_date="2026-03-31"),
            PotentialSignal(
                status="ok",
                model_name="Logistic Regression",
                prediction_label="中期相對強勢",
                outperform_probability=0.58,
                underperform_probability=0.42,
                train_accuracy=0.65,
                test_accuracy=0.54,
                sample_count=280,
                feature_count=21,
            ),
            RevenueInfo(
                status="ok",
                latest_revenue=12_000_000_000,
                revenue_year=2026,
                revenue_month=5,
                month_over_month=0.05,
                year_over_year=0.2,
            ),
            industry_profiles_for_symbol(candidates, "3037"),
        )
        self.assertIn("ABF載板", prompt)
        self.assertIn("中期潛力", prompt)
        self.assertIn("月營收", prompt)
        self.assertIn("曝險尚未證實", prompt)


if __name__ == "__main__":
    unittest.main()
