from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NewsRecord:
    title: str
    source: str
    published: str = ""
    link: str = ""
    summary: str = ""


def normalize_news_records(rows: list[dict[str, str]]) -> list[NewsRecord]:
    return [
        NewsRecord(
            title=str(row.get("title", "")).strip(),
            source=str(row.get("source", "")).strip() or "Unknown",
            published=str(row.get("published", "")).strip(),
            link=str(row.get("link", "")).strip(),
            summary=str(row.get("summary", "")).strip(),
        )
        for row in rows
        if str(row.get("title", "")).strip()
    ]


def deduplicate_news(records: list[NewsRecord]) -> list[NewsRecord]:
    seen: set[tuple[str, str]] = set()
    unique: list[NewsRecord] = []
    for record in records:
        key = (record.title.lower(), record.source.lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)
    return unique

