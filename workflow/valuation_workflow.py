from __future__ import annotations

from analytics.dcf import DCFInputs, build_dcf_model
from analytics.scenario import ScenarioAssumption, probability_weighted_value, run_dcf_scenarios
from analytics.valuation_methods import select_valuation_methods
from research.valuation_prompt import build_valuation_prompt_context
from workflow.pipeline import Pipeline, WorkflowContext
from workflow.steps import FunctionStep, RequiredKeysStep


def valuation_method_step(context: WorkflowContext) -> WorkflowContext:
    rec = select_valuation_methods(
        str(context.data.get("security_type", "stock")),
        has_cash_flow=bool(context.data.get("has_cash_flow", True)),
        is_financial_company=bool(context.data.get("is_financial_company", False)),
    )
    return context.with_value("valuation_methods", rec)


def dcf_step(context: WorkflowContext) -> WorkflowContext:
    inputs: DCFInputs = context.data["dcf_inputs"]
    return context.with_value("dcf_result", build_dcf_model(inputs))


def scenarios_step(context: WorkflowContext) -> WorkflowContext:
    inputs: DCFInputs = context.data["dcf_inputs"]
    scenarios: list[ScenarioAssumption] = context.data.get("scenarios", [])
    results = run_dcf_scenarios(inputs, scenarios) if scenarios else []
    return context.with_value("scenario_results", results).with_value("probability_weighted_value", probability_weighted_value(results) if results else None)


def valuation_prompt_context_step(context: WorkflowContext) -> WorkflowContext:
    methods = context.data["valuation_methods"]
    scenarios = {result.name.lower(): result.dcf_result.value_per_share for result in context.data.get("scenario_results", [])}
    prompt_context = build_valuation_prompt_context(
        methods.preferred_methods,
        scenarios,
        {"discount_rate": context.data["dcf_inputs"].discount_rate, "terminal_growth_rate": context.data["dcf_inputs"].terminal_growth_rate},
        methods.rejected_methods,
    )
    return context.with_value("valuation_prompt_context", prompt_context)


def build_valuation_workflow() -> Pipeline:
    return Pipeline(
        [
            RequiredKeysStep("require_valuation_inputs", ("dcf_inputs",)),
            FunctionStep("select_valuation_methods", valuation_method_step),
            FunctionStep("build_dcf", dcf_step),
            FunctionStep("run_scenarios", scenarios_step),
            FunctionStep("build_valuation_prompt_context", valuation_prompt_context_step),
        ],
        name="valuation",
    )

