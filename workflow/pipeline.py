from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Protocol


class WorkflowStep(Protocol):
    name: str

    def run(self, context: "WorkflowContext") -> "WorkflowContext":
        ...


@dataclass(frozen=True)
class WorkflowContext:
    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def with_value(self, key: str, value: Any) -> "WorkflowContext":
        next_data = dict(self.data)
        next_data[key] = value
        return WorkflowContext(data=next_data, metadata=dict(self.metadata))

    def with_metadata(self, key: str, value: Any) -> "WorkflowContext":
        next_metadata = dict(self.metadata)
        next_metadata[key] = value
        return WorkflowContext(data=dict(self.data), metadata=next_metadata)


@dataclass(frozen=True)
class StepExecution:
    name: str
    ok: bool
    started_at: datetime
    ended_at: datetime
    error: str = ""

    @property
    def duration_seconds(self) -> float:
        return max((self.ended_at - self.started_at).total_seconds(), 0.0)


@dataclass(frozen=True)
class PipelineResult:
    context: WorkflowContext
    executions: list[StepExecution]

    @property
    def ok(self) -> bool:
        return all(execution.ok for execution in self.executions)

    @property
    def errors(self) -> list[str]:
        return [execution.error for execution in self.executions if execution.error]


def ensure_context(value: WorkflowContext | Mapping[str, Any] | None = None) -> WorkflowContext:
    if value is None:
        return WorkflowContext()
    if isinstance(value, WorkflowContext):
        return value
    return WorkflowContext(data=dict(value))


class Pipeline:
    def __init__(self, steps: list[WorkflowStep], *, name: str = "pipeline", stop_on_error: bool = True) -> None:
        self.name = name
        self.steps = list(steps)
        self.stop_on_error = stop_on_error

    def run(self, initial_context: WorkflowContext | Mapping[str, Any] | None = None) -> PipelineResult:
        context = ensure_context(initial_context)
        executions: list[StepExecution] = []
        for step in self.steps:
            started_at = datetime.now(timezone.utc)
            try:
                context = step.run(context)
                executions.append(
                    StepExecution(
                        name=step.name,
                        ok=True,
                        started_at=started_at,
                        ended_at=datetime.now(timezone.utc),
                    )
                )
            except Exception as exc:
                executions.append(
                    StepExecution(
                        name=step.name,
                        ok=False,
                        started_at=started_at,
                        ended_at=datetime.now(timezone.utc),
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )
                if self.stop_on_error:
                    break
        return PipelineResult(context=context, executions=executions)

