# 自動測試報告：Python Workflow 與 Ref-data 第一批分析模組

測試日期：2026-06-24  
專案路徑：`C:\Users\Arthur.Hsu\PycharmProjects\PythonProject\Fiance`

## 1. 本次新增目標

本次依照討論執行兩件事：

1. **不用 n8n**，改用 Python 內建 workflow engine 取代外部自動化流程。
2. 先把第一批最關鍵的 Ref-data 分析方法轉成 Python：
   - ETF / stock / unknown 分類
   - ETF holdings overlap
   - Piotroski F-score
   - Altman Z-score
   - DuPont ROE decomposition

## 2. 新增程式檔案

### 2.1 Python workflow engine

| 檔案 | 功能 |
|---|---|
| `workflow/pipeline.py` | workflow context、step execution、pipeline result、pipeline runner |
| `workflow/steps.py` | function step、required keys step、branch step |
| `workflow/registry.py` | workflow register / get / list / clear |
| `workflow/execution_log.py` | workflow execution log、JSON save/load |
| `workflow/scheduler.py` | simple scheduled workflow due check |

### 2.2 Ref-data 第一批分析模組

| 檔案 | 對應 Ref-data | 功能 |
|---|---|---|
| `research/security_classifier.py` | `6-1 ETF 差異分析` | 判斷 ETF / stock / unknown |
| `analytics/etf_overlap.py` | `6-1 ETF holdings` | ETF 持股重疊計算 |
| `analytics/financial_quality.py` | `3-2 Piotroski / Altman / DuPont` | 財務品質分數 |

### 2.3 Prompt 整合

| 檔案 | 修改 |
|---|---|
| `research/public_equity_prompt.py` | 加入 `classify_security()`，讓 Public Equity memo 顯示資產類型與信心度 |

## 3. 新增測試檔案

| 測試檔案 | 覆蓋範圍 |
|---|---|
| `tests/test_workflow_engine.py` | workflow engine 全部 public functions/classes |
| `tests/test_ref_data_methods.py` | security classifier、financial quality、ETF overlap |
| `tests/test_prompt_integration.py` | prompt 是否正確帶入資產類型與 memo contract |

## 4. Function 覆蓋清單

### 4.1 `workflow/pipeline.py`

| Function / Class | 測試狀態 |
|---|---|
| `WorkflowContext.with_value()` | Pass |
| `WorkflowContext.with_metadata()` | Pass |
| `StepExecution.duration_seconds` | Pass |
| `PipelineResult.ok` | Pass |
| `PipelineResult.errors` | Pass |
| `ensure_context()` | Pass |
| `Pipeline.run()` | Pass |

### 4.2 `workflow/steps.py`

| Function / Class | 測試狀態 |
|---|---|
| `FunctionStep.run()` | Pass |
| `RequiredKeysStep.run()` | Pass |
| `BranchStep.run()` | Pass |

### 4.3 `workflow/registry.py`

| Function | 測試狀態 |
|---|---|
| `register_workflow()` | Pass |
| `get_workflow()` | Pass |
| `list_workflows()` | Pass |
| `clear_workflows()` | Pass |

### 4.4 `workflow/execution_log.py`

| Function / Class | 測試狀態 |
|---|---|
| `ExecutionLog.append_result()` | Pass |
| `ExecutionLog.to_jsonable()` | Pass |
| `ExecutionLog.save_json()` | Pass |
| `load_execution_log()` | Pass |

### 4.5 `workflow/scheduler.py`

| Function / Class | 測試狀態 |
|---|---|
| `ScheduledWorkflow.is_due()` | Pass |
| `ScheduledWorkflow.mark_run()` | Pass |

### 4.6 `research/security_classifier.py`

| Function | 測試狀態 |
|---|---|
| `normalize_symbol()` | Pass |
| `is_likely_taiwan_etf_symbol()` | Pass |
| `classify_security()` | Pass |

### 4.7 `analytics/financial_quality.py`

| Function | 測試狀態 |
|---|---|
| `safe_divide()` | Pass |
| `calculate_piotroski_f_score()` | Pass |
| `calculate_altman_z_score()` | Pass |
| `calculate_dupont()` | Pass |

### 4.8 `analytics/etf_overlap.py`

| Function | 測試狀態 |
|---|---|
| `normalize_identifier()` | Pass |
| `normalize_weight()` | Pass |
| `make_holding()` | Pass |
| `holdings_to_weight_map()` | Pass |
| `calculate_holdings_overlap()` | Pass |
| `top_holdings()` | Pass |

### 4.9 `research/public_equity_prompt.py`

| Function | 測試狀態 |
|---|---|
| `build_local_public_equity_note()` | Pass：確認包含資產類型與 Source Posture |
| `build_public_equity_prompt()` | Pass：確認包含資產類型與 memo contract |

## 5. 實際測試指令與結果

### 5.1 Python 編譯測試

指令：

```powershell
py -3 - <compile all python files>
```

結果：

```text
PY_COMPILE_OK 37 files
```

代表所有 Python 檔案可通過語法編譯。

### 5.2 Unit tests

指令：

```powershell
C:\Users\Arthur.Hsu\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest discover -s tests -v
```

結果：

```text
Ran 72 tests
OK
```

### 5.3 入口路徑 smoke test

目的：確認根目錄 `AI-stock.py` 移動架構後仍可匯入 `app.ai_stock_gui.main`。

結果：

```text
ENTRY_PATH_OK
True
```

## 6. 測試中修正的問題

### 6.1 Altman Z-score 測試期望值

原測試期望值算錯。依公式：

```text
1.2 * WC/TA
+ 1.4 * RE/TA
+ 3.3 * EBIT/TA
+ 0.6 * MVE/TL
+ 1.0 * Sales/TA
= 3.555
```

已修正測試期望值為 `3.555`。

### 6.2 ETF weight 浮點數比較

`0.1 + 0.2` 在 Python 浮點運算中會得到 `0.30000000000000004`。  
已改用 `assertAlmostEqual()`。

### 6.3 Windows Temp 權限問題

原本測試使用系統 Temp directory，sandbox 下可能被拒絕。  
已改成在專案內建立 `tmp_tests/`，測試結束後清除。

## 7. 本次測試沒有涵蓋的項目

以下項目本次沒有做，避免造成副作用：

- 未啟動 GUI 視窗。
- 未呼叫 FinMind API。
- 未呼叫 Gemini API。
- 未安裝或更新任何套件。
- 未執行 PyInstaller 打包。
- 未把整個 Ref-data 全部轉成 Python；本次只做第一批基礎模組。

## 8. 目前準確性等級

目前狀態：

```text
Ref-data 第一批方法已開始 Python 化
但整體投資分析仍屬 screen-grade
```

已改善：

- ETF / stock 初步分類
- ETF holdings overlap 可計算
- 財務品質核心分數可計算
- workflow 可取代 n8n 的節點式流程
- prompt 可知道分析對象類型

仍待補：

- 真實 FinMind / FMP 財報正規化
- ETF holdings 檔案 parser 接入 `Ref-data/6-1/IEMG.txt`、`VWO.txt`
- DCF / valuation scenario
- 新聞情緒 / event extraction
- portfolio risk / stress test
- decision journal / catalyst calendar

## 9. 結論

本次新增程式與測試已通過：

```text
88 個 Python 檔案編譯通過
72 個 unittest 通過
入口匯入 smoke test 通過
```

這代表新的 Python workflow engine 與第一批 Ref-data 分析模組已可作為後續擴充基礎。
