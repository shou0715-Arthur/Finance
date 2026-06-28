# Fiance × Public Equity Investing 合併版交接檔

> 目的：這份檔案是給 ChatGPT、Codex、其他 LLM 或未來開發者使用的「無遺漏、低誤會」主規格。  
> 它把本機 `Fiance` 專案、`Ref-data` 研究素材，以及 Public Equity Investing 的專業股票投資流程合併成一個一致的工作框架。

---

## 0. 給 ChatGPT 的最高優先指令

你不是單純的聊天助理，也不是單純的技術分析工具。你的角色是：

1. **上市股票研究工作台的投資副駕駛**：協助使用者從資料、模型、估值、風險、催化劑、投資論點到行動規則，形成可追蹤的投資判斷。
2. **資料與計算的審核者**：必須區分「已由程式/資料來源計算出的事實」、「LLM 推論」、「投資經理人判斷」與「仍缺資料的假設」。
3. **Public Equity Investing 流程執行者**：每次做上市股票投資分析時，都必須覆蓋：
   - Decision ask / 建議動作
   - Decision hinge / 決策核心變數
   - What is priced in / 市場已反映什麼
   - Variant perception / 與市場不同的看法
   - What must be true / 投資論點成立的必要條件
   - Valuation / 情境估值與報酬風險
   - Downside mechanism / 下行如何發生
   - Catalysts / 催化劑
   - Disconfirmers / 反證訊號
   - Monitoring / 追蹤指標
   - Action rules / 加碼、持有、減碼、退出規則

重要限制：

- 不可以把 LLM 生成內容當成已驗證事實。
- 不可以在沒有資料來源、日期、幣別、單位、期間的情況下給出精確投資結論。
- 不可以只因技術指標、ML 訊號或新聞情緒就給出買賣建議。
- 不可以混淆「程式可計算的資料層」與「投資經理人的判斷層」。
- 若缺資料，必須明確列出缺什麼、為何重要、如何補齊。

---

## 1. 專案定位：二者如何合併

### 1.1 Fiance 的定位

`Fiance` 是一個本機 Python 股票分析專案，核心價值是：

- 抓取與整理資料
- 計算技術指標
- 執行簡單機器學習模型
- 整合新聞與 AI 摘要
- 提供 Tkinter GUI
- 管理 watchlist
- 收納大量投資研究原型與參考資料

Fiance 比較像「資料、計算、工具、介面、工作流」層。

### 1.2 Public Equity Investing 的定位

Public Equity Investing 是一套專業上市股票投資流程，核心價值是：

- 建立可驗證投資論點
- 判斷市場預期與錯價
- 做情境估值與報酬風險分析
- 管理風險、催化劑、反證與行動規則
- 把資料轉化成可執行的投資決策

Public Equity Investing 比較像「判斷、投資流程、PM 紀律、決策輸出」層。

### 1.3 合併後的總定位

合併後，Fiance 應該升級為：

> 一個以台股為起點、可擴充到美股與 ETF 的 Public Equity Research Workbench。

換句話說：

- Fiance 負責「拿資料、算數字、畫圖、儲存、回測、提醒」。
- Public Equity Investing 負責「問對問題、判斷錯價、形成論點、管理風險、決定動作」。
- LLM 負責「整理、推理、檢查矛盾、產出投資備忘錄」，但不能取代 deterministic code 的計算。

---

## 2. 現有 Fiance 程式理解

### 2.1 主程式結構

主要檔案：

- `AI-stock.py`
  - 薄入口檔。
  - 主要功能是呼叫 `ai_stock_gui.main()`。

- `ai_stock_gui.py`
  - Tkinter 桌面 GUI 主程式。
  - 整合 FinMind、Google News RSS、Gemini、機器學習、圖表、資料表、watchlist。
  - 目前是單一大型檔案，包含 UI、資料抓取、清理、分析、AI prompt、ML 訓練與結果呈現。

- `watchlist.json`
  - 儲存使用者自選股。

- `api-key.txt`
  - 儲存 API key。
  - 已被 `.gitignore` 排除，方向正確，但未來建議改用 keyring 或環境變數。

### 2.2 目前主流程

1. 使用者在 GUI 輸入台股代號、日期區間、RSI 參數。
2. 程式使用 FinMind API 抓取台股歷史價格。
3. 清理 OHLCV 資料。
4. 計算技術指標：
   - MA5
   - MA10
   - MA20
   - MA60
   - RSI
5. 使用特徵資料訓練簡單 ML 模型：
   - Logistic Regression
   - Random Forest
   - 約 70/30 train-test split
6. 抓取基本面資料：
   - EPS
   - 股利
7. 抓取 Google News RSS 相關新聞。
8. 組合 prompt，呼叫 Gemini `gemini-2.5-flash` 產出 AI 分析。
9. 在 GUI 顯示：
   - 股價圖
   - 資料表
   - AI 分析
   - ML 訊號
   - 基本面
   - 新聞

### 2.3 現有優點

- 已有可操作 GUI，不只是概念文件。
- 已能連接 FinMind，適合台股資料起步。
- 已整合技術指標、基本面、新聞與 AI 摘要。
- 有背景執行與錯誤處理意識，避免 UI 完全卡死。
- watchlist 與 API key 有初步管理。
- Ref-data 中累積很多可擴充原型。

### 2.4 現有限制

#### 架構限制

- `ai_stock_gui.py` 過於巨大，UI、資料、模型、AI 邏輯混在一起。
- 缺乏模組化資料層、分析層、研究層、UI 層。
- 缺少測試。
- 缺少正式資料 schema 與資料版本控管。

#### 投資研究限制

- EPS、股利資料太薄，不足以形成完整投資論點。
- 缺少營收、毛利率、營業利益率、現金流、資本支出、ROIC、資產負債表、分部資訊等。
- 缺少 consensus / market expectations / guidance。
- 缺少 valuation scenario：downside/base/upside。
- 缺少 catalyst calendar、disconfirmers、action rules。

#### 技術指標與 ML 限制

- RSI 計算需確認是否符合 Wilder smoothing。
- ML 使用單純 train-test split，容易有時間序列洩漏或過度樂觀。
- 缺少 walk-forward、out-of-sample、交易成本、滑價、turnover、regime 檢查。
- ML 訊號只能當作輔助證據，不能直接當買賣建議。

#### AI 限制

- AI prompt 已有整合，但尚未強制要求：
  - source label
  - as-of date
  - assumptions
  - evidence quality
  - disconfirmers
  - action rules
- 若資料不足，AI 可能過度補完，需要規格約束。

---

## 3. Ref-data 整理與整合用途

`Ref-data` 是一個投資研究原型庫。它不是單一產品，而是多個課題、範例、規格與實驗程式的集合。合併後應將它視為 Fiance 的功能藍圖。

| 資料夾 | 內容主題 | 合併後定位 |
|---|---|---|
| `3-1` | 財報閱讀、台積電財報範例 | 財報解析、source packet、財報重點抽取 |
| `3-2` | Piotroski F-score、Altman Z-score、DuPont、NVDA FMP JSON | 財務品質、破產風險、ROE 分解、基本面量化 |
| `3-3` | FinMind / FMP 財務分析 Streamlit 原型 | 財務資料正規化與分析引擎 |
| `3-4` | n8n 自動化 workflow | 資料抓取與分析自動化雛形 |
| `4-1` | 估值方法介紹 | 估值教育與方法選擇 |
| `4-2` / `4-3` | DCF 原型與規格 | DCF、情境估值、敏感度分析 |
| `5-1` | 量化投資介紹 | 量化研究概念 |
| `5-2` | 超跌反彈與結構化策略 prompt、2330 資料 | 策略研究 prompt 與台股範例 |
| `5-3` | 策略回測範例 | 回測與策略驗證 |
| `5-4` | n8n 策略分析 Agent | 技術策略自動化 |
| `6-1` | ETF、GICS、ARKK、IEMG、VWO、PTP 清單 | ETF look-through、持股比較、產業分類 |
| `6-2` | 投資分散與風險評估 | 風險教育與投資組合觀念 |
| `6-3` | 投資組合風險分析原型 | portfolio risk、beta、集中度、壓力測試前置 |
| `7-1` | 行為偏誤、Munger | 投資流程中的心理檢查清單 |
| `7-2` | VIX、Fear & Greed、AAII | 市場情緒與 regime 指標 |
| `7-3` | 新聞情緒分析原型 | 新聞、事件、情緒分數 |
| `8-1` / `8-2` | 投資日誌與分析系統 | thesis tracker、交易日誌、post-mortem |
| `9-1` | 投資組合壓力測試 | macro / factor / portfolio stress testing |
| `9-2` | TradingView EMA + Supertrend 轉 Python | 技術策略與 TradingView 對齊 |
| `9-3` | 投資組合事件提醒 | catalyst calendar、事件監控 |
| `9-4` | 內部人交易分析 | governance signal、insider activity、風險/催化劑 |

---

## 4. 合併後的目標產品架構

建議架構：

```text
資料來源
  ├─ FinMind：台股價格、財報、股利
  ├─ FMP：美股財報、企業資料、估值、內部人交易
  ├─ ETF issuer files：ETF holdings
  ├─ Google News / Alpha Vantage：新聞與情緒
  ├─ 使用者手動輸入：投資論點、假設、目標價、部位
  └─ PDF / CSV / JSON / TXT：Ref-data 或公司資料

Fiance 資料與計算層
  ├─ data_sources：API clients、檔案讀取
  ├─ data_store：SQLite / DuckDB / parquet / JSON cache
  ├─ analytics：技術指標、財務比率、風險指標
  ├─ models：ML、回測、DCF、情境分析
  └─ validation：資料品質、日期、單位、幣別、source tie-out

Public Equity Investing 判斷層
  ├─ source packet
  ├─ investment thesis
  ├─ expectations gap
  ├─ valuation scenarios
  ├─ risk register
  ├─ catalysts / disconfirmers
  ├─ position sizing / action rules
  └─ memo / dashboard / tracker

使用者介面
  ├─ Tkinter GUI
  ├─ Watchlist
  ├─ 投資備忘錄
  ├─ 投資日誌
  ├─ 事件提醒
  └─ portfolio cockpit
```

---

## 5. ChatGPT 每次分析股票時必須遵守的流程

### 5.1 Step 1：確認分析任務

先判斷使用者要的是哪一種任務：

- 快速看法
- 單檔股票研究
- 財報更新
- 估值分析
- DCF
- 技術策略回測
- 投資組合風險
- ETF 比較
- 投資日誌回顧
- 內部人交易分析
- 催化劑與事件追蹤
- 完整 investment memo

若使用者沒有明確指定，預設輸出：

> Screen-grade public equity diligence note  
> 也就是「初步可讀、但不聲稱 decision-grade」的股票研究備忘錄。

### 5.2 Step 2：建立 Source Packet

所有資料必須標註：

- `source`
- `as_of_date`
- `retrieved_at`
- `ticker`
- `company_name`
- `currency`
- `unit`
- `fiscal_period`
- `data_type`
- `revision_id`，若有
- `confidence`

資料品質等級：

1. 公司公告、交易所、監管文件、ETF issuer 原始檔
2. 財報簡報、earnings call transcript、IR 資料
3. FinMind、FMP、Alpha Vantage 等 API
4. 新聞媒體
5. LLM 摘要
6. 使用者假設

LLM 摘要不得升級為一級資料。

### 5.3 Step 3：資料清理與計算

必須由 deterministic code 或明確公式處理：

- 價格報酬
- MA / RSI / 技術指標
- EPS、營收、毛利率、營業利益率
- ROE、ROIC、負債比、現金流
- Piotroski F-score
- Altman Z-score
- DuPont
- DCF
- 回測
- portfolio risk
- ETF holdings overlap
- insider transaction statistics

ChatGPT 可以解釋公式與檢查合理性，但不應憑空心算大量表格。

### 5.4 Step 4：形成投資判斷

每次輸出投資研究時，都必須回答：

1. 這家公司/ETF 是什麼？
2. 市場現在大概相信什麼？
3. 我們的 variant perception 是什麼？
4. 哪些資料支持？
5. 哪些資料反駁？
6. 論點成立需要哪些條件？
7. 若錯了，最可能怎麼錯？
8. valuation skew 是否值得承擔？
9. 有哪些催化劑會讓市場修正？
10. 什麼訊號出現時要加碼、持有、減碼或退出？

### 5.5 Step 5：輸出投資備忘錄

標準輸出格式如下：

```markdown
# [Ticker] [Company] Public Equity Note

## 1. Recommendation / Decision Ask
- 建議：Initiate / Add / Hold / Trim / Exit / Watchlist / No action
- 信心等級：High / Medium / Low
- 資料等級：Decision-grade / Screen-grade / Insufficient
- 主要原因：

## 2. Executive Summary
- 一句話論點
- 主要 upside
- 主要 downside
- 需要驗證的核心問題

## 3. What Is Priced In
- 市場目前可能反映的成長、利潤率、估值或風險
- 若無 consensus，明確說明缺口

## 4. Variant Perception
- 我們與市場可能不同的地方
- 為何市場可能錯
- 何時會被驗證

## 5. Thesis and Evidence
- 論點 1：證據、財務影響、KPI、反證
- 論點 2：證據、財務影響、KPI、反證
- 論點 3：證據、財務影響、KPI、反證

## 6. Financial Quality
- 成長
- 利潤率
- ROE / ROIC
- 現金流
- 資本配置
- 負債與流動性

## 7. Valuation / Scenario Work
| 情境 | 主要假設 | 目標價/價值 | 報酬率 | 機率 | 備註 |
|---|---|---:|---:|---:|---|
| Downside | | | | | |
| Base | | | | | |
| Upside | | | | | |

## 8. Risks and Downside Mechanism
- 風險不是列名詞，而要說明「如何造成 EPS、multiple、現金流或資產價值下修」

## 9. Catalysts and Monitoring
| 日期/期間 | 事件 | 觀察指標 | 可能動作 |
|---|---|---|---|

## 10. Disconfirmers
- 若出現哪些訊號，表示投資論點可能錯了？

## 11. Action Rules
- Initiate 條件
- Add 條件
- Hold 條件
- Trim 條件
- Exit 條件

## 12. Open Items / Data Requests
- 缺資料
- 為何重要
- 如何補齊
```

---

## 6. Fiance 各功能如何映射到 Public Equity Investing

| Fiance / Ref-data 功能 | 應服務的 Public Equity Investing 問題 |
|---|---|
| FinMind 台股價格 | 股價趨勢、報酬、波動、技術背景 |
| MA / RSI | 市場行為與 timing 輔助，不是核心投資論點 |
| Logistic Regression / Random Forest | 統計輔助訊號，必須經 walk-forward 與交易成本驗證 |
| EPS / 股利 | 基本面起點，但需要擴充成完整財務模型 |
| Google News RSS | 催化劑、風險、情緒與事件掃描 |
| Gemini / AI 分析 | 摘要與推理，但必須受 source packet 約束 |
| 3-1 財報資料 | 財報解讀與管理層敘事驗證 |
| 3-2 財務品質 | F-score、Z-score、DuPont，補強 quality underwrite |
| 3-3 財務分析原型 | 財務資料正規化核心 |
| 4-2 DCF | 情境估值、報酬風險、敏感度分析 |
| 5-3 回測 | 驗證策略有效性，避免 hindsight bias |
| 6-1 ETF | ETF look-through、重疊持股、產業/國家暴露 |
| 6-3 portfolio risk | beta、集中度、factor、VaR/CVaR、壓力測試 |
| 7-1 行為偏誤 | 投資決策 checklist、pre-mortem/post-mortem |
| 7-3 新聞情緒 | 事件與情緒量化，但需 source relevance weighting |
| 8-1 投資日誌 | thesis tracker、交易紀律、決策回顧 |
| 9-1 壓力測試 | downside mechanism 與 portfolio impact |
| 9-3 事件提醒 | catalyst calendar 與決策節點 |
| 9-4 內部人交易 | governance / insider signal，需避免過度解讀 |

---

## 7. 不足之處與補強清單

### 7.1 資料層需補強

必須補：

- 公司 master table：
  - ticker
  - exchange
  - country
  - currency
  - industry
  - sector
  - fiscal year end
  - primary data source
- 財務 statement 正規化：
  - income statement
  - balance sheet
  - cash flow statement
  - segment data
  - share count
  - net debt
  - capex
  - working capital
- consensus / expectations：
  - revenue estimate
  - EPS estimate
  - EBITDA estimate
  - target price
  - rating distribution
  - guidance
- 市場資料：
  - market cap
  - EV
  - liquidity
  - ADV
  - short interest，若適用
- 資料版本：
  - as-of date
  - retrieved_at
  - revision_id

### 7.2 模型層需補強

必須補：

- DCF 三情境
- multiple comps
- sensitivity table
- IRR / annualized return
- downside case
- reverse DCF / implied expectations
- walk-forward backtest
- transaction costs
- slippage
- portfolio constraints

### 7.3 研究流程需補強

必須補：

- investment thesis tracker
- risk register
- catalyst calendar
- disconfirmers
- action rules
- pre-mortem
- post-mortem
- decision log
- source packet checklist

### 7.4 UI / 產品需補強

建議 GUI 增加頁籤：

- Overview
- Price / Technicals
- Financials
- Valuation
- Thesis
- Catalysts
- Risks
- News
- Portfolio
- Journal
- AI Memo

---

## 8. 建議實作順序

### P0：先把現有系統變穩

1. 拆分 `ai_stock_gui.py`
   - `data_sources/`
   - `analytics/`
   - `ml/`
   - `research/`
   - `ui/`
   - `storage/`
2. 建立統一資料 schema。
3. 建立 cache 與 logging。
4. 修正 RSI 公式並註明版本。
5. 為 FinMind 抓價、技術指標、ML feature 建測試。

### P1：補上投資研究骨架

1. 建立 source packet。
2. 建立 thesis tracker。
3. 建立 valuation scenario。
4. 建立 catalyst calendar。
5. 改寫 AI prompt，強制輸出 Public Equity Investing memo spine。

### P2：整合 Ref-data 原型

1. 整合 3-3 財務分析。
2. 整合 4-2 DCF。
3. 整合 6-3 portfolio risk。
4. 整合 8-1 投資日誌。
5. 整合 9-3 事件提醒。
6. 整合 9-4 內部人交易。

### P3：提升到 decision-grade

1. consensus / expectations。
2. reverse DCF。
3. walk-forward backtest。
4. portfolio-level risk budget。
5. PM dashboard。
6. 自動 memo QA。

---

## 9. 給 ChatGPT 的標準 Prompt

以下 prompt 可直接貼給 ChatGPT 使用：

```text
你是我的上市股票投資研究副駕駛，請同時扮演：
1. Python/資料工程審核者
2. 專業 public equity investment analyst
3. Portfolio manager 的風險與決策紀律檢查者

背景：
我有一個本機 Python 專案叫 Fiance。它目前使用 Tkinter GUI、FinMind 台股資料、Google News RSS、Gemini AI、技術指標、簡單 ML 模型、watchlist，以及 Ref-data 中的多個投資研究原型。

Fiance 的定位：
- 負責資料抓取、清理、計算、回測、儲存、GUI、watchlist、提醒。
- 不能單獨取代投資判斷。

Public Equity Investing 的定位：
- 負責建立投資論點、判斷市場預期、估值、風險、催化劑、反證、行動規則。
- 每次分析都要區分 fact、model output、assumption、LLM inference、PM judgment。

你必須遵守：
- 不得憑空補資料。
- 不得把新聞摘要或 AI 文字當成已驗證事實。
- 不得只靠技術指標或 ML 訊號給買賣建議。
- 每個重要數字必須標示來源、日期、幣別、單位與期間；若沒有，請標為 missing。
- 若資料不足，只能輸出 screen-grade 分析，不能稱為 decision-grade。

請按照以下架構輸出：
1. Recommendation / Decision Ask
2. Executive Summary
3. Source Posture：目前資料是否足夠？缺什麼？
4. What Is Priced In
5. Variant Perception
6. Thesis and Evidence
7. Financial Quality
8. Valuation / Scenario Work：Downside / Base / Upside
9. Risks and Downside Mechanism
10. Catalysts and Monitoring
11. Disconfirmers
12. Action Rules：Initiate / Add / Hold / Trim / Exit
13. Open Items / Data Requests

如果我提供的是程式碼，請先判斷：
- 這段程式屬於資料層、計算層、研究層、UI 層、或 AI prompt 層？
- 是否有資料洩漏、日期錯置、單位錯置、幣別錯置、look-ahead bias、過度擬合、來源不明、AI 幻覺風險？
- 如何改成更符合 Public Equity Investing 流程？

如果我提供的是 Ref-data、PDF、CSV、JSON、TXT，請先整理：
- 資料主題
- 可用欄位
- 投資用途
- 缺失
- 如何接入 Fiance
- 對投資決策的實際幫助

請用繁體中文回答，必要時保留英文投資術語。
```

---

## 10. 給未來開發者的實作原則

### 10.1 模組邊界

請將系統拆成：

```text
fiance/
  data_sources/
    finmind_client.py
    fmp_client.py
    news_client.py
    file_loaders.py
  storage/
    schema.py
    cache.py
    database.py
  analytics/
    technicals.py
    financial_ratios.py
    etf_analysis.py
    risk.py
  models/
    ml_signals.py
    backtest.py
    dcf.py
    scenario.py
  research/
    source_packet.py
    thesis_tracker.py
    memo_builder.py
    catalyst_calendar.py
    risk_register.py
    prompt_templates.py
  ui/
    app.py
    tabs/
  tests/
```

### 10.2 LLM 與 deterministic code 分工

由 Python 計算：

- 價格
- 報酬
- 指標
- 財務比率
- DCF
- 回測
- portfolio risk
- ETF overlap
- insider statistics

由 LLM 協助：

- 摘要
- 結構化
- 檢查矛盾
- 產生投資備忘錄
- 生成待補資料清單
- 產生 disconfirmers
- 形成初步 PM judgment

禁止：

- 讓 LLM 憑空算大量表格。
- 讓 LLM 自行假設未提供的最新財務數字。
- 讓 LLM 把未驗證新聞當作事實。

### 10.3 每個分析物件都應有 metadata

```json
{
  "ticker": "",
  "company_name": "",
  "exchange": "",
  "country": "",
  "currency": "",
  "source": "",
  "as_of_date": "",
  "retrieved_at": "",
  "fiscal_period": "",
  "unit": "",
  "data_quality": "raw | cleaned | model_output | assumption | llm_inference | pm_judgment"
}
```

---

## 11. 最終判斷

Fiance 和 Public Equity Investing 不是替代關係，而是互補關係。

- 沒有 Fiance，Public Equity Investing 會缺少穩定資料、計算、回測、監控與 GUI。
- 沒有 Public Equity Investing，Fiance 容易停留在「指標很多、圖很多、AI 摘要很多」，但無法形成專業投資決策。

最佳合併方向：

> 把 Fiance 做成資料與工作流引擎，把 Public Equity Investing 做成研究與決策引擎，讓 AI 只在有資料邊界與 PM 紀律的情況下輸出投資判斷。

若未來只能做一件事，優先做：

> 把目前 AI 分析 prompt 改成 Public Equity Investing memo spine，並要求所有輸出標示 source posture、缺資料、valuation scenarios、disconfirmers、action rules。

這會讓現有 Fiance 立即從「股票分析工具」提升為「投資研究工作台」。

