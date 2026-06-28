from __future__ import annotations

from dataclasses import dataclass
import csv
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ParsedStatementFile:
    path: Path
    records: list[dict[str, Any]]
    source_type: str


def parse_json_statement_file(path: Path) -> ParsedStatementFile:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, dict):
        records = data.get("data") if isinstance(data.get("data"), list) else [data]
    elif isinstance(data, list):
        records = data
    else:
        records = []
    return ParsedStatementFile(path=path, records=[dict(record) for record in records if isinstance(record, dict)], source_type="json")


def parse_csv_statement_file(path: Path) -> ParsedStatementFile:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        records = list(csv.DictReader(handle))
    return ParsedStatementFile(path=path, records=records, source_type="csv")


def parse_statement_file(path: Path) -> ParsedStatementFile:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return parse_json_statement_file(path)
    if suffix == ".csv":
        return parse_csv_statement_file(path)
    raise ValueError(f"Unsupported statement file type: {path.suffix}")

