from __future__ import annotations

from research.behavioral_checklist import build_behavioral_checklist
from research.decision_journal import create_decision_journal_entry
from research.thesis_tracker import update_thesis_status
from workflow.pipeline import Pipeline, WorkflowContext
from workflow.steps import FunctionStep, RequiredKeysStep


def journal_entry_step(context: WorkflowContext) -> WorkflowContext:
    entry = create_decision_journal_entry(
        str(context.data["ticker"]),
        str(context.data["thesis"]),
        str(context.data["action"]),
        float(context.data["confidence"]),
        str(context.data.get("expected_catalyst", "")),
        str(context.data.get("invalidation", "")),
    )
    return context.with_value("journal_entry", entry)


def behavioral_checklist_step(context: WorkflowContext) -> WorkflowContext:
    checklist = build_behavioral_checklist(
        has_disconfirmers=bool(context.data.get("invalidation")),
        has_position_limit=bool(context.data.get("position_limit")),
        has_base_rate=bool(context.data.get("base_rate")),
        has_exit_rule=bool(context.data.get("exit_rule")),
    )
    return context.with_value("behavioral_checklist", checklist)


def thesis_status_step(context: WorkflowContext) -> WorkflowContext:
    status = update_thesis_status(
        str(context.data["ticker"]),
        str(context.data.get("thesis_id", "default")),
        list(context.data.get("evidence", [])),
        list(context.data.get("disconfirmers", [])),
    )
    return context.with_value("thesis_status", status)


def build_journal_workflow() -> Pipeline:
    return Pipeline(
        [
            RequiredKeysStep("require_journal_inputs", ("ticker", "thesis", "action", "confidence")),
            FunctionStep("create_journal_entry", journal_entry_step),
            FunctionStep("build_behavioral_checklist", behavioral_checklist_step),
            FunctionStep("update_thesis_status", thesis_status_step),
        ],
        name="journal",
    )

