"""Shared Public Equity Investing memo contract for Fiance.

The full human-readable master specification lives in
`docs/CHATGPT_FIANCE_PUBLIC_EQUITY_MASTER_SPEC.md`. This module keeps the compact
runtime contract that can be safely imported by GUI and prompt code.
"""

PUBLIC_EQUITY_MEMO_SECTIONS = [
    "Recommendation / Decision Ask",
    "Executive Summary",
    "Source Posture",
    "What Is Priced In",
    "Variant Perception",
    "Thesis and Evidence",
    "Technicals and ML Signal",
    "Valuation / Scenario Work",
    "Risks and Downside Mechanism",
    "Catalysts and Monitoring",
    "Disconfirmers",
    "Action Rules",
    "Open Items / Data Requests",
]

SCREEN_GRADE_NOTICE = (
    "Screen-grade。現有輸入主要包含價格、技術指標、有限基本面、新聞與 ML 輔助訊號；"
    "除非另有完整財報、consensus、估值模型與來源日期，否則不得宣稱 decision-grade。"
)

ALLOWED_SCREEN_GRADE_ACTIONS = [
    "Watchlist",
    "No action",
    "Hold",
    "Further work required",
]

DECISION_GRADE_OPEN_ITEMS = [
    "完整三表財務資料與最近一期財報來源",
    "管理層 guidance / 法說會逐字稿 / IR 簡報",
    "consensus 預估、評等分布與目標價區間",
    "Downside / Base / Upside 估值假設",
    "同業比較、估值倍數與 reverse DCF implied expectations",
    "部位規模、投資期限、benchmark 與風險限制",
    "明確 catalyst calendar、disconfirmers 與 action rules",
]
