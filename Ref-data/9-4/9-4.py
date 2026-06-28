import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

st.set_page_config(
    page_title="內部人交易分析系統",
    page_icon="🔍",
    layout="wide"
)

# ==================== 交易類型資料 ====================
TRANSACTION_CODES = {
    'P-Purchase': {'中文': '公開市場購買', '價值': '⭐⭐⭐⭐⭐', '類別': '一般交易代碼', '說明': '用真金白銀買入 - 最強看好信號'},
    'S-Sale': {'中文': '公開市場出售', '價值': '⭐⭐', '類別': '一般交易代碼', '說明': '需結合其他交易判斷'},
    'V-Voluntary': {'中文': '自願提前申報', '價值': 'ℹ️', '類別': '一般交易代碼', '說明': '僅表示申報時間'},
    'A-Award': {'中文': '獎勵授予', '價值': '⭐', '類別': 'Rule 16b-3 豁免交易代碼', '說明': '薪酬計劃無分析價值'},
    'D-Return': {'中文': '回售公司', '價值': '⭐', '類別': 'Rule 16b-3 豁免交易代碼', '說明': '技術性交易'},
    'F-InKind': {'中文': '以股支付', '價值': '⭐', '類別': 'Rule 16b-3 豁免交易代碼', '說明': '常與M和S組合出現'},
    'I-Discretionary': {'中文': '全權委託交易', '價值': '⭐⭐', '類別': 'Rule 16b-3 豁免交易代碼', '說明': '可能有意義需查看上下文'},
    'M-Exempt': {'中文': '行權/轉換豁免', '價值': '⭐', '類別': 'Rule 16b-3 豁免交易代碼', '說明': '薪酬計劃到期'},
    'C-Conversion': {'中文': '衍生品轉換', '價值': '⭐', '類別': '衍生證券代碼', '說明': '技術性操作'},
    'E-ExpireShort': {'中文': '空頭部位到期', '價值': '⭐', '類別': '衍生證券代碼', '說明': '技術性操作'},
    'H-ExpireLong': {'中文': '多頭部位到期', '價值': '⭐', '類別': '衍生證券代碼', '說明': '技術性操作'},
    'O-OutOfTheMoney': {'中文': '價外行權', '價值': '⭐', '類別': '衍生證券代碼', '說明': '罕見情況'},
    'X-InTheMoney': {'中文': '價內行權', '價值': '⭐⭐', '類別': '衍生證券代碼', '說明': '正常行權操作'},
    'G-Gift': {'中文': '贈與', '價值': '❌', '類別': '其他Section 16(b)豁免交易代碼', '說明': '無投資價值'},
    'L-Small': {'中文': '小額收購', '價值': '⭐', '類別': '其他Section 16(b)豁免交易代碼', '說明': '金額太小通常忽略'},
    'W-Will': {'中文': '遺囑/繼承', '價值': '❌', '類別': '其他Section 16(b)豁免交易代碼', '說明': '無投資價值'},
    'Z-Trust': {'中文': '信託操作', '價值': '⭐', '類別': '其他Section 16(b)豁免交易代碼', '說明': '技術性操作'},
    'J-Other': {'中文': '其他交易', '價值': '❓', '類別': '特殊交易代碼', '說明': '需要查看註腳'},
    'K-Swap': {'中文': '股權互換', '價值': '⭐⭐', '類別': '特殊交易代碼', '說明': '複雜金融操作'},
    'U-Tender': {'中文': '要約收購', '價值': '⭐⭐⭐', '類別': '特殊交易代碼', '說明': '公司併購相關'}
}

# ==================== API 函數 ====================
@st.cache_data(ttl=3600)
def get_company_profile(symbol, api_key):
    """獲取公司基本資料"""
    url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={api_key}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data and len(data) > 0:
            return data[0]
        return None
    except Exception as e:
        st.error(f"獲取公司資料失敗: {str(e)}")
        return None

@st.cache_data(ttl=1800)
def get_insider_trading_by_symbol(symbol, api_key):
    """按公司代碼獲取內部人交易"""
    url = f"https://financialmodelingprep.com/api/v4/insider-trading?symbol={symbol}&page=0&limit=100&apikey={api_key}"
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        if data and isinstance(data, list):
            return data
        return []
    except Exception as e:
        st.error(f"獲取內部人交易資料失敗: {str(e)}")
        return []

@st.cache_data(ttl=1800)
def get_insider_trading_by_cik(cik, api_key):
    """按內部人CIK獲取交易記錄"""
    url = f"https://financialmodelingprep.com/api/v4/insider-trading?reportingCik={cik}&page=0&limit=100&apikey={api_key}"
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        if data and isinstance(data, list):
            return data
        return []
    except Exception as e:
        st.error(f"獲取內部人交易資料失敗: {str(e)}")
        return []

# ==================== 數據處理函數 ====================
def process_insider_data(raw_data):
    """處理內部人交易數據"""
    if not raw_data:
        return pd.DataFrame()
    
    processed_data = []
    
    for trade in raw_data:
        # 計算交易金額
        transaction_value = trade.get('securitiesTransacted', 0) * trade.get('price', 0)
        
        # 處理買入/賣出 - 直接使用 acquisitionOrDisposition
        acq_disp = trade.get('acquisitionOrDisposition', '')
        
        processed_data.append({
            '交易日期': trade.get('transactionDate', ''),
            '股票代碼': trade.get('symbol', ''),
            '內部人姓名': trade.get('reportingName', ''),
            '內部人代碼': trade.get('reportingCik', ''),
            '職位': trade.get('typeOfOwner', ''),
            '交易類型': trade.get('transactionType', ''),
            '交易股數': trade.get('securitiesTransacted', 0),
            '交易價格': trade.get('price', 0),
            '交易金額': transaction_value,
            '交易後持股': trade.get('securitiesOwned', 0),
            'SEC_URL': trade.get('link', '')
        })
    
    df = pd.DataFrame(processed_data)
    
    # 排序：最新的在前面
    if not df.empty and '交易日期' in df.columns:
        df = df.sort_values('交易日期', ascending=False)
    
    return df

def format_number(num):
    """格式化數字為千分位"""
    try:
        return f"{int(num):,}"
    except:
        return str(num)

def format_currency(num):
    """格式化為貨幣"""
    try:
        return f"${num:,.2f}"
    except:
        return str(num)

def create_transaction_table(df):
    """創建顯示用的交易表格"""
    if df.empty:
        return pd.DataFrame()
    
    display_df = df.copy()
    
    # 格式化數字欄位
    display_df['交易股數'] = display_df['交易股數'].apply(format_number)
    display_df['交易價格'] = display_df['交易價格'].apply(format_currency)
    display_df['交易金額'] = display_df['交易金額'].apply(format_currency)
    display_df['交易後持股'] = display_df['交易後持股'].apply(format_number)
    
    # 準備最終顯示的欄位
    final_columns = [
        '交易日期', '股票代碼', '內部人姓名', '內部人代碼', '職位', 
        '交易類型', '交易股數', '交易價格', '交易金額', 
        '交易後持股', 'SEC_URL'
    ]
    
    return display_df[final_columns]

# ==================== 主程式 ====================
st.title("🔍 內部人交易分析系統")
st.markdown("---")

# ==================== 側邊欄 ====================
with st.sidebar:
    st.header("⚙️ 系統設定")
    
    # API 金鑰
    st.subheader("🔑 API 金鑰")
    fmp_api_key = st.text_input(
        "FMP API Key *", 
        type="password", 
        help="用於獲取內部人交易資料"
    )
    
    st.markdown("---")
    
    # 查詢設定
    st.subheader("🔍 查詢設定")
    
    # 公司代碼（必填）
    st.markdown("**🏢 公司代碼** *")
    symbol_input = st.text_input(
        "股票代碼",
        placeholder="例如: AAPL",
        help="輸入美股代碼",
        label_visibility="collapsed"
    ).upper().strip()
    st.caption("ℹ️ 輸入美股代碼")
    
    st.markdown("")
    
    # 內部人 CIK（可選）
    st.markdown("**👤 內部人 CIK** (可選)")
    cik_input = st.text_input(
        "內部人 CIK",
        placeholder="例如: 0001214156",
        help="從表格「內部人代碼」欄位複製",
        label_visibility="collapsed"
    ).strip()
    st.caption("ℹ️ 從表格「內部人代碼」欄位複製")
    
    st.markdown("---")
    
    # 執行分析按鈕
    run_button = st.button("🚀 執行分析", type="primary", use_container_width=True)
    
    st.markdown("---")
    
    # 使用說明
    st.subheader("📚 使用說明")
    st.markdown("""
    **基本使用**：
    1. 輸入公司股票代碼（必填）
    2. 點擊「執行分析」
    3. 查看「公司交易明細」頁籤
    
    **查詢特定內部人**：
    1. 從表格複製「內部人代碼」
    2. 貼到左側「內部人 CIK」輸入框
    3. 點擊「執行分析」
    4. 切換到「內部人交易明細」頁籤
    """)
    
    st.markdown("---")
    
    # 免責聲明
    st.caption("### ⚠️ 免責聲明")
    st.caption("""
本系統僅供學術研究與教育用途，資料來源為公開資訊。
**不構成投資建議或財務建議**。請使用者自行判斷投資決策，並承擔相關風險。
    """)

# ==================== 主要內容區域 ====================

# 檢查 API Key
if not fmp_api_key:
    st.info("👈 請在左側輸入 FMP API Key 開始使用")
    st.stop()

# 檢查是否執行分析
if not run_button:
    st.info("👈 請在左側輸入公司代碼，然後點擊「執行分析」開始")
    
    # 顯示簡單的使用說明
    st.markdown("""
    ## 🎯 系統功能
    
    本系統提供兩種查詢方式：
    
    ### 📊 公司交易明細
    - 查看指定公司的所有內部人交易記錄
    - 顯示每筆交易的詳細資訊
    - 包含「內部人代碼」方便進一步查詢
    
    ### 👤 內部人交易明細
    - 查看特定內部人在所有公司的交易記錄
    - 需要先從公司交易明細中複製「內部人代碼」
    - 了解該內部人的完整交易歷史
    
    ### 📋 交易明細功能
    - 完整顯示交易詳情
    - 點擊 SEC FORM 4 連結查看官方申報
    - 下載 CSV 進行進一步分析
    - 查看交易類型說明了解每種交易的意義
    """)
    st.stop()

# 檢查公司代碼
if not symbol_input:
    st.error("❌ 請輸入公司代碼")
    st.stop()

# ==================== 開始查詢 ====================

# 獲取公司資料和交易記錄
with st.spinner(f"正在獲取 {symbol_input} 的資料..."):
    company_profile = get_company_profile(symbol_input, fmp_api_key)
    company_trades = get_insider_trading_by_symbol(symbol_input, fmp_api_key)

# 如果有輸入 CIK，也獲取內部人交易
insider_trades = []
if cik_input:
    with st.spinner(f"正在獲取內部人交易記錄..."):
        insider_trades = get_insider_trading_by_cik(cik_input, fmp_api_key)

# ==================== 創建頁籤 ====================
tab1, tab2 = st.tabs(["📊 公司交易明細", "👤 內部人交易明細"])

# ==================== 頁籤 1: 公司交易明細 ====================
with tab1:
    # 顯示公司基本資訊
    if company_profile:
        st.subheader(f"📊 {symbol_input} - {company_profile.get('companyName', 'N/A')}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("當前價格", f"${company_profile.get('price', 0):.2f}")
        with col2:
            st.metric("產業", company_profile.get('sector', 'N/A'))
        with col3:
            market_cap = company_profile.get('mktCap', 0)
            if market_cap > 1e12:
                st.metric("市值", f"${market_cap/1e12:.2f}T")
            elif market_cap > 1e9:
                st.metric("市值", f"${market_cap/1e9:.2f}B")
            else:
                st.metric("市值", f"${market_cap/1e6:.2f}M")
    else:
        st.subheader(f"📊 {symbol_input}")
    
    st.markdown("---")
    
    # 檢查是否有交易記錄
    if not company_trades:
        st.warning(f"⚠️ 未找到 {symbol_input} 的內部人交易記錄")
    else:
        st.info(f"📅 顯示最近 {len(company_trades)} 筆交易記錄")
        
        # 處理數據
        df_company = process_insider_data(company_trades)
        
        if not df_company.empty:
            # 顯示交易明細表
            st.subheader("📋 內部人交易明細")
            
            display_df = create_transaction_table(df_company)
            
            st.dataframe(
                display_df,
                column_config={
                    '交易日期': st.column_config.DateColumn('交易日期', format='YYYY-MM-DD'),
                    '內部人代碼': st.column_config.TextColumn(
                        '內部人代碼',
                        help='複製此代碼到左側輸入框，可查詢該內部人的所有交易'
                    ),
                    'SEC_URL': st.column_config.LinkColumn(
                        'SEC FORM 4',
                        help='點擊查看 SEC 官方申報文件',
                        display_text='🔗 查看'
                    )
                },
                use_container_width=True,
                height=500,
                hide_index=True
            )
            
            st.info("💡 提示：複製「內部人代碼」到左側輸入框，切換到「內部人交易明細」頁籤可查詢該內部人的所有交易")
            
            # 下載 CSV
            st.markdown("---")
            csv_data = display_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 下載公司交易明細 CSV",
                data=csv_data,
                file_name=f"insider_trading_{symbol_input}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

# ==================== 頁籤 2: 內部人交易明細 ====================
with tab2:
    if not cik_input:
        # 未輸入 CIK 時顯示提示
        st.info("ℹ️ 請在左側輸入內部人 CIK")
        st.markdown("""
        ### 💡 如何使用
        
        1. 切換到「公司交易明細」頁籤
        2. 從表格中找到想查詢的內部人
        3. 複製該內部人的「內部人代碼」
        4. 貼到左側的「內部人 CIK」輸入框
        5. 點擊「執行分析」
        6. 返回此頁籤查看結果
        
        **範例**：
        - Tim Cook (Apple CEO) 的 CIK: `0001214156`
        - Satya Nadella (Microsoft CEO) 的 CIK: `0001618159`
        """)
    elif not insider_trades:
        st.warning(f"⚠️ 未找到 CIK {cik_input} 的交易記錄")
    else:
        # 顯示內部人資訊
        insider_name = insider_trades[0].get('reportingName', 'N/A')
        st.subheader(f"👤 {insider_name} 的所有交易記錄")
        st.info(f"📅 顯示最近 {len(insider_trades)} 筆交易記錄 | CIK: {cik_input}")
        
        st.markdown("---")
        
        # 處理數據
        df_insider = process_insider_data(insider_trades)
        
        if not df_insider.empty:
            # 顯示交易明細表
            st.subheader("📋 交易明細")
            
            display_df = create_transaction_table(df_insider)
            
            st.dataframe(
                display_df,
                column_config={
                    '交易日期': st.column_config.DateColumn('交易日期', format='YYYY-MM-DD'),
                    '內部人代碼': st.column_config.TextColumn('內部人代碼'),
                    'SEC_URL': st.column_config.LinkColumn(
                        'SEC FORM 4',
                        help='點擊查看 SEC 官方申報文件',
                        display_text='🔗 查看'
                    )
                },
                use_container_width=True,
                height=500,
                hide_index=True
            )
            
            # 顯示統計資訊
            st.markdown("---")
            st.subheader("📊 交易統計")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_trades = len(df_insider)
                st.metric("總交易筆數", f"{total_trades} 筆")
            
            with col2:
                buy_count = len(df_insider[df_insider['交易類型'].str.contains('P', na=False)])
                st.metric("買入相關", f"{buy_count} 筆")
            
            with col3:
                sell_count = len(df_insider[df_insider['交易類型'].str.contains('S', na=False)])
                st.metric("賣出相關", f"{sell_count} 筆")
            
            with col4:
                unique_companies = df_insider['股票代碼'].nunique()
                st.metric("涉及公司", f"{unique_companies} 家")
            
            # 下載 CSV
            st.markdown("---")
            csv_data = display_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 下載內部人交易明細 CSV",
                data=csv_data,
                file_name=f"insider_trading_{cik_input}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

# ==================== 交易類型說明（頁籤外共用） ====================
st.markdown("---")
st.markdown("---")

with st.expander("📚 交易類型說明 - 點擊展開", expanded=False):
    st.markdown("""
    以下是 SEC Form 4 中可能出現的交易類型及其含義：
    
    ### ⭐⭐⭐⭐⭐ 重要參考
    """)
    
    high_value_codes = {k: v for k, v in TRANSACTION_CODES.items() if '⭐⭐⭐⭐⭐' in v['價值']}
    for code, info in high_value_codes.items():
        st.markdown(f"""
        **{code}** | {info['中文']}  
        💡 {info['說明']}
        """)
    
    st.markdown("### ⭐⭐⭐ 需要分析")
    medium_value_codes = {k: v for k, v in TRANSACTION_CODES.items() if v['價值'] == '⭐⭐⭐'}
    for code, info in medium_value_codes.items():
        st.markdown(f"""
        **{code}** | {info['中文']}  
        💡 {info['說明']}
        """)
    
    st.markdown("### ⭐⭐ 補充參考")
    ref_value_codes = {k: v for k, v in TRANSACTION_CODES.items() if v['價值'] == '⭐⭐'}
    for code, info in ref_value_codes.items():
        st.markdown(f"""
        **{code}** | {info['中文']}  
        💡 {info['說明']}
        """)
    
    st.markdown("### ⭐ 技術性交易（通常可忽略）")
    low_value_codes = {k: v for k, v in TRANSACTION_CODES.items() if v['價值'] == '⭐'}
    for code, info in low_value_codes.items():
        st.markdown(f"""
        **{code}** | {info['中文']}  
        💡 {info['說明']}
        """)
    
    st.markdown("### ❌ 無分析價值（可忽略）")
    no_value_codes = {k: v for k, v in TRANSACTION_CODES.items() if v['價值'] == '❌'}
    for code, info in no_value_codes.items():
        st.markdown(f"""
        **{code}** | {info['中文']}  
        💡 {info['說明']}
        """)
    
    st.markdown("---")
    st.markdown("### 📖 完整交易類型清單")
    
    # 建立完整的交易類型 DataFrame
    codes_data = []
    for code, info in TRANSACTION_CODES.items():
        codes_data.append({
            '代碼': code,
            '中文名稱': info['中文'],
            '交易類別': info['類別'],
            '說明': info['說明']
        })
    
    codes_df = pd.DataFrame(codes_data)
    st.dataframe(codes_df, use_container_width=True, hide_index=True)
    
    # 下載交易類型 CSV
    codes_csv = codes_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 下載交易類型清單 CSV",
        data=codes_csv,
        file_name="transaction_codes.csv",
        mime="text/csv"
    )
    
    st.markdown("""
    ---
    ### 💡 如何判斷計劃性變現 vs 主動交易
    
    **計劃性變現的特徵**（正常薪酬兌現）：
    - 在 ±2 天內出現 M-Exempt + F-InKind + S-Sale 的組合
    - 這是公司股權激勵計劃到期的正常流程
    
    **主動交易**：
    - 單純的 P-Purchase 或 S-Sale，沒有 M-Exempt 和 F-InKind
    - 代表內部人主動決定買入或賣出，但仍然需要到SEC 官網確認其交易資訊，請勿單獨使用此資訊判斷進出場訊號
    - 確認方式請依照課程影片中的閱讀SEC FORM 4 教學判別
    
    建議：查看同一內部人在相近日期（±2天）的其他交易來判斷。
    """)