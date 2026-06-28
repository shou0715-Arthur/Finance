# AI投資組合事件提醒系統 規格說明書

> **用途說明**: 本規格說明書作為AI提示語使用，將此完整內容提交給AI，AI將根據規格生成完整的應用程式碼。

## 📋 系統概述

### 系統名稱
【Code Gym】AI投資組合事件提醒系統

### 核心功能描述
建立一個基於網頁的投資組合事件提醒應用，能夠：
1. 上傳CSV格式的投資組合持股資料（股票代碼、持股數量）
2. 自動獲取未來3個月的財報日曆（Earnings Calendar）
3. 可選擇性獲取經濟行事曆（Economic Calendar，需付費訂閱）
4. 使用三層智能匹配邏輯識別與投資組合相關的事件
5. 根據產業、國家、Impact等級進行事件篩選和關聯度評分
6. 使用AI生成智慧提醒，包含異常檢測、密集事件週識別、產業連鎖反應分析
7. 提供事件時間表，標示優先級和倒數天數

### 技術架構要求
- **界面框架**: 使用 Streamlit 框架
- **數據來源**: 
  - Financial Modeling Prep API (新版 /stable/ 端點) - 公司資料、經濟日曆
  - Alpha Vantage API - 財報日曆
- **AI 模型**: OpenAI
- **AI 模型版本**: gpt-5-mini
- **數據處理**: Pandas
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
- 頁面配置: `st.set_page_config(page_title="AI投資組合事件提醒系統", page_icon="🔔", layout="wide")`
- 頁面標題: "🔔 AI投資組合事件提醒系統"，使用 `st.title()` 和 `st.markdown("---")`
- 左側控制區 (`st.sidebar`) 包含：
  - **系統設定區塊** (`st.header("⚙️ 系統設定")`)
    
  - **API金鑰區塊** (`st.subheader("🔑 API 金鑰")`)
    - FMP API Key輸入: `st.text_input("FMP API Key *", type="password")` - 必填
    - Alpha Vantage API Key輸入: `st.text_input("Alpha Vantage API Key *", type="password")` - 必填
    - OpenAI API Key輸入: `st.text_input("OpenAI API Key", type="password")` - 選填
  
  - **投資組合區塊** (`st.subheader("📂 投資組合")`)
    - CSV範例檔案下載按鈕: "📥 下載CSV範例檔案"
    - CSV格式說明: `st.info("**CSV格式**:股票代碼,持股數量(無需標題列，每行一支股票)")`
    - CSV上傳區: `st.file_uploader("上傳投資組合CSV", type=['csv'])`
  
  - **日曆設定區塊** (`st.subheader("📅 日曆設定")`)
    - 起始日期選擇: `st.date_input("起始日期")`
    - 結束日期選擇: `st.date_input("結束日期")`
    - 日期說明: 說明日期範圍用於篩選財報事件和經濟事件
    - 經濟行事曆checkbox: `st.checkbox("使用經濟行事曆 (Economic Calendar)")` - 預設不勾選
  
  - **篩選條件區塊** (`st.subheader("🎯 篩選條件")`)
    - Impact等級選擇: `st.selectbox("Impact 等級", ['High', 'Medium', 'Low'])` - 預設Medium
    - 關注國家選擇: `st.multiselect("關注國家")` - 預設美國、台灣
  
  - **執行按鈕**: `st.button("🚀 執行分析", type="primary", use_container_width=True)`
  - **免責聲明**: 使用 `st.caption()` 顯示免責聲明

### F-002: CSV投資組合上傳與驗證
**功能目標**: 讓用戶上傳投資組合CSV檔案，系統自動驗證格式

**CSV格式要求**:
- **無標題列**: CSV檔案不包含標題行
- **兩欄格式**: 股票代碼,持股數量
- **範例內容**:
```
AAPL,100
MSFT,50
TSLA,30
JPM,200
JNJ,150
```

**範例檔案下載功能**:
```python
sample_csv = """AAPL,100
MSFT,50
TSLA,30
JPM,200
JNJ,150"""

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
portfolio_df = pd.read_csv(uploaded_file, header=None, names=['symbol', 'quantity'])
portfolio_df['symbol'] = portfolio_df['symbol'].str.strip().str.upper()
```

**驗證後展示**:
- 使用 `st.success(f"✅ 已載入 {len(portfolio_df)} 檔股票")`
- 使用 `st.expander("📋 查看上傳的投資組合", expanded=True)` 展示DataFrame

### F-003: 產業經濟指標映射系統
**功能目標**: 定義11個標準產業與經濟指標的關聯性，用於Layer 2產業間接匹配

**產業映射數據結構**: 使用Python字典 `SECTOR_ECONOMIC_MAPPING`，每個產業包含：
- `keywords`: 相關經濟指標關鍵字列表
- `high_impact_keywords`: 高影響力關鍵字（匹配得分1.0）
- `sensitivity`: 產業敏感度係數（0.0-1.0）

**11個標準產業與經濟指標關聯**:

**1. Technology (科技) - 敏感度 0.8**
```python
'Technology': {
    'keywords': [
        'GDP', 'Consumer Confidence', 'Interest Rate', 
        'Inflation', 'CPI', 'Manufacturing PMI', 
        'Retail Sales', 'Unemployment'
    ],
    'high_impact_keywords': ['Interest Rate', 'GDP'],
    'sensitivity': 0.8
}
```

**2. Financial Services (金融服務) - 敏感度 1.0**
```python
'Financial Services': {
    'keywords': [
        'Interest Rate', 'Fed', 'Federal Reserve', 
        'Inflation', 'CPI', 'PPI', 'Treasury', 
        'Unemployment', 'GDP'
    ],
    'high_impact_keywords': ['Interest Rate', 'Fed'],
    'sensitivity': 1.0
}
```

**3. Energy (能源) - 敏感度 0.9**
```python
'Energy': {
    'keywords': [
        'Oil', 'Crude', 'Petroleum', 'Natural Gas',
        'Energy', 'OPEC', 'Industrial Production'
    ],
    'high_impact_keywords': ['Oil', 'Crude'],
    'sensitivity': 0.9
}
```

**4. Consumer Cyclical (非必需消費品) - 敏感度 0.7**
```python
'Consumer Cyclical': {
    'keywords': [
        'Retail Sales', 'Consumer Confidence', 
        'Consumer Spending', 'Unemployment', 'Wage',
        'GDP', 'CPI'
    ],
    'high_impact_keywords': ['Retail Sales', 'Consumer Confidence'],
    'sensitivity': 0.7
}
```

**5. Healthcare (醫療保健) - 敏感度 0.4**
```python
'Healthcare': {
    'keywords': [
        'GDP', 'CPI', 'Healthcare', 'Medicare',
        'Drug', 'FDA'
    ],
    'high_impact_keywords': ['Healthcare', 'Drug'],
    'sensitivity': 0.4
}
```

**6. Industrials (工業) - 敏感度 0.7**
```python
'Industrials': {
    'keywords': [
        'Manufacturing PMI', 'Industrial Production',
        'GDP', 'Trade', 'Tariff', 'Exports', 'Imports'
    ],
    'high_impact_keywords': ['Manufacturing PMI', 'Trade'],
    'sensitivity': 0.7
}
```

**7. Consumer Defensive (必需消費品) - 敏感度 0.3**
```python
'Consumer Defensive': {
    'keywords': [
        'CPI', 'Inflation', 'Consumer Spending',
        'Retail Sales'
    ],
    'high_impact_keywords': ['CPI'],
    'sensitivity': 0.3
}
```

**8. Real Estate (房地產) - 敏感度 0.9**
```python
'Real Estate': {
    'keywords': [
        'Interest Rate', 'Fed', 'Housing', 'Mortgage',
        'Construction', 'Building Permits'
    ],
    'high_impact_keywords': ['Interest Rate', 'Housing'],
    'sensitivity': 0.9
}
```

**9. Communication Services (通訊服務) - 敏感度 0.6**
```python
'Communication Services': {
    'keywords': [
        'GDP', 'Consumer Confidence', 'Interest Rate',
        'Advertising', 'Retail Sales'
    ],
    'high_impact_keywords': ['GDP'],
    'sensitivity': 0.6
}
```

**10. Utilities (公用事業) - 敏感度 0.5**
```python
'Utilities': {
    'keywords': [
        'Interest Rate', 'Energy', 'Natural Gas',
        'Inflation'
    ],
    'high_impact_keywords': ['Interest Rate'],
    'sensitivity': 0.5
}
```

**11. Basic Materials (基礎材料) - 敏感度 0.8**
```python
'Basic Materials': {
    'keywords': [
        'Manufacturing PMI', 'Industrial Production',
        'GDP', 'Trade', 'China', 'Commodity'
    ],
    'high_impact_keywords': ['Manufacturing PMI'],
    'sensitivity': 0.8
}
```

**產業標準化映射表 SECTOR_MAPPING**:
將不同API回傳的產業名稱映射到11個標準產業
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
    "Basic Materials": "Basic Materials",
    "Technology": "Technology",
    "Healthcare": "Healthcare",
    "Consumer Electronics": "Technology",
    "Biotechnology": "Healthcare"
}
```

**國家代碼映射表 COUNTRY_MAPPING**:
支援59個國家的中文到代碼映射
```python
COUNTRY_MAPPING = {
    "美國": "US", "台灣": "TW", "日本": "JP", "中國": "CN",
    "德國": "DE", "印度": "IN", "英國": "UK", "義大利": "IT",
    "加拿大": "CA", "巴西": "BR", "俄羅斯": "RU", "南韓": "KR",
    "墨西哥": "MX", "澳大利亞": "AU", "西班牙": "ES", "印尼": "ID",
    "土耳其": "TR", "荷蘭": "NL", "沙烏地阿拉伯": "SA", "瑞士": "CH",
    "波蘭": "PL", "比利時": "BE", "瑞典": "SE", "愛爾蘭": "IE",
    "奧地利": "AT", "新加坡": "SG", "泰國": "TH", "以色列": "IL",
    "挪威": "NO", "菲律賓": "PH", "越南": "VN", "馬來西亞": "MY",
    "丹麥": "DK", "南非": "ZA", "羅馬尼亞": "RO", "埃及": "EG",
    "捷克": "CZ", "智利": "CL", "芬蘭": "FI", "希臘": "GR",
    "紐西蘭": "NZ", "匈牙利": "HU", "卡達": "QA", "多明尼加": "DO",
    "肯亞": "KE", "烏茲別克": "UZ", "阿曼": "OM", "斯里蘭卡": "LK",
    "保加利亞": "BG", "克羅埃西亞": "HR", "塞爾維亞": "RS",
    "波士尼亞與赫塞哥維納": "BA", "波札那": "BW", "賽普勒斯": "CY",
    "愛沙尼亞": "EE", "厄利垂亞": "ER", "歐元區/歐盟": "EU",
    "冰島": "IS", "柬埔寨": "KH", "拉脫維亞": "LV", "摩爾多瓦": "MD",
    "馬爾他": "MT", "模里西斯": "MU", "尼泊爾": "NP", "巴布亞紐幾內亞": "PG"
}
```

### F-004: Financial Modeling Prep & Alpha Vantage API整合
**功能目標**: 從FMP和Alpha Vantage API獲取公司資料、財報日曆和經濟日曆

**API端點規格**:

**1. 獲取公司基本資料 (get_fmp_profile) - FMP**
- **端點**: `https://financialmodelingprep.com/stable/profile?symbol={symbol}&apikey={api_key}`
- **方法**: GET
- **參數**: 
  - symbol: 股票代碼
  - apikey: FMP API金鑰
- **回傳**: JSON陣列，取第一個元素
- **回傳欄位範例**:
```json
{
  "symbol": "AAPL",
  "price": 232.8,
  "marketCap": 3500823120000,
  "beta": 1.24,
  "companyName": "Apple Inc.",
  "industry": "Consumer Electronics",
  "sector": "Technology",
  "country": "US",
  "ceo": "Mr. Timothy D. Cook",
  "fullTimeEmployees": "164000",
  "website": "https://www.apple.com"
}
```
- **需要欄位**: 
  - `companyName`: 公司名稱
  - `sector`: 產業分類（需映射到11個標準產業）
  - `country`: 國家代碼
  - `price`: 當前股價
- **錯誤處理**: 
  - 超時10秒
  - 回傳None時顯示錯誤訊息
  - 捕獲所有異常

**2. 獲取財報日曆 (get_earning_calendar) - Alpha Vantage**
- **端點**: `https://www.alphavantage.co/query?function=EARNINGS_CALENDAR&horizon=3month&apikey={api_key}`
- **方法**: GET
- **參數**: 
  - function: EARNINGS_CALENDAR（固定）
  - horizon: 3month（固定）
  - apikey: Alpha Vantage API金鑰
- **回傳**: CSV格式，需轉換為DataFrame
- **需要欄位**: 
  - `symbol`: 股票代碼
  - `name`: 公司名稱
  - `reportDate`: 財報日期
  - `estimate`: 預估EPS
- **錯誤處理**: 
  - 超時15秒
  - 使用 `pd.read_csv(StringIO(response.text))` 解析CSV
  - 捕獲所有異常

**3. 獲取經濟日曆 (get_economic_calendar) - FMP**
- **端點**: `https://financialmodelingprep.com/stable/economic-calendar?from={from_date}&to={to_date}&apikey={api_key}`
- **方法**: GET
- **參數**: 
  - from: 起始日期（YYYY-MM-DD格式）
  - to: 結束日期（YYYY-MM-DD格式）
  - apikey: FMP API金鑰
- **回傳**: JSON陣列
- **回傳欄位範例**:
```json
{
  "date": "2025-10-15 23:50:00",
  "country": "JP",
  "event": "Machinery Orders YoY (Aug)",
  "currency": "JPY",
  "previous": 4.9,
  "estimate": 4.8,
  "actual": null,
  "impact": "Medium",
  "unit": "%"
}
```
- **需要欄位**: 
  - `date`: 事件日期時間
  - `country`: 國家代碼
  - `event`: 事件名稱
  - `previous`: 前值
  - `estimate`: 預期值
  - `actual`: 實際值（可為null）
  - `impact`: 影響等級（High/Medium/Low）
- **錯誤處理**: 
  - 超時15秒
  - 轉換為DataFrame處理
  - 捕獲所有異常

### F-005: 三層事件匹配引擎
**功能目標**: 使用三層匹配邏輯識別與投資組合相關的事件，並計算關聯度分數

**Layer 1: 直接匹配（財報事件）- match_earning_events**

**匹配邏輯**:
```python
def match_earning_events(earning_df, portfolio_symbols, holdings_df, from_date=None, to_date=None):
    """
    直接匹配：投資組合股票代碼 == 財報日曆股票代碼
    
    參數:
    - earning_df: 財報日曆DataFrame
    - portfolio_symbols: 投資組合股票代碼集合
    - holdings_df: 持股詳細資料DataFrame
    - from_date: 篩選起始日期
    - to_date: 篩選結束日期
    
    回傳: 匹配事件列表
    """
```

**匹配條件**:
- `symbol in portfolio_symbols` → 100%直接相關
- 日期在 from_date 和 to_date 範圍內

**事件資料結構**:
```python
{
    'date': report_date,                    # 財報日期（datetime）
    'symbol': symbol,                       # 股票代碼
    'event_name': f"{company_name} 財報",   # 事件名稱
    'event_type': 'earning',                # 事件類型
    'country': country,                     # 國家
    'impact': 'High',                       # 影響等級（財報固定為High）
    'relevance_score': 1.0,                 # 關聯度100%
    'match_type': 'direct',                 # 匹配類型
    'affected_holding': {                   # 受影響持股資訊
        'symbol': symbol,
        'quantity': quantity,
        'value': market_value,
        'sector': sector
    },
    'estimate': estimate,                   # 預估值
    'previous': None,                       # 前值（財報無此欄位）
    'actual': None                          # 實際值（未發生前為None）
}
```

**Layer 2: 產業間接匹配（經濟事件）- match_economic_events (Part 1)**

**匹配邏輯**:
```python
# 對每個經濟事件，檢查是否包含產業關鍵字
for sector, weight in sector_dist.items():
    mapping = SECTOR_ECONOMIC_MAPPING[sector]
    match_score = 0
    
    # 關鍵字匹配
    for keyword in mapping['keywords']:
        if keyword.lower() in event_name.lower():
            if keyword in mapping['high_impact_keywords']:
                match_score = 1.0  # 高影響關鍵字
                break
            else:
                match_score = max(match_score, 0.6)  # 一般關鍵字
    
    if match_score > 0:
        # 計算產業關聯度 = 匹配分數 × 產業敏感度 × 投資組合權重
        relevance = match_score * mapping['sensitivity'] * weight
```

**匹配範例**:
- 經濟事件: "Fed Interest Rate Decision"
- 投資組合: Technology 40%, Financial Services 30%
- Technology 匹配:
  - "Interest Rate" in high_impact_keywords → match_score = 1.0
  - relevance = 1.0 × 0.8 (sensitivity) × 0.4 (weight) = **0.32**
- Financial Services 匹配:
  - "Interest Rate" in high_impact_keywords → match_score = 1.0
  - relevance = 1.0 × 1.0 (sensitivity) × 0.3 (weight) = **0.30**
- 總產業關聯度 = 0.32 + 0.30 = **0.62**

**Layer 3: 國家關聯匹配（經濟事件）- match_economic_events (Part 2)**

**匹配邏輯**:
```python
# 檢查事件國家是否在投資組合國家分布中
if event_country in country_dist:
    impact_multiplier = {
        'High': 1.0, 
        'Medium': 0.7, 
        'Low': 0.4
    }.get(event_impact, 0.5)
    
    # 國家關聯度 = 國家權重 × Impact係數
    country_relevance = country_dist[event_country] * impact_multiplier

# 歐元區特殊處理
elif event_country in ['EU', 'EMU']:
    eu_countries = ['DE', 'FR', 'IT', 'ES', 'NL', 'BE']
    eu_exposure = sum(country_dist.get(c, 0) for c in eu_countries)
    if eu_exposure > 0:
        country_relevance = eu_exposure * 0.8
```

**綜合關聯度計算**:
```python
# 取產業和國家關聯度的最大值
final_relevance = max(sector_relevance, country_relevance)

# 如果同時有產業和國家匹配，給予加成（上限1.0）
if sector_relevance > 0 and country_relevance > 0:
    final_relevance = min(final_relevance * 1.2, 1.0)

# 只保留關聯度 > 0.2 的事件
if final_relevance > 0.2:
    # 加入匹配事件列表
```

**Impact篩選邏輯**:
```python
impact_hierarchy = {
    'High': ['High'],                    # 只顯示High
    'Medium': ['High', 'Medium'],        # 顯示High + Medium
    'Low': ['High', 'Medium', 'Low']     # 顯示全部
}
```

### F-006: 投資組合分布計算
**功能目標**: 計算投資組合的產業分布和國家分布，用於事件匹配

**計算函數 (calculate_portfolio_distribution)**:
```python
def calculate_portfolio_distribution(holdings_df):
    """
    計算投資組合分布
    
    輸入: holdings_df - 包含所有持股的DataFrame
    輸出: {
        'sectors': {產業: 權重},
        'countries': {國家: 權重},
        'total_value': 總市值
    }
    """
    total_value = holdings_df['market_value'].sum()
    
    # 產業分布 = 各產業市值 / 總市值
    sector_dist = holdings_df.groupby('sector')['market_value'].sum() / total_value
    
    # 國家分布 = 各國家市值 / 總市值
    country_dist = holdings_df.groupby('country')['market_value'].sum() / total_value
    
    return {
        'sectors': sector_dist.to_dict(),
        'countries': country_dist.to_dict(),
        'total_value': total_value
    }
```

**範例輸出**:
```python
{
    'sectors': {
        'Technology': 0.45,        # 45%科技股
        'Financial Services': 0.30, # 30%金融股
        'Healthcare': 0.25         # 25%醫療股
    },
    'countries': {
        'US': 0.80,               # 80%美股
        'TW': 0.15,               # 15%台股
        'JP': 0.05                # 5%日股
    },
    'total_value': 150000.00      # 總市值$150,000
}
```

### F-007: 時間敏感度與優先級計算
**功能目標**: 計算距離事件的天數，並標示優先級

**天數計算函數 (calculate_days_until)**:
```python
def calculate_days_until(event_date):
    """
    計算距離事件的天數
    
    輸入: event_date (datetime)
    輸出: 整數天數（負數表示已過期，正數表示未來）
    """
    today = datetime.now()
    delta = (event_date - today).days
    return delta
```

**優先級標示函數 (get_priority_emoji)**:
```python
def get_priority_emoji(days_until):
    """
    根據天數返回優先級emoji
    
    優先級定義:
    - D-1 ~ D-3: 🔴 緊急（需立即關注）
    - D-4 ~ D-7: 🟠 重要（本週內）
    - D-8 ~ D-30: 🟡 關注（近期）
    - D-30+: 🟢 長期
    """
    if days_until <= 3:
        return "🔴"
    elif days_until <= 7:
        return "🟠"
    elif days_until <= 30:
        return "🟡"
    else:
        return "🟢"
```

### F-008: AI智慧提醒生成
**功能目標**: 使用OpenAI分析事件，生成智慧提醒和深度分析

**AI分析函數 (generate_ai_analysis)**

**輸入數據準備**:
```python
# 準備事件摘要（前20個事件）
for event in matched_events[:20]:
    days_until = calculate_days_until(event['date'])
    priority = get_priority_emoji(days_until)
    
    event_summary = f"""
事件 {i}:
- 日期: {event['date'].strftime('%Y-%m-%d')} (D{days_until:+d}) {priority}
- 類型: {'🏢 財報' if event['event_type'] == 'earning' else '📊 經濟指標'}
- 名稱: {event['event_name']}
- 國家: {event['country']}
- Impact: {event['impact']}
- 關聯度: {event['relevance_score']:.0%}
- 受影響: {affected_info}
- 前值: {event.get('previous', 'N/A')}
- 預期: {event.get('estimate', 'N/A')}
- 實際: {event.get('actual', '待公布')}
    """

# 準備投資組合資訊
portfolio_info = {
    'total_value': total_value,
    'sectors': {sector: weight, ...},
    'countries': {country: weight, ...}
}
```

**完整AI提示語**:
```python
prompt = f"""
你是專業的投資組合事件分析師。以下是系統已匹配的相關事件和用戶的投資組合。

## 投資組合概況
- 總市值: ${portfolio_info['total_value']:,.2f}
- 產業分布:
{sector_summary}
- 國家分布:
{country_summary}

## 未來事件清單（已按關聯度和日期篩選，僅列出前20個）
{events_summary}

---

請執行以下分析任務：

### 1️⃣ 單一事件異常檢測
檢查是否有"預期 vs 前值"差異較大的事件（可能是重大轉折點）。
若 estimate 與 previous 差異超過20%，標記為"異常"並說明潛在影響。

### 2️⃣ 多事件聚合分析
識別同一時間窗口（±3天）內的事件群組：
- 如果有 ≥2 個 High Impact 事件同週發生，標記為"密集事件週"
- 分析這些事件的疊加效應

### 3️⃣ 產業連鎖反應識別
對於影響多個產業的經濟事件（如Fed利率決議），分析：
- 哪些產業最脆弱
- 可能的傳導路徑（例如：利率↑ → 金融股↓ → 貸款收緊 → 房地產↓）
- 用戶投資組合的連鎖反應風險

### 4️⃣ 時間敏感度分級
根據距離事件的天數，標記優先級：
- D-1 ~ D-3: 🔴 緊急（需立即關注）
- D-4 ~ D-7: 🟠 重要（本週內）
- D-8 ~ D-30: 🟡 關注（近期）

### 5️⃣ 智慧提醒生成
生成 3-5 條可執行的提醒，每條包含：
- 🔴/🟠/🟡 優先級
- 簡短標題（<15字）
- 詳細說明（50-80字）
- 建議動作（關注/準備/監控，但不給買賣建議）

---

## 輸出格式

請用 Markdown 格式輸出，結構如下：

### 🚨 高優先級提醒 (D-3內)
[列出緊急事件及建議]

### ⚠️ 重要事件提醒 (本週)
[列出重要事件]

### 📊 事件深度分析

#### 異常檢測結果
[標記異常事件]

#### 密集事件週識別
[如果有]

#### 產業連鎖反應路徑
[畫出傳導鏈]

### 💡 綜合建議
[總結性建議，不給具體買賣指示]

---

**重要原則**：
- 專注於風險識別和監控建議
- 不提供具體買賣建議
- 保持客觀中立的分析語氣
- 使用繁體中文
"""
```

**OpenAI API調用**:
```python
client = OpenAI(api_key=openai_api_key)

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
except Exception as e:
    return f"⚠️ AI 分析生成失敗: {str(e)}"
```

### F-009: 結果展示系統
**功能目標**: 顯示投資組合概況、事件時間表和AI分析報告

**展示區塊1: 投資組合概況**
```python
with st.expander("💼 投資組合概況", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("總市值", f"${portfolio_dist['total_value']:,.2f}")
    
    with col2:
        st.metric("持股數量", len(holdings_df))
    
    with col3:
        st.metric("涵蓋產業", len(portfolio_dist['sectors']))
    
    st.subheader("產業分布")
    # 顯示產業分布表格
    
    st.subheader("國家分布")
    # 顯示國家分布表格
```

**展示區塊2: 事件時間表**
```python
st.subheader("📅 相關事件時間表")

# 準備表格資料
table_data = []
for event in all_events:
    table_data.append({
        '優先級': event['priority'],
        '日期': event['date'].strftime('%Y-%m-%d'),
        '倒數': f"D{event['days_until']:+d}",
        '類型': '🏢 財報' if event['event_type'] == 'earning' else '📊 經濟',
        '事件名稱': event['event_name'],
        '國家': event['country'],
        'Impact': event['impact'],
        '關聯度': f"{event['relevance_score']:.0%}",
        '前值': event.get('previous', '-'),
        '預期': event.get('estimate', '-'),
        '實際': event.get('actual', '-')
    })

events_table_df = pd.DataFrame(table_data)
st.dataframe(events_table_df, use_container_width=True, height=500, hide_index=True)

# CSV下載按鈕
st.download_button("📥 下載事件清單 CSV", ...)
```

**表格欄位說明**:
- **優先級**: 🔴/🟠/🟡/🟢 emoji標示
- **日期**: YYYY-MM-DD格式
- **倒數**: D+n 或 D-n 格式
- **類型**: 🏢 財報 或 📊 經濟
- **事件名稱**: 完整事件描述
- **國家**: 兩字母國家代碼
- **Impact**: High/Medium/Low
- **關聯度**: 百分比格式（0%-100%）
- **前值**: 經濟指標的前期數值（可為"-"）
- **預期**: 經濟指標的預期數值（可為"-"）
- **實際**: 經濟指標的實際數值（可為"-"）

**展示區塊3: AI深度分析**
```python
if all_events and has_openai_key:
    st.markdown("---")
    st.subheader("🤖 AI 深度分析")
    
    with st.spinner("AI 正在生成深度分析..."):
        ai_report = generate_ai_analysis(all_events, portfolio_dist, openai_api_key)
        st.markdown(ai_report)
elif all_events and not has_openai_key:
    st.info("💡 提供 OpenAI API Key 可獲得 AI 深度分析報告\n\n包含：異常檢測、密集事件週識別、產業連鎖反應分析、智慧提醒等功能")
```

## 🔧 核心函數實施要求

### 數據處理函數

**1. map_sector(sector)**
- **功能**: 將FMP回傳的產業名稱映射到11個標準產業
- **輸入**: FMP產業名稱（字串）
- **輸出**: 標準產業名稱（字串）
- **邏輯**: 使用SECTOR_MAPPING字典查找，找不到則回傳原始名稱

**2. calculate_portfolio_distribution(holdings_df)**
- **功能**: 計算投資組合的產業和國家分布
- **輸入**: 持股DataFrame
- **輸出**: 包含sectors、countries、total_value的字典
- **邏輯**: 按產業和國家分組計算市值總和，除以總市值得到權重

**3. calculate_days_until(event_date)**
- **功能**: 計算距離事件的天數
- **輸入**: 事件日期（datetime）
- **輸出**: 整數天數
- **邏輯**: (event_date - today).days

**4. get_priority_emoji(days_until)**
- **功能**: 根據天數返回優先級emoji
- **輸入**: 天數（整數）
- **輸出**: emoji字串（🔴/🟠/🟡/🟢）
- **邏輯**: 根據天數範圍返回對應emoji

### API函數

**5. get_fmp_profile(symbol, api_key)**
- **端點**: /stable/profile
- **超時**: 10秒
- **錯誤處理**: 捕獲異常並顯示st.error()
- **回傳**: 字典或None

**6. get_earning_calendar(api_key)**
- **端點**: Alpha Vantage EARNINGS_CALENDAR
- **超時**: 15秒
- **數據處理**: 使用StringIO解析CSV為DataFrame
- **錯誤處理**: 捕獲異常並顯示st.error()
- **回傳**: DataFrame或None

**7. get_economic_calendar(from_date, to_date, fmp_api_key)**
- **端點**: /stable/economic-calendar
- **超時**: 15秒
- **數據處理**: JSON轉DataFrame
- **錯誤處理**: 捕獲異常並顯示st.error()
- **回傳**: DataFrame或None

### 事件匹配函數

**8. match_earning_events(earning_df, portfolio_symbols, holdings_df, from_date, to_date)**
- **功能**: Layer 1 直接匹配財報事件
- **匹配邏輯**: symbol in portfolio_symbols
- **日期篩選**: 根據from_date和to_date篩選
- **輸出**: 匹配事件列表，每個事件包含完整資訊
- **關聯度**: 固定1.0（100%）

**9. match_economic_events(economic_df, portfolio_dist, selected_countries, impact_filter)**
- **功能**: Layer 2 & 3 產業和國家匹配經濟事件
- **匹配邏輯**: 
  - Layer 2: 關鍵字匹配產業
  - Layer 3: 國家權重計算
  - 綜合: 取最大值，有雙重匹配時加成
- **篩選**: 只保留關聯度 > 0.2 的事件
- **輸出**: 匹配事件列表

### AI函數

**10. generate_ai_analysis(matched_events, portfolio_info, openai_api_key)**
- **功能**: AI生成智慧提醒和深度分析
- **模型**: gpt-4o-mini
- **輸入**: 匹配事件列表（限前20個）、投資組合資訊
- **輸出**: Markdown格式的分析報告（字串）
- **提示語**: 包含5大分析任務
- **錯誤處理**: API失敗時回傳錯誤訊息字串

## 📐 主程式流程規格

### 初始化階段
```python
st.set_page_config(
    page_title="AI投資組合事件提醒系統",
    page_icon="🔔",
    layout="wide"
)

st.title("🔔 AI投資組合事件提醒系統")
st.markdown("---")
```

### 側邊欄設定階段
1. 顯示系統設定標題
2. API金鑰輸入（FMP必填、Alpha Vantage必填、OpenAI選填）
3. 投資組合上傳（CSV範例下載、格式說明、上傳介面）
4. 日曆設定（起始日期、結束日期、經濟行事曆checkbox）
5. 篩選條件（Impact等級、關注國家）
6. 執行分析按鈕
7. 免責聲明

### 主內容區初始狀態
- 如果未上傳CSV: 顯示操作說明，然後 `st.stop()`
- 如果已上傳CSV: 顯示投資組合預覽

### 執行分析流程
**觸發**: 點擊"執行分析"按鈕

**步驟1: API金鑰驗證**
```python
if not fmp_api_key:
    st.error("❌ 請輸入 FMP API Key（必填）")
    st.stop()

if not alphavantage_api_key:
    st.error("❌ 請輸入 Alpha Vantage API Key（必填）")
    st.stop()

# OpenAI API Key 檢查（選填）
has_openai_key = openai_api_key and len(openai_api_key.strip()) > 0
if not has_openai_key:
    st.info("💡 未輸入 OpenAI API Key，將只顯示事件清單，不進行 AI 深度分析")
```

**步驟2: 獲取公司基本資料**
```python
with st.spinner("正在獲取公司基本資料..."):
    progress_bar = st.progress(0)
    
    for idx, row in portfolio_df.iterrows():
        symbol = row['symbol']
        quantity = row['quantity']
        
        # 調用 FMP Profile API
        profile = get_fmp_profile(symbol, fmp_api_key)
        
        if profile:
            # 提取必要欄位並映射產業
            sector = map_sector(profile.get('sector', 'Unknown'))
            country = profile.get('country', 'Unknown')
            price = profile.get('price', 0)
            
            holdings_data.append({
                'symbol': symbol,
                'company_name': profile.get('companyName', symbol),
                'quantity': quantity,
                'price': price,
                'market_value': price * quantity,
                'sector': sector,
                'country': country
            })
        else:
            failed_symbols.append(symbol)
        
        progress_bar.progress((idx + 1) / len(portfolio_df))
        time.sleep(0.3)  # 避免API限制
    
    progress_bar.empty()
```

**步驟3: 計算投資組合分布**
```python
holdings_df = pd.DataFrame(holdings_data)
portfolio_dist = calculate_portfolio_distribution(holdings_df)
```

**步驟4: 獲取日曆資料**
```python
with st.spinner("正在獲取日曆資料..."):
    # 獲取財報日曆（必定執行）
    earning_df = get_earning_calendar(alphavantage_api_key)
    
    # 獲取經濟日曆（只有在勾選時才執行）
    economic_df = None
    if use_economic_calendar:
        from_date_str = from_date.strftime('%Y-%m-%d')
        to_date_str = to_date.strftime('%Y-%m-%d')
        economic_df = get_economic_calendar(from_date_str, to_date_str, fmp_api_key)
        
        if economic_df is None or economic_df.empty:
            st.warning("⚠️ 無法獲取經濟行事曆資料，可能是 API Key 無權限或網路問題")
```

**步驟5: 事件匹配**
```python
with st.spinner("正在匹配相關事件..."):
    portfolio_symbols = set(holdings_df['symbol'].tolist())
    
    # Layer 1: 財報匹配
    earning_events = match_earning_events(earning_df, portfolio_symbols, holdings_df, from_date, to_date)
    
    # Layer 2 & 3: 經濟事件匹配
    economic_events = []
    if use_economic_calendar and economic_df is not None:
        selected_country_codes = [COUNTRY_MAPPING[c] for c in selected_countries]
        economic_events = match_economic_events(
            economic_df, 
            portfolio_dist, 
            selected_country_codes, 
            impact_filter
        )
    
    # 合併所有事件
    all_events = earning_events + economic_events
    
    # 排序：先按日期，再按關聯度
    all_events.sort(key=lambda x: (x['date'], -x['relevance_score']))
    
    # 計算天數和優先級
    for event in all_events:
        event['days_until'] = calculate_days_until(event['date'])
        event['priority'] = get_priority_emoji(event['days_until'])
```

**步驟6: 顯示結果**
- 顯示投資組合概況（市值、產業分布、國家分布）
- 顯示事件時間表（表格+CSV下載）
- 顯示AI深度分析（如果有OpenAI API Key）

## 💡 通用界面設計標準

### 配色方案
- **主色調**: Streamlit預設藍色
- **成功/正值**: 綠色
- **警告/中性**: 橙色
- **錯誤/負值**: 紅色
- **資訊**: 藍色

### 字體與排版
- **字體家族**: "Microsoft JhengHei, Arial"（支援中文）
- **標題大小**: 使用Streamlit預設標題大小
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
- **完整性**: 所有功能都必須完整實施，不能有placeholder
- **準確性**: 匹配邏輯必須精確，關聯度計算正確
- **穩定性**: 能處理各種邊界情況和異常輸入
- **效能**: API調用有超時設定，避免長時間等待

### 界面品質
- **直觀性**: 操作流程清晰，不需要額外說明
- **友善性**: 提供充足的提示和說明文字
- **回饋性**: 所有操作都有明確的視覺回饋
- **一致性**: 界面元素風格統一，符合設計標準

### 程式碼品質
- **可讀性**: 程式碼結構清晰，有適當的註釋
- **可維護性**: 函數功能單一，模組化組織
- **錯誤處理**: 所有可能失敗的操作都有try-except
- **效能優化**: 避免重複計算，合理使用快取

### 安全性
- **API金鑰保護**: 使用password類型輸入，不在程式碼中硬編碼
- **輸入驗證**: 驗證CSV格式和數據有效性
- **錯誤訊息**: 不洩露敏感的系統資訊

## 🎓 免責聲明標準文字

```python
st.caption("### ⚠️ 免責聲明")
st.caption("""
本系統僅供學術研究與教育用途，AI提供的數據與分析結果僅供參考，
**不構成投資建議或財務建議**。請使用者自行判斷投資決策，並承擔相關風險。
本系統作者不對任何投資行為負責，亦不承擔任何損失責任。
""")
```

## AI實作指令

**請根據以上完整規格說明書，生成一個完整可運行的 Streamlit 網頁應用程式。**

### 必要實現要求
1. **完全實現所有功能需求**: 從F-001到F-009的所有功能都必須完整實施
2. **嚴格遵循技術架構要求**: 使用OpenAI新版API格式和FMP /stable/ 端點
3. **實施三層匹配邏輯**: Layer 1直接匹配、Layer 2產業匹配、Layer 3國家匹配
4. **符合專業界面設計標準**: 使用指定的配色方案和佈局結構
5. **具備投資事件分析專業水準**: 匹配邏輯精確、AI分析客觀深入

### 技術實現要求
- **界面框架**: 使用Streamlit框架建立完整的網頁界面
- **API整合**: 整合FMP /stable/ API和Alpha Vantage API，實施完整錯誤處理
- **AI分析**: 使用OpenAI新版API格式（client.chat.completions.create），模型gpt-4o-mini
- **程式品質**: 程式碼清晰易懂，有適當中文註釋，實施所有必要功能

### 關鍵技術限制和要求
1. **OpenAI API版本限制**: 必須使用客戶端初始化和chat.completions.create方法，禁用舊版格式
2. **FMP API端點要求**: 所有FMP API端點必須使用 /stable/ 路徑
3. **Alpha Vantage固定參數**: horizon=3month固定在URL中
4. **三層匹配邏輯準確性**: 必須按照規格精確實施關聯度計算
5. **AI提示語精確性**: AI提示語必須與規格說明書中的一致
6. **日期篩選功能**: 財報事件必須支援日期範圍篩選

### 特別注意事項
- 程式必須完整可執行，可直接用 `streamlit run portfolio_event_alert.py` 運行
- 所有用戶輸入都要有完整驗證和友善錯誤處理
- AI分析內容要客觀專業，聚焦風險識別，避免投資建議
- 界面要直觀易用，符合投資分析專業人士使用習慣
- 免責聲明要清楚顯示，強調系統僅供教育研究用途
- Economic Calendar為選擇性功能，預設不勾選
- 表格要支援CSV匯出功能
- 進度提示要即時，讓用戶了解系統正在處理

### 程式碼組織要求
1. **導入區塊**: 包含所有必要的套件導入（streamlit, pandas, requests, openai, datetime, json, time, io）
2. **常數定義區塊**: SECTOR_ECONOMIC_MAPPING、SECTOR_MAPPING、COUNTRY_MAPPING字典
3. **函數定義區塊**: 按照功能分類組織所有函數（API、數據處理、匹配、AI）
4. **主程式區塊**: 
   - 頁面配置設定
   - 側邊欄界面建立
   - 主內容區初始狀態
   - 執行按鈕觸發的完整流程
   - 結果展示
5. **註釋要求**: 每個重要函數和複雜邏輯都要有清楚的中文說明

### 成功驗收標準
生成的程式必須能夠成功實現：
1. 正確上傳和驗證CSV格式的投資組合
2. 成功調用FMP /stable/ API獲取公司資料
3. 成功調用Alpha Vantage API獲取財報日曆
4. 可選擇性調用FMP Economic Calendar API
5. 正確計算投資組合的產業和國家分布
6. 精確執行三層匹配邏輯（直接、產業、國家）
7. 正確計算關聯度分數和優先級
8. 支援日期範圍篩選財報事件
9. 成功調用OpenAI gpt-4o-mini生成智慧提醒（如果有API Key）
10. 顯示完整的事件時間表和投資組合概況
11. 提供CSV匯出功能
12. 提供流暢的用戶體驗（進度提示、錯誤處理、操作指引）

### 交付物要求
**最終交付物**: 一個完整的Python程式檔案（檔名: portfolio_event_alert.py），包含：
- 所有必要的套件導入語句
- 完整的常數定義（產業映射、經濟指標關聯、國家代碼）
- 完整的函數實現（API調用、匹配邏輯、分布計算、AI分析）
- 主程式邏輯（界面建立、流程控制、結果展示）
- 適當的中文註釋（解釋關鍵邏輯和匹配規則）
- 可直接執行的完整程式碼（無需任何修改即可運行）
- 體現「投資組合事件提醒與智慧分析」的核心專業價值