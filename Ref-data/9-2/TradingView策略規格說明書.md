# Pine Script 策略轉換系統 規格說明書

> **用途說明**: 本規格說明書作為 AI 提示語使用，將此完整內容連同策略資訊一起提交給 AI，AI 將根據規格生成完整的 Streamlit 應用程式碼。

---

## 📋 系統概述

### 系統名稱
【Code Gym】TradingView 策略分析系統

### 核心功能描述
建立一個基於網頁的交易策略分析工具，能夠：
1. 將 TradingView Pine Script 策略轉換為 Python 實現
2. 從 FMP API 獲取股票歷史價格數據
3. 計算技術指標並產生買賣信號
4. 以清晰的表格形式展示進出場點位
5. 提供策略的完整說明和使用指引

### 技術架構要求
- **界面框架**: Streamlit
- **數據來源**: Financial Modeling Prep (FMP) API
- **數據處理**: Pandas, NumPy
- **HTTP 請求**: requests
- **日期處理**: datetime (內建)
- **部署方式**: 單一 Python 檔案 (app.py)，可直接在 Docker 容器中運行

---

## 🛠 技術環境限制

### Docker 環境資訊
**基礎映像**: `python:3.11-slim`
**系統套件**: curl, build-essential, fonts-dejavu-core, fontconfig

### 可用 Python 模組清單
根據 Dockerfile 定義，**僅能使用以下模組**：

**核心模組** (必須使用):
- `streamlit` - Web 界面框架
- `pandas` - 數據處理和分析
- `numpy` - 數值計算
- `requests` - HTTP 請求處理

**可選模組** (視需求使用):
- `plotly` - 互動式圖表（本系統不使用繪圖）
- `openai` - OpenAI API（本系統不使用）
- `yfinance` - Yahoo Finance 數據（本系統使用 FMP API）
- `matplotlib` - 靜態圖表（本系統不使用繪圖）
- `seaborn` - 統計圖表（本系統不使用繪圖）
- `fpdf` - PDF 生成（本系統不使用）

**內建模組** (可使用):
- `datetime` - 日期時間處理
- `json` - JSON 處理
- `typing` - 類型註解
- `functools` - 函數工具

**嚴格限制**:
- ❌ 不可使用 `ta-lib` (未安裝)
- ❌ 不可使用 `pandas-ta` (未安裝)
- ❌ 所有技術指標必須使用 pandas 和 numpy 自行實現

### 資料來源規範

#### FMP API 規格
**API 端點**: 
```
https://financialmodelingprep.com/stable/historical-price-eod/full
```

**請求參數**:
- `symbol` (必填): 股票代碼，如 AAPL
- `apikey` (必填): FMP API Key
- `from` (可選): 起始日期，格式 YYYY-MM-DD，如 2024-01-01
- `to` (可選): 結束日期，格式 YYYY-MM-DD，如 2025-01-01

**完整請求範例**:
```
https://financialmodelingprep.com/stable/historical-price-eod/full?symbol=AAPL&from=2024-01-01&to=2025-01-01&apikey=YOUR_API_KEY
```

**返回數據格式 (JSON)**:
```json
[
    {
        "symbol": "AAPL",
        "date": "2025-02-04",
        "open": 227.2,
        "high": 233.13,
        "low": 226.65,
        "close": 232.8,
        "volume": 44489128,
        "change": 5.6,
        "changePercent": 2.46479,
        "vwap": 230.86
    },
    ...
]
```

**數據處理要求**:
1. 將 JSON 轉換為 pandas DataFrame
2. 將 `date` 欄位轉換為 datetime 並設為索引
3. 確保數據按時間升序排列
4. 只保留必要欄位：open, high, low, close, volume
5. 檢查數據完整性，處理缺失值

---

## 🎯 功能需求規格

### F-001: 用戶界面設計
**基本要求**: 
- 頁面標題: "📈 TradingView 策略分析系統"，使用彩虹色分隔線 (divider="rainbow")
- 左側控制區（側邊欄）包含：
  - 系統 Logo "🎯 策略分析器" (divider="rainbow")
  - **FMP API Key 輸入**：安全輸入框 (type="password")，必填
  - **股票代碼輸入**：文字輸入框，預設值 "AAPL"
  - **分析期間選擇**：下拉選單，選項：["最近 1 年", "最近 2 年", "最近 3 年", "最近 5 年", "自訂區間"]
  - **自訂日期範圍**（當選擇"自訂區間"時顯示）：起始日期和結束日期選擇器
  - **策略選擇**：下拉選單（初始只有範例策略，可擴展）
- 主要執行按鈕: "🚀 開始分析" (use_container_width=True)

**側邊欄底部**: 免責聲明 (st.sidebar.markdown)

### F-002: 數據獲取功能
**功能目標**: 從 FMP API 獲取指定股票的歷史價格數據

**用戶操作**: 
1. 用戶輸入 FMP API Key
2. 用戶輸入股票代碼（如 AAPL）
3. 用戶選擇分析期間
4. 點擊"開始分析"按鈕

**數據獲取流程**:
1. 驗證 API Key 格式（非空白）
2. 驗證股票代碼格式（非空白，轉大寫）
3. 根據選擇的期間計算起始和結束日期
4. 構建 FMP API 請求 URL
5. 發送 HTTP GET 請求
6. 解析 JSON 回應
7. 轉換為 pandas DataFrame
8. 數據清理和驗證

**錯誤處理**:
- API Key 無效：顯示錯誤訊息並停止
- 股票代碼不存在：顯示友善錯誤訊息
- 網路連線問題：提示重試
- 數據格式異常：顯示技術細節供除錯

**成功回饋**:
- 使用 st.success() 顯示成功訊息
- 顯示獲取的數據筆數和日期範圍

### F-003: 數據處理與計算
**處理目標**: 計算策略所需的技術指標

**處理流程**:
1. 接收原始 OHLCV 數據
2. 根據策略需求計算技術指標（如 EMA、SMA、RSI、MACD 等）
3. 產生買入和賣出信號
4. 整理成標準化的信號表格

**技術指標實現要求**:
- 所有指標必須使用 pandas 和 numpy 實現
- 不可依賴外部技術分析庫（如 ta-lib）
- 計算邏輯必須與 Pine Script 一致
- 處理邊界情況（如數據不足時）

**品質要求**: 
- 計算結果準確可靠
- 妥善處理 NaN 值
- 確保時間序列對齊
- 實施適當的數據驗證

### F-004: 主要顯示區域設計
**頁籤結構**: 使用 st.tabs 創建 3 個主要區域

#### Tab 1: "📊 策略說明"
**顯示內容**:
1. **策略名稱**: 大標題顯示
2. **策略來源**: 顯示 TradingView 策略連結（可點擊）
3. **核心概念**: 以段落形式說明策略的基本原理（2-3 段）
4. **技術指標**: 條列式列出使用的所有指標及參數
5. **買入條件**: 清楚說明買入信號的觸發條件
6. **賣出條件**: 清楚說明賣出信號的觸發條件
7. **適用場景**: 說明策略適合的市場環境
8. **風險提示**: 說明策略的限制和風險

**格式要求**:
- 使用 markdown 格式
- 適當使用粗體、標題、列表
- 段落間留白適當
- 重要資訊用 info box 或 warning box 顯示

#### Tab 2: "📋 交易信號"
**顯示內容**:
1. **摘要統計**: 使用 st.columns(3) 顯示
   - 總信號數量
   - 買入信號數量
   - 賣出信號數量

2. **最新信號**: 使用 st.info() 或 st.success()/st.error() 顯示
   - 最新信號類型（BUY/SELL）
   - 信號日期
   - 信號價格
   - 關鍵指標數值

3. **完整信號表格**: 使用 st.dataframe() 顯示
   - 必要欄位：
     * 日期 (datetime)
     * 信號類型 (BUY/SELL)
     * 價格 (close price)
     * [策略相關的關鍵指標]
   - 表格特性：
     * 可排序
     * 可搜尋
     * 高度自適應
     * use_container_width=True

4. **資料匯出**: 
   - 提供 CSV 下載按鈕
   - 檔案名稱：{symbol}_{strategy_name}_signals_{date}.csv

**視覺提示**:
- 買入信號使用綠色標記
- 賣出信號使用紅色標記
- 最新信號特別突顯

#### Tab 3: "📈 原始數據"
**顯示內容**:
1. **數據摘要**: 
   - 數據筆數
   - 日期範圍
   - 價格範圍（最高、最低）

2. **完整數據表格**:
   - 顯示所有 OHLCV 數據
   - 包含計算的技術指標欄位
   - 可排序和搜尋
   - 顯示最近 100 筆（可調整）

3. **資料匯出**:
   - 提供完整數據的 CSV 下載

### F-005: 基本資訊展示
**展示方式**: 在主標題下方，使用 st.columns(4) 展示基本資訊

**展示內容**:
- 第一欄: 股票代碼和公司名稱
- 第二欄: 分析期間（起始日～結束日）
- 第三欄: 數據筆數
- 第四欄: 策略名稱

**顯示格式**: 使用 st.metric() 或簡單的 markdown

### F-006: 輔助功能
**進度顯示**: 
- 使用 st.spinner() 顯示處理進度
- 關鍵步驟：
  * "正在驗證 API Key..."
  * "正在獲取股票數據..."
  * "正在計算技術指標..."
  * "正在產生交易信號..."
  * "分析完成！"

**狀態管理**: 
- 使用 st.session_state 儲存分析結果
- 避免重複計算
- 支援重新分析

**狀態反饋標準**: 
- st.success() - 操作成功
- st.error() - 錯誤訊息，提供解決建議
- st.warning() - 警告和注意事項
- st.info() - 一般資訊和操作指引

### F-007: 錯誤處理與用戶體驗
**輸入驗證**:
- 檢查 API Key 是否為空
- 檢查股票代碼是否為空
- 驗證日期範圍的合理性
- 提供即時的輸入提示

**錯誤處理**:
- 所有 API 調用都要有 try-except
- 網路問題要有友善的錯誤訊息
- 數據格式錯誤要有清楚說明
- 提供可能的解決方案

**用戶指導**:
- 提供 API Key 申請連結
- 提供股票代碼查詢說明
- 解釋各個參數的意義
- 提供使用範例

### F-008: 免責聲明與安全
**免責聲明位置**: 側邊欄底部 (st.sidebar.markdown)

**免責聲明內容**:
```markdown
---
### ⚠️ 免責聲明
本系統僅供學術研究與教育用途，所提供的數據與分析結果僅供參考，**不構成投資建議**。

請使用者自行判斷決策，並承擔相關風險。本系統作者不對任何投資行為負責，亦不承擔任何損失責任。

**風險提示**: 
- 過去的績效不代表未來的表現
- 技術分析有其局限性
- 請謹慎評估自身風險承受能力
```

**安全要求**:
- API Key 使用 type="password" 輸入
- 不在日誌或錯誤訊息中顯示完整 API Key
- 實施適當的輸入清理

---

## 🔄 策略轉換規範

### T-001: 策略輸入資訊
**必要輸入**：
- **策略名稱**: [策略的中文名稱]
- **策略來源**: [TradingView 完整 URL]
- **Pine Script 版本**: [如 @version=6]
- **Pine Script 完整程式碼**: [貼上完整的 Pine Script 程式碼]

### T-002: 策略解釋輸出要求
AI 必須在程式碼開頭的註釋中，用**繁體中文**提供以下說明：

1. **核心概念** (2-3 段文字):
   - 用簡單易懂的方式說明策略的基本原理
   - 說明策略的設計思路和目的
   - 不使用過多技術術語

2. **技術指標清單** (條列式):
   - 列出所有使用的技術指標
   - 說明每個指標的參數設定
   - 範例：EMA 9（9 期指數移動平均線）

3. **買入條件** (具體且明確):
   - 清楚說明觸發買入信號的條件
   - 可使用數學式或邏輯式表達
   - 範例：當 EMA 9 向上穿越 EMA 21 時買入

4. **賣出條件** (具體且明確):
   - 清楚說明觸發賣出信號的條件
   - 可使用數學式或邏輯式表達
   - 範例：當 EMA 9 向下穿越 EMA 21 時賣出

5. **適用場景**:
   - 說明策略適合什麼類型的市場環境
   - 範例：適合趨勢明確的市場

6. **風險提示**:
   - 說明策略可能的限制
   - 提醒使用者注意的風險
   - 範例：在震盪市場可能產生較多假信號

### T-003: Python 程式碼轉換要求

#### 程式碼結構要求
**必須使用單一檔案** (app.py) 包含所有功能，按以下順序組織：

1. **檔案標頭註釋**: 包含策略完整說明（T-002 要求的內容）
2. **模組導入區**: 所有 import 語句
3. **全域配置區**: 常數定義（如 FMP_BASE_URL）
4. **技術指標函數庫**: 所有技術指標的計算函數
5. **FMP API 客戶端類別**: 處理 API 請求
6. **策略基類**: BaseStrategy 抽象類別
7. **具體策略實現**: 繼承 BaseStrategy 的策略類別
8. **Streamlit UI 界面**: 主程式邏輯

#### 技術指標實現限制
- **只能使用**: pandas 的內建方法（如 `.ewm()`, `.rolling()`, `.shift()`）和 numpy
- **不可使用**: ta-lib, pandas-ta 或任何外部技術分析庫
- **必須自行實現**: 所有技術指標的計算邏輯

#### 常用技術指標實現參考

**EMA (指數移動平均)**:
```python
def calculate_ema(series, period):
    """計算指數移動平均線"""
    return series.ewm(span=period, adjust=False).mean()
```

**SMA (簡單移動平均)**:
```python
def calculate_sma(series, period):
    """計算簡單移動平均線"""
    return series.rolling(window=period).mean()
```

**Crossover (向上穿越)**:
```python
# 當 series1 向上穿越 series2
crossover = (series1 > series2) & (series1.shift(1) <= series2.shift(1))
```

**Crossunder (向下穿越)**:
```python
# 當 series1 向下穿越 series2
crossunder = (series1 < series2) & (series1.shift(1) >= series2.shift(1))
```

**ATR (平均真實範圍)**:
```python
def calculate_atr(df, period=14):
    """計算 ATR"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr
```

#### 信號產生邏輯要求
- 使用 pandas 的布林索引產生信號
- 買入信號欄位命名：`buy_signal` (True/False)
- 賣出信號欄位命名：`sell_signal` (True/False)
- 確保信號不會重疊（同一時間點不會同時有買入和賣出）

#### 信號表格標準格式
必須包含以下欄位：
- `日期` (datetime): 信號發生的日期
- `信號類型` (str): "BUY" 或 "SELL"
- `價格` (float): 收盤價，保留 2 位小數
- [其他策略相關指標]: 如 EMA 值、RSI 值等

### T-004: 程式碼品質標準

**註釋要求**:
- 每個類別都要有 docstring 說明用途
- 每個函數都要有 docstring 說明參數和返回值
- 關鍵計算步驟要有行內註釋
- 所有註釋使用繁體中文

**命名規範**:
- 類別名稱：PascalCase (如 `EMASuperStrategy`)
- 函數名稱：snake_case (如 `calculate_ema`)
- 變數名稱：snake_case (如 `buy_signal`)
- 常數名稱：UPPER_SNAKE_CASE (如 `FMP_BASE_URL`)

**錯誤處理**:
- 所有 API 請求都要有 try-except
- 所有數據處理都要檢查 None 和 NaN
- 提供有意義的錯誤訊息
- 使用 Streamlit 的錯誤顯示方法

**程式碼組織**:
- 邏輯清晰，易於理解
- 避免過長的函數（超過 50 行考慮拆分）
- 適當的空行分隔邏輯區塊
- 遵循 PEP 8 風格指南

### T-005: 轉換正確性驗證
**驗證建議**:
1. 使用相同的歷史數據在 TradingView 和 Python 系統中測試
2. 對比關鍵時間點的信號是否一致
3. 檢查技術指標數值的準確性
4. 測試邊界情況（數據不足、異常值等）

**常見差異來源**:
- 數據源不同（TradingView 和 FMP 的數據可能略有差異）
- 計算精度差異（容許誤差範圍：小數點後 4 位）
- 時區處理差異
- 數據對齊方式不同

---

## 💻 Python 程式碼標準架構

### 檔案名稱
`app.py` (單一檔案包含所有功能)

### 完整程式碼模板

```python
"""
TradingView 策略分析系統
================================================

策略名稱: [策略中文名稱]
策略來源: [TradingView URL]
Pine Script 版本: [版本號]

================================================
策略說明
================================================

## 核心概念
[2-3 段文字說明策略的基本原理]

## 技術指標
[條列式列出所有使用的指標及參數]
- 指標1: 說明和參數
- 指標2: 說明和參數

## 買入條件
[具體說明買入信號的觸發條件]

## 賣出條件
[具體說明賣出信號的觸發條件]

## 適用場景
[說明策略適合的市場環境]

## 風險提示
[說明策略的限制和風險]

================================================
"""

# ===== 區塊 1: 模組導入 =====
import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any

# ===== 區塊 2: 全域配置 =====
FMP_BASE_URL = "https://financialmodelingprep.com/stable/historical-price-eod/full"

# 策略資訊（用於顯示）
STRATEGY_INFO = {
    'name': '[策略名稱]',
    'source_url': '[TradingView URL]',
    'version': '[Pine Script 版本]'
}

# ===== 區塊 3: 技術指標函數庫 =====
def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """
    計算指數移動平均線 (EMA)
    
    參數:
        series: 價格序列
        period: 週期
    
    返回:
        EMA 序列
    """
    return series.ewm(span=period, adjust=False).mean()


def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    """
    計算簡單移動平均線 (SMA)
    
    參數:
        series: 價格序列
        period: 週期
    
    返回:
        SMA 序列
    """
    return series.rolling(window=period).mean()


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    計算平均真實範圍 (ATR)
    
    參數:
        df: 包含 high, low, close 的 DataFrame
        period: ATR 週期
    
    返回:
        ATR 序列
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr


# [根據策略需求添加其他技術指標函數]


# ===== 區塊 4: FMP API 客戶端 =====
class FMPClient:
    """FMP API 客戶端類別"""
    
    def __init__(self, api_key: str):
        """
        初始化 FMP 客戶端
        
        參數:
            api_key: FMP API Key
        """
        self.api_key = api_key
        self.base_url = FMP_BASE_URL
    
    def get_historical_data(
        self, 
        symbol: str, 
        from_date: Optional[str] = None, 
        to_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """
        獲取股票歷史價格數據
        
        參數:
            symbol: 股票代碼
            from_date: 起始日期 (YYYY-MM-DD)
            to_date: 結束日期 (YYYY-MM-DD)
        
        返回:
            包含 OHLCV 數據的 DataFrame，或 None（如果失敗）
        """
        try:
            # 構建請求 URL
            params = {
                'symbol': symbol.upper(),
                'apikey': self.api_key
            }
            
            if from_date:
                params['from'] = from_date
            if to_date:
                params['to'] = to_date
            
            # 發送請求
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            # 解析 JSON
            data = response.json()
            
            if not data or not isinstance(data, list):
                st.error(f"未找到股票代碼 {symbol} 的數據")
                return None
            
            # 轉換為 DataFrame
            df = pd.DataFrame(data)
            
            # 數據處理
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)
            
            # 只保留需要的欄位
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            df = df[required_columns]
            
            return df
            
        except requests.exceptions.Timeout:
            st.error("請求超時，請檢查網路連線")
            return None
        except requests.exceptions.RequestException as e:
            st.error(f"API 請求失敗: {str(e)}")
            return None
        except Exception as e:
            st.error(f"數據處理錯誤: {str(e)}")
            return None
    
    def validate_api_key(self) -> bool:
        """
        驗證 API Key 是否有效
        
        返回:
            True 如果有效，否則 False
        """
        if not self.api_key or len(self.api_key) < 10:
            return False
        
        # 嘗試獲取少量數據來驗證
        try:
            params = {
                'symbol': 'AAPL',
                'apikey': self.api_key
            }
            response = requests.get(self.base_url, params=params, timeout=10)
            return response.status_code == 200
        except:
            return False


# ===== 區塊 5: 策略基類 =====
class BaseStrategy:
    """所有策略的基類"""
    
    def __init__(self, df: pd.DataFrame, strategy_name: str):
        """
        初始化策略
        
        參數:
            df: 包含 OHLCV 數據的 DataFrame
            strategy_name: 策略名稱
        """
        self.df = df.copy()
        self.strategy_name = strategy_name
        self.signals = None
    
    def calculate_indicators(self) -> None:
        """計算策略所需的技術指標 - 子類必須實現"""
        raise NotImplementedError("子類必須實現 calculate_indicators 方法")
    
    def generate_signals(self) -> None:
        """產生買賣信號 - 子類必須實現"""
        raise NotImplementedError("子類必須實現 generate_signals 方法")
    
    def get_signal_table(self) -> pd.DataFrame:
        """
        返回標準化的信號表格
        
        返回:
            包含交易信號的 DataFrame
        """
        if self.signals is None:
            raise ValueError("請先調用 generate_signals()")
        return self.signals
    
    def run(self) -> pd.DataFrame:
        """
        執行完整的策略分析流程
        
        返回:
            信號表格
        """
        self.calculate_indicators()
        self.generate_signals()
        return self.get_signal_table()


# ===== 區塊 6: [策略名稱] 策略實現 =====
class [StrategyName]Strategy(BaseStrategy):
    """
    [策略中文名稱]
    
    來源: [TradingView URL]
    
    這裡簡短重複核心概念說明
    """
    
    def __init__(self, df: pd.DataFrame):
        """初始化策略"""
        super().__init__(df, "[策略名稱]")
        
        # 策略參數（根據 Pine Script 定義）
        self.param1 = value1
        self.param2 = value2
        # ...
    
    def calculate_indicators(self) -> None:
        """計算策略所需的技術指標"""
        # 根據 Pine Script 實現各項技術指標
        # 範例：
        # self.df['ema_9'] = calculate_ema(self.df['close'], 9)
        # self.df['ema_21'] = calculate_ema(self.df['close'], 21)
        # ...
        
        pass  # 實際實現時移除這行
    
    def generate_signals(self) -> None:
        """產生買賣信號"""
        # 實現買入和賣出信號邏輯
        # 範例：
        # self.df['buy_signal'] = (
        #     (self.df['ema_9'] > self.df['ema_21']) & 
        #     (self.df['ema_9'].shift(1) <= self.df['ema_21'].shift(1))
        # )
        # self.df['sell_signal'] = (
        #     (self.df['ema_9'] < self.df['ema_21']) & 
        #     (self.df['ema_9'].shift(1) >= self.df['ema_21'].shift(1))
        # )
        
        # 整理成標準信號表格
        signals = self.df[self.df['buy_signal'] | self.df['sell_signal']].copy()
        
        self.signals = pd.DataFrame({
            '日期': signals.index,
            '信號類型': signals.apply(
                lambda row: 'BUY' if row['buy_signal'] else 'SELL', 
                axis=1
            ),
            '價格': signals['close'].round(2),
            # 添加其他相關指標欄位
        })
        
        self.signals.reset_index(drop=True, inplace=True)


# ===== 區塊 7: Streamlit UI 界面 =====
def main():
    """主程式"""
    
    # 頁面配置
    st.set_page_config(
        page_title="TradingView 策略分析系統",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 初始化 session state
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'raw_data' not in st.session_state:
        st.session_state.raw_data = None
    
    # ===== 側邊欄 =====
    with st.sidebar:
        st.markdown("# 🎯 策略分析器")
        st.divider()
        
        # API Key 輸入
        api_key = st.text_input(
            "FMP API Key",
            type="password",
            help="請輸入您的 Financial Modeling Prep API Key"
        )
        
        # 股票代碼輸入
        symbol = st.text_input(
            "股票代碼",
            value="AAPL",
            help="請輸入美股代碼，如 AAPL, TSLA, GOOGL"
        ).upper()
        
        # 分析期間選擇
        period_options = ["最近 1 年", "最近 2 年", "最近 3 年", "最近 5 年", "自訂區間"]
        period = st.selectbox("分析期間", period_options)
        
        # 自訂日期範圍
        from_date = None
        to_date = None
        if period == "自訂區間":
            col1, col2 = st.columns(2)
            with col1:
                from_date = st.date_input(
                    "起始日期",
                    value=datetime.now() - timedelta(days=365)
                )
            with col2:
                to_date = st.date_input(
                    "結束日期",
                    value=datetime.now()
                )
        else:
            # 計算日期範圍
            to_date = datetime.now()
            years = int(period.split()[1])
            from_date = to_date - timedelta(days=years*365)
        
        # 轉換為字串格式
        from_date_str = from_date.strftime('%Y-%m-%d') if from_date else None
        to_date_str = to_date.strftime('%Y-%m-%d') if to_date else None
        
        # 策略選擇（未來可擴展）
        strategy_name = st.selectbox(
            "選擇策略",
            [STRATEGY_INFO['name']]
        )
        
        st.divider()
        
        # 分析按鈕
        analyze_button = st.button("🚀 開始分析", use_container_width=True)
        
        # 免責聲明
        st.divider()
        st.markdown("""
        ### ⚠️ 免責聲明
        本系統僅供學術研究與教育用途，所提供的數據與分析結果僅供參考，**不構成投資建議**。
        
        請使用者自行判斷決策，並承擔相關風險。本系統作者不對任何投資行為負責，亦不承擔任何損失責任。
        
        **風險提示**: 
        - 過去的績效不代表未來的表現
        - 技術分析有其局限性
        - 請謹慎評估自身風險承受能力
        """)
    
    # ===== 主畫面 =====
    st.title("📈 TradingView 策略分析系統")
    st.divider()
    
    # 分析邏輯
    if analyze_button:
        # 驗證輸入
        if not api_key:
            st.error("❌ 請輸入 FMP API Key")
            st.info("💡 您可以在 [FMP 官網](https://financialmodelingprep.com/) 免費申請 API Key")
            st.stop()
        
        if not symbol:
            st.error("❌ 請輸入股票代碼")
            st.stop()
        
        # 執行分析
        with st.spinner("正在分析中..."):
            try:
                # 步驟 1: 驗證 API Key
                status = st.empty()
                status.info("🔍 正在驗證 API Key...")
                
                fmp = FMPClient(api_key)
                if not fmp.validate_api_key():
                    st.error("❌ API Key 無效，請檢查後重試")
                    st.stop()
                
                # 步驟 2: 獲取數據
                status.info(f"📊 正在獲取 {symbol} 的歷史數據...")
                
                df = fmp.get_historical_data(symbol, from_date_str, to_date_str)
                
                if df is None or len(df) == 0:
                    st.error(f"❌ 無法獲取 {symbol} 的數據，請檢查股票代碼是否正確")
                    st.stop()
                
                # 檢查數據量是否足夠
                if len(df) < 50:
                    st.warning(f"⚠️ 數據量不足（僅 {len(df)} 筆），可能影響分析準確性")
                
                # 步驟 3: 執行策略
                status.info("⚙️ 正在計算技術指標...")
                
                strategy = [StrategyName]Strategy(df)
                
                status.info("🎯 正在產生交易信號...")
                
                signal_table = strategy.run()
                
                # 步驟 4: 儲存結果
                st.session_state.results = signal_table
                st.session_state.raw_data = strategy.df
                st.session_state.symbol = symbol
                st.session_state.date_range = f"{from_date_str} ~ {to_date_str}"
                
                status.empty()
                st.success(f"✅ 分析完成！共找到 {len(signal_table)} 個交易信號")
                
            except Exception as e:
                st.error(f"❌ 分析過程發生錯誤: {str(e)}")
                st.exception(e)
    
    # ===== 結果展示區域 =====
    if st.session_state.results is not None:
        # 基本資訊
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("股票代碼", st.session_state.symbol)
        with col2:
            st.metric("分析期間", st.session_state.date_range)
        with col3:
            st.metric("數據筆數", len(st.session_state.raw_data))
        with col4:
            st.metric("策略名稱", STRATEGY_INFO['name'])
        
        st.divider()
        
        # 頁籤
        tab1, tab2, tab3 = st.tabs(["📊 策略說明", "📋 交易信號", "📈 原始數據"])
        
        # Tab 1: 策略說明
        with tab1:
            st.markdown(f"## {STRATEGY_INFO['name']}")
            st.markdown(f"**來源**: [{STRATEGY_INFO['source_url']}]({STRATEGY_INFO['source_url']})")
            
            st.markdown("### 📖 核心概念")
            st.markdown("""
            [從程式碼開頭註釋中的「核心概念」部分複製到這裡]
            """)
            
            st.markdown("### 🔧 技術指標")
            st.markdown("""
            [從程式碼開頭註釋中的「技術指標」部分複製到這裡]
            """)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📈 買入條件")
                st.info("""
                [從程式碼開頭註釋中的「買入條件」部分複製到這裡]
                """)
            
            with col2:
                st.markdown("### 📉 賣出條件")
                st.warning("""
                [從程式碼開頭註釋中的「賣出條件」部分複製到這裡]
                """)
            
            st.markdown("### 🎯 適用場景")
            st.markdown("""
            [從程式碼開頭註釋中的「適用場景」部分複製到這裡]
            """)
            
            st.markdown("### ⚠️ 風險提示")
            st.warning("""
            [從程式碼開頭註釋中的「風險提示」部分複製到這裡]
            """)
        
        # Tab 2: 交易信號
        with tab2:
            signals = st.session_state.results
            
            # 摘要統計
            st.markdown("### 📊 信號統計")
            col1, col2, col3 = st.columns(3)
            
            buy_count = len(signals[signals['信號類型'] == 'BUY'])
            sell_count = len(signals[signals['信號類型'] == 'SELL'])
            
            with col1:
                st.metric("總信號數", len(signals))
            with col2:
                st.metric("買入信號", buy_count, delta=None, delta_color="normal")
            with col3:
                st.metric("賣出信號", sell_count, delta=None, delta_color="inverse")
            
            st.divider()
            
            # 最新信號
            if len(signals) > 0:
                latest = signals.iloc[-1]
                signal_type = latest['信號類型']
                
                if signal_type == 'BUY':
                    st.success(f"""
                    ### 🟢 最新信號: {signal_type}
                    - **日期**: {latest['日期']}
                    - **價格**: ${latest['價格']}
                    """)
                else:
                    st.error(f"""
                    ### 🔴 最新信號: {signal_type}
                    - **日期**: {latest['日期']}
                    - **價格**: ${latest['價格']}
                    """)
            
            st.divider()
            
            # 完整信號表格
            st.markdown("### 📋 完整交易信號")
            
            # 應用顏色標記
            def highlight_signals(row):
                if row['信號類型'] == 'BUY':
                    return ['background-color: #d4edda'] * len(row)
                else:
                    return ['background-color: #f8d7da'] * len(row)
            
            styled_signals = signals.style.apply(highlight_signals, axis=1)
            
            st.dataframe(
                styled_signals,
                use_container_width=True,
                height=400
            )
            
            # 匯出功能
            csv = signals.to_csv(index=False, encoding='utf-8-sig')
            filename = f"{st.session_state.symbol}_{STRATEGY_INFO['name']}_signals_{datetime.now().strftime('%Y%m%d')}.csv"
            
            st.download_button(
                label="📥 下載信號表格 (CSV)",
                data=csv,
                file_name=filename,
                mime="text/csv"
            )
        
        # Tab 3: 原始數據
        with tab3:
            raw_data = st.session_state.raw_data
            
            # 數據摘要
            st.markdown("### 📊 數據摘要")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("數據筆數", len(raw_data))
            with col2:
                st.metric("最高價", f"${raw_data['high'].max():.2f}")
            with col3:
                st.metric("最低價", f"${raw_data['low'].min():.2f}")
            with col4:
                st.metric("日期範圍", 
                         f"{raw_data.index[0].strftime('%Y-%m-%d')} ~ {raw_data.index[-1].strftime('%Y-%m-%d')}")
            
            st.divider()
            
            # 完整數據表格
            st.markdown("### 📈 完整歷史數據")
            st.dataframe(
                raw_data,
                use_container_width=True,
                height=400
            )
            
            # 匯出功能
            csv_data = raw_data.to_csv(encoding='utf-8-sig')
            filename_data = f"{st.session_state.symbol}_data_{datetime.now().strftime('%Y%m%d')}.csv"
            
            st.download_button(
                label="📥 下載完整數據 (CSV)",
                data=csv_data,
                file_name=filename_data,
                mime="text/csv"
            )


if __name__ == "__main__":
    main()
```

---

## 🤖 AI 轉換提示語模板

當您需要 AI 將 Pine Script 策略轉換為 Python 程式時，請使用以下完整提示語：

```
請根據「Pine Script 策略轉換系統 規格說明書」，將以下 TradingView 策略轉換為完整的 Python Streamlit 應用程式。

## 策略資訊

**策略名稱**: [填入策略的中文名稱]
**策略來源**: [填入 TradingView 完整 URL]
**Pine Script 版本**: [填入版本號，如 @version=6]

## Pine Script 完整程式碼

[貼上完整的 Pine Script 程式碼]
```

## 轉換要求

### 第一階段：策略理解與說明
請先用繁體中文詳細說明：

1. **核心概念** (2-3 段文字)
   - 用簡單易懂的方式說明策略的基本原理
   - 說明策略的設計思路和目的

2. **技術指標清單** (條列式)
   - 列出所有使用的技術指標及其參數

3. **買入條件** (具體明確)
   - 清楚說明觸發買入信號的條件

4. **賣出條件** (具體明確)
   - 清楚說明觸發賣出信號的條件

5. **適用場景**
   - 說明策略適合什麼類型的市場環境

6. **風險提示**
   - 說明策略可能的限制和風險

### 第二階段：Python 程式碼生成
基於上述理解，生成符合「Python 程式碼標準架構」的完整 app.py 檔案。

**必須遵守的技術限制**:
- 只能使用規格書中列出的 Python 模組
- 所有技術指標使用 pandas 和 numpy 實現，不使用 ta-lib
- 單一檔案包含所有功能
- 遵循規格書定義的程式碼結構

**必須實現的功能**:
- FMP API 數據獲取
- 技術指標計算
- 買賣信號產生
- Streamlit UI 界面
- 錯誤處理和驗證
- 結果表格展示
- CSV 匯出功能

請生成完整可執行的 Python 程式碼。
```

---

## 📊 品質標準

### 功能品質標準
- 所有主要功能都要能穩定運作
- 數據處理要準確可靠，與 Pine Script 邏輯一致
- 信號產生要正確，與 TradingView 結果對應
- 用戶操作要流暢無阻礙

### 界面品質標準
- 版面配置要合理美觀
- 文字要清晰易讀
- 操作要直觀簡單
- 錯誤提示要友善有用

### 效能品質標準
- 數據處理在 10 秒內完成
- 支援至少 1000 筆歷史數據
- 頁面載入順暢

### 安全品質標準
- API Key 安全處理
- 輸入驗證完整
- 錯誤處理妥善

---

## ✅ AI 實作檢查清單

程式碼生成後，請確認以下項目：

### 程式碼結構
- [ ] 單一 app.py 檔案包含所有功能
- [ ] 按照 7 個區塊組織程式碼
- [ ] 所有區塊都有清楚的註釋標記

### 策略說明
- [ ] 檔案開頭有完整的策略說明註釋
- [ ] 包含核心概念、技術指標、買賣條件等所有必要說明
- [ ] 使用繁體中文撰寫

### 技術實現
- [ ] 只使用允許的 Python 模組
- [ ] 所有技術指標使用 pandas/numpy 實現
- [ ] 買賣信號邏輯正確
- [ ] FMP API 整合完整

### UI 功能
- [ ] 側邊欄包含所有必要輸入項
- [ ] 三個 Tab 頁籤功能完整
- [ ] 錯誤處理和驗證完善
- [ ] 免責聲明顯示清楚

### 輸出格式
- [ ] 信號表格包含必要欄位
- [ ] 支援 CSV 匯出
- [ ] 數據格式正確（日期、小數位數等）

### 品質標準
- [ ] 程式碼有適當的註釋
- [ ] 變數命名清晰
- [ ] 錯誤處理完整
- [ ] 可以直接執行

---

## AI 最終實作指令

**請根據以上完整規格說明書和提供的策略資訊，生成一個完整可運行的 Python Streamlit 應用程式（app.py）。**

程式必須：
1. 完全符合「Python 程式碼標準架構」模板
2. 只使用允許的 Python 模組
3. 包含完整的策略說明註釋（繁體中文）
4. 實現所有必要功能（F-001 到 F-008）
5. 滿足所有品質標準
6. 可以直接用 `streamlit run app.py` 執行

**交付物**: 一個完整的 app.py 檔案，包含所有必要的程式碼和註釋，可以立即部署使用。