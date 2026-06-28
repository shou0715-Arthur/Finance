from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketSentimentSnapshot:
    vix: float | None = None
    fear_greed: float | None = None
    aaii_bullish: float | None = None


def classify_market_regime(snapshot: MarketSentimentSnapshot) -> str:
    if snapshot.vix is not None and snapshot.vix >= 30:
        return "risk_off"
    if snapshot.fear_greed is not None and snapshot.fear_greed >= 75:
        return "euphoric"
    if snapshot.fear_greed is not None and snapshot.fear_greed <= 25:
        return "fearful"
    return "neutral"

