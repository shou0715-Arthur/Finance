# AI投資組合壓力測試系統 規格說明書

> **用途說明**: 本規格說明書作為AI提示語使用,將此完整內容提交給AI,AI將根據規格生成完整的應用程式碼。

## 📋 系統概述

### 系統名稱
【Code Gym】AI投資組合壓力測試系統

### 核心功能描述
建立一個基於網頁的投資組合壓力測試應用,能夠:
1. 上傳CSV格式的投資組合持股資料(股票代碼、持股數量、購入成本)
2. 選擇7種歷史市場危機情境進行壓力測試(含AI自訂黑天鵝模式)
3. 基於歷史數據、Beta值、波動率計算混合式壓力測試影響
4. 從Financial Modeling Prep API獲取即時股價、公司資料、歷史數據
5. 使用AI生成專業的風險分析報告,評估投資組合在極端情境下的表現
6. 提供互動式視覺化圖表,展示投資組合暴露度和個股表現

### 技術架構要求
- **界面框架**: 使用 Streamlit 框架
- **數據來源**: Financial Modeling Prep API (新版 /stable/ 端點)
- **AI 模型**: OpenAI
- **AI 模型版本**: gpt-5-mini
- **視覺化工具**: 互動式圖表 (使用 Plotly Graph Objects)
- **數據處理**: Pandas, NumPy
- **HTTP請求**: requests
- **日期處理**: datetime
- **部署方式**: 可直接在瀏覽器中運行

### 重要套件版本要求
- **OpenAI套件**: 使用 openai 版本 1.0.0 或以上的新API格式
- **禁用舊版API**: 絕對不可使用 ChatCompletion.create 舊格式
- **必須使用新格式**: 使用 OpenAI 客戶端初始化方式和 chat.completions.create 方法

## 🎯 功能需求規格

### F-001: 用戶界面設計
**基本要求**: 
- 頁面配置: `st.set_page_config(page_title="AI投資組合壓力測試系統", page_icon="📊", layout="wide")`
- 頁面標題: "🎯 AI投資組合壓力測試系統",使用 `st.title()` 和 `st.markdown("---")`
- 左側控制區 (`st.sidebar`) 包含:
  - **投資組合設定區塊** (`st.header("📝 投資組合設定")`)
    - CSV範例檔案下載按鈕: "📥 下載CSV範例檔案"
    - CSV格式說明: `st.info("**CSV格式**:股票代碼,持股數量,購入成本(無需標題列)")`
    - CSV上傳區: `st.file_uploader("上傳投資組合CSV", type=['csv'])`
  
  - **壓力測試情境區塊** (`st.header("🎯 壓力測試情境")`)
    - 情境選擇下拉選單: 顯示7個情境的圖示+名稱
    - 情境詳情展開區: 使用 `st.expander("📖 歷史事件詳情", expanded=True)` 顯示歷史事件和描述
    - 黑天鵝自訂文字區: 僅在選擇黑天鵝模式時顯示,`st.text_area()` 讓用戶輸入自訂情境
    - 進階參數調整: `st.expander("⚙️ 進階參數調整", expanded=False)` 包含嚴重度滑桿(0.5-2.0)
  
  - **API設定區塊** (`st.header("🔑 API設定")`)
    - FMP API Key輸入: `st.text_input("FMP API Key", type="password")`
    - OpenAI API Key輸入: `st.text_input("OpenAI API Key", type="password")`
  
  - **執行按鈕**: `st.button("🚀 執行壓力測試", type="primary", use_container_width=True)`
  - **免責聲明**: 使用 `st.caption()` 顯示免責聲明

### F-002: CSV投資組合上傳與驗證
**功能目標**: 讓用戶上傳投資組合CSV檔案,系統自動驗證格式

**CSV格式要求**:
- **無標題列**: CSV檔案不包含標題行
- **三欄格式**: 股票代碼,持股數量,購入成本
- **範例內容**:
```
AAPL,100,150.50
MSFT,50,300.20
TSLA,30,250.00
JPM,200,140.00
JNJ,150,160.00
```

**範例檔案下載功能**:
```python
sample_csv = """AAPL,100,150.50
MSFT,50,300.20
TSLA,30,250.00
JPM,200,140.00
JNJ,150,160.00"""

st.download_button(
    label="📥 下載CSV範例檔案",
    data=sample_csv,
    file_name="portfolio_example.csv",
    mime="text/csv",
    use_container_width=True
)
```

**CSV讀取與驗證**:
```python
portfolio_df = pd.read_csv(uploaded_file, header=None, names=['symbol', 'quantity', 'cost'])
```

**驗證後展示**:
- 使用 `st.success(f"✅ 已載入 {len(portfolio_df)} 檔股票")`
- 使用 `st.expander("📋 查看上傳的投資組合", expanded=True)` 展示DataFrame

### F-003: 歷史情境模板系統
**功能目標**: 提供7種預設的歷史市場危機情境,每個情境包含11個產業的影響係數

**情境模板數據結構**: 使用Python字典 `SCENARIO_TEMPLATES`,每個情境包含:
- `name`: 情境名稱
- `historical_event`: 歷史事件標題
- `description`: 歷史影響摘要(Markdown格式)
- `icon`: 情境圖示emoji
- `market_benchmark`: 包含 `sp500_change` 和 `duration_weeks`
- `sector_impacts`: 11個產業的影響係數字典
- `custom_mode`: (僅黑天鵝模式) 布林值,啟用AI自訂功能

**11個標準產業分類**:
1. Energy (能源)
2. Technology (科技)
3. Financial Services (金融服務)
4. Industrials (工業)
5. Consumer Cyclical (非必需消費品)
6. Consumer Defensive (必需消費品)
7. Healthcare (醫療保健)
8. Communication Services (通訊服務)
9. Utilities (公用事業)
10. Real Estate (房地產)
11. Basic Materials (基礎材料)

**情境1: 俄烏戰爭 2022**
```python
"俄烏戰爭_2022": {
    "name": "地緣政治衝突(參考:2022俄烏戰爭)",
    "historical_event": "2022年2月俄羅斯入侵烏克蘭",
    "description": """
    **歷史影響摘要:**
    - 標普500在3-4週內下跌約10-12%
    - 能源股因油價飆升而上漲25%
    - 科技股下跌18%,金融股下跌15%
    - 工業股下跌12%
    """,
    "icon": "⚔️",
    "market_benchmark": {
        "sp500_change": -0.12,
        "duration_weeks": 4
    },
    "sector_impacts": {
        "Energy": 0.25,
        "Technology": -0.18,
        "Financial Services": -0.15,
        "Industrials": -0.12,
        "Communication Services": -0.14,
        "Consumer Cyclical": -0.16,
        "Real Estate": -0.10,
        "Utilities": -0.02,
        "Consumer Defensive": -0.05,
        "Healthcare": -0.03,
        "Basic Materials": -0.11
    }
}
```

**情境2: 油價崩盤 2020**
```python
"油價崩盤_2020": {
    "name": "油價崩盤(參考:2020年COVID衝擊)",
    "historical_event": "2020年3月COVID-19疫情 + 油價暴跌",
    "description": """
    **歷史影響摘要:**
    - 標普500在4-5週內暴跌34%
    - 能源股崩盤50%(石油服務業-77%)
    - 房地產下跌72%,酒店娛樂下跌70%
    - 科技股相對抗跌,下跌20%
    """,
    "icon": "🛢️",
    "market_benchmark": {
        "sp500_change": -0.34,
        "duration_weeks": 5
    },
    "sector_impacts": {
        "Energy": -0.50,
        "Real Estate": -0.72,
        "Consumer Cyclical": -0.40,
        "Financial Services": -0.35,
        "Industrials": -0.30,
        "Basic Materials": -0.28,
        "Technology": -0.20,
        "Communication Services": -0.18,
        "Healthcare": -0.15,
        "Utilities": -0.08,
        "Consumer Defensive": 0.05
    }
}
```

**情境3: 激進升息 2022**
```python
"激進升息_2022": {
    "name": "激進升息週期(參考:2022年聯準會升息)",
    "historical_event": "2022年聯準會激進升息抗通膨",
    "description": """
    **歷史影響摘要:**
    - 標普500全年下跌18%
    - 科技股NASDAQ暴跌33%
    - 房地產REITs下跌25%
    - 金融股受利差擴大影響相對穩定
    """,
    "icon": "📈",
    "market_benchmark": {
        "sp500_change": -0.18,
        "duration_weeks": 52
    },
    "sector_impacts": {
        "Technology": -0.33,
        "Real Estate": -0.25,
        "Consumer Cyclical": -0.22,
        "Communication Services": -0.20,
        "Industrials": -0.18,
        "Basic Materials": -0.16,
        "Healthcare": -0.10,
        "Financial Services": -0.08,
        "Consumer Defensive": -0.05,
        "Utilities": 0.02,
        "Energy": 0.65
    }
}
```

**情境4: 金融海嘯 2008**
```python
"金融海嘯_2008": {
    "name": "金融危機(參考:2008金融海嘯)",
    "historical_event": "2008年9月雷曼兄弟倒閉引發全球金融危機",
    "description": """
    **歷史影響摘要:**
    - 標普500在4個月內暴跌42%
    - 金融股崩盤55%
    - 房地產下跌48%,非必需消費品下跌50%
    - 必需消費品相對抗跌,僅下跌15%
    """,
    "icon": "💥",
    "market_benchmark": {
        "sp500_change": -0.42,
        "duration_weeks": 16
    },
    "sector_impacts": {
        "Financial Services": -0.55,
        "Consumer Cyclical": -0.50,
        "Real Estate": -0.48,
        "Basic Materials": -0.47,
        "Energy": -0.45,
        "Industrials": -0.42,
        "Technology": -0.40,
        "Communication Services": -0.38,
        "Utilities": -0.30,
        "Healthcare": -0.25,
        "Consumer Defensive": -0.15
    }
}
```

**情境5: 貿易戰 2018**
```python
"貿易戰_2018": {
    "name": "貿易戰(參考:2018美中貿易戰)",
    "historical_event": "2018年Q4美中貿易戰升級",
    "description": """
    **歷史影響摘要:**
    - 標普500在Q4下跌13.5%
    - 工業股下跌18%(供應鏈擔憂)
    - 科技股下跌17%
    - 必需消費品相對抗跌,僅下跌5%
    """,
    "icon": "📊",
    "market_benchmark": {
        "sp500_change": -0.135,
        "duration_weeks": 13
    },
    "sector_impacts": {
        "Consumer Cyclical": -0.20,
        "Energy": -0.21,
        "Industrials": -0.18,
        "Technology": -0.17,
        "Communication Services": -0.15,
        "Basic Materials": -0.14,
        "Financial Services": -0.13,
        "Real Estate": -0.10,
        "Healthcare": -0.06,
        "Consumer Defensive": -0.05,
        "Utilities": 0.03
    }
}
```

**情境6: 全球關稅戰 2025**
```python
"全球關稅戰_2025": {
    "name": "全球關稅戰(參考:2025川普關稅政策)",
    "historical_event": "2025年4月「Liberation Day」全面關稅",
    "description": """
    **歷史影響摘要:**
    - 標普500在宣布前6週內下跌10.1%,政策持續引發震盪
    - 科技股因中國供應鏈依賴受創(Nvidia -4.89%, AMD -7.7%)
    - 汽車業損失慘重(通用汽車單季損失$11億)
    - 4月9日宣布90天暫停,市場單日暴漲9.52%
    - VIX恐慌指數飆升至25,政策不確定性創40年新高
    - 能源類股逆勢上漲(稀土材料股MP Materials +15%)
    """,
    "icon": "🌍",
    "market_benchmark": {
        "sp500_change": -0.10,
        "duration_weeks": 8
    },
    "sector_impacts": {
        "Technology": -0.18,
        "Consumer Cyclical": -0.13,
        "Industrials": -0.11,
        "Communication Services": -0.11,
        "Financial Services": -0.09,
        "Basic Materials": -0.09,
        "Real Estate": -0.07,
        "Healthcare": -0.04,
        "Consumer Defensive": -0.02,
        "Utilities": 0.01,
        "Energy": 0.08
    }
}
```

**情境7: 黑天鵝自訂模式**
```python
"黑天鵝_自訂": {
    "name": "黑天鵝事件(AI自訂參數)",
    "historical_event": "用戶自訂極端情境",
    "description": """
    **使用方式:**
    描述您想模擬的情境(例如:「美國國債違約」),
    AI將分析並建議各產業的影響參數。
    """,
    "icon": "🦢",
    "market_benchmark": {
        "sp500_change": -0.20,
        "duration_weeks": 4
    },
    "sector_impacts": {},
    "custom_mode": True
}
```

**產業映射表 SECTOR_MAPPING**:
```python
SECTOR_MAPPING = {
    "Consumer Discretionary": "Consumer Cyclical",
    "Consumer Staples": "Consumer Defensive",
    "Information Technology": "Technology",
    "Health Care": "Healthcare",
    "Communication Services": "Communication Services",
    "Financials": "Financial Services",
    "Financial Services": "Financial Services",
    "Industrials": "Industrials",
    "Real Estate": "Real Estate",
    "Utilities": "Utilities",
    "Energy": "Energy",
    "Materials": "Basic Materials",
    "Basic Materials": "Basic Materials"
}
```

### F-004: Financial Modeling Prep API整合
**功能目標**: 從FMP API獲取股票的即時報價、公司資料、歷史數據和關鍵指標

**API端點規格** (所有端點使用 /stable/ 路徑):

**1. 獲取即時報價 (get_fmp_quote)**
- **端點**: `https://financialmodelingprep.com/stable/quote?symbol={symbol}&apikey={api_key}`
- **方法**: GET
- **參數**: 
  - symbol: 股票代碼
  - apikey: FMP API金鑰
- **回傳**: JSON陣列,取第一個元素
- **需要欄位**: `price` (當前股價)
- **錯誤處理**: 
  - 超時10秒
  - 回傳None時顯示錯誤訊息
  - 捕獲所有異常

**2. 獲取公司基本資料 (get_fmp_profile)**
- **端點**: `https://financialmodelingprep.com/stable/profile?symbol={symbol}&apikey={api_key}`
- **方法**: GET
- **參數**: 
  - symbol: 股票代碼
  - apikey: FMP API金鑰
- **回傳**: JSON陣列,取第一個元素
- **需要欄位**: `sector` (產業分類)
- **產業映射**: 使用 `map_sector()` 函數將FMP產業名稱映射到11個標準產業
- **錯誤處理**: 同上

**3. 獲取歷史股價數據 (get_fmp_historical)**
- **端點**: `https://financialmodelingprep.com/stable/historical-price-eod/full?symbol={symbol}&apikey={api_key}`
- **方法**: GET
- **參數**: 
  - symbol: 股票代碼
  - apikey: FMP API金鑰
- **回傳**: JSON陣列,包含歷史日線數據
- **數據處理**:
  - 轉換為Pandas DataFrame
  - 將date欄位轉換為datetime格式
  - 按日期排序
  - 只取最近252個交易日(約1年)
- **需要欄位**: `date`, `close` (收盤價)
- **用途**: 計算歷史波動率
- **錯誤處理**: 同上

**4. 獲取關鍵財務指標 (get_fmp_key_metrics)**
- **端點**: `https://financialmodelingprep.com/stable/key-metrics?symbol={symbol}&apikey={api_key}`
- **方法**: GET
- **參數**: 
  - symbol: 股票代碼
  - apikey: FMP API金鑰
- **回傳**: JSON陣列,取第一個元素
- **需要欄位**: `beta` (Beta係數)
- **預設值**: 如果無Beta值,使用1.0
- **錯誤處理**: 同上

### F-005: 壓力測試計算引擎
**功能目標**: 基於歷史數據、Beta值和波動率,計算每檔股票在特定情境下的預測影響

**計算流程**:

**1. 年化波動率計算 (calculate_volatility)**
```python
def calculate_volatility(historical_df):
    """計算年化波動率"""
    if historical_df is None or len(historical_df) < 30:
        return 0.20  # 預設20%
    
    # 計算日收益率
    returns = historical_df['close'].pct_change().dropna()
    
    # 計算年化標準差(假設252個交易日)
    daily_volatility = returns.std()
    annual_volatility = daily_volatility * np.sqrt(252)
    
    return annual_volatility
```

**2. 混合式壓力測試影響計算 (calculate_stress_impact)**
```python
def calculate_stress_impact(sector_impact, beta, volatility, severity):
    """
    混合式計算壓力測試影響
    
    參數:
    - sector_impact: 該產業的歷史影響(例如:-0.18)
    - beta: 該股票的Beta值
    - volatility: 該股票的歷史波動率
    - severity: 用戶設定的嚴重度係數(0.5-2.0)
    """
    # 步驟1: 基於歷史數據的基礎影響
    base_impact = sector_impact * severity
    
    # 步驟2: Beta調整
    beta_adjusted_impact = base_impact * beta
    
    # 步驟3: 波動率調整
    volatility_adjustment = 1 + (volatility * 0.1)
    
    # 步驟4: 最終影響
    final_impact = beta_adjusted_impact * volatility_adjustment
    
    return final_impact
```

**計算邏輯說明**:
- **基礎影響**: 產業歷史影響 × 嚴重度係數
- **Beta調整**: 考慮個股對市場的敏感度
- **波動率調整**: 高波動股票在壓力情境下影響更大
- **最終影響**: 綜合三個因素的混合結果

**3. 預測價格和損益計算**
```python
predicted_price = current_price * (1 + final_impact)
current_value = current_price * quantity
predicted_value = predicted_price * quantity
pnl = predicted_value - current_value  # 壓力測試後的市值變化
change_pct = final_impact * 100  # 百分比變化
```

**4. 風險評級標準**
- **低風險**: 損失 < 5%
- **中風險**: 損失 5-15%
- **高風險**: 損失 > 15%

### F-006: 黑天鵝AI情境生成功能
**功能目標**: 當用戶選擇黑天鵝模式並輸入自訂情境描述時,使用AI自動生成各產業影響參數

**AI情境生成函數 (generate_ai_scenario)**

**輸入**:
- `scenario_description`: 用戶輸入的情境描述(例如:"美國國債違約")
- `openai_api_key`: OpenAI API金鑰

**OpenAI API調用設定**:
- **模型**: gpt-5-mini
- **方法**: client.chat.completions.create()
- **溫度**: 預設值

**完整AI提示語**:
```python
prompt = f"""
你是一位專業的金融風險分析師。用戶描述了一個極端市場情境:

"{scenario_description}"

請分析這個情境對各產業的影響,並以JSON格式輸出。

輸出格式(純JSON,不要包含任何其他文字或markdown標記):
{{
  "scenario_name": "情境名稱",
  "description": "情境詳細說明(2-3句話)",
  "sp500_impact": -0.25,
  "duration_weeks": 8,
  "sector_impacts": {{
    "Energy": -0.20,
    "Technology": -0.30,
    "Financial Services": -0.35,
    "Industrials": -0.25,
    "Consumer Cyclical": -0.28,
    "Consumer Defensive": -0.10,
    "Healthcare": -0.15,
    "Communication Services": -0.25,
    "Utilities": -0.12,
    "Real Estate": -0.30,
    "Basic Materials": -0.22
  }},
  "reasoning": "簡要說明各產業受影響的原因"
}}

重要:
1. sector_impacts的值範圍應在-0.60到+0.40之間
2. 必須包含所有11個產業(Energy, Technology, Financial Services, Industrials, Consumer Cyclical, Consumer Defensive, Healthcare, Communication Services, Utilities, Real Estate, Basic Materials)
3. 只輸出JSON,不要有其他內容
"""
```

**JSON解析與錯誤處理**:
```python
try:
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    
    result_text = response.choices[0].message.content.strip()
    # 移除可能的markdown標記
    result_text = result_text.replace("```json", "").replace("```", "").strip()
    
    result = json.loads(result_text)
    return result
except Exception as e:
    st.error(f"AI生成情境失敗: {str(e)}")
    return None
```

**情境模板更新**:
```python
# 更新情境模板
selected_scenario['description'] = ai_scenario['description']
selected_scenario['sector_impacts'] = ai_scenario['sector_impacts']
selected_scenario['market_benchmark']['sp500_change'] = ai_scenario['sp500_impact']
```

### F-007: AI風險分析報告生成
**功能目標**: 基於壓力測試結果,使用AI生成專業的風險分析報告

**AI分析報告函數 (generate_ai_analysis)**

**輸入數據準備**:
```python
total_original = portfolio_results['total_original_value']
total_predicted = portfolio_results['total_predicted_value']
total_change_pct = portfolio_results['total_change_pct']
holdings_df = portfolio_results['holdings_df']

# 準備詳細持股數據
holdings_summary = "\n".join([
    f"- {row['symbol']} ({row['sector']}): "
    f"當前${row['current_price']:.2f} → 預測${row['predicted_price']:.2f} "
    f"({row['change_pct']:+.2f}%) | "
    f"Beta={row['beta']:.2f}, 波動率={row['volatility']:.1%}"
    for _, row in holdings_df.iterrows()
])

# 計算產業分布
sector_exposure = holdings_df.groupby('sector')['current_value'].sum()
sector_summary = "\n".join([
    f"- {sector}: ${value:,.2f} ({value/total_original*100:.1f}%)"
    for sector, value in sector_exposure.items()
])

# 風險評級標準
risk_level = "低風險" if abs(total_change_pct) < 5 else "中風險" if abs(total_change_pct) < 15 else "高風險"
```

**完整AI分析提示語**:
```python
prompt = f"""
你是一位資深的量化風險分析師,專精於投資組合壓力測試與風險評估。請針對以下壓力測試結果,提供一份**詳細且深度的風險分析報告**(目標2000字以上)。

**重要準則:**
1. **絕對禁止**提供具體的投資建議(如:應買入、賣出、減碼、加碼、持有等操作建議)
2. 報告應**聚焦於風險識別、風險量化、脆弱性分析**
3. 使用專業金融術語,目標讀者為有經驗的投資者
4. 保持客觀中立,基於數據分析而非主觀判斷
5. 深入分析風險傳導路徑和潛在連鎖效應

---

## 情境背景
{scenario_info['description']}

標普500預期影響:{scenario_info['market_benchmark']['sp500_change']*100:.1f}%
影響持續時間:約{scenario_info['market_benchmark']['duration_weeks']}週

---

## 投資組合壓力測試結果

### 整體指標
- 原始市值:${total_original:,.2f}
- 壓力測試後市值:${total_predicted:,.2f}
- 預估變化:{total_change_pct:+.2f}%
- 風險初步評級:{risk_level}

### 產業配置分布
{sector_summary}

### 個股壓力測試結果
{holdings_summary}

---

## 報告要求

請以Markdown格式輸出,包含以下章節:

### 📋 執行摘要(Executive Summary)
[50-80字的精煉總結,直接點出核心風險與投資組合在此情境下的主要脆弱點]

### 🎯 投資組合韌性評估(Portfolio Resilience Assessment)

#### 整體風險量化
- **風險評級**:[根據損失幅度評定:損失<5%為低風險,5-15%為中風險,>15%為高風險]
- **預估最大損失**:[具體金額與百分比]
- **風險集中度分析**:[指出哪些產業或個股佔據主要風險敞口]

#### 脆弱性分析
- **最脆弱部位識別**:[列出受創最嚴重的前3-5個持股,說明其脆弱的結構性原因]
- **產業層面風險**:[分析哪些產業在此情境下風險最高,原因為何]
- **Beta與波動率分析**:[評估高Beta或高波動個股對整體風險的貢獻]

#### 相對抗跌部位
- [指出表現相對穩健的持股,分析其抗跌特性的來源]

### 📊 情境風險傳導分析(Risk Transmission Analysis)

#### 一階效應(Direct Impact)
- [分析情境對各產業的直接衝擊機制]
- [說明為何某些產業受創特別嚴重]

#### 二階效應(Cascading Risk)
- [探討可能的連鎖反應和間接影響]
- [評估產業間的風險關聯性]
- [分析是否存在系統性風險放大因子]

#### 尾部風險評估(Tail Risk)
- [評估極端情境下的潛在損失]
- [指出可能被低估的風險點]

### 🔍 關鍵風險因子深度剖析(Deep Dive on Risk Factors)

#### 市場風險
- [分析Beta暴露和市場系統性風險]
- [評估與標普500相關性]

#### 產業集中風險
- [量化產業集中度]
- [分析產業配置對整體風險的影響]

#### 個股特定風險
- [深入分析風險最高的2-3檔個股]
- [探討公司基本面、財務槓桿、競爭地位等因素]

#### 流動性風險
- [評估壓力情境下的變現難易度]
- [考慮波動率對交易執行的影響]

### 📉 歷史回測與壓力測試假設(Backtesting & Stress Test Assumptions)

#### 模型假設與限制
- [說明壓力測試採用的方法論]
- [討論Beta、波動率等參數的局限性]
- [指出歷史數據可能無法預測未來的原因]

#### 情境設定合理性
- [評估選定情境的代表性]
- [討論實際情況可能更嚴重或較溫和的可能性]

### 🎓 投資組合特性總結(Portfolio Characteristics Summary)

#### 風險特徵
- [總結投資組合的核心風險特徵]
- [指出在其他市場情境下可能表現如何]

#### 多元化程度
- [評估投資組合的分散化水平]
- [討論是否有過度集中於特定主題或因子]

---

**輸出要求:**
1. 使用Markdown格式,包含適當的標題層級
2. 每個章節都要有實質內容,避免空泛描述
3. 引用具體數字和數據支撐論點
4. 保持專業客觀的分析語氣
5. 篇幅至少2000字,深入而非表面分析
6. **絕對不要提供任何操作建議或投資決策指引**
"""
```

**OpenAI API調用**:
```python
client = OpenAI(api_key=openai_api_key)

try:
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content
except Exception as e:
    return f"❌ AI分析生成失敗: {str(e)}\n\n請檢查 OpenAI API Key 是否正確,或稍後再試。"
```

### F-008: 視覺化圖表系統
**功能目標**: 提供3個互動式視覺化圖表,展示投資組合分析結果

**圖表1: 投資組合產業配置圓餅圖**
- **函數名稱**: create_sector_pie_chart()
- **圖表類型**: Plotly Graph Objects Pie Chart
- **數據來源**: 按產業分組的持股市值總和
- **配色方案**: Plotly預設配色
- **顯示內容**:
  - 扇形標籤: 產業名稱
  - 數值: 市值金額和百分比
  - 懸停資訊: 產業名稱、市值、佔比
- **圖表設定**:
  - `hole=0.3` (甜甜圈圖)
  - 標題: "投資組合產業配置"
  - 高度: 400px

**圖表2: 個股壓力測試表現條狀圖**
- **函數名稱**: create_performance_bar_chart()
- **圖表類型**: Plotly Graph Objects Bar Chart (水平)
- **數據來源**: 每檔股票的變化百分比
- **配色方案**:
  - 正值(上漲): 綠色 `#26a69a`
  - 負值(下跌): 紅色 `#ef5350`
- **顯示內容**:
  - X軸: 變化百分比
  - Y軸: 股票代碼
  - 懸停資訊: 股票代碼、變化百分比、產業
- **圖表設定**:
  - 按變化百分比排序(由低到高)
  - 標題: "個股壓力測試表現"
  - 高度: 600px

**圖表3: 投資組合價值變化堆疊條狀圖**
- **函數名稱**: create_portfolio_value_chart()
- **圖表類型**: Plotly Graph Objects Bar Chart (堆疊)
- **數據來源**: 原始市值 vs 壓力測試後市值
- **配色方案**:
  - 原始市值: 藍色 `#1f77b4`
  - 壓力測試後市值: 橙色 `#ff7f0e`
- **顯示內容**:
  - X軸: ["原始投資組合", "壓力測試後"]
  - Y軸: 市值金額
  - 懸停資訊: 市值金額
- **圖表設定**:
  - 標題: "投資組合價值變化"
  - 高度: 400px
  - Y軸格式: 貨幣格式

**通用圖表設定**:
```python
layout = dict(
    template="plotly_white",
    hovermode="closest",
    showlegend=True,
    font=dict(family="Microsoft JhengHei, Arial", size=12)
)
```

### F-009: 結果展示頁籤系統
**功能目標**: 使用Streamlit頁籤組織展示分析結果

**頁籤結構**:
```python
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 投資組合總覽",
    "📈 視覺化圖表", 
    "📋 詳細持股分析",
    "🤖 AI風險分析報告"
])
```

**頁籤1: 投資組合總覽**
- **整體績效指標**: 使用 `st.columns(4)` 並排顯示4個指標
  - 原始市值
  - 壓力測試後市值
  - 預估變化金額
  - 預估變化百分比
- **風險評級**: 大字體顯示風險等級,配色:
  - 低風險: 綠色
  - 中風險: 橙色
  - 高風險: 紅色
- **情境資訊**: 顯示選定的情境名稱和描述

**頁籤2: 視覺化圖表**
- 產業配置圓餅圖
- 個股表現條狀圖
- 投資組合價值變化圖
- 使用 `st.plotly_chart()` 展示,設定 `use_container_width=True`

**頁籤3: 詳細持股分析**
- **持股明細表**: 使用 `st.dataframe()` 展示完整的holdings_df
- **欄位**:
  - 股票代碼
  - 產業
  - 持股數量
  - 當前價格
  - 預測價格
  - 變化百分比
  - Beta值
  - 波動率
  - 當前市值
  - 預測市值
  - 預估損益
- **格式化**:
  - 貨幣欄位顯示$符號
  - 百分比欄位顯示%符號
  - 數值右對齊

**頁籤4: AI風險分析報告**
- 顯示AI生成的完整Markdown報告
- 使用 `st.markdown()` 渲染
- 包含所有章節和分析內容

**排除股票警告**:
- 如果有股票因數據不足被排除,在主要內容區顯示警告訊息
- 使用 `st.warning()` 列出排除的股票和原因

## 🔧 核心函數實施要求

### 數據處理函數

**1. map_sector(fmp_sector)**
- **功能**: 將FMP回傳的產業名稱映射到11個標準產業
- **輸入**: FMP產業名稱(字串)
- **輸出**: 標準產業名稱(字串)
- **邏輯**: 使用SECTOR_MAPPING字典查找,找不到則回傳原始名稱

**2. calculate_volatility(historical_df)**
- **功能**: 計算股票的年化波動率
- **輸入**: 包含歷史收盤價的DataFrame
- **輸出**: 年化波動率(浮點數)
- **邏輯**:
  - 計算日收益率: pct_change()
  - 計算日波動率: std()
  - 年化: 日波動率 × √252
- **預設值**: 如果數據不足30天,回傳0.20 (20%)

**3. calculate_stress_impact(sector_impact, beta, volatility, severity)**
- **功能**: 計算混合式壓力測試影響
- **輸入**:
  - sector_impact: 產業影響係數
  - beta: Beta值
  - volatility: 波動率
  - severity: 嚴重度係數
- **輸出**: 最終影響係數(浮點數)
- **邏輯**: 見F-005詳細說明

### API函數

**4. get_fmp_quote(symbol, api_key)**
- **端點**: /stable/quote
- **超時**: 10秒
- **錯誤處理**: 捕獲異常並顯示st.error()
- **回傳**: 字典或None

**5. get_fmp_profile(symbol, api_key)**
- **端點**: /stable/profile
- **超時**: 10秒
- **錯誤處理**: 同上
- **回傳**: 字典或None

**6. get_fmp_historical(symbol, api_key)**
- **端點**: /stable/historical-price-eod/full
- **超時**: 10秒
- **數據處理**: 轉DataFrame → 轉datetime → 排序 → 取最近252天
- **錯誤處理**: 同上
- **回傳**: DataFrame或None

**7. get_fmp_key_metrics(symbol, api_key)**
- **端點**: /stable/key-metrics
- **超時**: 10秒
- **錯誤處理**: 同上
- **回傳**: 字典或None

### AI函數

**8. generate_ai_scenario(scenario_description, openai_api_key)**
- **功能**: AI生成自訂情境參數
- **模型**: gpt-5-mini
- **輸入**: 情境描述字串
- **輸出**: 包含情境參數的字典
- **提示語**: 見F-006完整提示語
- **錯誤處理**: JSON解析失敗時顯示錯誤並回傳None

**9. generate_ai_analysis(portfolio_results, scenario_info, openai_api_key)**
- **功能**: AI生成風險分析報告
- **模型**: gpt-5-mini
- **輸入**: 投資組合結果和情境資訊
- **輸出**: Markdown格式的分析報告(字串)
- **提示語**: 見F-007完整提示語
- **錯誤處理**: API失敗時回傳錯誤訊息字串

### 視覺化函數

**10. create_sector_pie_chart(holdings_df)**
- **輸入**: 持股DataFrame
- **處理**: 按產業分組並計算市值總和
- **輸出**: Plotly圖表物件
- **設定**: 見F-008圖表1規格

**11. create_performance_bar_chart(holdings_df)**
- **輸入**: 持股DataFrame
- **處理**: 按變化百分比排序
- **輸出**: Plotly圖表物件
- **設定**: 見F-008圖表2規格

**12. create_portfolio_value_chart(total_original, total_predicted)**
- **輸入**: 原始市值和預測市值
- **輸出**: Plotly圖表物件
- **設定**: 見F-008圖表3規格

## 📐 主程式流程規格

### 初始化階段
```python
st.set_page_config(
    page_title="AI投資組合壓力測試系統",
    page_icon="📊",
    layout="wide"
)

st.title("🎯 AI投資組合壓力測試系統")
st.markdown("---")
```

### 側邊欄設定階段
1. 顯示投資組合設定區
2. 提供CSV範例下載
3. CSV上傳介面
4. 情境選擇下拉選單
5. 黑天鵝自訂文字區(條件顯示)
6. 進階參數調整(嚴重度滑桿)
7. API金鑰輸入
8. 執行按鈕
9. 免責聲明

### 主內容區初始狀態
- 如果未上傳CSV: 顯示操作說明,然後 `st.stop()`
- 如果已上傳CSV: 顯示投資組合預覽

### 執行壓力測試流程
**觸發**: 點擊"執行壓力測試"按鈕

**步驟1: API金鑰驗證**
```python
if not fmp_api_key:
    st.error("❌ 請輸入FMP API Key")
    st.stop()

if not openai_api_key:
    st.error("❌ 請輸入OpenAI API Key")
    st.stop()
```

**步驟2: 處理黑天鵝自訂模式**
```python
if selected_scenario.get("custom_mode"):
    if not custom_scenario_desc:
        st.error("❌ 請描述您想模擬的黑天鵝情境")
        st.stop()
    
    with st.spinner("🤖 AI正在分析自訂情境..."):
        ai_scenario = generate_ai_scenario(custom_scenario_desc, openai_api_key)
        
        if ai_scenario:
            st.success("✅ AI情境生成成功")
            # 更新情境模板
            selected_scenario['description'] = ai_scenario['description']
            selected_scenario['sector_impacts'] = ai_scenario['sector_impacts']
            selected_scenario['market_benchmark']['sp500_change'] = ai_scenario['sp500_impact']
            
            # 顯示AI生成的參數
            with st.expander("🔍 查看AI生成的情境參數", expanded=True):
                st.markdown(f"**情境名稱**: {ai_scenario['scenario_name']}")
                st.markdown(f"**說明**: {ai_scenario['description']}")
                st.markdown(f"**AI分析**: {ai_scenario['reasoning']}")
        else:
            st.error("AI情境生成失敗,請檢查描述或稍後再試")
            st.stop()
```

**步驟3: 獲取所有股票數據**
```python
progress_bar = st.progress(0)
status_text = st.empty()

holdings_data = []
excluded_stocks = []

for idx, row in portfolio_df.iterrows():
    symbol = row['symbol'].strip().upper()
    quantity = row['quantity']
    cost = row['cost']
    
    status_text.text(f"正在處理 {symbol}... ({idx+1}/{len(portfolio_df)})")
    progress_bar.progress((idx + 1) / len(portfolio_df))
    
    # 獲取數據
    quote = get_fmp_quote(symbol, fmp_api_key)
    profile = get_fmp_profile(symbol, fmp_api_key)
    historical = get_fmp_historical(symbol, fmp_api_key)
    metrics = get_fmp_key_metrics(symbol, fmp_api_key)
    
    # 檢查必要數據
    if not quote or not profile:
        excluded_stocks.append(f"{symbol} (無法獲取基本數據)")
        continue
    
    current_price = quote.get('price', 0)
    sector = profile.get('sector', 'Unknown')
    mapped_sector = map_sector(sector)
    
    # 獲取Beta值
    beta = 1.0  # 預設值
    if metrics and 'beta' in metrics:
        try:
            beta = float(metrics['beta']) if metrics['beta'] else 1.0
        except:
            beta = 1.0
    
    # 檢查產業是否在情境中
    if mapped_sector not in selected_scenario['sector_impacts']:
        excluded_stocks.append(f"{symbol} (產業 '{mapped_sector}' 不在情境模板中)")
        continue
    
    # 計算波動率
    volatility = calculate_volatility(historical)
    
    # 計算壓力測試影響
    sector_impact = selected_scenario['sector_impacts'][mapped_sector]
    final_impact = calculate_stress_impact(sector_impact, beta, volatility, severity)
    
    # 計算預測價格和損益
    predicted_price = current_price * (1 + final_impact)
    current_value = current_price * quantity
    predicted_value = predicted_price * quantity
    pnl = predicted_value - current_value
    change_pct = final_impact * 100
    
    holdings_data.append({
        'symbol': symbol,
        'quantity': quantity,
        'cost': cost,
        'current_price': current_price,
        'predicted_price': predicted_price,
        'sector': mapped_sector,
        'beta': beta,
        'volatility': volatility,
        'sector_impact': sector_impact,
        'final_impact': final_impact,
        'current_value': current_value,
        'predicted_value': predicted_value,
        'pnl': pnl,
        'change_pct': change_pct
    })

progress_bar.empty()
status_text.empty()
```

**步驟4: 檢查是否有有效持股**
```python
if len(holdings_data) == 0:
    st.error("❌ 沒有任何股票通過數據驗證,無法進行分析")
    if excluded_stocks:
        st.warning("排除的股票:")
        for stock in excluded_stocks:
            st.write(f"- {stock}")
    st.stop()
```

**步驟5: 建立結果DataFrame**
```python
holdings_df = pd.DataFrame(holdings_data)

# 計算投資組合總計
total_original_value = holdings_df['current_value'].sum()
total_predicted_value = holdings_df['predicted_value'].sum()
total_pnl = total_predicted_value - total_original_value
total_change_pct = (total_pnl / total_original_value) * 100

portfolio_results = {
    'holdings_df': holdings_df,
    'total_original_value': total_original_value,
    'total_predicted_value': total_predicted_value,
    'total_pnl': total_pnl,
    'total_change_pct': total_change_pct
}
```

**步驟6: 生成AI分析報告**
```python
with st.spinner("🤖 AI正在生成風險分析報告..."):
    ai_report = generate_ai_analysis(
        portfolio_results, 
        selected_scenario, 
        openai_api_key
    )
```

**步驟7: 顯示結果**
- 顯示排除股票警告(如果有)
- 顯示分析結果標題
- 創建4個頁籤並填充內容

### 頁籤內容實施

**頁籤1實施**:
```python
with tab1:
    st.header("📊 投資組合總覽")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("原始市值", f"${total_original_value:,.2f}")
    with col2:
        st.metric("壓力測試後市值", f"${total_predicted_value:,.2f}")
    with col3:
        st.metric("預估變化金額", f"${total_pnl:,.2f}", delta=f"{total_change_pct:+.2f}%")
    with col4:
        risk_level = "低風險" if abs(total_change_pct) < 5 else "中風險" if abs(total_change_pct) < 15 else "高風險"
        risk_color = "🟢" if abs(total_change_pct) < 5 else "🟠" if abs(total_change_pct) < 15 else "🔴"
        st.metric("風險評級", f"{risk_color} {risk_level}")
    
    st.markdown("---")
    st.subheader(f"{selected_scenario['icon']} {selected_scenario['name']}")
    st.markdown(selected_scenario['description'])
```

**頁籤2實施**:
```python
with tab2:
    st.header("📈 視覺化圖表")
    
    col1, col2 = st.columns(2)
    with col1:
        sector_chart = create_sector_pie_chart(holdings_df)
        st.plotly_chart(sector_chart, use_container_width=True)
    
    with col2:
        value_chart = create_portfolio_value_chart(total_original_value, total_predicted_value)
        st.plotly_chart(value_chart, use_container_width=True)
    
    st.markdown("---")
    performance_chart = create_performance_bar_chart(holdings_df)
    st.plotly_chart(performance_chart, use_container_width=True)
```

**頁籤3實施**:
```python
with tab3:
    st.header("📋 詳細持股分析")
    
    display_df = holdings_df[[
        'symbol', 'sector', 'quantity', 'current_price', 'predicted_price',
        'change_pct', 'beta', 'volatility', 'current_value', 
        'predicted_value', 'pnl'
    ]].copy()
    
    # 格式化欄位名稱
    display_df.columns = [
        '股票代碼', '產業', '持股數量', '當前價格', '預測價格',
        '變化%', 'Beta值', '波動率', '當前市值', '預測市值', '預估損益'
    ]
    
    st.dataframe(
        display_df.style.format({
            '當前價格': '${:.2f}',
            '預測價格': '${:.2f}',
            '變化%': '{:+.2f}%',
            'Beta值': '{:.2f}',
            '波動率': '{:.1%}',
            '當前市值': '${:,.2f}',
            '預測市值': '${:,.2f}',
            '預估損益': '${:+,.2f}'
        }),
        use_container_width=True,
        height=600
    )
```

**頁籤4實施**:
```python
with tab4:
    st.header("🤖 AI風險分析報告")
    st.markdown(ai_report)
```

## 💡 通用界面設計標準

### 配色方案
- **主色調**: Streamlit預設藍色
- **成功/正值**: 綠色 `#26a69a`
- **警告/中性**: 橙色 `#ff7f0e`
- **錯誤/負值**: 紅色 `#ef5350`
- **資訊**: 藍色 `#1f77b4`

### 字體與排版
- **字體家族**: "Microsoft JhengHei, Arial" (支援中文)
- **標題大小**: 使用Streamlit預設標題大小
- **正文大小**: 12px
- **間距**: 使用 `st.markdown("---")` 作為區段分隔

### 互動元素
- **按鈕**: 使用 `type="primary"` 強調主要操作
- **輸入框**: 密碼欄位使用 `type="password"`
- **進度條**: 使用 `st.progress()` 和 `st.spinner()`
- **展開區**: 使用 `st.expander()` 組織可選內容

### 錯誤處理UI
- **錯誤訊息**: `st.error()` 紅色背景
- **警告訊息**: `st.warning()` 黃色背景
- **資訊訊息**: `st.info()` 藍色背景
- **成功訊息**: `st.success()` 綠色背景

## 💡 通用品質標準

### 功能品質
- **完整性**: 所有功能都必須完整實施,不能有placeholder
- **準確性**: 計算結果必須精確,公式實施正確
- **穩定性**: 能處理各種邊界情況和異常輸入
- **效能**: API調用有超時設定,避免長時間等待

### 界面品質
- **直觀性**: 操作流程清晰,不需要額外說明
- **友善性**: 提供充足的提示和說明文字
- **回饋性**: 所有操作都有明確的視覺回饋
- **一致性**: 界面元素風格統一,符合設計標準

### 程式碼品質
- **可讀性**: 程式碼結構清晰,有適當的註釋
- **可維護性**: 函數功能單一,模組化組織
- **錯誤處理**: 所有可能失敗的操作都有try-except
- **效能優化**: 避免重複計算,合理使用快取

### 安全性
- **API金鑰保護**: 使用password類型輸入,不在程式碼中硬編碼
- **輸入驗證**: 驗證CSV格式和數據有效性
- **錯誤訊息**: 不洩露敏感的系統資訊

## 🎓 免責聲明標準文字

```python
st.caption("### ⚠️ 免責聲明")
st.caption("""
本系統僅供學術研究與教育用途,AI提供的數據與分析結果僅供參考,
**不構成投資建議或財務建議**。請使用者自行判斷投資決策,並承擔相關風險。
本系統作者不對任何投資行為負責,亦不承擔任何損失責任。
""")
```

## AI實作指令

**請根據以上完整規格說明書,生成一個完整可運行的 Streamlit 網頁應用程式。**

### 必要實現要求
1. **完全實現所有功能需求**: 從F-001到F-009的所有功能都必須完整實施
2. **嚴格遵循技術架構要求**: 使用OpenAI新版API格式和FMP /stable/ 端點
3. **實施所有核心功能**: 6個情境模板、混合式計算、AI分析、視覺化
4. **符合專業界面設計標準**: 使用指定的配色方案和圖表樣式
5. **具備風險分析專業水準**: 壓力測試邏輯精確、AI分析客觀深入

### 技術實現要求
- **界面框架**: 使用Streamlit框架建立完整的網頁界面
- **API整合**: 整合FMP /stable/ API和OpenAI API,實施完整錯誤處理
- **AI分析**: 使用OpenAI新版API格式(client.chat.completions.create),模型gpt-5-mini
- **視覺化**: 使用Plotly Graph Objects創建專業圖表,遵循配色方案
- **程式品質**: 程式碼清晰易懂,有適當中文註釋,實施所有必要功能

### 關鍵技術限制和要求
1. **OpenAI API版本限制**: 必須使用客戶端初始化和chat.completions.create方法,禁用舊版格式
2. **FMP API端點要求**: 所有FMP API端點必須使用 /stable/ 路徑
3. **情境模板完整性**: 6個情境的JSON參數必須完全按照規格實施
4. **AI提示語精確性**: AI提示語必須與規格說明書中的一字不差
5. **計算邏輯準確性**: 混合式壓力測試計算必須按照公式精確實施
6. **視覺化專業性**: 使用Plotly Graph Objects,配色符合標準

### 特別注意事項
- 程式必須完整可執行,可直接用 `streamlit run 9-1.py` 運行
- 所有用戶輸入都要有完整驗證和友善錯誤處理
- AI分析內容要客觀專業,聚焦風險識別,避免投資建議
- 界面要直觀易用,符合投資分析專業人士使用習慣
- 免責聲明要清楚顯示,強調系統僅供教育研究用途
- 黑天鵝自訂模式要能正確調用AI並更新情境參數
- 視覺化圖表要美觀專業,符合現代金融分析工具標準
- 進度提示要即時,讓用戶了解系統正在處理

### 程式碼組織要求
1. **導入區塊**: 包含所有必要的套件導入(streamlit, pandas, numpy, plotly, requests, openai, datetime, json, io)
2. **常數定義區塊**: SCENARIO_TEMPLATES字典和SECTOR_MAPPING字典
3. **函數定義區塊**: 按照功能分類組織所有函數(API、計算、視覺化、AI)
4. **主程式區塊**: 
   - 頁面配置設定
   - 側邊欄界面建立
   - 主內容區初始狀態
   - 執行按鈕觸發的完整流程
   - 結果頁籤展示
5. **註釋要求**: 每個重要函數和複雜邏輯都要有清楚的中文說明

### 成功驗收標準
生成的程式必須能夠成功實現:
1. 正確上傳和驗證CSV格式的投資組合
2. 提供6個完整的歷史情境選擇(含黑天鵝自訂)
3. 成功調用FMP /stable/ API獲取股票數據(報價、資料、歷史、指標)
4. 精確計算混合式壓力測試影響(產業×Beta×波動率×嚴重度)
5. 黑天鵝模式能成功調用AI生成自訂情境參數
6. 成功調用OpenAI gpt-5-mini生成專業風險分析報告
7. 生成3個專業視覺化圖表(產業配置、個股表現、價值變化)
8. 展示完整的4個頁籤內容(總覽、圖表、持股、AI報告)
9. 提供流暢的用戶體驗(進度提示、錯誤處理、操作指引)
10. 所有計算邏輯準確,AI分析專業客觀,圖表美觀專業

### 交付物要求
**最終交付物**: 一個完整的Python程式檔案(建議檔名: 9-1.py),包含:
- 所有必要的套件導入語句
- 完整的常數定義(情境模板、產業映射)
- 完整的函數實現(API調用、計算邏輯、視覺化、AI分析)
- 主程式邏輯(界面建立、流程控制、結果展示)
- 適當的中文註釋(解釋關鍵邏輯和計算公式)
- 可直接執行的完整程式碼(無需任何修改即可運行)
- 體現「投資組合壓力測試與風險評估」的核心專業價值