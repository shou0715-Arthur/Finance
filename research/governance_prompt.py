from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GovernancePromptContext:
    summary: dict[str, int]
    cluster_buying: bool
    unusual_selling: bool
    warnings: list[str]


def build_governance_prompt_context(summary: dict[str, int], cluster_buying: bool, unusual_selling: bool) -> GovernancePromptContext:
    warnings: list[str] = []
    if cluster_buying:
        warnings.append("Cluster buying may be a positive governance/sentiment signal, but requires Form 4 tie-out.")
    if unusual_selling:
        warnings.append("Unusual selling requires classification: 10b5-1, tax, option exercise, or discretionary sale.")
    return GovernancePromptContext(summary, cluster_buying, unusual_selling, warnings)

