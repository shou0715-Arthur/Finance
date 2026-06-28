from __future__ import annotations

POSITIVE_WORDS = {"beat", "growth", "upgrade", "record", "strong", "surge", "上修", "成長", "創高", "強勁"}
NEGATIVE_WORDS = {"miss", "downgrade", "weak", "decline", "risk", "lawsuit", "下修", "衰退", "疲弱", "風險"}


def score_sentiment(text: str) -> float:
    lower = text.lower()
    positive = sum(1 for word in POSITIVE_WORDS if word in lower)
    negative = sum(1 for word in NEGATIVE_WORDS if word in lower)
    total = positive + negative
    if total == 0:
        return 0.0
    return (positive - negative) / total


def score_news_relevance(text: str, keywords: list[str]) -> float:
    lower = text.lower()
    if not keywords:
        return 0.0
    hits = sum(1 for keyword in keywords if keyword.lower() in lower)
    return hits / len(keywords)

