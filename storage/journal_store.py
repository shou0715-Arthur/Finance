from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from research.decision_journal import DecisionJournalEntry


def save_journal_entries(path: Path, entries: list[DecisionJournalEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([asdict(entry) for entry in entries], ensure_ascii=False, indent=2), encoding="utf-8")


def load_journal_entries(path: Path) -> list[DecisionJournalEntry]:
    if not path.exists():
        return []
    rows = json.loads(path.read_text(encoding="utf-8-sig"))
    return [DecisionJournalEntry(**row) for row in rows]

