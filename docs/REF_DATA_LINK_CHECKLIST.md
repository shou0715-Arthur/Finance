# Ref-data Python 連結完成 Checklist

產出日期：2026-06-24

## 總結

本次已將先前標示為「未轉」的 Ref-data 分批轉成 Python 模組、workflow 與 unittest。  
目前完成的是「可測、可擴充、可被 GUI/AI prompt 逐步接入」的分析地基。

重要限制：

- 已建立 deterministic Python 分析方法與 workflow。
- 已建立 unittest。
- 尚未把所有 workflow 都接到 GUI 按鈕或分頁。
- 尚未對 live FinMind / FMP / Gemini / Google News / SEC API 做整合測試。
- 因此投資輸出仍應標示為 screen-grade，除非後續補齊 live source packet 與完整資料。

---

## Batch 1：財務資料地基

對應 Ref-data：

- `3-1 財報閱讀`
- `3-3 財務分析 Agent`

| 項目 | 狀態 | 檔案 |
|---|---|---|
| FinMind record normalizer | 完成 | `data_sources/finmind_client.py` |
| FMP statement normalizer | 完成 | `data_sources/fmp_client.py` |
| JSON / CSV 財報 parser | 完成 | `analytics/financial_statement_parser.py` |
| 財務資料正規化 | 完成 | `analytics/financial_normalizer.py` |
| Source packet | 完成 | `research/source_packet.py` |
| Financial workflow | 完成 | `workflow/financial_analysis_workflow.py` |
| Unit tests | 完成 | `tests/test_batch1_financial_foundation.py` |

完成標準：

- [x] Python module
- [x] dataclass result
- [x] deterministic calculation / parser
- [x] workflow
- [x] unittest

---

## Batch 2：估值與情境分析

對應 Ref-data：

- `4-1 估值方法`
- `4-2 / 4-3 DCF`

| 項目 | 狀態 | 檔案 |
|---|---|---|
| 估值方法選擇 | 完成 | `analytics/valuation_methods.py` |
| WACC / DCF | 完成 | `analytics/dcf.py` |
| Downside / Base / Upside scenario | 完成 | `analytics/scenario.py` |
| Valuation prompt context | 完成 | `research/valuation_prompt.py` |
| Valuation workflow | 完成 | `workflow/valuation_workflow.py` |
| Unit tests | 完成 | `tests/test_batch2_valuation.py` |

完成標準：

- [x] Python module
- [x] dataclass result
- [x] deterministic valuation
- [x] workflow
- [x] unittest

---

## Batch 3：ETF 完整化

對應 Ref-data：

- `6-1 ETF 差異分析`

| 項目 | 狀態 | 檔案 |
|---|---|---|
| ETF / stock / unknown classifier | 完成 | `research/security_classifier.py` |
| ETF holdings overlap | 完成 | `analytics/etf_overlap.py` |
| ETF holdings file loader | 完成 | `data_sources/etf_files.py` |
| ETF exposure / PTP detection | 完成 | `analytics/etf_exposure.py` |
| ETF prompt context | 完成 | `research/etf_prompt.py` |
| ETF workflow | 完成 | `workflow/etf_analysis_workflow.py` |
| Unit tests | 完成 | `tests/test_batch3_etf_complete.py` |

完成標準：

- [x] Python module
- [x] dataclass result
- [x] deterministic ETF analysis
- [x] workflow
- [x] unittest

---

## Batch 4：新聞、情緒、事件

對應 Ref-data：

- `7-2 市場情緒指標`
- `7-3 新聞情緒分析`
- `9-3 事件提醒`

| 項目 | 狀態 | 檔案 |
|---|---|---|
| News record normalizer | 完成 | `data_sources/news_client.py` |
| Market sentiment snapshot | 完成 | `data_sources/market_sentiment_client.py` |
| Sentiment / relevance scoring | 完成 | `analytics/sentiment.py` |
| Market regime summary | 完成 | `analytics/market_regime.py` |
| Event extractor | 完成 | `research/event_extractor.py` |
| Catalyst calendar | 完成 | `research/catalyst_calendar.py` |
| Event store | 完成 | `storage/event_store.py` |
| Event workflow | 完成 | `workflow/event_monitoring_workflow.py` |
| Unit tests | 完成 | `tests/test_batch4_events.py` |

完成標準：

- [x] Python module
- [x] dataclass result
- [x] deterministic event extraction
- [x] workflow
- [x] unittest

---

## Batch 5：投資日誌與行為偏誤

對應 Ref-data：

- `7-1 行為偏誤`
- `8-1 / 8-2 投資日誌`

| 項目 | 狀態 | 檔案 |
|---|---|---|
| Behavioral checklist | 完成 | `research/behavioral_checklist.py` |
| Decision journal | 完成 | `research/decision_journal.py` |
| Thesis tracker | 完成 | `research/thesis_tracker.py` |
| Journal store | 完成 | `storage/journal_store.py` |
| Journal workflow | 完成 | `workflow/journal_workflow.py` |
| Unit tests | 完成 | `tests/test_batch5_journal.py` |

完成標準：

- [x] Python module
- [x] dataclass result
- [x] deterministic decision discipline
- [x] workflow
- [x] unittest

---

## Batch 6：量化策略與回測

對應 Ref-data：

- `5-1 量化投資概論`
- `5-2 策略提示語`
- `5-3 策略回測`
- `5-4 AI Agent 技術策略`
- `9-2 TradingView EMA / Supertrend`

| 項目 | 狀態 | 檔案 |
|---|---|---|
| Backtest controls | 完成 | `analytics/backtest_controls.py` |
| EMA / Supertrend direction / signal | 完成 | `analytics/technical_strategy.py` |
| Backtest metrics | 完成 | `analytics/backtest.py` |
| Strategy prompt context | 完成 | `research/strategy_prompt.py` |
| Strategy agent guardrails | 完成 | `research/strategy_agent_prompt.py` |
| Strategy workflow | 完成 | `workflow/strategy_analysis_workflow.py` |
| Unit tests | 完成 | `tests/test_batch6_strategy.py` |

完成標準：

- [x] Python module
- [x] dataclass result
- [x] deterministic signal / backtest
- [x] workflow
- [x] unittest

---

## Batch 7：投資組合風險與壓力測試

對應 Ref-data：

- `6-2 分散投資`
- `6-3 投資組合風險`
- `9-1 壓力測試`

| 項目 | 狀態 | 檔案 |
|---|---|---|
| Diversification / weights / concentration | 完成 | `analytics/diversification.py` |
| Portfolio volatility / beta / VaR / CVaR | 完成 | `analytics/portfolio_risk.py` |
| Macro / sector / rate / FX shock | 完成 | `analytics/stress_test.py` |
| Risk prompt context | 完成 | `research/risk_prompt.py` |
| Portfolio risk workflow | 完成 | `workflow/portfolio_risk_workflow.py` |
| Unit tests | 完成 | `tests/test_batch7_portfolio_risk.py` |

完成標準：

- [x] Python module
- [x] dataclass result
- [x] deterministic risk calculation
- [x] workflow
- [x] unittest

---

## Batch 8：內部人交易與治理風險

對應 Ref-data：

- `9-4 內部人交易`

| 項目 | 狀態 | 檔案 |
|---|---|---|
| Insider transaction normalizer | 完成 | `data_sources/insider_client.py` |
| Transaction classification | 完成 | `analytics/insider_analysis.py` |
| Cluster buying / unusual selling | 完成 | `analytics/insider_analysis.py` |
| Governance prompt context | 完成 | `research/governance_prompt.py` |
| Governance workflow | 完成 | `workflow/governance_workflow.py` |
| Unit tests | 完成 | `tests/test_batch8_governance.py` |

完成標準：

- [x] Python module
- [x] dataclass result
- [x] deterministic insider analysis
- [x] workflow
- [x] unittest

---

## 最終測試結果

最後一次完整測試結果：

```text
PY_COMPILE_OK 88 files
Ran 72 tests
OK
```

入口 smoke test：

```text
ENTRY_PATH_OK
True
```

---

## 尚未完成的產品化接線

雖然 Ref-data 方法已 Python 化並測試通過，但仍有幾個產品化接線尚未做：

- [ ] 將各 workflow 全部接入 GUI 分頁。
- [ ] 建立 unified research orchestrator，依 security type 自動選 workflow。
- [ ] 將 live API 回傳資料接入這些 deterministic modules。
- [ ] 建立 source packet database / cache。
- [ ] 把 workflow output 完整注入 Gemini/Public Equity memo prompt。
- [ ] 對真實 FinMind/FMP/Google/SEC API 做 integration test。
- [ ] 建立使用者可視化的 Batch 狀態面板。

---

## 使用者確認 Checklist

請確認你是否同意下一步進入「產品化接線」：

- [ ] GUI 要新增 ETF 分析分頁。
- [ ] GUI 要新增 Valuation / DCF 分頁。
- [ ] GUI 要新增 Portfolio Risk 分頁。
- [ ] GUI 要新增 Journal / Thesis Tracker 分頁。
- [ ] AI memo 要自動讀取 workflow outputs，而不是只讀價格與新聞。
- [ ] 每次分析都要保存 source packet 與 workflow log。

