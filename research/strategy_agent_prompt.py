from __future__ import annotations


def build_strategy_agent_guardrails() -> str:
    return (
        "LLM may explain deterministic Python strategy outputs, but must not invent signals, "
        "ignore transaction costs, or describe backtest results as guaranteed future returns."
    )

