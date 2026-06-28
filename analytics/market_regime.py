from __future__ import annotations

from data_sources.market_sentiment_client import MarketSentimentSnapshot, classify_market_regime


def build_market_regime_summary(snapshot: MarketSentimentSnapshot) -> dict[str, float | str | None]:
    return {
        "regime": classify_market_regime(snapshot),
        "vix": snapshot.vix,
        "fear_greed": snapshot.fear_greed,
        "aaii_bullish": snapshot.aaii_bullish,
    }

