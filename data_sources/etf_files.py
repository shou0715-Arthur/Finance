from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analytics.etf_overlap import Holding, make_holding


def load_json_holdings(path: Path) -> list[Holding]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, dict):
        rows = data.get("holdings") or data.get("data") or []
    else:
        rows = data
    return [make_holding(row) for row in rows if isinstance(row, dict)]


def load_ref_data_txt_holdings(path: Path) -> list[Holding]:
    """Load Ref-data ETF holdings text files that contain JSON-like arrays."""

    text = path.read_text(encoding="utf-8-sig")
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"Could not locate JSON array in ETF holdings file: {path}")
    rows: Any = json.loads(text[start : end + 1])
    return [make_holding(row) for row in rows if isinstance(row, dict)]


def load_etf_holdings_file(path: Path) -> list[Holding]:
    if path.suffix.lower() == ".json":
        return load_json_holdings(path)
    if path.suffix.lower() == ".txt":
        return load_ref_data_txt_holdings(path)
    raise ValueError(f"Unsupported ETF holdings file type: {path.suffix}")


def load_ptp_symbols(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8-sig", errors="ignore")
    symbols: set[str] = set()
    for line in text.splitlines():
        tokens = [token.strip().upper() for token in line.replace(",", " ").split()]
        for token in tokens:
            if token.isalnum() and 1 <= len(token) <= 8:
                symbols.add(token)
    return symbols

