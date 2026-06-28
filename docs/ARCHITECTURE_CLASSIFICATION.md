# Fiance 程式分類與擴充邊界

> 目的：讓既有功能與新增功能彼此隔離，後續擴充時先找正確分類，再接入 GUI。

## 1. 現階段策略

目前採用「相容優先」策略：

1. 保留根目錄 `AI-stock.py` 作為唯一啟動入口，GUI 主程式移到 `app/ai_stock_gui.py`。
2. 新增分類資料夾，作為未來功能的固定落點。
3. 先抽離最容易干擾 AI 輸出的 prompt 邏輯。
4. 暫不大規模搬移 GUI、資料抓取、ML 或圖表邏輯，避免破壞既有功能。

## 2. 分類資料夾

| 資料夾 | 負責內容 | 不應放入 |
|---|---|---|
| `app/` | 應用程式設定、共用型別、全域常數 | API 呼叫、GUI widget |
| `data_sources/` | FinMind、FMP、新聞、外部 API client、檔案讀取 | 投資判斷、GUI 顯示 |
| `storage/` | watchlist、API key、cache、SQLite/DuckDB 儲存 | 指標計算、AI prompt |
| `analytics/` | 技術指標、財務比率、ETF overlap、風險指標 | API 連線、GUI |
| `ml/` | ML feature、模型訓練、walk-forward、回測訊號 | 投資備忘錄文字 |
| `research/` | Public Equity prompt、source packet、thesis tracker、memo builder、catalyst calendar | 原始 API client、Tkinter widget |
| `ui/` | Tkinter 視窗、tab、event handler | 財務公式、資料抓取實作 |

## 3. 已完成的第一步

已新增下列分類入口：

- `app/__init__.py`
- `data_sources/__init__.py`
- `analytics/__init__.py`
- `ml/__init__.py`
- `research/__init__.py`
- `storage/__init__.py`
- `ui/__init__.py`
- `research/public_equity_prompt.py`
- `app/ai_stock_gui.py`
- `research/memo_contract.py`

`app/ai_stock_gui.py` 目前保留 GUI 相容邏輯，並新增一個安全接線：

```python
from research.public_equity_prompt import build_public_equity_prompt
```

並讓既有 `build_ai_prompt()` 呼叫新模組。這樣外部呼叫點不變，GUI 流程不變，但 AI prompt 已經可獨立擴充。

## 4. 兩者合併功能的落地方式

Fiance 與 Public Equity Investing 目前已用三層方式合併：

1. **最高規格文件**
   - `CHATGPT_FIANCE_PUBLIC_EQUITY_MASTER_SPEC.md`
   - 保存完整背景、角色分工、投資流程、資料限制與開發原則。

2. **程式可執行契約**
   - `research/memo_contract.py`
   - 保存 Public Equity memo sections、screen-grade 資料等級、允許的初步建議動作、decision-grade 待補資料。

3. **GUI 實際 prompt / 備忘錄輸出**
   - `research/public_equity_prompt.py`
   - 有 Gemini API key 時：建立 Public Equity Investing prompt，要求模型輸出投資備忘錄。
   - 沒有 Gemini API key 時：建立本機 deterministic screen-grade note，至少讓使用者看到 source posture、缺資料、action rules 與 open items。

`app/ai_stock_gui.py` 只保留相容函式 `build_ai_prompt()`，並轉呼叫 `research/public_equity_prompt.py`。這是刻意設計：後續研究功能擴充時，不必再改 GUI 主檔。

## 5. Gemini 3.5 與模型自我控制

Gemini 呼叫集中在：

```text
data_sources/gemini_client.py
```

模型設定集中在：

```text
app/config.py
```

目前模型策略：

1. 優先使用 `gemini-3.5-flash`。
2. 如果 3.5 發生 503、高需求、空回覆、套件缺失或其他錯誤，自動 fallback。
3. fallback 順序：
   - `gemini-3.5-flash`
   - `gemini-2.5-flash`
   - `gemini-2.5-pro`
   - `gemini-2.0-flash`
4. GUI 的 Public Equity 備忘錄開頭會顯示實際使用模型與嘗試紀錄。
5. 若本機環境沒有安裝 `google-genai`，程式會自動改用 REST API，不會直接中斷。

這是「自我控制」設計：新模型可用時優先使用，新模型不穩時不影響既有分析功能。

## 6. 後續新增功能規則

新增功能時請遵守：

1. 先判斷功能分類，再放入對應資料夾。
2. 不在 `app/ai_stock_gui.py` 直接寫新的 API client、財務公式、DCF、回測或大型 prompt。
3. 新功能先做成純函式或小 class，再由 GUI 呼叫。
4. 新功能若需要資料，請用明確輸入/輸出，不直接讀寫 UI 狀態。
5. 每次接入 GUI 前，先確認原有查詢、watchlist、AI 分析流程仍可編譯。

## 7. CHATGPT_FIANCE_PUBLIC_EQUITY_MASTER_SPEC.md 的角色

`CHATGPT_FIANCE_PUBLIC_EQUITY_MASTER_SPEC.md` 是最高層規格文件，保留完整投資流程與開發原則。

程式執行時不會每次把整份 Markdown 塞進 prompt，而是由：

```text
research/public_equity_prompt.py
```

提供濃縮、可執行、適合 API 呼叫的 Public Equity Investing prompt。

如此可避免：

- prompt 太長
- token 浪費
- 模型抓錯重點
- 規格文件和程式邏輯混在一起
