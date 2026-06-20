# AI 台股技術分析 GUI

版本：v1.6

這個版本改用 FinMind 台股日成交資料，並以桌面 GUI 執行，不再啟動 Streamlit 網站。

## 啟動

```powershell
python .\AI-stock.py
```

或使用：

```powershell
.\run_ai_stock.ps1
```

## API key 檔案

程式會讀取程式所在資料夾中的 `api-key.txt`。

Python 版執行時，位置是：

```text
api-key.txt
```

`.exe` 版執行時，位置是：

```text
dist\AIStockAnalysis\api-key.txt
```

建議內容：

```text
FINMIND_API_KEY=你的_FinMind_token
GEMINI_API_KEY=你的_Gemini_key
```

如果檔案不存在，程式啟動時會嘗試建立空白範本。GUI 內可以輸入 key 後按「儲存 Key」寫回同一個檔案，下次啟動會自動載入。請不要把 `api-key.txt` 上傳到 GitHub。

## 資料來源

FinMind API:

```text
https://api.finmindtrade.com/api/v4/data
```

使用資料集：

```text
TaiwanStockPrice
```

主要欄位轉換：

- `max` -> `high`
- `min` -> `low`
- `Trading_Volume` -> `volume`

## 功能

- 台股代號查詢，例如 `2330`、`2317`、`2454`、`0050`
- 左側自選清單，可儲存自訂股票或 ETF 代碼
- 自選清單儲存在 `watchlist.json`
- 總覽、走勢圖、歷史資料、AI 綜合分析、ML 訊號、基本股利、相關新聞分頁
- 每次查詢會同步搜尋該股市場新聞
- 每次查詢會同步抓取最新 EPS、預計股息發放月份與股息金額
- AI 綜合分析整合技術面、新聞、Public Equity Investing 視角、輕量 Investment Banking 視角與 ML 訊號
- AI 綜合分析會納入 EPS / 股利資訊
- ML 訊號使用歷史價量與技術指標訓練分類模型，輸出上漲 / 下跌機率與測試準確率
- K 線、成交量、RSI 圖表
- MA5、MA10、MA20、MA60
- RSI 超買 / 超賣狀態
- 歷史資料表
- Gemini AI 教育性技術分析

## GitHub 同步

可使用下列腳本把目前專案主要檔案提交並推送到 GitHub：

```powershell
.\sync_to_github.ps1
```

腳本只會 stage 已列入清單的專案檔，避免把 API key 或不相關檔案推上去。
