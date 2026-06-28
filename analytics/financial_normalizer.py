from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class NormalizedFinancials:
    ticker: str
    fiscal_period: str
    currency: str
    income_statement: dict[str, float | None] = field(default_factory=dict)
    balance_sheet: dict[str, float | None] = field(default_factory=dict)
    cash_flow: dict[str, float | None] = field(default_factory=dict)
    source: str = ""
    warnings: list[str] = field(default_factory=list)


FIELD_ALIASES = {
    "revenue": ("revenue", "Revenue", "營業收入", "totalRevenue"),
    "gross_profit": ("grossProfit", "Gross Profit", "gross_profit", "營業毛利"),
    "operating_income": ("operatingIncome", "Operating Income", "operating_income", "營業利益"),
    "net_income": ("netIncome", "Net Income", "net_income", "本期淨利"),
    "total_assets": ("totalAssets", "Total Assets", "total_assets", "資產總計"),
    "total_liabilities": ("totalLiabilities", "Total Liabilities", "total_liabilities", "負債總計"),
    "equity": ("totalStockholdersEquity", "Total Equity", "equity", "權益總計"),
    "operating_cash_flow": ("operatingCashFlow", "Operating Cash Flow", "operating_cash_flow", "營業活動現金流量"),
    "capex": ("capitalExpenditure", "Capital Expenditure", "capex", "資本支出"),
    "free_cash_flow": ("freeCashFlow", "Free Cash Flow", "free_cash_flow", "自由現金流"),
}


def to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None


def pick_field(row: dict[str, Any], canonical_name: str) -> float | None:
    for alias in FIELD_ALIASES[canonical_name]:
        if alias in row:
            return to_float(row[alias])
    return None


def normalize_financial_row(ticker: str, row: dict[str, Any], *, source: str = "") -> NormalizedFinancials:
    fiscal_period = str(row.get("date") or row.get("fiscal_period") or row.get("period") or "")
    currency = str(row.get("currency") or row.get("reportedCurrency") or "TWD")
    income = {key: pick_field(row, key) for key in ("revenue", "gross_profit", "operating_income", "net_income")}
    balance = {key: pick_field(row, key) for key in ("total_assets", "total_liabilities", "equity")}
    cash_flow = {key: pick_field(row, key) for key in ("operating_cash_flow", "capex", "free_cash_flow")}
    warnings = [key for key, value in {**income, **balance, **cash_flow}.items() if value is None]
    return NormalizedFinancials(
        ticker=ticker.upper(),
        fiscal_period=fiscal_period,
        currency=currency,
        income_statement=income,
        balance_sheet=balance,
        cash_flow=cash_flow,
        source=source,
        warnings=[f"missing:{key}" for key in warnings],
    )

