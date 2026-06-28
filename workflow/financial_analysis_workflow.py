from __future__ import annotations

from analytics.financial_normalizer import normalize_financial_row
from research.source_packet import SourceItem, build_source_packet
from workflow.pipeline import Pipeline, WorkflowContext
from workflow.steps import FunctionStep, RequiredKeysStep


def normalize_financials_step(context: WorkflowContext) -> WorkflowContext:
    financial_row = context.data["financial_row"]
    ticker = str(context.data["ticker"])
    normalized = normalize_financial_row(ticker, financial_row, source=str(context.data.get("source", "")))
    return context.with_value("normalized_financials", normalized)


def source_packet_step(context: WorkflowContext) -> WorkflowContext:
    ticker = str(context.data["ticker"])
    source = str(context.data.get("source", "financial_row"))
    items = [
        SourceItem(name=source, source_type="income_statement", confidence=0.7),
        SourceItem(name=source, source_type="balance_sheet", confidence=0.7),
        SourceItem(name=source, source_type="cash_flow", confidence=0.7),
    ]
    return context.with_value("source_packet", build_source_packet(ticker, items))


def build_financial_analysis_workflow() -> Pipeline:
    return Pipeline(
        [
            RequiredKeysStep("require_financial_inputs", ("ticker", "financial_row")),
            FunctionStep("normalize_financials", normalize_financials_step),
            FunctionStep("build_source_packet", source_packet_step),
        ],
        name="financial_analysis",
    )

