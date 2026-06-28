from __future__ import annotations

from dataclasses import dataclass

from research.event_extractor import ExtractedEvent


@dataclass(frozen=True)
class CatalystEvent:
    ticker: str
    event_date: str
    event_type: str
    title: str
    relevance: float
    expected_impact: str
    action_required: str


def build_catalyst_calendar(ticker: str, events: list[ExtractedEvent], *, min_relevance: float = 0.0) -> list[CatalystEvent]:
    calendar: list[CatalystEvent] = []
    for event in events:
        relevance = min(abs(event.sentiment_score) + (0.5 if event.event_type != "general" else 0.1), 1.0)
        if relevance < min_relevance:
            continue
        impact = "positive" if event.sentiment_score > 0 else "negative" if event.sentiment_score < 0 else "watch"
        calendar.append(
            CatalystEvent(
                ticker=ticker.upper(),
                event_date=event.published,
                event_type=event.event_type,
                title=event.title,
                relevance=relevance,
                expected_impact=impact,
                action_required="review" if relevance >= 0.5 else "monitor",
            )
        )
    return calendar

