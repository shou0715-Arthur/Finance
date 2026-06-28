from __future__ import annotations

from analytics.insider_analysis import detect_cluster_buying, detect_unusual_selling, summarize_insider_activity
from data_sources.insider_client import normalize_insider_transactions
from research.governance_prompt import build_governance_prompt_context
from workflow.pipeline import Pipeline, WorkflowContext
from workflow.steps import FunctionStep, RequiredKeysStep


def normalize_insider_step(context: WorkflowContext) -> WorkflowContext:
    transactions = normalize_insider_transactions(str(context.data["symbol"]), context.data["insider_rows"])
    return context.with_value("insider_transactions", transactions)


def insider_analysis_step(context: WorkflowContext) -> WorkflowContext:
    transactions = context.data["insider_transactions"]
    summary = summarize_insider_activity(transactions)
    cluster = detect_cluster_buying(transactions)
    unusual = detect_unusual_selling(transactions, float(context.data.get("sell_threshold", 100_000)))
    return context.with_value("insider_summary", summary).with_value("cluster_buying", cluster).with_value("unusual_selling", unusual)


def governance_prompt_step(context: WorkflowContext) -> WorkflowContext:
    prompt_context = build_governance_prompt_context(context.data["insider_summary"], context.data["cluster_buying"], context.data["unusual_selling"])
    return context.with_value("governance_prompt_context", prompt_context)


def build_governance_workflow() -> Pipeline:
    return Pipeline(
        [
            RequiredKeysStep("require_governance_inputs", ("symbol", "insider_rows")),
            FunctionStep("normalize_insider_transactions", normalize_insider_step),
            FunctionStep("analyze_insider_transactions", insider_analysis_step),
            FunctionStep("build_governance_prompt_context", governance_prompt_step),
        ],
        name="governance",
    )

