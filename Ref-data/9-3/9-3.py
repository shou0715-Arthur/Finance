import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
from openai import OpenAI
import time

st.set_page_config(
    page_title="AI投資組合事件提醒系統",
    page_icon="🔔",
    layout="wide"
)

# ==================== 產業經濟指標映射表 ====================
SECTOR_ECONOMIC_MAPPING = {
    'Technology': {
        'keywords': [
            'GDP', 'Consumer Confidence', 'Interest Rate', 
            'Inflation', 'CPI', 'Manufacturing PMI', 
            'Retail Sales', 'Unemployment'
        ],
        'high_impact_keywords': ['Interest Rate', 'GDP'],
        'sensitivity': 0.8
    },
    'Financial Services': {
        'keywords': [
            'Interest Rate', 'Fed', 'Federal Reserve', 
            'Inflation', 'CPI', 'PPI', 'Treasury', 
            'Unemployment', 'GDP'
        ],
        'high_impact_keywords': ['Interest Rate', 'Fed'],
        'sensitivity': 1.0
    },
    'Energy': {
        'keywords': [
            'Oil', 'Crude', 'Petroleum', 'Natural Gas',
            'Energy', 'OPEC', 'Industrial Production'
        ],
        'high_impact_keywords': ['Oil', 'Crude'],
        'sensitivity': 0.9
    },
    'Consumer Cyclical': {
        'keywords': [
            'Retail Sales', 'Consumer Confidence', 
            'Consumer Spending', 'Unemployment', 'Wage',
            'GDP', 'CPI'
        ],
        'high_impact_keywords': ['Retail Sales', 'Consumer Confidence'],
        'sensitivity': 0.7
    },
    'Healthcare': {
        'keywords': [
            'GDP', 'CPI', 'Healthcare', 'Medicare',
            'Drug', 'FDA'
        ],
        'high_impact_keywords': ['Healthcare', 'Drug'],
        'sensitivity': 0.4
    },
    'Industrials': {
        'keywords': [
            'Manufacturing PMI', 'Industrial Production',
            'GDP', 'Trade', 'Tariff', 'Exports', 'Imports'
        ],
        'high_impact_keywords': ['Manufacturing PMI', 'Trade'],
        'sensitivity': 0.7
    },
    'Consumer Defensive': {
        'keywords': [
            'CPI', 'Inflation', 'Consumer Spending',
            'Retail Sales'
        ],
        'high_impact_keywords': ['CPI'],
        'sensitivity': 0.3
    },
    'Real Estate': {
        'keywords': [
            'Interest Rate', 'Fed', 'Housing', 'Mortgage',
            'Construction', 'Building Permits'
        ],
        'high_impact_keywords': ['Interest Rate', 'Housing'],
        'sensitivity': 0.9
    },
    'Communication Services': {
        'keywords': [
            'GDP', 'Consumer Confidence', 'Interest Rate',
            'Advertising', 'Retail Sales'
        ],
        'high_impact_keywords': ['GDP'],
        'sensitivity': 0.6
    },
    'Utilities': {
        'keywords': [
            'Interest Rate', 'Energy', 'Natural Gas',
            'Inflation'
        ],
        'high_impact_keywords': ['Interest Rate'],
        'sensitivity': 0.5
    },
    'Basic Materials': {
        'keywords': [
            'Manufacturing PMI', 'Industrial Production',
            'GDP', 'Trade', 'China', 'Commodity'
        ],
        'high_impact_keywords': ['Manufacturing PMI'],
        'sensitivity': 0.8
    }
}

# 產業映射（標準化不同API的產業名稱）
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

# 國家代碼映射
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

# ==================== API 函數 ====================
def get_fmp_profile(symbol, api_key):
    """獲取公司基本資料"""
    url = f"https://financialmodelingprep.com/stable/profile?symbol={symbol}&apikey={api_key}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data and len(data) > 0:
            return data[0]
        return None
    except Exception as e:
        st.error(f"獲取 {symbol} 公司資料失敗: {str(e)}")
        return None

def get_earning_calendar(api_key):
    """獲取未來3個月財報日曆（Alpha Vantage）"""
    url = f"https://www.alphavantage.co/query?function=EARNINGS_CALENDAR&horizon=3month&apikey={api_key}"
    try:
        response = requests.get(url, timeout=15)
        # Alpha Vantage 返回 CSV 格式
        from io import StringIO
        df = pd.read_csv(StringIO(response.text))
        return df
    except Exception as e:
        st.error(f"獲取 Earning Calendar 失敗: {str(e)}")
        return None

def get_economic_calendar(from_date, to_date, fmp_api_key):
    """獲取經濟日曆（FMP）"""
    url = f"https://financialmodelingprep.com/stable/economic-calendar?from={from_date}&to={to_date}&apikey={fmp_api_key}"
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        if data and isinstance(data, list):
            return pd.DataFrame(data)
        return None
    except Exception as e:
        st.error(f"獲取 Economic Calendar 失敗: {str(e)}")
        return None

# ==================== 數據處理函數 ====================
def map_sector(sector):
    """標準化產業名稱"""
    return SECTOR_MAPPING.get(sector, sector)

def calculate_portfolio_distribution(holdings_df):
    """計算投資組合的產業和國家分布"""
    total_value = holdings_df['market_value'].sum()
    
    # 產業分布
    sector_dist = holdings_df.groupby('sector')['market_value'].sum() / total_value
    
    # 國家分布
    country_dist = holdings_df.groupby('country')['market_value'].sum() / total_value
    
    return {
        'sectors': sector_dist.to_dict(),
        'countries': country_dist.to_dict(),
        'total_value': total_value
    }

def match_earning_events(earning_df, portfolio_symbols, holdings_df):
    """Layer 1: 直接匹配財報事件"""
    if earning_df is None or earning_df.empty:
        return []
    
    matched_events = []
    
    for _, row in earning_df.iterrows():
        symbol = str(row.get('symbol', '')).strip().upper()
        
        if symbol in portfolio_symbols:
            # 獲取持股資訊
            holding_rows = holdings_df[holdings_df['symbol'] == symbol]
            if holding_rows.empty:
                continue
            
            holding = holding_rows.iloc[0]
            
            try:
                report_date = pd.to_datetime(row.get('reportDate', ''))
            except:
                continue
            
            # 使用 Alpha Vantage 提供的公司名稱（如果有的話）
            company_name = row.get('name', symbol)
            
            matched_events.append({
                'date': report_date,
                'symbol': symbol,
                'event_name': f"{company_name} 財報",
                'event_type': 'earning',
                'country': holding.get('country', 'Unknown'),
                'impact': 'High',
                'relevance_score': 1.0,
                'match_type': 'direct',
                'affected_holding': {
                    'symbol': symbol,
                    'quantity': holding.get('quantity', 0),
                    'value': holding.get('market_value', 0),
                    'sector': holding.get('sector', 'Unknown')
                },
                'estimate': row.get('estimate', None),
                'previous': None,
                'actual': None
            })
    
    return matched_events

def match_economic_events(economic_df, portfolio_dist, selected_countries, impact_filter):
    """Layer 2 & 3: 產業和國家匹配經濟事件"""
    if economic_df is None or economic_df.empty:
        return []
    
    matched_events = []
    sector_dist = portfolio_dist['sectors']
    country_dist = portfolio_dist['countries']
    
    # Impact 篩選邏輯
    impact_hierarchy = {
        'High': ['High'],
        'Medium': ['High', 'Medium'],
        'Low': ['High', 'Medium', 'Low']
    }
    allowed_impacts = impact_hierarchy.get(impact_filter, ['High', 'Medium', 'Low'])
    
    for _, row in economic_df.iterrows():
        event_name = str(row.get('event', ''))
        event_country = str(row.get('country', ''))
        event_impact = str(row.get('impact', 'Low'))
        
        # 篩選 Impact
        if event_impact not in allowed_impacts:
            continue
        
        # 篩選國家
        if selected_countries and event_country not in selected_countries:
            continue
        
        # Layer 2: 產業匹配
        sector_matches = []
        for sector, weight in sector_dist.items():
            if sector not in SECTOR_ECONOMIC_MAPPING:
                continue
            
            mapping = SECTOR_ECONOMIC_MAPPING[sector]
            match_score = 0
            
            # 關鍵字匹配
            for keyword in mapping['keywords']:
                if keyword.lower() in event_name.lower():
                    if keyword in mapping['high_impact_keywords']:
                        match_score = 1.0
                        break
                    else:
                        match_score = max(match_score, 0.6)
            
            if match_score > 0:
                relevance = match_score * mapping['sensitivity'] * weight
                sector_matches.append({
                    'sector': sector,
                    'weight': weight,
                    'relevance': relevance
                })
        
        # Layer 3: 國家匹配
        country_relevance = 0
        if event_country in country_dist:
            impact_multiplier = {'High': 1.0, 'Medium': 0.7, 'Low': 0.4}.get(event_impact, 0.5)
            country_relevance = country_dist[event_country] * impact_multiplier
        elif event_country in ['EU', 'EMU']:
            eu_countries = ['DE', 'FR', 'IT', 'ES', 'NL', 'BE']
            eu_exposure = sum(country_dist.get(c, 0) for c in eu_countries)
            if eu_exposure > 0:
                country_relevance = eu_exposure * 0.8
        
        # 計算最終關聯度
        sector_relevance = sum(m['relevance'] for m in sector_matches)
        final_relevance = max(sector_relevance, country_relevance)
        
        # 如果同時有產業和國家匹配，給予加成
        if sector_relevance > 0 and country_relevance > 0:
            final_relevance = min(final_relevance * 1.2, 1.0)
        
        # 只保留關聯度 > 0.2 的事件
        if final_relevance > 0.2:
            try:
                event_date = pd.to_datetime(row.get('date', ''))
            except:
                continue
            
            matched_events.append({
                'date': event_date,
                'symbol': None,
                'event_name': event_name,
                'event_type': 'economic',
                'country': event_country,
                'impact': event_impact,
                'relevance_score': final_relevance,
                'match_type': 'indirect',
                'affected_sectors': [m['sector'] for m in sector_matches],
                'previous': row.get('previous', None),
                'estimate': row.get('estimate', None),
                'actual': row.get('actual', None)
            })
    
    return matched_events

def calculate_days_until(event_date):
    """計算距離事件的天數"""
    today = datetime.now()
    delta = (event_date - today).days
    return delta

def get_priority_emoji(days_until):
    """根據天數返回優先級emoji"""
    if days_until <= 3:
        return "🔴"
    elif days_until <= 7:
        return "🟠"
    elif days_until <= 30:
        return "🟡"
    else:
        return "🟢"

# ==================== AI 分析 ====================
def generate_ai_analysis(matched_events, portfolio_info, openai_api_key):
    """生成 AI 深度分析"""
    client = OpenAI(api_key=openai_api_key)
    
    # 準備事件摘要
    events_summary = []
    for i, event in enumerate(matched_events[:20], 1):  # 限制前20個事件
        days_until = calculate_days_until(event['date'])
        priority = get_priority_emoji(days_until)
        
        event_type = "🏢 財報" if event['event_type'] == 'earning' else "📊 經濟指標"
        
        affected_info = ""
        if event['event_type'] == 'earning':
            affected_info = f"持股: {event['affected_holding']['symbol']} ({event['affected_holding']['quantity']}股)"
        else:
            sectors = ', '.join(event.get('affected_sectors', []))
            affected_info = f"受影響產業: {sectors}" if sectors else "全市場影響"
        
        events_summary.append(f"""
事件 {i}:
- 日期: {event['date'].strftime('%Y-%m-%d')} (D{days_until:+d}) {priority}
- 類型: {event_type}
- 名稱: {event['event_name']}
- 國家: {event['country']}
- Impact: {event['impact']}
- 關聯度: {event['relevance_score']:.0%}
- {affected_info}
- 前值: {event.get('previous') if event.get('previous') is not None else 'N/A'}
- 預期: {event.get('estimate') if event.get('estimate') is not None else 'N/A'}
- 實際: {event.get('actual') if event.get('actual') is not None else '待公布'}
        """)
    
    # 準備產業分布
    sector_summary = "\n".join([
        f"  - {sector}: {weight*100:.1f}%"
        for sector, weight in portfolio_info['sectors'].items()
    ])
    
    # 準備國家分布
    country_summary = "\n".join([
        f"  - {country}: {weight*100:.1f}%"
        for country, weight in portfolio_info['countries'].items()
    ])
    
    prompt = f"""
你是專業的投資組合事件分析師。以下是系統已匹配的相關事件和用戶的投資組合。

## 投資組合概況
- 總市值: ${portfolio_info['total_value']:,.2f}
- 產業分布:
{sector_summary}
- 國家分布:
{country_summary}

## 未來事件清單（已按關聯度和日期篩選，僅列出前20個）
{chr(10).join(events_summary)}

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
    
    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ AI 分析生成失敗: {str(e)}\n\n請檢查 OpenAI API Key 是否正確，或稍後再試。"

# ==================== 主程式 ====================
st.title("🔔 AI投資組合事件提醒系統")
st.markdown("---")

# 側邊欄
with st.sidebar:
    st.header("⚙️ 系統設定")
    
    st.subheader("🔑 API 金鑰")
    fmp_api_key = st.text_input("FMP API Key *", type="password", help="【必填】用於獲取公司資料（免費帳號可用）")
    alphavantage_api_key = st.text_input("Alpha Vantage API Key *", type="password", help="【必填】用於獲取財報日曆")
    openai_api_key = st.text_input("OpenAI API Key", type="password", help="【選填】用於 AI 深度分析，不填只顯示事件清單")
    
    st.markdown("---")
    st.subheader("📂 投資組合")
    
    # 範例 CSV
    sample_csv = """AAPL,100
MSFT,50
TSLA,30
JPM,200
JNJ,150"""
    
    st.download_button(
        label="📥 下載 CSV 範例檔案",
        data=sample_csv,
        file_name="portfolio_example.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    st.info("**CSV 格式**: 股票代碼,持股數量\n（無需標題列，每行一支股票）")
    
    uploaded_file = st.file_uploader("上傳投資組合 CSV", type=['csv'])
    
    st.markdown("---")
    st.subheader("📅 日曆設定")
    
    col1, col2 = st.columns(2)
    with col1:
        from_date = st.date_input("起始日期", value=datetime.now())
    with col2:
        to_date = st.date_input("結束日期", value=datetime.now() + timedelta(days=90))
    
    st.caption("📌 日期範圍將用於篩選財報事件和經濟事件")
    
    st.markdown("---")
    
    use_economic_calendar = st.checkbox("使用經濟行事曆 (Economic Calendar)", value=False, help="需要 FMP 付費訂閱方案")
    
    if use_economic_calendar:
        st.caption("💡 經濟行事曆需要 FMP 付費訂閱，若 API Key 無權限將無法獲取資料")
    
    st.markdown("---")
    st.subheader("🎯 篩選條件")
    
    impact_filter = st.selectbox(
        "Impact 等級",
        options=['High', 'Medium', 'Low'],
        index=1,
        help="Medium: 包含 High + Medium；Low: 包含全部"
    )
    
    selected_countries = st.multiselect(
        "關注國家",
        options=list(COUNTRY_MAPPING.keys()),
        default=['美國', '台灣'],
        help="只顯示這些國家的經濟事件"
    )
    
    st.markdown("---")
    run_button = st.button("🚀 執行分析", type="primary", use_container_width=True)
    
    st.markdown("---")
    st.caption("### ⚠️ 免責聲明")
    st.caption("""
本系統僅供學術研究與教育用途，AI提供的數據與分析結果僅供參考，
**不構成投資建議或財務建議**。請使用者自行判斷投資決策，並承擔相關風險。
本系統作者不對任何投資行為負責，亦不承擔任何損失責任。
    """)

# 主內容
if uploaded_file is not None:
    try:
        portfolio_df = pd.read_csv(uploaded_file, header=None, names=['symbol', 'quantity'])
        portfolio_df['symbol'] = portfolio_df['symbol'].str.strip().str.upper()
        
        st.success(f"✅ 已載入 {len(portfolio_df)} 檔股票")
        
        with st.expander("📋 查看上傳的投資組合", expanded=True):
            st.dataframe(portfolio_df, use_container_width=True)
        
    except Exception as e:
        st.error(f"CSV 讀取失敗: {str(e)}")
        st.stop()
else:
    st.info("👆 請從左側邊欄上傳投資組合 CSV 檔案開始")
    st.stop()

# 執行分析
if run_button:
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
    
    st.markdown("---")
    st.header("📊 分析結果")
    
    # Step 1: 獲取公司基本資料
    with st.spinner("正在獲取公司基本資料..."):
        holdings_data = []
        failed_symbols = []
        
        progress_bar = st.progress(0)
        
        for idx, row in portfolio_df.iterrows():
            symbol = row['symbol']
            quantity = row['quantity']
            
            profile = get_fmp_profile(symbol, fmp_api_key)
            
            if profile:
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
            time.sleep(0.3)
        
        progress_bar.empty()
        
        if failed_symbols:
            st.warning(f"⚠️ 以下股票無法獲取資料: {', '.join(failed_symbols)}")
        
        if not holdings_data:
            st.error("❌ 沒有有效的股票資料，無法進行分析")
            st.stop()
        
        holdings_df = pd.DataFrame(holdings_data)
        portfolio_dist = calculate_portfolio_distribution(holdings_df)
        
        st.success(f"✅ 成功獲取 {len(holdings_df)} 支股票的資料")
    
    # 顯示投資組合概況
    with st.expander("💼 投資組合概況", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("總市值", f"${portfolio_dist['total_value']:,.2f}")
        
        with col2:
            st.metric("持股數量", len(holdings_df))
        
        with col3:
            st.metric("涵蓋產業", len(portfolio_dist['sectors']))
        
        st.subheader("產業分布")
        sector_df = pd.DataFrame([
            {'產業': sector, '比例': f"{weight*100:.1f}%", '市值': f"${portfolio_dist['total_value']*weight:,.2f}"}
            for sector, weight in portfolio_dist['sectors'].items()
        ]).sort_values('比例', ascending=False)
        st.dataframe(sector_df, use_container_width=True, hide_index=True)
        
        st.subheader("國家分布")
        country_df = pd.DataFrame([
            {'國家': country, '比例': f"{weight*100:.1f}%", '市值': f"${portfolio_dist['total_value']*weight:,.2f}"}
            for country, weight in portfolio_dist['countries'].items()
        ]).sort_values('比例', ascending=False)
        st.dataframe(country_df, use_container_width=True, hide_index=True)
    
    # Step 2: 獲取日曆資料
    st.markdown("---")
    
    with st.spinner("正在獲取日曆資料..."):
        # Earning Calendar
        earning_df = get_earning_calendar(alphavantage_api_key)
        
        # Economic Calendar（只有在用戶勾選時才獲取）
        economic_df = None
        if use_economic_calendar:
            from_date_str = from_date.strftime('%Y-%m-%d')
            to_date_str = to_date.strftime('%Y-%m-%d')
            economic_df = get_economic_calendar(from_date_str, to_date_str, fmp_api_key)
            
            if economic_df is None or economic_df.empty:
                st.warning("⚠️ 無法獲取經濟行事曆資料，可能是 API Key 無權限或網路問題")
    
    # Step 3: 事件匹配
    with st.spinner("正在匹配相關事件..."):
        portfolio_symbols = set(holdings_df['symbol'].tolist())
        
        # Layer 1: 財報匹配
        earning_events = match_earning_events(earning_df, portfolio_symbols, holdings_df)
        
        # Layer 2 & 3: 經濟事件匹配（只有在用戶勾選且有資料時才進行）
        economic_events = []
        if use_economic_calendar and economic_df is not None and not economic_df.empty:
            selected_country_codes = [COUNTRY_MAPPING[c] for c in selected_countries if c in COUNTRY_MAPPING]
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
        
        # 計算天數
        for event in all_events:
            event['days_until'] = calculate_days_until(event['date'])
            event['priority'] = get_priority_emoji(event['days_until'])
    
    st.success(f"✅ 找到 {len(all_events)} 個相關事件（財報: {len(earning_events)}, 經濟: {len(economic_events)}）")
    
    # Step 4: 顯示事件表格
    st.markdown("---")
    st.subheader("📅 相關事件時間表")
    
    if all_events:
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
                '前值': event.get('previous') if event.get('previous') is not None else '-',
                '預期': event.get('estimate') if event.get('estimate') is not None else '-',
                '實際': event.get('actual') if event.get('actual') is not None else '-'
            })
        
        events_table_df = pd.DataFrame(table_data)
        
        # 顯示表格
        st.dataframe(events_table_df, use_container_width=True, height=500, hide_index=True)
        
        # 下載按鈕
        csv_data = events_table_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 下載事件清單 CSV",
            data=csv_data,
            file_name=f"events_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.warning("⚠️ 未找到相關事件")
    
    # Step 5: AI 分析（只有在有 OpenAI API Key 時才執行）
    if all_events and has_openai_key:
        st.markdown("---")
        st.subheader("🤖 AI 深度分析")
        
        with st.spinner("AI 正在生成深度分析..."):
            ai_report = generate_ai_analysis(
                all_events,
                portfolio_dist,
                openai_api_key
            )
            
            st.markdown(ai_report)
    elif all_events and not has_openai_key:
        st.markdown("---")
        st.info("💡 提供 OpenAI API Key 可獲得 AI 深度分析報告\n\n包含：異常檢測、密集事件週識別、產業連鎖反應分析、智慧提醒等功能")
    
    st.markdown("---")
    st.success("✅ 分析完成！")

else:
    if uploaded_file:
        st.info("👈 請設定篩選條件並點擊「執行分析」按鈕")