from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionJournalEntry:
    ticker: str
    thesis: str
    action: str
    confidence: float
    expected_catalyst: str
    invalidation: str
    outcome: str = ""


def create_decision_journal_entry(ticker: str, thesis: str, action: str, confidence: float, expected_catalyst: str, invalidation: str) -> DecisionJournalEntry:
    if not 0 <= confidence <= 1:
        raise ValueError("Confidence must be between 0 and 1.")
    return DecisionJournalEntry(ticker=ticker.upper(), thesis=thesis, action=action, confidence=confidence, expected_catalyst=expected_catalyst, invalidation=invalidation)


def evaluate_decision_quality(entry: DecisionJournalEntry) -> str:
    if not entry.thesis or not entry.invalidation:
        return "incomplete"
    if entry.outcome and entry.outcome.lower() in {"hit", "validated"}:
        return "validated"
    if entry.outcome and entry.outcome.lower() in {"miss", "invalidated"}:
        return "invalidated"
    return "pending"

