from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThesisStatus:
    ticker: str
    thesis_id: str
    status: str
    evidence: list[str]


def update_thesis_status(ticker: str, thesis_id: str, evidence: list[str], disconfirmers: list[str]) -> ThesisStatus:
    if disconfirmers:
        status = "challenged"
    elif evidence:
        status = "active"
    else:
        status = "unproven"
    return ThesisStatus(ticker=ticker.upper(), thesis_id=thesis_id, status=status, evidence=evidence)

