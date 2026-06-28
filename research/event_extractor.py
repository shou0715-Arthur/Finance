from __future__ import annotations

from dataclasses import dataclass

from data_sources.news_client import NewsRecord
from analytics.sentiment import score_sentiment


@dataclass(frozen=True)
class ExtractedEvent:
    title: str
    event_type: str
    sentiment_score: float
    source: str
    published: str = ""


EVENT_KEYWORDS = {
    "earnings": ("earnings", "eps", "財報", "法說"),
    "guidance": ("guidance", "forecast", "展望", "財測"),
    "regulatory": ("regulator", "lawsuit", "sec", "監管", "訴訟"),
    "product": ("launch", "product", "新產品", "發布"),
}


def classify_event_type(text: str) -> str:
    lower = text.lower()
    for event_type, keywords in EVENT_KEYWORDS.items():
        if any(keyword in lower for keyword in keywords):
            return event_type
    return "general"


def extract_events(news_records: list[NewsRecord]) -> list[ExtractedEvent]:
    return [
        ExtractedEvent(
            title=record.title,
            event_type=classify_event_type(record.title + " " + record.summary),
            sentiment_score=score_sentiment(record.title + " " + record.summary),
            source=record.source,
            published=record.published,
        )
        for record in news_records
    ]

