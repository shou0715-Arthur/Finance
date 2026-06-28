from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FinMindRecord:
    dataset: str
    data_id: str
    date: str
    fields: dict[str, Any]


def normalize_finmind_records(dataset: str, data_id: str, rows: list[dict[str, Any]]) -> list[FinMindRecord]:
    records: list[FinMindRecord] = []
    for row in rows:
        date = str(row.get("date") or row.get("origin_name") or "")
        fields = {key: value for key, value in row.items() if key not in {"date", "data_id"}}
        records.append(FinMindRecord(dataset=dataset, data_id=data_id, date=date, fields=fields))
    return records


def extract_latest_finmind_record(records: list[FinMindRecord]) -> FinMindRecord | None:
    if not records:
        return None
    return sorted(records, key=lambda record: record.date)[-1]

