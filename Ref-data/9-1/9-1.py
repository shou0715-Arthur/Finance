import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import json
from datetime import datetime, timedelta
import numpy as np
from openai import OpenAI
import time
import io

st.set_page_config(
    page_title="AI投資組合壓力測試系統",
    page_icon="📊",
    layout="wide"
)

# ==================== 情境模板定義 ====================
SCENARIO_TEMPLATES = {
    "俄烏戰爭_2022": {
        "name": "地緣政治衝突（參考：2022俄烏戰爭）",
        "historical_event": "2022年2月俄羅斯入侵烏克蘭",
        "description": """
        **歷史影響摘要：**
        - 標普500在3-4週內下跌約10-12%
        - 能源股因油價飆升而上漲25%
        - 科技股下跌18%，金融股下跌15%
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
    },
    "油價崩盤_2020": {
        "name": "油價崩盤（參考：2020年COVID衝擊）",
        "historical_event": "2020年3月COVID-19疫情 + 油價暴跌",
        "description": """
        **歷史影響摘要：**
        - 標普500在4-5週內暴跌34%
        - 能源股崩盤50%（石油服務業-77%）
        - 房地產下跌72%，酒店娛樂下跌70%
        - 科技股相對抗跌，下跌20%
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
    },
    "激進升息_2022": {
        "name": "激進升息（參考：2022年聯準會抗通膨）",
        "historical_event": "2022年聯準會升息4.5個百分點",
        "description": """
        **歷史影響摘要：**
        - 標普500全年下跌18.1%
        - 科技股（納斯達克）暴跌32.5%
        - 能源股逆勢大漲59%
        - 房地產下跌25%，通訊服務下跌40%
        """,
        "icon": "💰",
        "market_benchmark": {
            "sp500_change": -0.181,
            "duration_weeks": 52
        },
        "sector_impacts": {
            "Energy": 0.59,
            "Technology": -0.33,
            "Communication Services": -0.40,
            "Consumer Cyclical": -0.37,
            "Real Estate": -0.25,
            "Financial Services": -0.10,
            "Basic Materials": -0.07,
            "Industrials": -0.05,
            "Consumer Defensive": -0.03,
            "Healthcare": -0.02,
            "Utilities": -0.02
        }
    },
    "貿易戰_2018": {
        "name": "貿易戰（參考：2018美中貿易戰）",
        "historical_event": "2018年Q4美中貿易戰升級",
        "description": """
        **歷史影響摘要：**
        - 標普500在Q4下跌13.5%
        - 工業股下跌18%（供應鏈擔憂）
        - 科技股下跌17%
        - 必需消費品相對抗跌，僅下跌5%
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
    },
    "金融危機_2008": {
        "name": "金融危機（參考：2008雷曼兄弟倒閉）",
        "historical_event": "2008年9月雷曼兄弟破產",
        "description": """
        **歷史影響摘要：**
        - 標普500在4個月內暴跌42%
        - 金融股崩盤55%
        - 非必需消費品和房地產下跌50%
        - 必需消費品最抗跌，僅下跌15%
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
    },
    "全球關稅戰_2025": {
        "name": "全球關稅戰（參考：2025川普關稅政策）",
        "historical_event": "2025年4月「Liberation Day」全面關稅",
        "description": """
        **歷史影響摘要：**
        - 標普500在宣布前6週內下跌10.1%，政策持續引發震盪
        - 科技股因中國供應鏈依賴受創（Nvidia -4.89%, AMD -7.7%）
        - 汽車業損失慘重（通用汽車單季損失$11億）
        - 4月9日宣布90天暫停，市場單日暴漲9.52%
        - VIX恐慌指數飆升至25，政策不確定性創40年新高
        - 能源類股逆勢上漲（稀土材料股MP Materials +15%）
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
    },
    "黑天鵝_自訂": {
        "name": "黑天鵝事件（AI自訂參數）",
        "historical_event": "用戶自訂極端情境",
        "description": """
        **使用方式：**
        描述您想模擬的情境（例如：「美國國債違約」），
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
}

# 產業映射表
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

# ==================== FMP API 函數 ====================
def get_fmp_quote(symbol, api_key):
    """獲取即時報價"""
    url = f"https://financialmodelingprep.com/stable/quote?symbol={symbol}&apikey={api_key}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data and len(data) > 0:
            return data[0]
        return None
    except Exception as e:
        st.error(f"獲取 {symbol} 報價失敗: {str(e)}")
        return None

def get_fmp_profile(symbol, api_key):
    """獲取公司基本資料（產業分類）"""
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

def get_fmp_historical(symbol, api_key):
    """獲取歷史股價（過去1年）"""
    url = f"https://financialmodelingprep.com/stable/historical-price-eod/full?symbol={symbol}&apikey={api_key}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data and isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            # 只取最近252個交易日（約1年）
            return df.tail(252)
        return None
    except Exception as e:
        st.error(f"獲取 {symbol} 歷史數據失敗: {str(e)}")
        return None

def get_fmp_key_metrics(symbol, api_key):
    """獲取關鍵指標（Beta值）"""
    url = f"https://financialmodelingprep.com/stable/key-metrics?symbol={symbol}&apikey={api_key}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data and len(data) > 0:
            return data[0]
        return None
    except Exception as e:
        st.error(f"獲取 {symbol} Beta值失敗: {str(e)}")
        return None

# ==================== 計算函數 ====================
def calculate_volatility(historical_df):
    """計算年化波動率"""
    if historical_df is None or len(historical_df) < 30:
        return 0.20  # 預設20%
    
    # 計算日收益率
    returns = historical_df['close'].pct_change().dropna()
    
    # 計算年化標準差（假設252個交易日）
    daily_volatility = returns.std()
    annual_volatility = daily_volatility * np.sqrt(252)
    
    return annual_volatility

def calculate_stress_impact(sector_impact, beta, volatility, severity):
    """
    混合式計算壓力測試影響
    
    參數：
    - sector_impact: 該產業的歷史影響（例如：-0.18）
    - beta: 該股票的Beta值
    - volatility: 該股票的歷史波動率
    - severity: 用戶設定的嚴重度係數（0.5-2.0）
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

def map_sector(fmp_sector):
    """映射FMP產業到我們的分類"""
    return SECTOR_MAPPING.get(fmp_sector, fmp_sector)

# ==================== OpenAI 函數 ====================
def generate_ai_scenario(scenario_description, openai_api_key):
    """黑天鵝模式：AI生成自訂情境參數"""
    client = OpenAI(api_key=openai_api_key)
    
    prompt = f"""
你是一位專業的金融風險分析師。用戶描述了一個極端市場情境：

"{scenario_description}"

請分析這個情境對各產業的影響，並以JSON格式輸出。

輸出格式（純JSON，不要包含任何其他文字或markdown標記）：
{{
  "scenario_name": "情境名稱",
  "description": "情境詳細說明（2-3句話）",
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

重要：
1. sector_impacts的值範圍應在-0.60到+0.40之間
2. 必須包含所有11個產業（Energy, Technology, Financial Services, Industrials, Consumer Cyclical, Consumer Defensive, Healthcare, Communication Services, Utilities, Real Estate, Basic Materials）
3. 只輸出JSON，不要有其他內容
"""
    
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

def generate_ai_analysis(portfolio_results, scenario_info, openai_api_key):
    """生成AI分析報告"""
    client = OpenAI(api_key=openai_api_key)
    
    # 準備數據摘要
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
    
    prompt = f"""
你是一位資深的量化風險分析師，專精於投資組合壓力測試與風險評估。請針對以下壓力測試結果，提供一份**詳細且深度的風險分析報告**（目標2000字以上）。

**重要準則：**
1. **絕對禁止**提供具體的投資建議（如：應買入、賣出、減碼、加碼、持有等操作建議）
2. 報告應**聚焦於風險識別、風險量化、脆弱性分析**
3. 使用專業金融術語，目標讀者為有經驗的投資者
4. 保持客觀中立，基於數據分析而非主觀判斷
5. 深入分析風險傳導路徑和潛在連鎖效應

---

## 情境背景
{scenario_info['description']}

標普500預期影響：{scenario_info['market_benchmark']['sp500_change']*100:.1f}%
影響持續時間：約{scenario_info['market_benchmark']['duration_weeks']}週

---

## 投資組合壓力測試結果

### 整體指標
- 原始市值：${total_original:,.2f}
- 壓力測試後市值：${total_predicted:,.2f}
- 預估變化：{total_change_pct:+.2f}%
- 風險初步評級：{risk_level}

### 產業配置分布
{sector_summary}

### 個股壓力測試結果
{holdings_summary}

---

## 報告要求

請以Markdown格式輸出，包含以下章節：

### 📋 執行摘要（Executive Summary）
[50-80字的精煉總結，直接點出核心風險與投資組合在此情境下的主要脆弱點]

### 🎯 投資組合韌性評估（Portfolio Resilience Assessment）

#### 整體風險量化
- **風險評級**：[根據損失幅度評定：損失<5%為低風險，5-15%為中風險，>15%為高風險]
- **預估最大損失**：[具體金額與百分比]
- **風險集中度分析**：[指出哪些產業或個股佔據主要風險敞口]

#### 脆弱性分析
- **最脆弱部位識別**：[列出受創最嚴重的前3-5個持股，說明其脆弱的結構性原因]
- **產業層面風險**：[分析哪些產業在此情境下風險最高，原因為何]
- **Beta與波動率分析**：[評估高Beta或高波動個股對整體風險的貢獻]

#### 相對抗跌部位
- [指出表現相對穩健的持股，分析其抗跌特性的來源]

### 📊 情境風險傳導分析（Risk Transmission Analysis）

#### 一階效應（Direct Impact）
- [分析情境對各產業的直接衝擊機制]
- [說明為何某些產業受創特別嚴重]

#### 二階效應（Cascading Risk）
- [探討可能的連鎖反應和間接影響]
- [評估產業間的風險關聯性]
- [分析是否存在系統性風險放大因子]

#### 尾部風險評估（Tail Risk）
- [評估極端情境下的潛在損失]
- [指出可能被低估的風險點]

### 🔍 關鍵風險因子深度剖析（Deep Dive on Risk Factors）

[針對3-5個最重要的風險驅動因子進行深入分析，每個因子包括：]
- 風險描述
- 影響機制
- 對投資組合的具體影響路徑
- 風險程度評估（量化）

### ⚠️ 風險警示與監控要點（Risk Alerts & Monitoring）

#### 高優先級風險警示
- [列出3-5個最需要密切關注的風險點]
- [每個警示應包含：風險描述、觸發條件、潛在影響]

#### 關鍵監控指標
- [建議應持續追蹤的市場指標或個股指標]
- [設定預警閾值的建議]

#### 情境演變可能性
- [分析情境可能如何演變（惡化或緩解）]
- [指出值得關注的市場信號]

### 📈 產業配置結構分析（Sector Allocation Structure）
- [評估當前產業配置在此情境下的適切性]
- [指出過度集中或曝險不足的產業]
- [從風險分散角度分析配置結構]

### 💡 風險管理視角（Risk Management Perspective）

**注意：本節僅提供風險管理思維方向，不提供具體操作建議**

- [從風險管理角度探討可能的思考方向]
- [分析不同風險管理策略的優劣（純理論討論）]
- [指出投資組合在風險管理上的盲點或不足]

### 🔬 技術性風險指標分析（Technical Risk Metrics）
- [分析投資組合的VaR（風險價值）特徵]
- [評估夏普比率在壓力情境下的變化]
- [計算並解讀最大回撤風險]

### 📌 總結與風險展望（Conclusion & Risk Outlook）
[總結核心風險，展望情境可能的發展方向，強調需要持續監控的要點]

---

**報告撰寫原則：**
- 使用專業金融術語（VaR, Beta, Sharpe Ratio, 尾部風險等）
- 每個分析點都要有數據或邏輯支撐
- 深入探討「為什麼」而非只描述「是什麼」
- 保持客觀中立，避免情緒化描述
- **絕對不能**出現「建議買入/賣出/減碼/加碼/持有」等投資指示
- 重點在於**識別風險、量化風險、理解風險**，而非提供交易建議

請用繁體中文撰寫，展現專業深度。
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ AI分析生成失敗: {str(e)}\n\n請檢查OpenAI API Key是否正確，或稍後再試。"

# ==================== 主程式 ====================
st.title("🎯 AI投資組合壓力測試系統")
st.markdown("---")

# 側邊欄
with st.sidebar:
    st.header("📁 投資組合設定")
    
    # 提供範例下載
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
    
    st.info("**CSV格式**：股票代碼,持股數量,購入成本（無需標題列）")
    
    # CSV上傳
    uploaded_file = st.file_uploader("上傳投資組合CSV", type=['csv'])
    
    st.markdown("---")
    st.header("🎯 壓力測試情境")
    
    # 情境選擇
    scenario_key = st.selectbox(
        "選擇歷史參考情境",
        options=list(SCENARIO_TEMPLATES.keys()),
        format_func=lambda x: f"{SCENARIO_TEMPLATES[x]['icon']} {SCENARIO_TEMPLATES[x]['name']}"
    )
    
    selected_scenario = SCENARIO_TEMPLATES[scenario_key]
    
    # 顯示情境說明
    with st.expander("📖 歷史事件詳情", expanded=True):
        st.markdown(f"**{selected_scenario['historical_event']}**")
        st.markdown(selected_scenario['description'])
    
    # 黑天鵝自訂模式
    custom_scenario_desc = None
    if selected_scenario.get("custom_mode"):
        st.markdown("### 🦢 自訂情境描述")
        custom_scenario_desc = st.text_area(
            "描述您想模擬的極端情境",
            placeholder="例如：美國國債違約、全球糧食危機、量子電腦突破導致加密技術崩潰...",
            height=100
        )
    
    # 進階設定
    with st.expander("⚙️ 進階參數調整", expanded=False):
        severity = st.slider(
            "情境嚴重度",
            min_value=0.5,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="1.0 = 歷史事件原始影響，>1.0 = 更嚴重，<1.0 = 較溫和"
        )
        st.caption(f"將歷史影響數據 × {severity}")
    
    st.markdown("---")
    st.header("🔑 API設定")
    
    fmp_api_key = st.text_input("FMP API Key", type="password")
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    
    st.markdown("---")
    
    # 執行按鈕
    run_button = st.button("🚀 執行壓力測試", type="primary", use_container_width=True)
    
    st.markdown("---")
    st.caption("### ⚠️ 免責聲明")
    st.caption("""
本系統僅供學術研究與教育用途，AI提供的數據與分析結果僅供參考，
**不構成投資建議或財務建議**。請使用者自行判斷投資決策，並承擔相關風險。
本系統作者不對任何投資行為負責，亦不承擔任何損失責任。
    """)

# 主內容區
if uploaded_file is not None:
    # 讀取CSV
    try:
        portfolio_df = pd.read_csv(uploaded_file, header=None, names=['symbol', 'quantity', 'cost'])
        
        st.success(f"✅ 已載入 {len(portfolio_df)} 檔股票")
        
        # 顯示投資組合
        with st.expander("📋 查看上傳的投資組合", expanded=True):
            st.dataframe(portfolio_df, use_container_width=True)
        
    except Exception as e:
        st.error(f"CSV讀取失敗: {str(e)}")
        st.stop()
else:
    st.info("👆 請從左側邊欄上傳投資組合CSV檔案開始")
    st.stop()

# 執行壓力測試
if run_button:
    if not fmp_api_key:
        st.error("❌ 請輸入FMP API Key")
        st.stop()
    
    if not openai_api_key:
        st.error("❌ 請輸入OpenAI API Key")
        st.stop()
    
    # 處理黑天鵝自訂模式
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
                
                with st.expander("🔍 查看AI生成的情境參數", expanded=True):
                    st.markdown(f"**情境名稱**: {ai_scenario['scenario_name']}")
                    st.markdown(f"**說明**: {ai_scenario['description']}")
                    st.markdown(f"**AI分析**: {ai_scenario['reasoning']}")
            else:
                st.error("AI情境生成失敗，請檢查描述或稍後再試")
                st.stop()
    
    st.markdown("---")
    st.header("📊 投資組合分析結果")
    
    # 獲取所有股票數據
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
        pnl = predicted_value - current_value  # 壓力測試後的市值變化
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
        
        time.sleep(0.3)  # 避免API限制
    
    progress_bar.empty()
    status_text.empty()
    
    # 顯示排除的股票
    if excluded_stocks:
        st.warning(f"⚠️ 以下股票已被排除：")
        for stock in excluded_stocks:
            st.caption(f"- {stock}")
    
    if not holdings_data:
        st.error("❌ 沒有有效的股票數據，無法進行壓力測試")
        st.stop()
    
    # 創建結果DataFrame
    holdings_df = pd.DataFrame(holdings_data)
    
    # 計算總結
    total_original_value = holdings_df['current_value'].sum()
    total_predicted_value = holdings_df['predicted_value'].sum()
    total_change = total_predicted_value - total_original_value
    total_change_pct = (total_change / total_original_value) * 100
    
    # 1. 壓力測試結果摘要
    st.subheader("💰 壓力測試結果摘要")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="原始市值",
            value=f"${total_original_value:,.2f}"
        )
    
    with col2:
        st.metric(
            label="預測市值",
            value=f"${total_predicted_value:,.2f}",
            delta=f"{total_change_pct:.2f}%"
        )
    
    with col3:
        change_color = "🔴" if total_change < 0 else "🟢"
        st.metric(
            label="預估損益",
            value=f"{change_color} ${total_change:,.2f}"
        )
    
    # 集中度風險警示
    holdings_df['weight'] = holdings_df['current_value'] / total_original_value
    concentrated_holdings = holdings_df[holdings_df['weight'] > 0.20]
    
    if not concentrated_holdings.empty:
        st.warning("⚠️ **集中度風險警示**")
        st.markdown("以下持股佔比超過20%，建議注意分散風險：")
        for _, row in concentrated_holdings.iterrows():
            st.caption(f"- {row['symbol']}: {row['weight']*100:.1f}%")
    
    st.markdown("---")
    
    # 2. 個股表現詳細表格
    st.subheader("📈 個股表現分析")
    
    # 準備顯示用的DataFrame
    display_df = holdings_df[[
        'symbol', 'sector', 'quantity', 'current_price', 'predicted_price', 
        'change_pct', 'pnl', 'current_value', 'predicted_value'
    ]].copy()
    
    display_df.columns = [
        '股票代碼', '產業', '持股數量', '當前價格', '預測價格', 
        '漲跌幅(%)', '損益($)', '當前市值', '預測市值'
    ]
    
    # 格式化數字
    display_df['當���價格'] = display_df['當前價格'].apply(lambda x: f"${x:.2f}")
    display_df['預測價格'] = display_df['預測價格'].apply(lambda x: f"${x:.2f}")
    display_df['漲跌幅(%)'] = display_df['漲跌幅(%)'].apply(lambda x: f"{x:+.2f}%")
    display_df['損益($)'] = display_df['損益($)'].apply(lambda x: f"${x:+,.2f}")
    display_df['當前市值'] = display_df['當前市值'].apply(lambda x: f"${x:,.2f}")
    display_df['預測市值'] = display_df['預測市值'].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(display_df, use_container_width=True, height=400)
    
    # 3. 視覺化圖表
    st.markdown("---")
    st.subheader("📊 視覺化分析")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("**產業分布（當前市值）**")
        sector_distribution = holdings_df.groupby('sector')['current_value'].sum()
        
        fig_sector = go.Figure(data=[go.Pie(
            labels=sector_distribution.index,
            values=sector_distribution.values,
            hole=0.3,
            textinfo='label+percent'
        )])
        fig_sector.update_layout(height=400, showlegend=True)
        st.plotly_chart(fig_sector, use_container_width=True)
    
    with col_chart2:
        st.markdown("**個股表現排名**")
        top_bottom = pd.concat([
            holdings_df.nsmallest(5, 'change_pct'),
            holdings_df.nlargest(5, 'change_pct')
        ]).sort_values('change_pct')
        
        fig_performance = go.Figure(data=[go.Bar(
            x=top_bottom['change_pct'],
            y=top_bottom['symbol'],
            orientation='h',
            marker_color=['red' if x < 0 else 'green' for x in top_bottom['change_pct']]
        )])
        fig_performance.update_layout(
            height=400,
            xaxis_title="變化百分比 (%)",
            yaxis_title="股票代碼"
        )
        st.plotly_chart(fig_performance, use_container_width=True)
    
    # 4. AI分析報告
    st.markdown("---")
    st.subheader("🤖 AI深度分析報告")
    
    with st.spinner("AI正在生成分析報告..."):
        portfolio_results = {
            'total_original_value': total_original_value,
            'total_predicted_value': total_predicted_value,
            'total_change_pct': total_change_pct,
            'holdings_df': holdings_df
        }
        
        ai_report = generate_ai_analysis(
            portfolio_results, 
            selected_scenario, 
            openai_api_key
        )
        
        st.markdown(ai_report)
    
    st.markdown("---")
    st.success("✅ 壓力測試完成！")

else:
    if uploaded_file:
        st.info("👈 請設定情境參數並點擊「執行壓力測試」按鈕")