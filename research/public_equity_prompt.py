from __future__ import annotations

from typing import Any, Callable

from research.memo_contract import (
    ALLOWED_SCREEN_GRADE_ACTIONS,
    DECISION_GRADE_OPEN_ITEMS,
    PUBLIC_EQUITY_MEMO_SECTIONS,
    SCREEN_GRADE_NOTICE,
)
from research.security_classifier import classify_security


def _is_missing_number(value: Any) -> bool:
    try:
        return value != value
    except Exception:
        return True


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _format_news_items(news_items: list[Any], limit: int = 8) -> str:
    rows: list[str] = []
    for item in news_items[:limit]:
        title = str(getattr(item, "title", "")).strip()
        source = str(getattr(item, "source", "")).strip() or "Unknown"
        published = str(getattr(item, "published", "")).strip() or "n/a"
        if title:
            rows.append(f"- {title}（{source}；{published}）")
    return "\n".join(rows) if rows else "- 目前沒有可用新聞。"


def _format_open_items() -> str:
    return "\n".join(f"- {item}" for item in DECISION_GRADE_OPEN_ITEMS)


def _format_section_contract() -> str:
    return "\n".join(f"{index}. {section}" for index, section in enumerate(PUBLIC_EQUITY_MEMO_SECTIONS, start=1))


def build_local_public_equity_note(
    *,
    symbol: str,
    df: Any,
    rsi_period: int,
    news_items: list[Any],
    ml_summary: str,
    fundamental_summary: str,
    rsi_status_func: Callable[[float], str],
) -> str:
    """Build a deterministic screen-grade note when no LLM key is available."""

    start_row = df.iloc[0]
    end_row = df.iloc[-1]
    start_price = _safe_float(start_row["close"])
    end_price = _safe_float(end_row["close"])
    change_abs = end_price - start_price
    change_pct = change_abs / start_price * 100 if start_price else 0.0
    latest_rsi_series = df["RSI"].dropna()
    latest_rsi = _safe_float(latest_rsi_series.iloc[-1]) if not latest_rsi_series.empty else float("nan")
    latest_rsi_text = "資料不足" if _is_missing_number(latest_rsi) else f"{latest_rsi:.2f}"
    classification = classify_security(symbol)
    news_text = _format_news_items(news_items, limit=5)

    return f"""
# {symbol} Public Equity Screen-Grade Note

## 1. Recommendation / Decision Ask
- 建議：Further work required
- 信心等級：Low
- 資料等級：{SCREEN_GRADE_NOTICE}
- 說明：目前尚未接入完整財報、consensus 與估值模型，因此只能做初步篩選與研究待辦，不應輸出強烈買賣結論。

## 2. Executive Summary
- 資料期間：{start_row["date"].strftime("%Y-%m-%d")} 至 {end_row["date"].strftime("%Y-%m-%d")}
- 資產類型：{classification.security_type}（confidence {classification.confidence:.0%}；{", ".join(classification.reasons) or "no reason"}）
- 區間收盤價變化：{start_price:.2f} → {end_price:.2f}，漲跌 {change_abs:.2f}（{change_pct:.2f}%）
- RSI({rsi_period})：{latest_rsi_text}，狀態：{rsi_status_func(latest_rsi)}
- 基本面摘要：{fundamental_summary}
- ML 輔助訊號：{ml_summary}

## 3. Source Posture
- 已有資料：FinMind 價格資料、MA / RSI 技術指標、有限 EPS / 股利摘要、Google News RSS、ML 輔助訊號。
- 資料限制：目前缺少完整三表、分部資料、管理層 guidance、consensus、估值模型與明確 source packet。

## 4. What Is Priced In
- 目前只能根據價格趨勢與新聞標題推論市場情緒，無法判斷市場是否已反映未來營收、EPS、毛利率或資本配置變化。
- 若要回答「市場錯估了什麼」，需要補入 consensus 與 reverse DCF。

## 5. Variant Perception
- 待建立。現階段沒有足夠證據支持明確 variant perception。
- 下一步應把財報驅動因子、產業資料與市場預期放入同一張 source packet。

## 6. Thesis and Evidence
- 初步論點只能來自技術面、新聞與有限基本面，不足以作為 decision-grade thesis。
- 每個未來論點都應補齊：證據、財務影響、追蹤 KPI、反證訊號、驗證日期。

## 7. Technicals and ML Signal
- 技術面與 ML 訊號可作 timing / screening 參考。
- 它們不是獨立投資論點；必須搭配基本面、估值與催化劑驗證。

## 8. Valuation / Scenario Work
- Downside：待補營收、EPS、multiple 或 DCF 假設。
- Base：待補 consensus 與管理層 guidance。
- Upside：待補 variant driver 與可量化財務影響。

## 9. Risks and Downside Mechanism
- 目前風險尚未量化。未來需把風險連到 EPS 下修、multiple 壓縮、現金流惡化或折現率上升。

## 10. Catalysts and Monitoring
可先追蹤新聞與事件：
{news_text}

## 11. Disconfirmers
- 技術訊號失效、基本面資料與原始假設相反、新聞催化劑未轉化為營收/EPS、估值無法支持報酬風險。

## 12. Action Rules
- Initiate：需要完整財務模型、估值情境與正向報酬風險。
- Add：需要 thesis 被驗證且 upside / downside 更佳。
- Hold：資料不足但尚無明確反證。
- Trim：估值反映過度、催化劑兌現或風險升高。
- Exit：核心論點被反證，或 downside mechanism 開始發生。

## 13. Open Items / Data Requests
{_format_open_items()}
""".strip()


def build_public_equity_prompt(
    *,
    symbol: str,
    df: Any,
    rsi_period: int,
    news_items: list[Any],
    ml_summary: str,
    fundamental_summary: str,
    rsi_status_func: Callable[[float], str],
) -> str:
    """Build the compact Public Equity Investing prompt used by the GUI.

    This module intentionally holds the prompt contract outside `ai_stock_gui.py`
    so new research workflows can expand without disturbing the existing UI.
    The full operating specification is documented in
    `docs/CHATGPT_FIANCE_PUBLIC_EQUITY_MASTER_SPEC.md`.
    """

    start_row = df.iloc[0]
    end_row = df.iloc[-1]
    start_price = _safe_float(start_row["close"])
    end_price = _safe_float(end_row["close"])
    change_abs = end_price - start_price
    change_pct = change_abs / start_price * 100 if start_price else 0.0

    latest_rsi_series = df["RSI"].dropna()
    latest_rsi = _safe_float(latest_rsi_series.iloc[-1]) if not latest_rsi_series.empty else float("nan")
    latest_rsi_text = "資料不足" if _is_missing_number(latest_rsi) else f"{latest_rsi:.2f}"
    classification = classify_security(symbol)

    cols = ["date", "open", "high", "low", "close", "volume", "MA5", "MA10", "MA20", "MA60", "RSI"]
    prompt_df = df[cols].tail(120).copy()
    prompt_df["date"] = prompt_df["date"].dt.strftime("%Y-%m-%d")
    data_json = prompt_df.round(4).to_json(orient="records", force_ascii=False)

    news_text = _format_news_items(news_items)
    analysis_grade = SCREEN_GRADE_NOTICE

    return f"""
你是一位專業的 Public Equity Investing 股票研究副駕駛，請使用繁體中文回答，必要時保留英文投資術語。

最高優先規則：
- 不得把 LLM 生成內容當成已驗證事實。
- 不得只因技術指標、ML 訊號或新聞情緒給出買賣建議。
- 必須區分 fact、model output、assumption、LLM inference、PM judgment。
- 目前若缺少完整財報、consensus、估值模型或明確資料來源日期，必須標示為 screen-grade。
- 請不要假裝知道未提供的最新資料；缺資料就列在 Open Items / Data Requests。

分析標的：
- 股票代號：{symbol}
- 資產類型：{classification.security_type}
- 資產類型判斷理由：confidence {classification.confidence:.0%}；{", ".join(classification.reasons) or "no reason"}
- 資料期間：{start_row["date"].strftime("%Y-%m-%d")} 至 {end_row["date"].strftime("%Y-%m-%d")}
- 起始收盤價：{start_price:.2f}
- 最新收盤價：{end_price:.2f}
- 區間漲跌：{change_abs:.2f}（{change_pct:.2f}%）
- RSI 週期：{rsi_period}
- 最新 RSI：{latest_rsi_text}
- RSI 狀態：{rsi_status_func(latest_rsi)}
- EPS / 股利摘要：{fundamental_summary}
- ML 輔助訊號：{ml_summary}
- 資料等級：{analysis_grade}
- 允許的 screen-grade 建議動作：{", ".join(ALLOWED_SCREEN_GRADE_ACTIONS)}

必須輸出的 memo 契約：
{_format_section_contract()}

請依照以下格式輸出：

## 1. Recommendation / Decision Ask
- 建議只能是：Watchlist / No action / Hold / Further work required。若資料不足，不可直接給強烈買賣結論。
- 說明信心等級與資料等級。

## 2. Executive Summary
- 用 3-5 點摘要最重要結論。

## 3. Source Posture
- 已有資料：價格、技術指標、EPS/股利摘要、新聞、ML 訊號。
- 明確列出缺少的 decision-grade 資料。

## 4. What Is Priced In
- 根據股價走勢與可用資料，推論市場可能正在反映什麼。
- 若無 consensus，請明確說明這只是推論。

## 5. Variant Perception
- 說明可能與市場不同的看法。
- 必須標示哪些仍是待驗證假設。

## 6. Thesis and Evidence
- 每個論點都要包含：證據、財務影響、追蹤 KPI、反證訊號。

## 7. Technicals and ML Signal
- 說明 MA、RSI、成交量與 ML 訊號。
- 強調這些是輔助，不是獨立投資論點。

## 8. Valuation / Scenario Work
- 若缺乏估值輸入，請建立 Downside / Base / Upside 的「待補假設框架」，不要捏造目標價。

## 9. Risks and Downside Mechanism
- 風險必須說明如何影響 EPS、multiple、現金流、資產價值或折現率。

## 10. Catalysts and Monitoring
- 從新聞與資料中整理可能催化劑。
- 給出後續需追蹤指標。

## 11. Disconfirmers
- 列出哪些訊號出現時，代表論點可能錯了。

## 12. Action Rules
- 分別列出 Initiate / Add / Hold / Trim / Exit 需要的條件。

## 13. Open Items / Data Requests
- 列出補足 decision-grade 分析還需要的資料。
- 至少包含以下待補資料：
{_format_open_items()}

相關新聞：
{news_text}

近 120 筆價格與技術資料 JSON：
{data_json}
""".strip()
