from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class ScheduledWorkflow:
    workflow_name: str
    interval_seconds: int
    last_run_at: datetime | None = None

    def is_due(self, now: datetime | None = None) -> bool:
        current_time = now or datetime.now(timezone.utc)
        if self.last_run_at is None:
            return True
        return current_time - self.last_run_at >= timedelta(seconds=self.interval_seconds)

    def mark_run(self, now: datetime | None = None) -> None:
        self.last_run_at = now or datetime.now(timezone.utc)

