from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FMPStatementRecord:
    symbol: str
    period: str
    fiscal_year: str
    currency: str
    fields: dict[str, Any]


def normalize_fmp_statement_rows(symbol: str, rows: list[dict[str, Any]]) -> list[FMPStatementRecord]:
    records: list[FMPStatementRecord] = []
    for row in rows:
        records.append(
            FMPStatementRecord(
                symbol=symbol.upper(),
                period=str(row.get("period") or row.get("fiscalPeriod") or ""),
                fiscal_year=str(row.get("calendarYear") or row.get("fiscalYear") or ""),
                currency=str(row.get("reportedCurrency") or row.get("currency") or ""),
                fields={key: value for key, value in row.items() if key not in {"period", "calendarYear", "fiscalYear", "reportedCurrency", "currency"}},
            )
        )
    return records


def latest_fmp_statement(records: list[FMPStatementRecord]) -> FMPStatementRecord | None:
    if not records:
        return None
    return sorted(records, key=lambda record: (record.fiscal_year, record.period))[-1]

