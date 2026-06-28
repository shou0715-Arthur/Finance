from __future__ import annotations

from analytics.diversification import calculate_concentration, calculate_position_weights
from analytics.portfolio_risk import calculate_cvar, calculate_var, calculate_volatility
from analytics.stress_test import run_macro_shock
from research.risk_prompt import build_risk_prompt_context
from workflow.pipeline import Pipeline, WorkflowContext
from workflow.steps import FunctionStep, RequiredKeysStep


def weights_step(context: WorkflowContext) -> WorkflowContext:
    weights = calculate_position_weights(context.data["position_values"])
    return context.with_value("weights", weights)


def risk_metrics_step(context: WorkflowContext) -> WorkflowContext:
    returns = list(context.data.get("portfolio_returns", []))
    return (
        context.with_value("concentration", calculate_concentration(context.data["weights"]))
        .with_value("volatility", calculate_volatility(returns))
        .with_value("var", calculate_var(returns))
        .with_value("cvar", calculate_cvar(returns))
    )


def stress_step(context: WorkflowContext) -> WorkflowContext:
    shock = float(context.data.get("macro_shock", -0.1))
    return context.with_value("stress_losses", {"macro": run_macro_shock(context.data["weights"], shock)})


def risk_prompt_step(context: WorkflowContext) -> WorkflowContext:
    prompt_context = build_risk_prompt_context(
        context.data["weights"],
        context.data["concentration"],
        context.data["volatility"],
        context.data["var"],
        context.data["cvar"],
        context.data["stress_losses"],
    )
    return context.with_value("risk_prompt_context", prompt_context)


def build_portfolio_risk_workflow() -> Pipeline:
    return Pipeline(
        [
            RequiredKeysStep("require_portfolio_inputs", ("position_values",)),
            FunctionStep("calculate_weights", weights_step),
            FunctionStep("calculate_risk_metrics", risk_metrics_step),
            FunctionStep("run_stress", stress_step),
            FunctionStep("build_risk_prompt_context", risk_prompt_step),
        ],
        name="portfolio_risk",
    )

