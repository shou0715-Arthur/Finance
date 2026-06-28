# Fiance 程式與 Ref-data 投資研究盤點

盤點日期：2026-06-22（Asia/Taipei）

## 一、結論先行

這個專案目前是「可運作的台股桌面分析工具」加上「尚未整合的投資研究教材／原型庫」。主程式已把台股歷史價量、MA／RSI、簡易機器學習、EPS／股利、Google News RSS 與 Gemini 摘要串成一條可使用的流程；`Ref-data` 則涵蓋財報、價值篩選、DCF、量化策略、ETF、投資組合、行為偏誤、新聞情緒、交易日誌、壓力測試、事件提醒與內部人交易。

若以專業股票投資經理人的標準衡量，現有資產很適合做「投資教育與研究工具原型」，但還不是能直接支援建倉、加碼、減碼與退出決策的 decision-grade 平台。最大缺口不是再多一個技術指標，而是：一致且有時間戳的資料層、公司／股票論點、預期差、估值與情境報酬、投資組合風險、可驗證的催化劑與反證條件，以及完整的研究稽核軌跡。

## 二、我對主程式的理解

### 2.1 架構與執行方式

- `AI-stock.py` 是極薄的啟動入口，只呼叫 `ai_stock_gui.main()`。
- `ai_stock_gui.py` 是單體式 Tkinter 桌面應用，資料取得、資料清理、指標計算、ML、AI prompt、畫圖與 UI 全在同一檔案。
- 若以 PyInstaller 執行，程式把執行檔所在目錄視為專案根目錄；Python 模式則使用原始碼所在目錄。
- `watchlist.json` 保存自選股；`api-key.txt` 保存 FinMind 與 Gemini 憑證；`.gitignore` 已排除 key 檔。

### 2.2 實際資料流

1. 使用者輸入台股／ETF 代碼、名稱、日期與 RSI 週期。
2. 背景執行緒向 FinMind `TaiwanStockPrice` 取得 OHLCV。
3. 清理日期與數值，依日期排序、去除重複，再計算 MA5／10／20／60 與 RSI。
4. 以 11 個歷史價量／技術特徵訓練 Logistic Regression 和 Random Forest，使用前 70% 訓練、後 30% 測試，選測試準確率較高者預測次日方向。
5. 再向 FinMind 讀取 `TaiwanStockFinancialStatements` 的 EPS 與 `TaiwanStockDividend` 的股利資料。
6. 以股票代碼、名稱、「台股」「股票」查 Google News RSS，最多抓 12 則標題。
7. 將最近 120 筆價量、技術指標、EPS／股利、ML 結果及最多 8 則新聞標題送給 `gemini-2.5-flash`，要求輸出台股技術面、基本面、新聞、Public Equity Investing、Investment Banking、ML 與追蹤清單。
8. Tkinter 顯示總覽、手繪 K 線／均線／成交量／RSI、歷史表、AI 報告、ML、基本股利與新聞。

### 2.3 做得好的地方

- 網路請求有 timeout、HTTP／JSON／欄位檢查與繁中錯誤訊息。
- UI 長任務放在背景執行緒，並透過 `root.after()` 回主執行緒更新畫面。
- AI、新聞或基本面部分失敗時，部分功能仍可降級運作。
- ML 明確揭露只使用歷史價量，不把結果包裝成確定預測。
- 代碼、日期、watchlist 與 API key 均有基本正規化／遮罩處理。
- Python AST 靜態解析顯示主程式與 `Ref-data` 內 10 個 Python 範例皆可通過語法解析。

### 2.4 主程式的重要限制

- **研究深度不足**：EPS 只取最新一筆 `EPS`，沒有區分單季、累計、年度、TTM、會計期間與重編；股利也沒有殖利率、配發率、FCF 覆蓋率與歷史穩定性。
- **RSI 定義**：目前使用簡單移動平均的漲跌均值，不是市場常見的 Wilder smoothing；結果可能和券商／TradingView 不一致。
- **ML 驗證偏樂觀**：只做一次 70/30 時序切分，並用同一測試集挑選模型；缺少 walk-forward、基準命中率、機率校準、交易成本、訊號門檻與穩健性檢驗。
- **目標過短**：只預測次日漲跌，未連結投資期間、預期報酬、下檔、勝率／賠率或部位大小，對股票經理人的決策價值有限。
- **新聞證據薄弱**：AI 只看標題，沒有正文、去重、事件實體解析、來源品質分級、引用與明確 as-of 時間。
- **AI prompt 過度混合**：技術分析、股票研究、Investment Banking 與 ML 被塞進單一 prompt，容易產生表面完整、證據不足的敘述。
- **價格視覺化效能**：Tkinter Canvas 對每筆資料逐根畫 K 線，長區間可能變慢，也缺乏 hover、縮放與 tooltip。
- **安全性**：憑證以純文字寫入本機檔案；雖已 gitignore，仍建議改用 Windows Credential Manager／keyring 或環境變數。
- **可維護性**：1,435 行單檔同時負責 API、domain logic、模型與 UI；缺少測試、快取、結構化 logging、資料契約與依賴注入。
- **資產未整合**：主程式僅支援 FinMind 台股；`Ref-data` 中的 FMP、美股、ETF、DCF、組合風險、情緒、事件與內部人資料仍是孤立範例。

## 三、Ref-data 全部資料的投資研究地圖

| 模組 | 內容與可用資產 | PM 評價與主要缺口 |
|---|---|---|
| 3-1 財報閱讀 | 財報三表教學；台積電 2025Q1 合併財報 63 頁 | 適合建立會計基礎；缺少 segment/KPI、會計政策變化、一次性項目、盈餘品質與 management credibility 檢核 |
| 3-2 價值／品質篩選 | Piotroski F-score、Altman Z-score、DuPont、現金流；NVDA 2025 年 FMP 原始財報、EV、profile；四階段 prompt | 可做初篩，不足以直接投資；Altman 模型需依產業版本調整，F-score 對高成長／金融股適用性有限；資料已過期且缺 consensus |
| 3-3 財務分析 Agent | FinMind 與 FMP 兩套 Streamlit 原型；資料品質、F-score、Z-score、DuPont、現金流與 OpenAI 分析 | 是 Ref-data 中最完整的公司基本面分析原型；但資料映射與補償邏輯需 point-in-time tie-out，且缺少預估修正、segment driver、估值與反證 |
| 3-4 n8n 自動化 | 12 節點 workflow，統一 FMP／FinMind 價格資料並呼叫 AI | 適合資料管線 PoC；缺 retry、idempotency、schema version、告警、憑證管理、來源 lineage 與人工覆核 |
| 4-1 估值概論 | DCF、DDM、NAV、P/E、PEG、P/B 等 | 教學正確但非常概括；缺產業適用性、歷史／同業區間、估值驅動因素與回報門檻 |
| 4-2／4-3 DCF | FMP custom DCF Streamlit 原型、WACC 分解、敏感度、情境與教育規格 | 可展示 DCF 概念；不宜把供應商黑盒 DCF 當投資結論。應自建 revenue-to-FCF 模型、股數／淨負債橋、終值、PV／IRR 與可稽核公式 |
| 5-1 量化概論 | 基本面、技術面、籌碼、情緒四類資料與策略分類 | 適合作為研究目錄；缺研究假說、資料可得時點、樣本設計與統計顯著性 |
| 5-2 綜合策略 | 超跌反彈等十類技術策略；2330 51 筆價格樣本；結構化 prompt | 規則可讀但多數仍為自然語言；W 底等型態未形式化，容易產生主觀判讀與 hindsight bias |
| 5-3 回測範例 | 大型歷史資料與交易／績效輸出要求 | 有回測報告框架；仍需查核交易成本、滑價、股利、公司行動、停牌、漲跌停、倖存者偏誤、前視偏誤、參數挖掘與 out-of-sample |
| 5-4 自動策略 Agent | 17 節點 n8n workflow，拆成 trend／chart pattern／technical indicator 工具；v1/v2 差異主要為 workflow 身分資訊 | 多 Agent 分工比單 prompt 清楚；但 LLM 不應負責精確指標計算，應由 deterministic engine 計算後讓 LLM 解釋 |
| 6-1 ETF | ETF／GICS 教學、ARKK 2025-09-16 持股、VWO 4,848 筆、IEMG 2,727 筆、PTP 證券清單、VWO/IEMG 比較 prompt | 資料很適合 ETF look-through。IEMG／VWO 共同 ISIN 1,328 檔，約占各自 54.6%／55.6%；但持股已逾 9 個月，且缺國家／產業映射、費用、追蹤差、流動性、稅務與指數規則版本 |
| 6-2 分散與風險屬性 | GICS 分散、個人風險問卷與 FMP 免費股清單 | 個人風險容忍度不等於投資組合風險；專業組合應改用 active weight、factor beta、tracking error、drawdown、liquidity、crowding 與情境損失 |
| 6-3 組合風險 | FMP 價格／公司資料、波動與綜合風險分數、Perplexity 輔助 | 有資產層風險雛形；缺持倉權重、相關矩陣、邊際／成分風險、VaR/CVaR、benchmark、FX、流動性與集中度，綜合分數的權重也需校準 |
| 7-1 行為偏誤 | 蒙格人類誤判心理學 | 對建立投資流程很有價值；應轉成 pre-mortem、反方論點、交易前 checklist 與 post-mortem，而非停在閱讀材料 |
| 7-2 市場情緒 | VIX、CNN Fear & Greed、AAII、FMP 社群情緒 | 可作背景 regime 指標；不能直接映射單一股票報酬，需做增量解釋力與極端區間測試 |
| 7-3 新聞情緒 | Alpha Vantage 價格／新聞、topic/ticker relevance、OpenAI 市場情緒與投資建議 | 已有 relevance weighting；缺正文證據、來源信譽、事件去重、時間衰減、預期差與價格反應分離 |
| 8-1／8-2 投資日誌 | FIFO 績效、價格／公司／財務／新聞背景、AI 決策品質評估與規格 | 是建立投資流程紀律的好底座；缺 lot-level fees/tax/FX、benchmark、MAE/MFE、thesis version、事前信心、決策時間戳與原因碼 |
| 9-1 壓力測試 | 五檔示例組合、歷史／黑天鵝情境、波動與 sector/beta 傳導、AI 報告 | 情境化方向正確；目前 impact 公式偏啟發式，未重估營收／毛利／EPS／multiple，也未處理相關性在壓力期上升與二階效應 |
| 9-2 策略轉換 | Pine Script 到 Python；EMA + Supertrend；FMP Client 與 Streamlit | 具 deterministic 策略骨架；需逐 bar 對照 TradingView、統一 adjusted price、warm-up、訊號成交時點、費用與 walk-forward |
| 9-3 事件提醒 | 財報日、經濟日曆、產業／國家映射、相關度與優先級、AI 提醒 | 很接近 PM 工作流；但關鍵字映射仍粗糙，缺公司自有 IR／法說／產品／監管事件、時區與異動偵測、owner／status／decision gate |
| 9-4 內部人交易 | FMP symbol／CIK 查詢、交易代碼映射、表格／統計／CSV | 可作治理與訊號輔助；需區分 10b5-1、贈與、選擇權執行、稅務賣出、持股比例與 cluster buying，並和 SEC Form 4 原始文件 tie-out |

## 四、資料品質與時效判斷

- NVDA 的財報／企業價值／profile 樣本主要落在 2025 年 1 月附近；不能當作 2026-06-22 的現況。
- ARKK 持股日期為 2025-09-16；IEMG 為 2025-09-16；VWO 為 2025-09-17。ETF 持股會變動，使用前必須刷新。
- IEMG 權重加總約 100.023%，VWO 約 100.011%，屬四捨五入可接受；VWO 前列包含流動性／現金類代碼，做股票曝險時應另行分類。
- `3-2.pdf` 與「更新版」內容高度接近；`5-4.json` 與 `5-4(v2).json` 節點結構相同，主要不是投資邏輯升級，應建立正式 changelog。
- 多份 PDF 的文字層含異常 Unicode 相容字／部首字，畫面閱讀正常，但機器抽取與搜尋可能失真；若要做 RAG，需先正規化。
- PTP 清單本身明示非完整且可隨時變動，只能作初步合規提示，不能作交易前唯一判斷來源。
- 多個規格與程式綁定 FMP／Alpha Vantage／OpenAI 舊版或不同代 API；正式整合前需逐一確認供應商方案、端點、欄位與授權。

## 五、以專業股票經理人角度應補上的內容

### 5.1 單一股票研究最小完備集

每個標的至少需要以下可稽核物件：

1. `Security master`：ticker、交易所、ISIN、幣別、時區、產業、指數／ETF 身分。
2. `Source packet`：最新年報／季報、法說稿、逐字稿、IR deck、重大訊息、proxy／治理資料。
3. `Operating model`：營收量價、產品／地區／客戶組合、毛利、費用、稅率、營運資本、capex、FCF、股數與淨負債。
4. `Expectations`：市場共識、公司指引、內部預估及其差異，全部帶 as-of date。
5. `Thesis tracker`：2-5 個可被證偽的論點，每項有證據、KPI、反證與 time-to-truth。
6. `Valuation`：主要方法加 1-2 個交叉驗證；base／upside／downside、機率、現值或年化 IRR、目標回報門檻。
7. `Catalyst calendar`：硬日期、證據窗口、軟催化劑，並定義結果後的 add／hold／trim／exit 規則。
8. `Risk register`：衝擊 → 傳導 → 限制 → 結果，包含會計、治理、資產負債表、競爭、政策、流動性與擁擠度。

### 5.2 組合層最小完備集

- 持倉數量、成本、現價、權重、active weight、benchmark 與投資期間。
- sector／country／currency／style factor／beta 曝險與 factor-adjusted alpha。
- 波動、最大回撤、tracking error、VaR／CVaR、邊際風險貢獻與壓力情境損失。
- ADV、days-to-liquidate、容量、漲跌停／停牌、short interest／borrow（如適用）。
- 單名、產業、主題、因子與事件集中度；壓力情境下相關性上升。
- 部位規則：starter／full size、加碼、減碼、退出、避險與再承作觸發條件。

### 5.3 量化與 AI 治理

- 所有市場／財報資料必須保存 `source`、`as_of`、`retrieved_at`、`currency`、`unit`、`fiscal_period`、`revision_id`。
- 指標計算與估值由 deterministic code 完成；LLM 負責解釋、反方檢查與摘要，不負責憑空算數。
- 回測使用 point-in-time universe、adjusted prices、公司行動、交易成本、滑價、可成交性與 walk-forward；另留 untouched holdout。
- 比較策略與 ML 時，至少報告基準命中率、AUC／Brier、機率校準、turnover、含成本報酬、最大回撤與不同 regime 表現。
- AI 產出每一項重要事實要能回到原始文件或資料列；明確分開 fact、management claim、consensus、model output、assumption、PM judgment。

## 六、建議的整合優先順序

### P0：先把資料可信度做好

- 把 `ai_stock_gui.py` 拆成 `data_sources/`、`analytics/`、`models/`、`research/`、`ui/`。
- 建立 canonical schema 與 SQLite／DuckDB 儲存層，所有資料帶來源與時間戳。
- 將 API key 改用 keyring／環境變數；加 structured logging、cache、retry/backoff。
- 為 FinMind 清理、RSI、EPS／股利期間、ML feature 與 watchlist 建單元測試。

### P1：把主程式升級成「研究工作台」

- 整合 3-3 的財務品質分析，但保留原始欄位與 tie-out。
- 新增三表／segment/KPI、歷史與 forward estimates、valuation scenario、thesis／catalyst／risk tabs。
- 新聞改為事件化：去重、來源評級、全文摘要、ticker relevance、事件日期與引用。
- AI 報告改成固定 PM spine：decision hinge、what is priced in、what must be true、downside、catalysts、disconfirmers、missing evidence。

### P2：加入組合與決策紀律

- 整合 8-1 日誌、9-3 事件提醒與 9-4 內部人資料。
- 將 6-3／9-1 改為以真實持倉權重、benchmark、factor 與 liquidity 為核心的組合風險模組。
- 每次研究輸出都保存版本、當時價格、資料 freeze time、決策與後續 outcome，形成可回測的研究流程。

### P3：最後才擴大量化策略

- 將 5-2、5-3、9-2 的規則形式化並做 point-in-time、walk-forward 與成本後驗證。
- 只有在訊號展現跨期間／跨標的穩健性後，才進入 paper portfolio；不要直接把 LLM 的技術型態判讀當交易訊號。

## 七、最終判斷

現有專案的強項是範圍廣、教學脈絡完整、原型很多，且主程式已經可用。弱項是每個模組各自成島，研究證據、估值、預期差、組合風險與決策紀律尚未形成同一條鏈。

最值得做的下一步不是把 20 個原型全部塞進 GUI，而是先建立一個共用資料與研究物件層，然後選一條最有價值的垂直流程做深：`台股公司資料 → 財報／KPI → 共識與估值 → 論點／催化劑／風險 → 組合與日誌`。做到這一步，這套系統才會從「AI 股票分析展示工具」跨到「可供投資經理人反覆使用、可稽核、可迭代的研究作業系統」。
