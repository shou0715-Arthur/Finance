from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BehavioralChecklist:
    overconfidence: bool
    anchoring: bool
    confirmation_bias: bool
    loss_aversion: bool
    checklist_items: list[str]


def build_behavioral_checklist(*, has_disconfirmers: bool, has_position_limit: bool, has_base_rate: bool, has_exit_rule: bool) -> BehavioralChecklist:
    return BehavioralChecklist(
        overconfidence=not has_base_rate,
        anchoring=not has_exit_rule,
        confirmation_bias=not has_disconfirmers,
        loss_aversion=not has_position_limit,
        checklist_items=[
            "Write the disconfirming evidence before acting.",
            "Compare thesis to base rates and prior similar cases.",
            "Set position size and exit rule before entry.",
            "Review outcome against original thesis.",
        ],
    )

