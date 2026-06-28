from __future__ import annotations

from analytics.etf_exposure import calculate_group_exposure, calculate_top_holdings_summary, detect_ptp_exposure
from data_sources.etf_files import load_etf_holdings_file
from research.etf_prompt import build_etf_prompt_context
from workflow.pipeline import Pipeline, WorkflowContext
from workflow.steps import FunctionStep, RequiredKeysStep


def load_holdings_step(context: WorkflowContext) -> WorkflowContext:
    holdings = load_etf_holdings_file(context.data["holdings_path"])
    return context.with_value("holdings", holdings)


def build_exposure_step(context: WorkflowContext) -> WorkflowContext:
    holdings = context.data["holdings"]
    country_mapping = context.data.get("country_mapping", {})
    sector_mapping = context.data.get("sector_mapping", {})
    country = calculate_group_exposure(holdings, country_mapping)
    sector = calculate_group_exposure(holdings, sector_mapping)
    return context.with_value("country_exposure", country).with_value("sector_exposure", sector)


def build_etf_context_step(context: WorkflowContext) -> WorkflowContext:
    holdings = context.data["holdings"]
    ptp_symbols = context.data.get("ptp_symbols", set())
    top = calculate_top_holdings_summary(holdings, limit=int(context.data.get("top_limit", 10)))
    ptp = detect_ptp_exposure(holdings, ptp_symbols)
    country = context.data["country_exposure"]
    sector = context.data["sector_exposure"]
    prompt_context = build_etf_prompt_context(
        str(context.data["symbol"]),
        holdings,
        top,
        country_exposure=country.exposure,
        sector_exposure=sector.exposure,
        ptp_holdings=ptp,
        missing_data=country.missing_identifiers + sector.missing_identifiers,
    )
    return context.with_value("etf_prompt_context", prompt_context)


def build_etf_analysis_workflow() -> Pipeline:
    return Pipeline(
        [
            RequiredKeysStep("require_etf_inputs", ("symbol", "holdings_path")),
            FunctionStep("load_holdings", load_holdings_step),
            FunctionStep("build_exposure", build_exposure_step),
            FunctionStep("build_etf_context", build_etf_context_step),
        ],
        name="etf_analysis",
    )

