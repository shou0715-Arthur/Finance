from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from research.catalyst_calendar import CatalystEvent


def save_events(path: Path, events: list[CatalystEvent]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([asdict(event) for event in events], ensure_ascii=False, indent=2), encoding="utf-8")


def load_events(path: Path) -> list[CatalystEvent]:
    if not path.exists():
        return []
    rows = json.loads(path.read_text(encoding="utf-8-sig"))
    return [CatalystEvent(**row) for row in rows]

