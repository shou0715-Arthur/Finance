from __future__ import annotations

import json
import os
import sys
import threading
import webbrowser
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

if getattr(sys, "frozen", False):
    PROJECT_ROOT = Path(sys.executable).resolve().parent
else:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
import numpy as np
import pandas as pd
import requests
import tkinter as tk
from tkinter import messagebox, ttk

from app.config import PREFERRED_GEMINI_MODEL
from app.self_control import run_startup_self_controls
from data_sources.gemini_client import generate_content_with_fallback
from research.public_equity_prompt import build_local_public_equity_note, build_public_equity_prompt


APP_VERSION = "v2.0"
FINMIND_API_URL = "https://api.finmindtrade.com/api/v4/data"
GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"
CONFIG_DIR = PROJECT_ROOT / "config"
API_KEY_FILE = CONFIG_DIR / "api-key.txt"
WATCHLIST_FILE = CONFIG_DIR / "watchlist.json"
DEFAULT_GEMINI_MODEL = PREFERRED_GEMINI_MODEL
APP_BG = "#f5f7fb"
PANEL_BG = "#ffffff"
TEXT_DARK = "#1f2937"
TEXT_MUTED = "#6b7280"
ACCENT = "#2563eb"
GAIN_COLOR = "#d93025"
LOSS_COLOR = "#188038"

DEFAULT_WATCHLIST = [
    {"symbol": "2330", "name": "TSMC"},
    {"symbol": "2317", "name": "Hon Hai"},
    {"symbol": "2454", "name": "MediaTek"},
    {"symbol": "2308", "name": "Delta Electronics"},
    {"symbol": "2412", "name": "Chunghwa Telecom"},
    {"symbol": "0050", "name": "Yuanta Taiwan 50 ETF"},
    {"symbol": "0056", "name": "Yuanta High Dividend ETF"},
]


@dataclass
class ApiKeys:
    finmind_api_key: str = ""
    gemini_api_key: str = ""


@dataclass
class NewsItem:
    title: str
    source: str
    published: str
    link: str


@dataclass
class MLSignal:
    status: str
    model_name: str = ""
    prediction_label: str = ""
    up_probability: float | None = None
    down_probability: float | None = None
    train_accuracy: float | None = None
    test_accuracy: float | None = None
    sample_count: int = 0
    feature_count: int = 0
    message: str = ""


@dataclass
class FundamentalInfo:
    status: str = "not_loaded"
    eps: float | None = None
    eps_date: str = ""
    dividend_year: str = ""
    cash_dividend: float | None = None
    stock_dividend: float | None = None
    cash_ex_dividend_date: str = ""
    cash_payment_date: str = ""
    cash_payment_month: str = ""
    stock_ex_dividend_date: str = ""
    announcement_date: str = ""
    message: str = ""


@dataclass
class GeminiAnalysisResult:
    report: str
    model_name: str
    attempts: list[str]
    source_packet: str
    ref_data_status: str


def configure_gui_fonts() -> None:
    """Reserved for future GUI font setup."""
    return


def ensure_api_key_file() -> None:
    if API_KEY_FILE.exists():
        return
    API_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    API_KEY_FILE.write_text(
        "\n".join(
            [
                "# AI Stock API keys",
                "FINMIND_API_KEY=",
                "GEMINI_API_KEY=",
                "",
            ]
        ),
        encoding="utf-8",
    )


def parse_api_key_file() -> ApiKeys:
    if not API_KEY_FILE.exists():
        ensure_api_key_file()
        return ApiKeys()

    values: dict[str, str] = {}
    bare_lines: list[str] = []
    for raw_line in API_KEY_FILE.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            bare_lines.append(line)
            continue
        key, value = line.split("=", 1)
        values[key.strip().upper()] = value.strip().strip('"').strip("'")

    finmind_key = values.get("FINMIND_API_KEY") or values.get("FINMIND_TOKEN") or ""
    if not finmind_key and bare_lines:
        finmind_key = bare_lines[0]
    gemini_key = values.get("GEMINI_API_KEY") or values.get("GOOGLE_API_KEY") or ""
    return ApiKeys(finmind_api_key=finmind_key, gemini_api_key=gemini_key)


def save_api_keys(keys: ApiKeys) -> None:
    API_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    API_KEY_FILE.write_text(
        "\n".join(
            [
                "# AI Stock API keys",
                "FINMIND_API_KEY=" + keys.finmind_api_key.strip(),
                "GEMINI_API_KEY=" + keys.gemini_api_key.strip(),
                "",
            ]
        ),
        encoding="utf-8",
    )


def mask_key(value: str) -> str:
    value = value.strip()
    if not value:
        return "Not set"
    if len(value) <= 8:
        return "Set ****"
    return f"Set {value[:4]}...{value[-4:]}"


def normalize_symbol(value: str) -> str:
    symbol = value.strip()
    if " " in symbol:
        symbol = symbol.split(" ", 1)[0]
    return symbol.upper().replace(".TW", "").replace(".TWO", "")


def load_watchlist() -> list[dict[str, str]]:
    if not WATCHLIST_FILE.exists():
        save_watchlist(DEFAULT_WATCHLIST)
        return list(DEFAULT_WATCHLIST)

    try:
        data = json.loads(WATCHLIST_FILE.read_text(encoding="utf-8-sig"))
    except Exception:
        return list(DEFAULT_WATCHLIST)

    items: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in data if isinstance(data, list) else []:
        if not isinstance(item, dict):
            continue
        symbol = normalize_symbol(str(item.get("symbol", "")))
        if not symbol or symbol in seen:
            continue
        name = str(item.get("name", "")).strip()
        items.append({"symbol": symbol, "name": name})
        seen.add(symbol)
    return items or list(DEFAULT_WATCHLIST)


def save_watchlist(items: list[dict[str, str]]) -> None:
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in items:
        symbol = normalize_symbol(str(item.get("symbol", "")))
        if not symbol or symbol in seen:
            continue
        normalized.append({"symbol": symbol, "name": str(item.get("name", "")).strip()})
        seen.add(symbol)
    WATCHLIST_FILE.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")


def display_name(item: dict[str, str]) -> str:
    name = item.get("name", "").strip()
    return f"{item['symbol']} {name}" if name else item["symbol"]


def fetch_finmind_stock_price(
    symbol: str,
    finmind_api_key: str,
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    headers = {}
    if finmind_api_key.strip():
        headers["Authorization"] = f"Bearer {finmind_api_key.strip()}"

    params = {
        "dataset": "TaiwanStockPrice",
        "data_id": symbol,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }

    try:
        response = requests.get(FINMIND_API_URL, params=params, headers=headers, timeout=30)
    except requests.exceptions.Timeout as exc:
        raise RuntimeError("FinMind API request timed out.") from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"FinMind API request failed: {exc}") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("FinMind API returned non-JSON response.") from exc

    rows: Any
    if isinstance(payload, dict):
        status = payload.get("status")
        msg = payload.get("msg") or payload.get("message") or payload.get("error")
        rows = payload.get("data", [])
        if status not in (None, 200, "200") and not rows:
            raise RuntimeError(f"FinMind API returned an error: {msg or status}")
    else:
        rows = payload

    if response.status_code >= 400:
        raise RuntimeError(f"FinMind API HTTP error: {response.status_code}")
    if not rows:
        raise RuntimeError(f"No FinMind price data returned for {symbol}.")

    df = pd.DataFrame(rows)
    required_columns = ["date", "stock_id", "open", "max", "min", "close", "Trading_Volume"]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise RuntimeError("FinMind response is missing columns: " + ", ".join(missing))

    result = pd.DataFrame(
        {
            "date": pd.to_datetime(df["date"], errors="coerce"),
            "stock_id": df["stock_id"].astype(str),
            "open": pd.to_numeric(df["open"], errors="coerce"),
            "high": pd.to_numeric(df["max"], errors="coerce"),
            "low": pd.to_numeric(df["min"], errors="coerce"),
            "close": pd.to_numeric(df["close"], errors="coerce"),
            "volume": pd.to_numeric(df["Trading_Volume"], errors="coerce"),
        }
    )
    result = result.dropna(subset=["date", "open", "high", "low", "close"])
    result = result.sort_values("date").drop_duplicates(subset=["date"]).reset_index(drop=True)
    if result.empty:
        raise RuntimeError("FinMind price data is empty after cleaning.")
    return result


def fetch_finmind_rows(
    dataset: str,
    symbol: str,
    finmind_api_key: str,
    start_date: date,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    headers = {}
    if finmind_api_key.strip():
        headers["Authorization"] = f"Bearer {finmind_api_key.strip()}"

    params: dict[str, Any] = {
        "dataset": dataset,
        "data_id": symbol,
        "start_date": start_date.isoformat(),
    }
    if end_date is not None:
        params["end_date"] = end_date.isoformat()

    try:
        response = requests.get(FINMIND_API_URL, params=params, headers=headers, timeout=30)
    except requests.exceptions.Timeout as exc:
        raise RuntimeError("FinMind API request timed out.") from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"FinMind API request failed: {exc}") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("FinMind API returned non-JSON response.") from exc

    if isinstance(payload, dict):
        status = payload.get("status")
        msg = payload.get("msg") or payload.get("message") or payload.get("error")
        rows = payload.get("data", [])
        if status not in (None, 200, "200") and not rows:
            raise RuntimeError(f"FinMind API returned an error: {msg or status}")
    else:
        rows = payload

    if response.status_code >= 400:
        raise RuntimeError(f"FinMind API HTTP error: {response.status_code}")
    return rows if isinstance(rows, list) else []


def _clean_date(value: Any) -> str:
    text = str(value or "").strip()
    return "" if text in {"", "0", "nan", "NaT"} else text


def _payment_month(value: str) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    return "" if pd.isna(parsed) else parsed.strftime("%Y-%m")


def fetch_fundamental_info(symbol: str, finmind_api_key: str) -> FundamentalInfo:
    start = date.today() - timedelta(days=365 * 8)
    end = date.today() + timedelta(days=365)
    info = FundamentalInfo(status="ok")
    messages: list[str] = []

    try:
        eps_rows = fetch_finmind_rows("TaiwanStockFinancialStatements", symbol, finmind_api_key, start, end)
        eps_df = pd.DataFrame(eps_rows)
        if not eps_df.empty and {"date", "type", "value"}.issubset(eps_df.columns):
            eps_df = eps_df[eps_df["type"] == "EPS"].copy()
            eps_df["date"] = pd.to_datetime(eps_df["date"], errors="coerce")
            eps_df["value"] = pd.to_numeric(eps_df["value"], errors="coerce")
            eps_df = eps_df.dropna(subset=["date", "value"]).sort_values("date")
            if not eps_df.empty:
                latest_eps = eps_df.iloc[-1]
                info.eps = float(latest_eps["value"])
                info.eps_date = latest_eps["date"].strftime("%Y-%m-%d")
            else:
                messages.append("?亦 EPS")
        else:
            messages.append("?亦 EPS")
    except Exception as exc:
        messages.append(f"EPS 霈?仃??{exc}")

    try:
        dividend_rows = fetch_finmind_rows("TaiwanStockDividend", symbol, finmind_api_key, start, end)
        div_df = pd.DataFrame(dividend_rows)
        if not div_df.empty:
            for col in [
                "CashEarningsDistribution",
                "CashStatutorySurplus",
                "StockEarningsDistribution",
                "StockStatutorySurplus",
            ]:
                div_df[col] = pd.to_numeric(div_df.get(col, 0), errors="coerce").fillna(0.0)
            div_df["cash_dividend"] = div_df["CashEarningsDistribution"] + div_df["CashStatutorySurplus"]
            div_df["stock_dividend"] = div_df["StockEarningsDistribution"] + div_df["StockStatutorySurplus"]
            div_df["payment_dt"] = pd.to_datetime(div_df.get("CashDividendPaymentDate", ""), errors="coerce")
            div_df["basis_dt"] = pd.to_datetime(div_df.get("date", ""), errors="coerce")
            useful = div_df[(div_df["cash_dividend"] > 0) | (div_df["stock_dividend"] > 0)].copy()
            if not useful.empty:
                today_ts = pd.Timestamp(date.today())
                upcoming = useful[useful["payment_dt"].notna() & (useful["payment_dt"] >= today_ts)].sort_values("payment_dt")
                row = upcoming.iloc[0] if not upcoming.empty else useful.sort_values(["payment_dt", "basis_dt"], na_position="first").iloc[-1]
                info.dividend_year = str(row.get("year", "")).strip()
                info.cash_dividend = float(row["cash_dividend"])
                info.stock_dividend = float(row["stock_dividend"])
                info.cash_ex_dividend_date = _clean_date(row.get("CashExDividendTradingDate", ""))
                info.cash_payment_date = _clean_date(row.get("CashDividendPaymentDate", ""))
                info.cash_payment_month = _payment_month(info.cash_payment_date)
                info.stock_ex_dividend_date = _clean_date(row.get("StockExDividendTradingDate", ""))
                info.announcement_date = _clean_date(row.get("AnnouncementDate", ""))
            else:
                messages.append("No dividend rows.")
        else:
            messages.append("No dividend rows.")
    except Exception as exc:
        messages.append(f"Dividend fetch failed: {exc}")

    info.message = "; ".join(messages)
    if info.eps is None and info.cash_dividend is None and info.stock_dividend is None:
        info.status = "unavailable"
    return info


def format_fundamental_summary(info: FundamentalInfo) -> str:
    eps_text = "EPS: n/a" if info.eps is None else f"EPS: {info.eps:.2f} ({info.eps_date or 'date n/a'})"
    if info.cash_dividend is None and info.stock_dividend is None:
        dividend_text = "Dividend: n/a"
    else:
        cash = 0.0 if info.cash_dividend is None else info.cash_dividend
        stock = 0.0 if info.stock_dividend is None else info.stock_dividend
        payment = info.cash_payment_month or info.cash_payment_date or "payment date n/a"
        dividend_text = f"Dividend: cash {cash:.2f} / stock {stock:.2f}; payment {payment}"
    return f"{eps_text}; {dividend_text}"


def add_indicators(df: pd.DataFrame, rsi_period: int) -> pd.DataFrame:
    result = df.copy()
    for window in (5, 10, 20, 60):
        result[f"MA{window}"] = result["close"].rolling(window=window, min_periods=window).mean()

    delta = result["close"].diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.rolling(window=rsi_period, min_periods=rsi_period).mean()
    avg_loss = losses.rolling(window=rsi_period, min_periods=rsi_period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.mask((avg_loss == 0) & (avg_gain > 0), 100)
    rsi = rsi.mask((avg_loss == 0) & (avg_gain == 0), 50)
    result["RSI"] = rsi
    return result


def rsi_status(value: float) -> str:
    if pd.isna(value):
        return "n/a"
    if value > 70:
        return "overbought"
    if value < 30:
        return "oversold"
    return "neutral"


def change_color(value: float) -> str:
    if value > 0:
        return GAIN_COLOR
    if value < 0:
        return LOSS_COLOR
    return TEXT_DARK


def fetch_market_news(symbol: str, name: str, limit: int = 12) -> list[NewsItem]:
    query_terms = [symbol, name.strip(), "?啗", "?∠巨"]
    query = " ".join(term for term in query_terms if term)
    params = {
        "q": query,
        "hl": "zh-TW",
        "gl": "TW",
        "ceid": "TW:zh-Hant",
    }
    try:
        response = requests.get(GOOGLE_NEWS_RSS_URL, params=params, timeout=20)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"News fetch failed: {exc}") from exc

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as exc:
        raise RuntimeError("News RSS response could not be parsed.") from exc

    items: list[NewsItem] = []
    for node in root.findall("./channel/item"):
        title = (node.findtext("title") or "").strip()
        link = (node.findtext("link") or "").strip()
        published = (node.findtext("pubDate") or "").strip()
        source_node = node.find("source")
        source = (source_node.text if source_node is not None and source_node.text else "").strip()
        if title and link:
            items.append(NewsItem(title=title, source=source or "Google News", published=published, link=link))
        if len(items) >= limit:
            break
    return items


def build_ml_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    features = df[["date", "open", "high", "low", "close", "volume", "MA5", "MA10", "MA20", "MA60", "RSI"]].copy()
    features["return_1d"] = features["close"].pct_change()
    features["return_5d"] = features["close"].pct_change(5)
    features["range_pct"] = (features["high"] - features["low"]) / features["close"].replace(0, np.nan)
    features["close_open_pct"] = (features["close"] - features["open"]) / features["open"].replace(0, np.nan)
    features["volume_change"] = features["volume"].pct_change()
    features["volatility_5d"] = features["return_1d"].rolling(5).std()
    features["ma5_gap"] = (features["close"] - features["MA5"]) / features["MA5"].replace(0, np.nan)
    features["ma20_gap"] = (features["close"] - features["MA20"]) / features["MA20"].replace(0, np.nan)
    features["ma5_slope"] = features["MA5"].pct_change()
    features["ma20_slope"] = features["MA20"].pct_change()
    features["target_up_next_day"] = (features["close"].shift(-1) > features["close"]).astype(int)
    return features


def train_ml_signal(df: pd.DataFrame) -> MLSignal:
    if len(df) < 90:
        return MLSignal(
            status="insufficient_data",
            message="At least 90 price rows are required for ML training.",
            sample_count=len(df),
        )

    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:
        return MLSignal(status="missing_dependency", message=f"scikit-learn is not available: {exc}")

    feature_df = build_ml_feature_frame(df)
    feature_cols = [
        "return_1d",
        "return_5d",
        "range_pct",
        "close_open_pct",
        "volume_change",
        "volatility_5d",
        "ma5_gap",
        "ma20_gap",
        "ma5_slope",
        "ma20_slope",
        "RSI",
    ]

    trainable = feature_df.iloc[:-1].dropna(subset=feature_cols + ["target_up_next_day"]).copy()
    latest_features = feature_df.iloc[[-1]].dropna(subset=feature_cols)
    if len(trainable) < 60 or latest_features.empty:
        return MLSignal(
            status="insufficient_features",
            message="Not enough complete feature rows for ML inference.",
            sample_count=len(trainable),
            feature_count=len(feature_cols),
        )

    split_index = max(int(len(trainable) * 0.7), 1)
    if len(trainable) - split_index < 15:
        return MLSignal(
            status="insufficient_test_data",
            message="Not enough holdout rows for ML validation.",
            sample_count=len(trainable),
            feature_count=len(feature_cols),
        )

    x_train = trainable.iloc[:split_index][feature_cols]
    y_train = trainable.iloc[:split_index]["target_up_next_day"].astype(int)
    x_test = trainable.iloc[split_index:][feature_cols]
    y_test = trainable.iloc[split_index:]["target_up_next_day"].astype(int)

    candidates = [
        (
            "Logistic Regression",
            Pipeline(
                [
                    ("scaler", StandardScaler()),
                    ("model", LogisticRegression(max_iter=1000, random_state=42)),
                ]
            ),
        ),
        (
            "Random Forest",
            RandomForestClassifier(
                n_estimators=200,
                max_depth=4,
                min_samples_leaf=5,
                random_state=42,
                class_weight="balanced_subsample",
            ),
        ),
    ]

    evaluated: list[tuple[str, Any, float, float]] = []
    for model_name, model in candidates:
        model.fit(x_train, y_train)
        train_accuracy = accuracy_score(y_train, model.predict(x_train))
        test_accuracy = accuracy_score(y_test, model.predict(x_test))
        evaluated.append((model_name, model, train_accuracy, test_accuracy))

    model_name, model, train_accuracy, test_accuracy = max(evaluated, key=lambda item: item[3])
    probability = model.predict_proba(latest_features[feature_cols])[0]
    class_order = list(model.classes_)
    up_probability = float(probability[class_order.index(1)]) if 1 in class_order else 0.0
    down_probability = 1.0 - up_probability
    prediction_label = "Up" if up_probability >= 0.5 else "Down"

    return MLSignal(
        status="ok",
        model_name=model_name,
        prediction_label=prediction_label,
        up_probability=up_probability,
        down_probability=down_probability,
        train_accuracy=float(train_accuracy),
        test_accuracy=float(test_accuracy),
        sample_count=len(trainable),
        feature_count=len(feature_cols),
        message="Model output is a screening signal only and must be interpreted by Gemini with the full source packet.",
    )


def format_ml_signal(signal: MLSignal) -> str:
    if signal.status != "ok":
        return f"ML status: {signal.status}; {signal.message}"

    return (
        f"ML signal: {signal.prediction_label}; "
        f"up probability {signal.up_probability:.1%}; down probability {signal.down_probability:.1%}; "
        f"model {signal.model_name}; "
        f"train accuracy {signal.train_accuracy:.1%}; test accuracy {signal.test_accuracy:.1%}; "
        f"samples {signal.sample_count}; {signal.message}"
    )


def build_ai_prompt(
    symbol: str,
    df: pd.DataFrame,
    rsi_period: int,
    news_items: list[NewsItem],
    ml_signal: MLSignal,
    fundamental_info: FundamentalInfo,
    ref_data_status: str = "",
) -> str:
    prompt = build_public_equity_prompt(
        symbol=symbol,
        df=df,
        rsi_period=rsi_period,
        news_items=news_items,
        ml_summary=format_ml_signal(ml_signal),
        fundamental_summary=format_fundamental_summary(fundamental_info),
        rsi_status_func=rsi_status,
    )
    if ref_data_status:
        prompt += "\n\nRef-data / Python workflow status packet:\n" + ref_data_status
    return prompt


def build_ref_data_status_packet(
    symbol: str,
    df: pd.DataFrame,
    rsi_period: int,
    news_items: list[NewsItem],
    ml_signal: MLSignal,
    fundamental_info: FundamentalInfo,
) -> str:
    latest = df.iloc[-1]
    latest_rsi_series = df["RSI"].dropna()
    latest_rsi = latest_rsi_series.iloc[-1] if not latest_rsi_series.empty else np.nan
    start_price = float(df.iloc[0]["close"])
    end_price = float(df.iloc[-1]["close"])
    change_pct = (end_price - start_price) / start_price * 100 if start_price else 0.0
    try:
        from research.security_classifier import classify_security

        classification = classify_security(symbol)
        security_type = classification.security_type
        classification_reasons = ", ".join(classification.reasons) or "n/a"
    except Exception as exc:
        security_type = "unknown"
        classification_reasons = f"classifier unavailable: {exc}"

    news_titles = "; ".join(item.title for item in news_items[:5] if item.title) or "no news items"
    return "\n".join(
        [
            "Version: v2.0",
            f"Symbol: {symbol}",
            f"Security type: {security_type}",
            f"Security classifier reasons: {classification_reasons}",
            f"Date range: {df.iloc[0]['date'].strftime('%Y-%m-%d')} to {df.iloc[-1]['date'].strftime('%Y-%m-%d')}",
            f"Latest close: {float(latest['close']):.2f}",
            f"Period return: {change_pct:.2f}%",
            f"Latest volume: {float(latest['volume']):.0f}",
            f"RSI({rsi_period}): {'n/a' if pd.isna(latest_rsi) else f'{float(latest_rsi):.2f}'}",
            f"Fundamental packet: {format_fundamental_summary(fundamental_info)}",
            f"ML packet: {format_ml_signal(ml_signal)}",
            f"News packet: {news_titles}",
            "Ref-data modules converted to Python: financial foundation, valuation, ETF analysis, news/events, journal/thesis tracker, strategy/backtest, portfolio risk/stress, governance/insider.",
            "Display rule: investment conclusions must come from Gemini analysis of this packet; raw data tabs are audit views only.",
        ]
    )


def generate_ai_insights(
    symbol: str,
    df: pd.DataFrame,
    gemini_api_key: str,
    rsi_period: int,
    news_items: list[NewsItem],
    ml_signal: MLSignal,
    fundamental_info: FundamentalInfo,
) -> GeminiAnalysisResult:
    ref_data_status = build_ref_data_status_packet(symbol, df, rsi_period, news_items, ml_signal, fundamental_info)
    if not gemini_api_key.strip():
        raise RuntimeError("v2.0 requires a Gemini API key before investment analysis is displayed.")
    try:
        result = generate_content_with_fallback(
            api_key=gemini_api_key,
            prompt=build_ai_prompt(symbol, df, rsi_period, news_items, ml_signal, fundamental_info, ref_data_status),
        )
    except Exception as exc:
        raise RuntimeError(f"Gemini API analysis failed: {exc}") from exc

    return GeminiAnalysisResult(
        report=result.text,
        model_name=result.model_name,
        attempts=list(result.attempts),
        source_packet=build_ai_prompt(symbol, df, rsi_period, news_items, ml_signal, fundamental_info, ref_data_status),
        ref_data_status=ref_data_status,
    )


class StockAnalysisGui:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(f"AI Stock Technical Analysis {APP_VERSION}")
        self.root.geometry("1360x900")
        self.root.minsize(1180, 760)
        self._configure_style()

        self.keys = parse_api_key_file()
        self.watchlist = load_watchlist()
        self.current_df: pd.DataFrame | None = None
        self.current_news: list[NewsItem] = []
        self.current_ml_signal = MLSignal(status="not_run", message="Not analyzed yet.")
        self.current_fundamental = FundamentalInfo(status="not_loaded", message="Not loaded yet.")
        self.chart_canvas: tk.Canvas | None = None

        self.symbol_var = tk.StringVar(value=self.watchlist[0]["symbol"])
        self.name_var = tk.StringVar(value=self.watchlist[0].get("name", ""))
        self.start_var = tk.StringVar(value=(date.today() - timedelta(days=180)).isoformat())
        self.end_var = tk.StringVar(value=date.today().isoformat())
        self.rsi_var = tk.IntVar(value=14)
        self.finmind_key_var = tk.StringVar(value=self.keys.finmind_api_key)
        self.gemini_key_var = tk.StringVar(value=self.keys.gemini_api_key)
        self.status_var = tk.StringVar(value=self._key_status_text())
        self.progress_var = tk.IntVar(value=0)
        self.progress_text_var = tk.StringVar(value="Ready 0%")

        self.summary_vars = {
            "title": tk.StringVar(value="Not analyzed"),
            "price": tk.StringVar(value="-"),
            "change": tk.StringVar(value="-"),
            "volume": tk.StringVar(value="-"),
            "rsi": tk.StringVar(value="-"),
            "fundamental": tk.StringVar(value="-"),
            "range": tk.StringVar(value="-"),
        }

        self._build_layout()
        self._refresh_watchlist_ui()

    def _configure_style(self) -> None:
        self.root.configure(bg=APP_BG)
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        base_font = ("Noto Sans TC", 10)
        style.configure(".", font=base_font, background=APP_BG, foreground=TEXT_DARK)
        style.configure("TFrame", background=APP_BG)
        style.configure("TLabelframe", background=APP_BG, bordercolor="#d8dee9", relief="solid")
        style.configure("TLabelframe.Label", background=APP_BG, foreground=TEXT_DARK, font=("Noto Sans TC", 10, "bold"))
        style.configure("TLabel", background=APP_BG, foreground=TEXT_DARK)
        style.configure("Muted.TLabel", background=APP_BG, foreground=TEXT_MUTED)
        style.configure("Title.TLabel", background=APP_BG, foreground=TEXT_DARK, font=("Noto Sans TC", 18, "bold"))
        style.configure("Price.TLabel", background=APP_BG, foreground=TEXT_DARK, font=("Noto Sans TC", 26, "bold"))
        style.configure("TButton", padding=(12, 6), font=base_font)
        style.configure("Accent.TButton", background=ACCENT, foreground="#ffffff", bordercolor=ACCENT)
        style.map("Accent.TButton", background=[("active", "#1d4ed8"), ("pressed", "#1e40af")])
        style.configure("TNotebook", background=APP_BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(16, 8), font=("Noto Sans TC", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", PANEL_BG)], foreground=[("selected", ACCENT)])
        style.configure("Treeview", rowheight=28, font=base_font, background=PANEL_BG, fieldbackground=PANEL_BG)
        style.configure("Treeview.Heading", font=("Noto Sans TC", 10, "bold"), background="#eef2f7", foreground=TEXT_DARK)

    def _key_status_text(self) -> str:
        return (
            f"Key file: {API_KEY_FILE} | "
            f"FinMind: {mask_key(self.finmind_key_var.get())} | "
            f"Gemini: {mask_key(self.gemini_key_var.get())}"
        )

    def _build_layout(self) -> None:
        root_frame = ttk.Frame(self.root, padding=10)
        root_frame.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(root_frame)
        header.pack(fill=tk.X)
        ttk.Label(header, text=f"AI Stock Technical Analysis {APP_VERSION}", style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Label(header, textvariable=self.status_var).pack(side=tk.RIGHT)

        body = ttk.PanedWindow(root_frame, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        left = ttk.Frame(body, width=230)
        right = ttk.Frame(body)
        body.add(left, weight=0)
        body.add(right, weight=1)

        self._build_watchlist_panel(left)
        self._build_query_panel(right)
        self._build_summary_panel(right)
        self._build_tabs(right)

    def _build_watchlist_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.LabelFrame(parent, text="Watchlist", padding=8)
        panel.pack(fill=tk.BOTH, expand=True)

        self.watchlist_box = tk.Listbox(panel, height=20, exportselection=False)
        self.watchlist_box.pack(fill=tk.BOTH, expand=True)
        self.watchlist_box.bind("<<ListboxSelect>>", self._on_watchlist_select)

        button_row = ttk.Frame(panel)
        button_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(button_row, text="Delete", command=self.delete_selected_watchlist_item).pack(side=tk.LEFT)
        ttk.Button(button_row, text="Reset", command=self.reset_watchlist).pack(side=tk.LEFT, padx=(8, 0))

        hint = "FinMind supports Taiwan stocks and ETFs. Non-Taiwan symbols may have no data."
        ttk.Label(panel, text=hint, wraplength=200, foreground="#666666").pack(fill=tk.X, pady=(10, 0))

    def _build_query_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.LabelFrame(parent, text="Query settings", padding=10)
        panel.pack(fill=tk.X)

        ttk.Label(panel, text="Stock / ETF code").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(panel, textvariable=self.symbol_var, width=14).grid(row=1, column=0, sticky=tk.W, padx=(0, 12))

        ttk.Label(panel, text="Name").grid(row=0, column=1, sticky=tk.W)
        ttk.Entry(panel, textvariable=self.name_var, width=18).grid(row=1, column=1, sticky=tk.W, padx=(0, 12))

        ttk.Label(panel, text="Start date").grid(row=0, column=2, sticky=tk.W)
        ttk.Entry(panel, textvariable=self.start_var, width=12).grid(row=1, column=2, sticky=tk.W, padx=(0, 12))

        ttk.Label(panel, text="End date").grid(row=0, column=3, sticky=tk.W)
        ttk.Entry(panel, textvariable=self.end_var, width=12).grid(row=1, column=3, sticky=tk.W, padx=(0, 12))

        ttk.Label(panel, text="RSI").grid(row=0, column=4, sticky=tk.W)
        ttk.Spinbox(panel, from_=2, to=60, textvariable=self.rsi_var, width=6).grid(row=1, column=4, sticky=tk.W, padx=(0, 12))

        self.analyze_button = ttk.Button(panel, text="Analyze", command=self.start_analysis, style="Accent.TButton")
        self.analyze_button.grid(row=1, column=5, padx=(0, 8))
        ttk.Button(panel, text="Save to watchlist", command=self.save_current_symbol_to_watchlist).grid(row=1, column=6, padx=(0, 8))
        ttk.Button(panel, text="Save Key", command=self.save_keys_from_gui).grid(row=1, column=7)

        key_row = ttk.Frame(panel)
        key_row.grid(row=2, column=0, columnspan=8, sticky=tk.EW, pady=(10, 0))
        ttk.Label(key_row, text="FinMind").pack(side=tk.LEFT)
        ttk.Entry(key_row, textvariable=self.finmind_key_var, width=44, show="*").pack(side=tk.LEFT, padx=(6, 16))
        ttk.Label(key_row, text="Gemini").pack(side=tk.LEFT)
        ttk.Entry(key_row, textvariable=self.gemini_key_var, width=44, show="*").pack(side=tk.LEFT, padx=(6, 0))

        progress_row = ttk.Frame(panel)
        progress_row.grid(row=3, column=0, columnspan=8, sticky=tk.EW, pady=(10, 0))
        progress_row.columnconfigure(0, weight=1)
        self.progress_bar = ttk.Progressbar(progress_row, maximum=100, mode="determinate", variable=self.progress_var)
        self.progress_bar.grid(row=0, column=0, sticky=tk.EW)
        ttk.Label(progress_row, textvariable=self.progress_text_var, width=30, anchor=tk.E).grid(
            row=0, column=1, sticky=tk.E, padx=(12, 0)
        )

    def _build_summary_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.LabelFrame(parent, text="蝮質汗", padding=10)
        panel.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(panel, textvariable=self.summary_vars["title"], font=("Noto Sans TC", 16, "bold")).grid(
            row=0, column=0, columnspan=5, sticky=tk.W
        )

        self.price_label = ttk.Label(panel, textvariable=self.summary_vars["price"], style="Price.TLabel")
        self.price_label.grid(row=1, column=0, sticky=tk.W, padx=(0, 30))

        self.change_label = ttk.Label(panel, textvariable=self.summary_vars["change"], font=("Noto Sans TC", 14, "bold"))
        self.change_label.grid(row=1, column=1, sticky=tk.W, padx=(0, 30))

        ttk.Label(panel, textvariable=self.summary_vars["volume"], font=("Noto Sans TC", 12)).grid(
            row=1, column=2, sticky=tk.W, padx=(0, 30)
        )
        ttk.Label(panel, textvariable=self.summary_vars["rsi"], font=("Noto Sans TC", 12)).grid(
            row=1, column=3, sticky=tk.W, padx=(0, 30)
        )
        ttk.Label(panel, textvariable=self.summary_vars["fundamental"], font=("Noto Sans TC", 12)).grid(
            row=1, column=4, sticky=tk.W
        )
        ttk.Label(panel, textvariable=self.summary_vars["range"], font=("Noto Sans TC", 12)).grid(
            row=2, column=0, columnspan=5, sticky=tk.W, pady=(6, 0)
        )

    def _build_tabs(self, parent: ttk.Frame) -> None:
        self.tabs = ttk.Notebook(parent)
        self.tabs.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.chart_tab = ttk.Frame(self.tabs)
        self.table_tab = ttk.Frame(self.tabs)
        self.gemini_tab = ttk.Frame(self.tabs)
        self.ai_tab = ttk.Frame(self.tabs)
        self.ml_tab = ttk.Frame(self.tabs)
        self.fundamental_tab = ttk.Frame(self.tabs)
        self.news_tab = ttk.Frame(self.tabs)

        self.tabs.add(self.chart_tab, text="Chart")
        self.tabs.add(self.table_tab, text="History")
        self.tabs.add(self.gemini_tab, text="Gemini Analysis")
        self.tabs.add(self.ai_tab, text="Public Equity Memo")
        self.tabs.add(self.ml_tab, text="ML Signal")
        self.tabs.add(self.fundamental_tab, text="Fundamentals")
        self.tabs.add(self.news_tab, text="News")

        self.chart_frame = ttk.Frame(self.chart_tab)
        self.chart_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("date", "open", "high", "low", "close", "volume", "MA5", "MA10", "MA20", "MA60", "RSI")
        self.table = ttk.Treeview(self.table_tab, columns=columns, show="headings")
        for col in columns:
            self.table.heading(col, text=self._table_heading(col))
            self.table.column(col, width=95, anchor=tk.E)
        self.table.column("date", width=110, anchor=tk.CENTER)
        y_scroll = ttk.Scrollbar(self.table_tab, orient=tk.VERTICAL, command=self.table.yview)
        self.table.configure(yscrollcommand=y_scroll.set)
        self.table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.gemini_text = tk.Text(self.gemini_tab, wrap=tk.WORD, font=("Noto Sans TC", 11), padx=10, pady=10)
        gemini_scroll = ttk.Scrollbar(self.gemini_tab, orient=tk.VERTICAL, command=self.gemini_text.yview)
        self.gemini_text.configure(yscrollcommand=gemini_scroll.set)
        self.gemini_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        gemini_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.ai_text = tk.Text(self.ai_tab, wrap=tk.WORD, font=("Noto Sans TC", 11), padx=10, pady=10)
        ai_scroll = ttk.Scrollbar(self.ai_tab, orient=tk.VERTICAL, command=self.ai_text.yview)
        self.ai_text.configure(yscrollcommand=ai_scroll.set)
        self.ai_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ai_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.ml_text = tk.Text(self.ml_tab, wrap=tk.WORD, font=("Noto Sans TC", 11), padx=10, pady=10)
        ml_scroll = ttk.Scrollbar(self.ml_tab, orient=tk.VERTICAL, command=self.ml_text.yview)
        self.ml_text.configure(yscrollcommand=ml_scroll.set)
        self.ml_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ml_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.fundamental_text = tk.Text(
            self.fundamental_tab,
            wrap=tk.WORD,
            font=("Noto Sans TC", 11),
            padx=10,
            pady=10,
            height=10,
        )
        self.fundamental_text.pack(fill=tk.BOTH, expand=True)

        news_columns = ("title", "source", "published")
        self.news_table = ttk.Treeview(self.news_tab, columns=news_columns, show="headings")
        self.news_table.heading("title", text="Title")
        self.news_table.heading("source", text="Source")
        self.news_table.heading("published", text="Published")
        self.news_table.column("title", width=760, anchor=tk.W)
        self.news_table.column("source", width=140, anchor=tk.W)
        self.news_table.column("published", width=260, anchor=tk.W)
        self.news_table.pack(fill=tk.BOTH, expand=True, padx=4, pady=(4, 8))
        self.news_table.bind("<Double-1>", self.open_selected_news)

        news_buttons = ttk.Frame(self.news_tab)
        news_buttons.pack(fill=tk.X, padx=4, pady=(0, 4))
        ttk.Button(news_buttons, text="Open selected news", command=self.open_selected_news).pack(side=tk.LEFT)
        ttk.Label(news_buttons, text="News source: Google News RSS. Raw news is an audit input for Gemini.", style="Muted.TLabel").pack(
            side=tk.LEFT,
            padx=(12, 0),
        )

    def _table_heading(self, col: str) -> str:
        return {
            "date": "Date",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }.get(col, col)

    def _refresh_watchlist_ui(self) -> None:
        self.watchlist_box.delete(0, tk.END)
        for item in self.watchlist:
            self.watchlist_box.insert(tk.END, display_name(item))

    def _on_watchlist_select(self, _event: Any) -> None:
        selection = self.watchlist_box.curselection()
        if not selection:
            return
        item = self.watchlist[selection[0]]
        self.symbol_var.set(item["symbol"])
        self.name_var.set(item.get("name", ""))

    def save_current_symbol_to_watchlist(self) -> None:
        symbol = normalize_symbol(self.symbol_var.get())
        if not symbol:
            messagebox.showerror("Input error", "Please enter a stock or ETF code.")
            return

        name = self.name_var.get().strip()
        for item in self.watchlist:
            if item["symbol"] == symbol:
                item["name"] = name or item.get("name", "")
                save_watchlist(self.watchlist)
                self._refresh_watchlist_ui()
                messagebox.showinfo("Saved", f"{symbol} has been updated in the watchlist.")
                return

        self.watchlist.append({"symbol": symbol, "name": name})
        save_watchlist(self.watchlist)
        self._refresh_watchlist_ui()
        messagebox.showinfo("Saved", f"{symbol} has been added to the watchlist.")

    def delete_selected_watchlist_item(self) -> None:
        selection = self.watchlist_box.curselection()
        if not selection:
            return
        index = selection[0]
        item = self.watchlist[index]
        if not messagebox.askyesno("Confirm delete", f"Delete {display_name(item)} from the watchlist?"):
            return
        del self.watchlist[index]
        if not self.watchlist:
            self.watchlist = list(DEFAULT_WATCHLIST)
        save_watchlist(self.watchlist)
        self._refresh_watchlist_ui()

    def reset_watchlist(self) -> None:
        if not messagebox.askyesno("Confirm reset", "Reset the watchlist to defaults?"):
            return
        self.watchlist = list(DEFAULT_WATCHLIST)
        save_watchlist(self.watchlist)
        self._refresh_watchlist_ui()

    def save_keys_from_gui(self) -> None:
        try:
            save_api_keys(ApiKeys(self.finmind_key_var.get(), self.gemini_key_var.get()))
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))
            return
        self.status_var.set(self._key_status_text())
        messagebox.showinfo("Saved", f"API keys saved to:\n{API_KEY_FILE}")

    def start_analysis(self) -> None:
        try:
            symbol = normalize_symbol(self.symbol_var.get())
            start_date = datetime.strptime(self.start_var.get().strip(), "%Y-%m-%d").date()
            end_date = datetime.strptime(self.end_var.get().strip(), "%Y-%m-%d").date()
            rsi_period = int(self.rsi_var.get())
        except ValueError:
            messagebox.showerror("Input error", "Dates must use YYYY-MM-DD and RSI must be an integer.")
            return

        if not symbol:
            messagebox.showerror("Input error", "Please enter a stock or ETF code.")
            return
        if start_date >= end_date:
            messagebox.showerror("Input error", "Start date must be earlier than end date.")
            return

        self._set_busy(True)
        self._set_progress(0, "Starting analysis")
        self.ai_text.delete("1.0", tk.END)
        self.gemini_text.delete("1.0", tk.END)
        self.ai_text.insert(tk.END, "Waiting for Gemini analysis...\n")
        self.gemini_text.insert(tk.END, "Building source packet and waiting for Gemini analysis...\n")
        worker = threading.Thread(
            target=self._run_analysis_worker,
            args=(symbol, start_date, end_date, rsi_period),
            daemon=True,
        )
        worker.start()

    def _run_analysis_worker(self, symbol: str, start_date: date, end_date: date, rsi_period: int) -> None:
        try:
            self._queue_progress(8, "Fetching FinMind prices")
            raw_df = fetch_finmind_stock_price(symbol, self.finmind_key_var.get(), start_date, end_date)
            self._queue_progress(24, "Calculating indicators")
            df = add_indicators(raw_df, rsi_period)
            self._queue_progress(40, "Training ML signal")
            ml_signal = train_ml_signal(df)
            self._queue_progress(58, "Fetching fundamentals")
            fundamental_info = fetch_fundamental_info(symbol, self.finmind_key_var.get())
            try:
                self._queue_progress(72, "Fetching news")
                news_items = fetch_market_news(symbol, self.name_var.get())
            except Exception as exc:
                news_items = [NewsItem(title=f"News fetch failed: {exc}", source="System", published="", link="")]
            self._queue_progress(84, "Gemini source-packet analysis")
            gemini_result = generate_ai_insights(
                symbol,
                df,
                self.gemini_key_var.get(),
                rsi_period,
                news_items,
                ml_signal,
                fundamental_info,
            )
            self._queue_progress(96, "Rendering result")
        except Exception as exc:
            self.root.after(0, lambda: self._show_error(str(exc)))
            return
        self.root.after(
            0,
            lambda: self._render_result(
                symbol,
                df,
                rsi_period,
                gemini_result,
                news_items,
                ml_signal,
                fundamental_info,
            ),
        )

    def _set_busy(self, busy: bool) -> None:
        self.root.config(cursor="watch" if busy else "")
        if hasattr(self, "analyze_button"):
            self.analyze_button.configure(state=tk.DISABLED if busy else tk.NORMAL)
        self.status_var.set("??銝?.." if busy else self._key_status_text())

    def _set_progress(self, percent: int, stage: str) -> None:
        percent = max(0, min(100, int(percent)))
        self.progress_var.set(percent)
        self.progress_text_var.set(f"{stage} {percent}%")
        if stage == "??憭望?":
            self.status_var.set("??憭望?")
        elif percent < 100:
            self.status_var.set(f"??銝哨?{stage} {percent}%")

    def _queue_progress(self, percent: int, stage: str) -> None:
        self.root.after(0, lambda: self._set_progress(percent, stage))

    def _show_error(self, message: str) -> None:
        self._set_busy(False)
        self._set_progress(0, "??憭望?")
        self.ai_text.delete("1.0", tk.END)
        self.ai_text.insert(tk.END, message)
        messagebox.showerror("??憭望?", message)

    def _render_result(
        self,
        symbol: str,
        df: pd.DataFrame,
        rsi_period: int,
        gemini_result: GeminiAnalysisResult,
        news_items: list[NewsItem],
        ml_signal: MLSignal,
        fundamental_info: FundamentalInfo,
    ) -> None:
        self._set_progress(100, "摰?")
        self._set_busy(False)
        self.current_df = df
        self.current_news = news_items
        self.current_ml_signal = ml_signal
        self.current_fundamental = fundamental_info
        self._update_summary(symbol, df, rsi_period, fundamental_info)
        self._draw_chart(symbol, df, rsi_period)
        self._fill_table(df)
        self._fill_news(news_items)
        self._fill_ml_signal(ml_signal)
        self._fill_fundamental(fundamental_info)
        self.ai_text.delete("1.0", tk.END)
        self.ai_text.insert(tk.END, gemini_result.report)
        self._fill_gemini_analysis(gemini_result)
        self.tabs.select(self.gemini_tab)

    def _fill_gemini_analysis(self, gemini_result: GeminiAnalysisResult) -> None:
        self.gemini_text.delete("1.0", tk.END)
        attempts = "\n".join(f"- {attempt}" for attempt in gemini_result.attempts) or "- n/a"
        content = "\n".join(
            [
                "Gemini 綜合分析 / v2.0",
                "",
                f"Gemini model used: {gemini_result.model_name}",
                "",
                "Gemini call attempts:",
                attempts,
                "",
                "Ref-data / Python workflow status included in Gemini prompt:",
                gemini_result.ref_data_status,
                "",
                "Gemini investment analysis:",
                gemini_result.report,
                "",
                "Audit note:",
                "The chart, historical table, ML tab, fundamentals tab, and news tab are raw-source audit views. Investment conclusions displayed in v2.0 are produced only after Gemini analyzes the full source packet above.",
            ]
        )
        self.gemini_text.insert(tk.END, content)

    def _update_summary(
        self,
        symbol: str,
        df: pd.DataFrame,
        rsi_period: int,
        fundamental_info: FundamentalInfo,
    ) -> None:
        name = self.name_var.get().strip()
        start_price = float(df.iloc[0]["close"])
        end_price = float(df.iloc[-1]["close"])
        change_abs = end_price - start_price
        change_pct = change_abs / start_price * 100 if start_price else 0
        latest = df.iloc[-1]
        latest_rsi_series = df["RSI"].dropna()
        latest_rsi = float(latest_rsi_series.iloc[-1]) if not latest_rsi_series.empty else np.nan

        self.summary_vars["title"].set(f"{symbol} {name}".strip())
        self.summary_vars["price"].set(f"{end_price:,.2f}")
        self.summary_vars["change"].set(f"{change_abs:+.2f} ({change_pct:+.2f}%)")
        self.summary_vars["volume"].set(f"?漱??{float(latest['volume']):,.0f}")
        self.summary_vars["rsi"].set(
            f"RSI({rsi_period}) {'鞈?銝雲' if pd.isna(latest_rsi) else f'{latest_rsi:.2f} {rsi_status(latest_rsi)}'}"
        )
        self.summary_vars["fundamental"].set(format_fundamental_summary(fundamental_info))
        self.summary_vars["range"].set(
            f"{df.iloc[0]['date'].strftime('%Y-%m-%d')} - {df.iloc[-1]['date'].strftime('%Y-%m-%d')}"
        )

        color = change_color(change_abs)
        self.price_label.configure(foreground=color)
        self.change_label.configure(foreground=color)

    def _draw_chart(self, symbol: str, df: pd.DataFrame, rsi_period: int) -> None:
        for child in self.chart_frame.winfo_children():
            child.destroy()

        canvas = tk.Canvas(self.chart_frame, bg=PANEL_BG, highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        self.chart_canvas = canvas

        def draw(_event: tk.Event | None = None) -> None:
            canvas.delete("all")
            width = max(canvas.winfo_width(), 900)
            height = max(canvas.winfo_height(), 520)
            left, right, top, bottom = 64, 24, 36, 46
            gap = 22
            plot_width = max(width - left - right, 1)
            usable_height = max(height - top - bottom - gap * 2, 1)
            price_h = int(usable_height * 0.54)
            volume_h = int(usable_height * 0.20)
            rsi_h = usable_height - price_h - volume_h
            price_top = top
            volume_top = price_top + price_h + gap
            rsi_top = volume_top + volume_h + gap

            def panel(y: int, h: int, label: str) -> None:
                canvas.create_rectangle(left, y, left + plot_width, y + h, outline="#d8dee9", fill=PANEL_BG)
                canvas.create_text(12, y + 14, anchor=tk.W, text=label, fill=TEXT_MUTED, font=("Noto Sans TC", 9))
                for step in range(1, 4):
                    yy = y + h * step / 4
                    canvas.create_line(left, yy, left + plot_width, yy, fill="#eef2f7")

            panel(price_top, price_h, "Price")
            panel(volume_top, volume_h, "Volume")
            panel(rsi_top, rsi_h, f"RSI({rsi_period})")
            canvas.create_text(left, 14, anchor=tk.W, text=f"{symbol} K / MA", fill=TEXT_DARK, font=("Noto Sans TC", 12, "bold"))

            count = len(df)
            if count == 0:
                return

            x_step = plot_width / max(count - 1, 1)
            candle_w = max(3, min(12, x_step * 0.62))
            price_cols = ["open", "high", "low", "close", "MA5", "MA10", "MA20", "MA60"]
            price_values = pd.to_numeric(df[price_cols].stack(), errors="coerce").dropna()
            if price_values.empty:
                return
            price_min = float(price_values.min())
            price_max = float(price_values.max())
            pad = max((price_max - price_min) * 0.06, 0.01)
            price_min -= pad
            price_max += pad
            price_span = max(price_max - price_min, 0.01)
            volume_max = max(float(pd.to_numeric(df["volume"], errors="coerce").max() or 0), 1.0)

            def x_pos(index: int) -> float:
                return left + index * x_step

            def y_price(value: float) -> float:
                return price_top + price_h - (value - price_min) / price_span * price_h

            def y_rsi(value: float) -> float:
                return rsi_top + rsi_h - max(0.0, min(100.0, value)) / 100 * rsi_h

            for value in (price_min, (price_min + price_max) / 2, price_max):
                canvas.create_text(left - 8, y_price(value), anchor=tk.E, text=f"{value:.2f}", fill=TEXT_MUTED, font=("Noto Sans TC", 8))

            for idx, row in df.reset_index(drop=True).iterrows():
                x = x_pos(idx)
                open_price = float(row["open"])
                high_price = float(row["high"])
                low_price = float(row["low"])
                close_price = float(row["close"])
                color = GAIN_COLOR if close_price >= open_price else LOSS_COLOR
                canvas.create_line(x, y_price(low_price), x, y_price(high_price), fill=color)
                y_open = y_price(open_price)
                y_close = y_price(close_price)
                canvas.create_rectangle(
                    x - candle_w / 2,
                    min(y_open, y_close),
                    x + candle_w / 2,
                    max(y_open, y_close) + 1,
                    outline=color,
                    fill=color,
                )

                volume = float(row["volume"])
                bar_h = volume / volume_max * volume_h
                canvas.create_rectangle(
                    x - candle_w / 2,
                    volume_top + volume_h - bar_h,
                    x + candle_w / 2,
                    volume_top + volume_h,
                    outline=color,
                    fill=color,
                )

            ma_colors = {"MA5": "#2563eb", "MA10": "#7c3aed", "MA20": "#f59e0b", "MA60": "#0f766e"}
            for offset, (ma, color) in enumerate(ma_colors.items()):
                points: list[float] = []
                for idx, value in enumerate(pd.to_numeric(df[ma], errors="coerce")):
                    if pd.isna(value):
                        if len(points) >= 4:
                            canvas.create_line(points, fill=color, width=2)
                        points = []
                        continue
                    points.extend([x_pos(idx), y_price(float(value))])
                if len(points) >= 4:
                    canvas.create_line(points, fill=color, width=2)
                legend_x = left + 8 + offset * 70
                canvas.create_line(legend_x, price_top + 16, legend_x + 18, price_top + 16, fill=color, width=2)
                canvas.create_text(legend_x + 22, price_top + 16, anchor=tk.W, text=ma, fill=TEXT_MUTED, font=("Noto Sans TC", 8))

            for level, color in ((70, GAIN_COLOR), (30, LOSS_COLOR)):
                y = y_rsi(level)
                canvas.create_line(left, y, left + plot_width, y, fill=color, dash=(4, 3))
                canvas.create_text(left - 8, y, anchor=tk.E, text=str(level), fill=TEXT_MUTED, font=("Noto Sans TC", 8))

            rsi_points: list[float] = []
            for idx, value in enumerate(pd.to_numeric(df["RSI"], errors="coerce")):
                if pd.isna(value):
                    continue
                rsi_points.extend([x_pos(idx), y_rsi(float(value))])
            if len(rsi_points) >= 4:
                canvas.create_line(rsi_points, fill="#1f77b4", width=2)

            tick_count = min(8, count)
            for pos in np.linspace(0, count - 1, tick_count, dtype=int):
                x = x_pos(int(pos))
                canvas.create_line(x, rsi_top + rsi_h, x, rsi_top + rsi_h + 5, fill="#9ca3af")
                label = df.iloc[int(pos)]["date"].strftime("%Y-%m-%d")
                canvas.create_text(x, rsi_top + rsi_h + 12, anchor=tk.N, text=label, fill=TEXT_MUTED, font=("Noto Sans TC", 8))

        canvas.bind("<Configure>", draw)
        canvas.after_idle(draw)

    def _fill_table(self, df: pd.DataFrame) -> None:
        for item in self.table.get_children():
            self.table.delete(item)

        for _, row in df.sort_values("date", ascending=False).iterrows():
            values = [
                row["date"].strftime("%Y-%m-%d"),
                f"{row['open']:.2f}",
                f"{row['high']:.2f}",
                f"{row['low']:.2f}",
                f"{row['close']:.2f}",
                f"{row['volume']:,.0f}",
                "" if pd.isna(row["MA5"]) else f"{row['MA5']:.2f}",
                "" if pd.isna(row["MA10"]) else f"{row['MA10']:.2f}",
                "" if pd.isna(row["MA20"]) else f"{row['MA20']:.2f}",
                "" if pd.isna(row["MA60"]) else f"{row['MA60']:.2f}",
                "" if pd.isna(row["RSI"]) else f"{row['RSI']:.2f}",
            ]
            self.table.insert("", tk.END, values=values)

    def _fill_news(self, items: list[NewsItem]) -> None:
        for item_id in self.news_table.get_children():
            self.news_table.delete(item_id)

        if not items:
            self.news_table.insert("", tk.END, values=("No news", "", ""))
            return

        for index, item in enumerate(items):
            self.news_table.insert("", tk.END, iid=str(index), values=(item.title, item.source, item.published))

    def _fill_ml_signal(self, signal: MLSignal) -> None:
        self.ml_text.delete("1.0", tk.END)
        if signal.status != "ok":
            self.ml_text.insert(tk.END, format_ml_signal(signal))
            return

        detail = "\n".join(
            [
                "ML raw audit view",
                "",
                f"Model: {signal.model_name}",
                f"Prediction label: {signal.prediction_label}",
                f"Up probability: {signal.up_probability:.1%}",
                f"Down probability: {signal.down_probability:.1%}",
                f"Train accuracy: {signal.train_accuracy:.1%}",
                f"Test accuracy: {signal.test_accuracy:.1%}",
                f"Sample count: {signal.sample_count}",
                f"Feature count: {signal.feature_count}",
                "",
                "Features: returns, range, close/open spread, volume change, volatility, MA gaps/slopes, RSI.",
                "",
                "Audit note: this raw ML signal is sent to Gemini and should not be used alone as an investment conclusion.",
            ]
        )
        self.ml_text.insert(tk.END, detail)

    def _fill_fundamental(self, info: FundamentalInfo) -> None:
        self.fundamental_text.delete("1.0", tk.END)
        lines = [
            "Fundamentals raw audit view",
            "",
            "EPS",
            f"Latest EPS: {'n/a' if info.eps is None else f'{info.eps:.2f}'}",
            f"EPS date: {info.eps_date or 'n/a'}",
            "",
            "Dividend",
            f"Dividend year: {info.dividend_year or 'n/a'}",
            f"Cash dividend: {'n/a' if info.cash_dividend is None else f'{info.cash_dividend:.2f}'}",
            f"Stock dividend: {'n/a' if info.stock_dividend is None else f'{info.stock_dividend:.2f}'}",
            f"Cash payment month: {info.cash_payment_month or 'n/a'}",
            f"Cash payment date: {info.cash_payment_date or 'n/a'}",
            f"Cash ex-dividend date: {info.cash_ex_dividend_date or 'n/a'}",
            f"Stock ex-dividend date: {info.stock_ex_dividend_date or 'n/a'}",
            f"Announcement date: {info.announcement_date or 'n/a'}",
        ]
        if info.message:
            lines.extend(["", "Message", info.message])
        lines.extend(
            [
                "",
                "Source: FinMind TaiwanStockFinancialStatements / TaiwanStockDividend.",
                "Audit note: this raw fundamentals packet is sent to Gemini and should not be used alone as an investment conclusion.",
            ]
        )
        self.fundamental_text.insert(tk.END, "\n".join(lines))

    def open_selected_news(self, _event: Any | None = None) -> None:
        selection = self.news_table.selection()
        if not selection:
            return
        try:
            item = self.current_news[int(selection[0])]
        except (ValueError, IndexError):
            return
        webbrowser.open(item.link)


def main() -> int:
    configure_gui_fonts()
    try:
        ensure_api_key_file()
        for check in run_startup_self_controls(PROJECT_ROOT):
            if not check.ok:
                print(f"[self-control] {check.name}: {check.message}", file=sys.stderr)
        if not WATCHLIST_FILE.exists():
            save_watchlist(DEFAULT_WATCHLIST)
    except Exception:
        pass

    root = tk.Tk()
    StockAnalysisGui(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
