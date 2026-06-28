from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from workflow.pipeline import PipelineResult


@dataclass(frozen=True)
class ExecutionLogRecord:
    workflow_name: str
    ok: bool
    steps: list[dict[str, Any]]
    errors: list[str]


@dataclass
class ExecutionLog:
    records: list[ExecutionLogRecord] = field(default_factory=list)

    def append_result(self, workflow_name: str, result: PipelineResult) -> ExecutionLogRecord:
        record = ExecutionLogRecord(
            workflow_name=workflow_name,
            ok=result.ok,
            steps=[
                {
                    "name": execution.name,
                    "ok": execution.ok,
                    "started_at": execution.started_at.isoformat(),
                    "ended_at": execution.ended_at.isoformat(),
                    "duration_seconds": execution.duration_seconds,
                    "error": execution.error,
                }
                for execution in result.executions
            ],
            errors=result.errors,
        )
        self.records.append(record)
        return record

    def to_jsonable(self) -> list[dict[str, Any]]:
        return [
            {
                "workflow_name": record.workflow_name,
                "ok": record.ok,
                "steps": record.steps,
                "errors": record.errors,
            }
            for record in self.records
        ]

    def save_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_jsonable(), ensure_ascii=False, indent=2), encoding="utf-8")


def load_execution_log(path: Path) -> ExecutionLog:
    if not path.exists():
        return ExecutionLog()
    raw_records = json.loads(path.read_text(encoding="utf-8-sig"))
    log = ExecutionLog()
    for raw in raw_records:
        log.records.append(
            ExecutionLogRecord(
                workflow_name=str(raw["workflow_name"]),
                ok=bool(raw["ok"]),
                steps=list(raw.get("steps", [])),
                errors=list(raw.get("errors", [])),
            )
        )
    return log

