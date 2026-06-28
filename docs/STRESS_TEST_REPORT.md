# 完整壓力測試報告

測試日期：2026-06-24  
測試範圍：Fiance Python 架構、Ref-data workflow modules、unit tests、入口匯入、PowerShell 腳本解析、合成資料壓測  
測試方式：不啟動 GUI、不呼叫外部 API、不安裝套件

## 1. 結論

本次完整壓力測試通過。

```text
PY_COMPILE_OK 88 files
Ran 72 tests
OK
PS_PARSE_OK 5 files
ENTRY_PATH_OK True
```

合成資料壓測也全部通過：

```text
financial_workflow_1000_runs        OK
dcf_5000_models                     OK
etf_overlap_5000x5000               OK
strategy_backtest_10000_prices      OK
portfolio_risk_1000_positions       OK
event_pipeline_2000_news            OK
governance_5000_transactions        OK
all_workflows_smoke_loop_100        OK
entry_import_smoke                  OK
```

## 2. 基礎測試

### 2.1 Python 編譯

目的：確認所有 Python 檔案語法正確。

結果：

```text
PY_COMPILE_OK 88 files
```

### 2.2 Unit tests

目的：確認每批 Ref-data Python 化後的 module / workflow / prompt context 沒有回歸錯誤。

結果：

```text
Ran 72 tests in 0.074s
OK
```

### 2.3 PowerShell 腳本解析

目的：確認整理到 `scripts/` 後的 `.ps1` 可被 PowerShell 正確解析。

結果：

```text
PS_PARSE_OK 5 files
```

### 2.4 入口匯入

目的：確認根目錄 `AI-stock.py` 仍可連到 `app.ai_stock_gui.main`。

結果：

```text
ENTRY_PATH_OK
True
```

## 3. 合成資料壓力測試

| 測試項目 | 規模 | 結果 | 耗時 |
|---|---:|---|---:|
| financial workflow | 1,000 runs | Pass | 0.0140s |
| DCF model | 5,000 models | Pass | 0.0136s |
| ETF overlap | 5,000 × 5,000 holdings | Pass | 0.0076s |
| strategy backtest | 10,000 prices | Pass | 0.0075s |
| portfolio risk | 1,000 positions / 5,000 returns | Pass | 0.0029s |
| event pipeline | 2,000 news rows | Pass | 0.0083s |
| governance / insider | 5,000 transactions | Pass | 0.0071s |
| all workflows smoke loop | 100 loops | Pass | 0.0125s |
| entry import smoke | 1 import | Pass | 0.7880s |

## 4. 重要觀察

### 4.1 Workflow engine 壓測正常

`financial_analysis_workflow`、`valuation_workflow`、`event_monitoring_workflow`、`journal_workflow`、`strategy_analysis_workflow`、`portfolio_risk_workflow`、`governance_workflow` 在 100 輪混合 smoke loop 中全部成功。

### 4.2 ETF overlap 大資料正常

5,000 筆對 5,000 筆 holdings overlap 測試成功，正確回傳 2,500 筆共同持股。

### 4.3 Strategy backtest 結果不可當投資結論

壓測中 `strategy_backtest_10000_prices` 使用單調上升的合成價格資料，因此累積報酬數字極端偏高。  
這個測試只用來確認演算法可以承受較大資料量，不代表策略有效。

### 4.4 Portfolio risk 壓測正常

1,000 檔持倉與 5,000 筆報酬序列可正常計算：

```text
concentration = 0.0013030605994182325
volatility    = 0.0199005356022069
VaR           = -0.03222074575692234
CVaR          = -0.04049312656422358
```

### 4.5 Event / governance 大量資料正常

- 2,000 筆新聞事件可正常轉 catalyst calendar。
- 5,000 筆 insider transaction 可正常 normalize。

## 5. 本次沒有測的項目

以下項目本次刻意不測，避免外部狀態干擾：

- GUI 實際開窗與人工操作。
- FinMind live API。
- FMP live API。
- Gemini live API。
- Google News live fetch。
- SEC / insider live source。
- PyInstaller 打包。
- 真實 ETF holdings 大檔案解析完整性。

## 6. 風險與下一步

目前壓測證明：

```text
程式架構、workflow、deterministic analytics、測試基礎是穩的。
```

但距離 production-grade 還需要：

- 將 workflow output 接進 GUI。
- 做 live API integration tests。
- 對真實 `Ref-data/6-1/IEMG.txt`、`VWO.txt` 做 parser 驗證。
- 對 Gemini prompt output 做格式驗證。
- 增加 GUI smoke / headless UI 測試。

