from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from workflow.pipeline import Pipeline, WorkflowContext, WorkflowStep


@dataclass
class FunctionStep:
    name: str
    function: Callable[[WorkflowContext], WorkflowContext]

    def run(self, context: WorkflowContext) -> WorkflowContext:
        return self.function(context)


@dataclass
class RequiredKeysStep:
    name: str
    required_keys: tuple[str, ...]

    def run(self, context: WorkflowContext) -> WorkflowContext:
        missing = [key for key in self.required_keys if key not in context.data]
        if missing:
            raise KeyError(f"Missing required context keys: {', '.join(missing)}")
        return context


@dataclass
class BranchStep:
    name: str
    predicate: Callable[[WorkflowContext], bool]
    true_steps: list[WorkflowStep]
    false_steps: list[WorkflowStep]

    def run(self, context: WorkflowContext) -> WorkflowContext:
        selected_steps = self.true_steps if self.predicate(context) else self.false_steps
        result = Pipeline(selected_steps, name=f"{self.name}.branch").run(context)
        if not result.ok:
            raise RuntimeError("; ".join(result.errors))
        return result.context

