from __future__ import annotations

import json
import os
import threading
import webbrowser
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / ".matplotlib_cache"))

import matplotlib as mpl
import numpy as np
import pandas as pd
import requests
import tkinter as tk
from matplotlib import font_manager
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from tkinter import messagebox, ttk


APP_VERSION = "v1.6"
FINMIND_API_URL = "https://api.finmindtrade.com/api/v4/data"
GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"
API_KEY_FILE = Path(r"C:\Users\shou0\PycharmProjects\api-key.txt")
WATCHLIST_FILE = PROJECT_ROOT / "watchlist.json"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
APP_BG = "#f5f7fb"
PANEL_BG = "#ffffff"
TEXT_DARK = "#1f2937"
TEXT_MUTED = "#6b7280"
ACCENT = "#2563eb"
GAIN_COLOR = "#d93025"
LOSS_COLOR = "#188038"

DEFAULT_WATCHLIST = [
    {"symbol": "2330", "name": "台積電"},
    {"symbol": "2317", "name": "鴻海"},
    {"symbol": "2454", "name": "聯發科"},
    {"symbol": "2308", "name": "台達電"},
    {"symbol": "2412", "name": "中華電"},
    {"symbol": "0050", "name": "元大台灣50"},
    {"symbol": "0056", "name": "元大高股息"},
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


def configure_matplotlib_fonts() -> None:
    """Use a Windows CJK font so chart labels render Traditional Chinese."""
    for font_path in [
        Path(r"C:\Windows\Fonts\NotoSansTC-VF.ttf"),
        Path(r"C:\Windows\Fonts\msjh.ttc"),
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\kaiu.ttf"),
    ]:
        if not font_path.exists():
            continue
        font_manager.fontManager.addfont(str(font_path))
        font_name = font_manager.FontProperties(fname=str(font_path)).get_name()
        mpl.rcParams["font.family"] = font_name
        mpl.rcParams["axes.unicode_minus"] = False
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
        return "未設定"
    if len(value) <= 8:
        return "已設定 ****"
    return f"已設定 {value[:4]}...{value[-4:]}"


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
        raise RuntimeError("FinMind API 連線逾時，請稍後再試。") from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"FinMind API 連線失敗：{exc}") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("FinMind API 回傳內容不是有效 JSON。") from exc

    rows: Any
    if isinstance(payload, dict):
        status = payload.get("status")
        msg = payload.get("msg") or payload.get("message") or payload.get("error")
        rows = payload.get("data", [])
        if status not in (None, 200, "200") and not rows:
            raise RuntimeError(f"FinMind API 回傳錯誤：{msg or status}")
    else:
        rows = payload

    if response.status_code >= 400:
        raise RuntimeError(f"FinMind API HTTP 錯誤：{response.status_code}")
    if not rows:
        raise RuntimeError(f"查無 {symbol} 在指定日期區間的台股日成交資料。")

    df = pd.DataFrame(rows)
    required_columns = ["date", "stock_id", "open", "max", "min", "close", "Trading_Volume"]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise RuntimeError("FinMind 回傳資料缺少欄位：" + ", ".join(missing))

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
        raise RuntimeError("FinMind 資料清理後沒有可用價格資料。")
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
        raise RuntimeError("FinMind API 連線逾時，請稍後再試。") from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"FinMind API 連線失敗：{exc}") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("FinMind API 回傳內容不是有效 JSON。") from exc

    if isinstance(payload, dict):
        status = payload.get("status")
        msg = payload.get("msg") or payload.get("message") or payload.get("error")
        rows = payload.get("data", [])
        if status not in (None, 200, "200") and not rows:
            raise RuntimeError(f"FinMind API 回傳錯誤：{msg or status}")
    else:
        rows = payload

    if response.status_code >= 400:
        raise RuntimeError(f"FinMind API HTTP 錯誤：{response.status_code}")
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
                messages.append("查無 EPS")
        else:
            messages.append("查無 EPS")
    except Exception as exc:
        messages.append(f"EPS 讀取失敗：{exc}")

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
                messages.append("查無股利政策")
        else:
            messages.append("查無股利政策")
    except Exception as exc:
        messages.append(f"股利讀取失敗：{exc}")

    info.message = "；".join(messages)
    if info.eps is None and info.cash_dividend is None and info.stock_dividend is None:
        info.status = "unavailable"
    return info


def format_fundamental_summary(info: FundamentalInfo) -> str:
    eps_text = "EPS：資料不足" if info.eps is None else f"EPS：{info.eps:.2f}（{info.eps_date}）"
    if info.cash_dividend is None and info.stock_dividend is None:
        dividend_text = "股利：資料不足"
    else:
        cash = 0.0 if info.cash_dividend is None else info.cash_dividend
        stock = 0.0 if info.stock_dividend is None else info.stock_dividend
        payment = info.cash_payment_month or info.cash_payment_date or "日期未定"
        dividend_text = f"股利：現金 {cash:.2f} / 股票 {stock:.2f}，發放 {payment}"
    return f"{eps_text}；{dividend_text}"


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
        return "資料不足"
    if value > 70:
        return "超買"
    if value < 30:
        return "超賣"
    return "中性"


def change_color(value: float) -> str:
    if value > 0:
        return GAIN_COLOR
    if value < 0:
        return LOSS_COLOR
    return TEXT_DARK


def fetch_market_news(symbol: str, name: str, limit: int = 12) -> list[NewsItem]:
    query_terms = [symbol, name.strip(), "台股", "股票"]
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
        raise RuntimeError(f"新聞搜尋失敗：{exc}") from exc

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as exc:
        raise RuntimeError("新聞來源回傳內容無法解析。") from exc

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
            message="資料筆數少於 90 筆，暫不訓練機器學習模型。",
            sample_count=len(df),
        )

    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:
        return MLSignal(status="missing_dependency", message=f"尚未安裝 scikit-learn：{exc}")

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
            message="可用特徵資料不足，暫不訓練機器學習模型。",
            sample_count=len(trainable),
            feature_count=len(feature_cols),
        )

    split_index = max(int(len(trainable) * 0.7), 1)
    if len(trainable) - split_index < 15:
        return MLSignal(
            status="insufficient_test_data",
            message="測試集筆數不足，暫不輸出機器學習訊號。",
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
    prediction_label = "偏多" if up_probability >= 0.5 else "偏空"

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
        message="模型僅使用歷史價量與技術指標，結果是統計訊號，不是投資建議。",
    )


def format_ml_signal(signal: MLSignal) -> str:
    if signal.status != "ok":
        return f"ML 訊號：未產生。{signal.message}"

    return (
        f"ML 訊號：{signal.prediction_label}；"
        f"上漲機率 {signal.up_probability:.1%}，下跌機率 {signal.down_probability:.1%}；"
        f"模型 {signal.model_name}；"
        f"訓練準確率 {signal.train_accuracy:.1%}，測試準確率 {signal.test_accuracy:.1%}；"
        f"樣本 {signal.sample_count} 筆。{signal.message}"
    )


def build_ai_prompt(
    symbol: str,
    df: pd.DataFrame,
    rsi_period: int,
    news_items: list[NewsItem],
    ml_signal: MLSignal,
    fundamental_info: FundamentalInfo,
) -> str:
    start_price = float(df.iloc[0]["close"])
    end_price = float(df.iloc[-1]["close"])
    change_abs = end_price - start_price
    change_pct = change_abs / start_price * 100 if start_price else 0
    latest_rsi_series = df["RSI"].dropna()
    latest_rsi = float(latest_rsi_series.iloc[-1]) if not latest_rsi_series.empty else np.nan
    cols = ["date", "open", "high", "low", "close", "volume", "MA5", "MA10", "MA20", "MA60", "RSI"]
    prompt_df = df[cols].tail(120).copy()
    prompt_df["date"] = prompt_df["date"].dt.strftime("%Y-%m-%d")
    data_json = prompt_df.round(4).to_json(orient="records", force_ascii=False)
    news_text = "\n".join(
        f"- {item.title}（{item.source}，{item.published}）" for item in news_items[:8]
    ) or "- 查無相關新聞。"
    ml_text = format_ml_signal(ml_signal)
    fundamental_text = format_fundamental_summary(fundamental_info)
    ib_applicability = "ETF 以成分股、產業曝險與資金流向為主，Investment Banking 視角僅作為市場事件提醒。" if symbol.startswith("00") else "個股可加入資本市場、公司行動、併購與估值事件視角。"

    return f"""
你是一位台股 AI 綜合分析助理。請使用繁體中文，整合技術面、相關新聞、Public Equity Investing 視角、輕量 Investment Banking 視角與機器學習訊號。
不要給保證獲利，也不要使用絕對買賣建議。請明確說明這不是投資建議。

股票代號：{symbol}
資料區間：{df.iloc[0]["date"].strftime("%Y-%m-%d")} 到 {df.iloc[-1]["date"].strftime("%Y-%m-%d")}
起始收盤價：{start_price:.2f}
結束收盤價：{end_price:.2f}
區間漲跌：{change_abs:.2f}，{change_pct:.2f}%
RSI 週期：{rsi_period}
最新 RSI：{"資料不足" if pd.isna(latest_rsi) else f"{latest_rsi:.2f}"}
RSI 狀態：{rsi_status(latest_rsi)}
EPS / 股利：{fundamental_text}
機器學習訊號：{ml_text}
Investment Banking 適用性：{ib_applicability}

請依序輸出：
1. 技術面摘要：價格趨勢、MA5 / MA10 / MA20 / MA60、成交量、RSI。
2. EPS / 股利：解讀最新 EPS、現金股利、股票股利、預計發放月份與配息金額；若是 ETF 或資料不足請明確說明。
3. 相關新聞解讀：只根據下方新聞標題做市場情緒與可能催化因子判斷，避免臆測新聞內文。
4. Public Equity Investing 視角：投資論點、多空情境、催化因子與主要風險。
5. Investment Banking 視角：資本市場、估值、公司行動或交易事件；若資料不足請明確說資料不足。
6. 機器學習訊號：說明方向、機率、測試準確率與限制，不可包裝成確定預測。
7. 綜合觀察清單：列出 3-5 個後續應追蹤事項。

相關新聞：
{news_text}

資料：
{data_json}
""".strip()


def generate_ai_insights(
    symbol: str,
    df: pd.DataFrame,
    gemini_api_key: str,
    rsi_period: int,
    news_items: list[NewsItem],
    ml_signal: MLSignal,
    fundamental_info: FundamentalInfo,
) -> str:
    if not gemini_api_key.strip():
        return (
            "未設定 Gemini API Key，已略過 AI 綜合分析。\n\n"
            + format_fundamental_summary(fundamental_info)
            + "\n"
            + format_ml_signal(ml_signal)
        )
    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError("尚未安裝 google-genai，請先執行 pip install -r requirements.txt。") from exc

    try:
        client = genai.Client(api_key=gemini_api_key.strip())
        response = client.models.generate_content(
            model=DEFAULT_GEMINI_MODEL,
            contents=build_ai_prompt(symbol, df, rsi_period, news_items, ml_signal, fundamental_info),
        )
    except Exception as exc:
        raise RuntimeError(f"Gemini API 分析失敗：{exc}") from exc

    text = getattr(response, "text", "")
    return text.strip() if text else "Gemini API 沒有回傳文字。"


class StockAnalysisGui:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(f"AI 台股技術分析 {APP_VERSION}")
        self.root.geometry("1360x900")
        self.root.minsize(1180, 760)
        self._configure_style()

        self.keys = parse_api_key_file()
        self.watchlist = load_watchlist()
        self.current_df: pd.DataFrame | None = None
        self.current_news: list[NewsItem] = []
        self.current_ml_signal = MLSignal(status="not_run", message="尚未查詢。")
        self.current_fundamental = FundamentalInfo(status="not_loaded", message="尚未查詢。")
        self.figure_canvas: FigureCanvasTkAgg | None = None

        self.symbol_var = tk.StringVar(value=self.watchlist[0]["symbol"])
        self.name_var = tk.StringVar(value=self.watchlist[0].get("name", ""))
        self.start_var = tk.StringVar(value=(date.today() - timedelta(days=180)).isoformat())
        self.end_var = tk.StringVar(value=date.today().isoformat())
        self.rsi_var = tk.IntVar(value=14)
        self.finmind_key_var = tk.StringVar(value=self.keys.finmind_api_key)
        self.gemini_key_var = tk.StringVar(value=self.keys.gemini_api_key)
        self.status_var = tk.StringVar(value=self._key_status_text())

        self.summary_vars = {
            "title": tk.StringVar(value="尚未查詢"),
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
            f"Key 檔案：{API_KEY_FILE} | "
            f"FinMind: {mask_key(self.finmind_key_var.get())} | "
            f"Gemini: {mask_key(self.gemini_key_var.get())}"
        )

    def _build_layout(self) -> None:
        root_frame = ttk.Frame(self.root, padding=10)
        root_frame.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(root_frame)
        header.pack(fill=tk.X)
        ttk.Label(header, text=f"AI 台股技術分析 {APP_VERSION}", style="Title.TLabel").pack(side=tk.LEFT)
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
        panel = ttk.LabelFrame(parent, text="自選清單", padding=8)
        panel.pack(fill=tk.BOTH, expand=True)

        self.watchlist_box = tk.Listbox(panel, height=20, exportselection=False)
        self.watchlist_box.pack(fill=tk.BOTH, expand=True)
        self.watchlist_box.bind("<<ListboxSelect>>", self._on_watchlist_select)

        button_row = ttk.Frame(panel)
        button_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(button_row, text="刪除", command=self.delete_selected_watchlist_item).pack(side=tk.LEFT)
        ttk.Button(button_row, text="重設", command=self.reset_watchlist).pack(side=tk.LEFT, padx=(8, 0))

        hint = "FinMind 台股資料源支援台股與台股 ETF。非台股代碼可儲存，但查詢時可能無資料。"
        ttk.Label(panel, text=hint, wraplength=200, foreground="#666666").pack(fill=tk.X, pady=(10, 0))

    def _build_query_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.LabelFrame(parent, text="查詢設定", padding=10)
        panel.pack(fill=tk.X)

        ttk.Label(panel, text="股票 / ETF 代碼").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(panel, textvariable=self.symbol_var, width=14).grid(row=1, column=0, sticky=tk.W, padx=(0, 12))

        ttk.Label(panel, text="名稱").grid(row=0, column=1, sticky=tk.W)
        ttk.Entry(panel, textvariable=self.name_var, width=18).grid(row=1, column=1, sticky=tk.W, padx=(0, 12))

        ttk.Label(panel, text="起始日期").grid(row=0, column=2, sticky=tk.W)
        ttk.Entry(panel, textvariable=self.start_var, width=12).grid(row=1, column=2, sticky=tk.W, padx=(0, 12))

        ttk.Label(panel, text="結束日期").grid(row=0, column=3, sticky=tk.W)
        ttk.Entry(panel, textvariable=self.end_var, width=12).grid(row=1, column=3, sticky=tk.W, padx=(0, 12))

        ttk.Label(panel, text="RSI").grid(row=0, column=4, sticky=tk.W)
        ttk.Spinbox(panel, from_=2, to=60, textvariable=self.rsi_var, width=6).grid(row=1, column=4, sticky=tk.W, padx=(0, 12))

        ttk.Button(panel, text="查詢分析", command=self.start_analysis, style="Accent.TButton").grid(row=1, column=5, padx=(0, 8))
        ttk.Button(panel, text="儲存為自選", command=self.save_current_symbol_to_watchlist).grid(row=1, column=6, padx=(0, 8))
        ttk.Button(panel, text="儲存 Key", command=self.save_keys_from_gui).grid(row=1, column=7)

        key_row = ttk.Frame(panel)
        key_row.grid(row=2, column=0, columnspan=8, sticky=tk.EW, pady=(10, 0))
        ttk.Label(key_row, text="FinMind").pack(side=tk.LEFT)
        ttk.Entry(key_row, textvariable=self.finmind_key_var, width=44, show="*").pack(side=tk.LEFT, padx=(6, 16))
        ttk.Label(key_row, text="Gemini").pack(side=tk.LEFT)
        ttk.Entry(key_row, textvariable=self.gemini_key_var, width=44, show="*").pack(side=tk.LEFT, padx=(6, 0))

    def _build_summary_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.LabelFrame(parent, text="總覽", padding=10)
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
        self.ai_tab = ttk.Frame(self.tabs)
        self.ml_tab = ttk.Frame(self.tabs)
        self.fundamental_tab = ttk.Frame(self.tabs)
        self.news_tab = ttk.Frame(self.tabs)

        self.tabs.add(self.chart_tab, text="走勢圖")
        self.tabs.add(self.table_tab, text="歷史資料")
        self.tabs.add(self.ai_tab, text="AI 綜合分析")
        self.tabs.add(self.ml_tab, text="ML 訊號")
        self.tabs.add(self.fundamental_tab, text="基本股利")
        self.tabs.add(self.news_tab, text="相關新聞")

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
        self.news_table.heading("title", text="標題")
        self.news_table.heading("source", text="來源")
        self.news_table.heading("published", text="時間")
        self.news_table.column("title", width=760, anchor=tk.W)
        self.news_table.column("source", width=140, anchor=tk.W)
        self.news_table.column("published", width=260, anchor=tk.W)
        self.news_table.pack(fill=tk.BOTH, expand=True, padx=4, pady=(4, 8))
        self.news_table.bind("<Double-1>", self.open_selected_news)

        news_buttons = ttk.Frame(self.news_tab)
        news_buttons.pack(fill=tk.X, padx=4, pady=(0, 4))
        ttk.Button(news_buttons, text="開啟選取新聞", command=self.open_selected_news).pack(side=tk.LEFT)
        ttk.Label(news_buttons, text="新聞來源：Google News RSS；雙擊列可開啟連結。", style="Muted.TLabel").pack(
            side=tk.LEFT,
            padx=(12, 0),
        )

    def _table_heading(self, col: str) -> str:
        return {
            "date": "日期",
            "open": "開盤",
            "high": "最高",
            "low": "最低",
            "close": "收盤",
            "volume": "成交量",
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
            messagebox.showerror("輸入錯誤", "請輸入股票或 ETF 代碼。")
            return

        name = self.name_var.get().strip()
        for item in self.watchlist:
            if item["symbol"] == symbol:
                item["name"] = name or item.get("name", "")
                save_watchlist(self.watchlist)
                self._refresh_watchlist_ui()
                messagebox.showinfo("已更新", f"{symbol} 已更新到自選清單。")
                return

        self.watchlist.append({"symbol": symbol, "name": name})
        save_watchlist(self.watchlist)
        self._refresh_watchlist_ui()
        messagebox.showinfo("已儲存", f"{symbol} 已加入自選清單。")

    def delete_selected_watchlist_item(self) -> None:
        selection = self.watchlist_box.curselection()
        if not selection:
            return
        index = selection[0]
        item = self.watchlist[index]
        if not messagebox.askyesno("確認刪除", f"要從自選清單刪除 {display_name(item)} 嗎？"):
            return
        del self.watchlist[index]
        if not self.watchlist:
            self.watchlist = list(DEFAULT_WATCHLIST)
        save_watchlist(self.watchlist)
        self._refresh_watchlist_ui()

    def reset_watchlist(self) -> None:
        if not messagebox.askyesno("確認重設", "要把自選清單重設為預設清單嗎？"):
            return
        self.watchlist = list(DEFAULT_WATCHLIST)
        save_watchlist(self.watchlist)
        self._refresh_watchlist_ui()

    def save_keys_from_gui(self) -> None:
        try:
            save_api_keys(ApiKeys(self.finmind_key_var.get(), self.gemini_key_var.get()))
        except Exception as exc:
            messagebox.showerror("儲存失敗", str(exc))
            return
        self.status_var.set(self._key_status_text())
        messagebox.showinfo("已儲存", f"API key 已儲存到：\n{API_KEY_FILE}")

    def start_analysis(self) -> None:
        try:
            symbol = normalize_symbol(self.symbol_var.get())
            start_date = datetime.strptime(self.start_var.get().strip(), "%Y-%m-%d").date()
            end_date = datetime.strptime(self.end_var.get().strip(), "%Y-%m-%d").date()
            rsi_period = int(self.rsi_var.get())
        except ValueError:
            messagebox.showerror("輸入錯誤", "日期請使用 YYYY-MM-DD，RSI 請輸入整數。")
            return

        if not symbol:
            messagebox.showerror("輸入錯誤", "請輸入股票或 ETF 代碼。")
            return
        if start_date >= end_date:
            messagebox.showerror("輸入錯誤", "起始日期必須早於結束日期。")
            return

        self._set_busy(True)
        self.ai_text.delete("1.0", tk.END)
        self.ai_text.insert(tk.END, "資料讀取與分析中...\n")
        worker = threading.Thread(
            target=self._run_analysis_worker,
            args=(symbol, start_date, end_date, rsi_period),
            daemon=True,
        )
        worker.start()

    def _run_analysis_worker(self, symbol: str, start_date: date, end_date: date, rsi_period: int) -> None:
        try:
            raw_df = fetch_finmind_stock_price(symbol, self.finmind_key_var.get(), start_date, end_date)
            df = add_indicators(raw_df, rsi_period)
            ml_signal = train_ml_signal(df)
            fundamental_info = fetch_fundamental_info(symbol, self.finmind_key_var.get())
            try:
                news_items = fetch_market_news(symbol, self.name_var.get())
            except Exception as exc:
                news_items = [NewsItem(title=f"新聞搜尋失敗：{exc}", source="System", published="", link="")]
            ai_report = generate_ai_insights(
                symbol,
                df,
                self.gemini_key_var.get(),
                rsi_period,
                news_items,
                ml_signal,
                fundamental_info,
            )
        except Exception as exc:
            self.root.after(0, lambda: self._show_error(str(exc)))
            return
        self.root.after(
            0,
            lambda: self._render_result(
                symbol,
                df,
                rsi_period,
                ai_report,
                news_items,
                ml_signal,
                fundamental_info,
            ),
        )

    def _set_busy(self, busy: bool) -> None:
        self.root.config(cursor="watch" if busy else "")
        self.status_var.set("分析中..." if busy else self._key_status_text())

    def _show_error(self, message: str) -> None:
        self._set_busy(False)
        self.ai_text.delete("1.0", tk.END)
        self.ai_text.insert(tk.END, message)
        messagebox.showerror("分析失敗", message)

    def _render_result(
        self,
        symbol: str,
        df: pd.DataFrame,
        rsi_period: int,
        ai_report: str,
        news_items: list[NewsItem],
        ml_signal: MLSignal,
        fundamental_info: FundamentalInfo,
    ) -> None:
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
        self.ai_text.insert(tk.END, ai_report)
        self.tabs.select(self.chart_tab)

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
        self.summary_vars["volume"].set(f"成交量 {float(latest['volume']):,.0f}")
        self.summary_vars["rsi"].set(
            f"RSI({rsi_period}) {'資料不足' if pd.isna(latest_rsi) else f'{latest_rsi:.2f} {rsi_status(latest_rsi)}'}"
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

        fig = Figure(figsize=(12, 6.6), dpi=100)
        price_ax = fig.add_subplot(3, 1, 1)
        volume_ax = fig.add_subplot(3, 1, 2, sharex=price_ax)
        rsi_ax = fig.add_subplot(3, 1, 3, sharex=price_ax)

        x = np.arange(len(df))
        for idx, row in df.iterrows():
            color = GAIN_COLOR if row["close"] >= row["open"] else LOSS_COLOR
            price_ax.vlines(idx, row["low"], row["high"], color=color, linewidth=1)
            body_low = min(row["open"], row["close"])
            body_high = max(row["open"], row["close"])
            height = max(body_high - body_low, 0.01)
            price_ax.add_patch(plt_rectangle(idx - 0.32, body_low, 0.64, height, color, 0.85))

        for ma in ("MA5", "MA10", "MA20", "MA60"):
            price_ax.plot(x, df[ma], linewidth=1.2, label=ma)
        price_ax.set_title(f"{symbol} 台股日 K / MA")
        price_ax.set_ylabel("價格")
        price_ax.grid(True, alpha=0.18)
        price_ax.legend(loc="upper left", ncol=4, fontsize=8)

        volume_colors = [GAIN_COLOR if close >= open_ else LOSS_COLOR for open_, close in zip(df["open"], df["close"])]
        volume_ax.bar(x, df["volume"], color=volume_colors, alpha=0.62)
        volume_ax.set_ylabel("成交量")
        volume_ax.grid(True, axis="y", alpha=0.18)

        rsi_ax.plot(x, df["RSI"], color="#1f77b4", linewidth=1.4)
        rsi_ax.axhline(70, color=GAIN_COLOR, linestyle="--", linewidth=1)
        rsi_ax.axhline(30, color=LOSS_COLOR, linestyle="--", linewidth=1)
        rsi_ax.fill_between(x, 70, 100, color=GAIN_COLOR, alpha=0.07)
        rsi_ax.fill_between(x, 0, 30, color=LOSS_COLOR, alpha=0.07)
        rsi_ax.set_ylim(0, 100)
        rsi_ax.set_ylabel(f"RSI({rsi_period})")
        rsi_ax.grid(True, alpha=0.18)

        tick_count = min(8, len(df))
        tick_positions = np.linspace(0, len(df) - 1, tick_count, dtype=int)
        tick_labels = [df.iloc[pos]["date"].strftime("%Y-%m-%d") for pos in tick_positions]
        rsi_ax.set_xticks(tick_positions)
        rsi_ax.set_xticklabels(tick_labels, rotation=20, ha="right")
        fig.tight_layout()

        self.figure_canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.figure_canvas.draw()
        self.figure_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

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
            self.news_table.insert("", tk.END, values=("查無相關新聞", "", ""))
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
                "機器學習漲跌訊號",
                "",
                f"模型：{signal.model_name}",
                f"預測方向：{signal.prediction_label}",
                f"上漲機率：{signal.up_probability:.1%}",
                f"下跌機率：{signal.down_probability:.1%}",
                f"訓練準確率：{signal.train_accuracy:.1%}",
                f"測試準確率：{signal.test_accuracy:.1%}",
                f"樣本數：{signal.sample_count}",
                f"特徵數：{signal.feature_count}",
                "",
                "特徵來源：日報酬、5 日報酬、日內振幅、成交量變化、5 日波動率、MA 乖離、MA 斜率、RSI。",
                "",
                "限制：模型只使用歷史價量與技術指標，沒有納入財報、籌碼、總經、產業資料或完整新聞語意。這是統計訊號，不是投資建議。",
            ]
        )
        self.ml_text.insert(tk.END, detail)

    def _fill_fundamental(self, info: FundamentalInfo) -> None:
        self.fundamental_text.delete("1.0", tk.END)
        lines = [
            "EPS / 股利資訊",
            "",
            "EPS",
            f"最新 EPS：{'資料不足' if info.eps is None else f'{info.eps:.2f}'}",
            f"EPS 財報日期：{info.eps_date or '資料不足'}",
            "",
            "股利",
            f"股利年度：{info.dividend_year or '資料不足'}",
            f"現金股利：{'資料不足' if info.cash_dividend is None else f'{info.cash_dividend:.2f}'}",
            f"股票股利：{'資料不足' if info.stock_dividend is None else f'{info.stock_dividend:.2f}'}",
            f"預計發放月份：{info.cash_payment_month or '資料不足'}",
            f"現金股利發放日：{info.cash_payment_date or '資料不足'}",
            f"除息交易日：{info.cash_ex_dividend_date or '資料不足'}",
            f"除權交易日：{info.stock_ex_dividend_date or '資料不足'}",
            f"公告日期：{info.announcement_date or '資料不足'}",
        ]
        if info.message:
            lines.extend(["", "備註", info.message])
        lines.extend(
            [
                "",
                "資料來源：FinMind TaiwanStockFinancialStatements / TaiwanStockDividend。",
                "說明：EPS 為 FinMind 最新 EPS 欄位；股利以最新可用或未來發放資料為準。ETF 或海外代碼可能沒有 EPS 或股利政策資料。",
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


def plt_rectangle(x: float, y: float, width: float, height: float, color: str, alpha: float):
    from matplotlib.patches import Rectangle

    return Rectangle((x, y), width, height, facecolor=color, edgecolor=color, alpha=alpha)


def main() -> int:
    configure_matplotlib_fonts()
    try:
        ensure_api_key_file()
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
