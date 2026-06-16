# AI 台股技術分析 v1.6 使用手冊

## 1. 程式用途

本程式是 Windows 桌面版台股分析工具，資料來源以 FinMind 台股資料為主，並整合 Gemini 產生 AI 綜合分析。

主要功能：

- 台股 / ETF 代碼查詢
- 自選清單儲存
- K 線、成交量、RSI、MA5 / MA10 / MA20 / MA60
- 最新 EPS
- 現金股利、股票股利、預計發放月份、除息日
- ML 漲跌訊號
- 相關新聞
- AI 綜合分析

## 2. 執行方式

### 使用 Python 執行

```powershell
.\run_ai_stock.ps1
```

或：

```powershell
.\.venv\Scripts\python.exe .\AI-stock.py
```

### 使用執行檔

打包完成後執行：

```text
dist\AIStockAnalysis\AIStockAnalysis.exe
```

若是單檔版本，則執行：

```text
dist\AIStockAnalysis.exe
```

## 3. API key 設定

程式會讀取下列檔案：

```text
C:\Users\shou0\PycharmProjects\api-key.txt
```

內容格式：

```text
FINMIND_API_KEY=你的_FinMind_token
GEMINI_API_KEY=你的_Gemini_API_key
```

FinMind key 用於抓台股資料。Gemini key 用於 AI 綜合分析；若未設定 Gemini key，程式仍可顯示圖表、ML 訊號、EPS、股利與新聞。

## 4. FinMind API key 申請

1. 前往 FinMind 官方網站：<https://finmind.github.io/>
2. 註冊或登入 FinMind。
3. 進入會員 / API token 頁面。
4. 複製你的 token。
5. 貼到 `api-key.txt`：

```text
FINMIND_API_KEY=你的_token
```

本程式使用的 FinMind 資料集：

- `TaiwanStockPrice`：台股日成交資料
- `TaiwanStockFinancialStatements`：EPS
- `TaiwanStockDividend`：股利政策

## 5. Gemini API key 申請

1. 前往 Google AI Studio API key 文件：<https://ai.google.dev/gemini-api/docs/api-key>
2. 點選官方頁面中的 `Get API key` / `Create or view a Gemini API Key`。
3. 登入 Google 帳號。
4. 選擇或建立 Google Cloud project。
5. 建立 Gemini API key。
6. 複製 API key。
7. 貼到 `api-key.txt`：

```text
GEMINI_API_KEY=你的_Gemini_API_key
```

Google 官方文件建議使用環境變數保存 key；本程式則使用本機 `api-key.txt`，請不要把該檔案上傳到 GitHub。

### Gemini key 版本注意事項

Google 文件說明，Gemini API 正在從 Standard API key 轉到 Authorization API key。新建的 AI Studio API key 會自動建立為 auth key。

若你使用很早以前建立的 Standard key，請到 AI Studio API Keys 頁面重新建立新的 auth key。Google 文件列出的時程如下：

- 2026-06-19 起，未限制用途的 Standard key 會被 Gemini API 拒絕。
- 2026-09 起，Standard key 會被 Gemini API 拒絕。

若 AI 綜合分析突然無法使用，請優先確認 `GEMINI_API_KEY` 是否為新建立的 auth key。

## 6. 操作流程

1. 開啟程式。
2. 從左側自選清單選股票，或手動輸入代碼。
3. 設定起始日期、結束日期與 RSI 週期。
4. 點選「查詢分析」。
5. 查看各分頁：
   - `走勢圖`
   - `歷史資料`
   - `AI 綜合分析`
   - `ML 訊號`
   - `基本股利`
   - `相關新聞`

## 7. 自選股

輸入股票或 ETF 代碼後，可按「儲存為自選」。

自選清單儲存在：

```text
watchlist.json
```

Python 版執行時，位置是專案資料夾內的 `watchlist.json`。

`.exe` 版執行時，位置是：

```text
dist\AIStockAnalysis\watchlist.json
```

## 8. 常見問題

### FinMind 顯示 Token is illegal

代表 `FINMIND_API_KEY` 不正確、過期，或 `api-key.txt` 仍是範例文字。

### Gemini 沒有產生 AI 分析

請確認 `GEMINI_API_KEY` 已填入。若未填，程式仍可顯示其他分析。

### DXYZ 查不到

目前資料來源是 FinMind 台股資料集，主要支援台股與台股 ETF。非台股代碼可能查無資料。

### EPS 或股利顯示資料不足

可能原因：

- ETF 沒有 EPS
- 該公司近期資料尚未公布
- FinMind 資料集沒有該欄位
- 海外代碼不支援

## 9. 安全提醒

- 不要把 `api-key.txt` 上傳到 GitHub。
- 不要在截圖中顯示完整 API key。
- 若 key 外洩，請立即到 FinMind 或 Google AI Studio 重新產生 key。

## 10. 重新打包執行檔

```powershell
.\build_exe.ps1
```

打包結果會出現在：

```text
dist\
```

## 11. 官方參考文件

- FinMind 登入與 API token：<https://finmind.github.io/login/>
- FinMind 更新 Token：<https://finmind.github.io/update_token/>
- FinMind 台股基本面資料集：<https://finmind.github.io/tutor/TaiwanMarket/Fundamental/>
- Gemini API key：<https://ai.google.dev/gemini-api/docs/api-key>
