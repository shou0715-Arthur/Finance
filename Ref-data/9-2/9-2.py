"""
TradingView 策略分析系統
================================================

策略名稱: EMA Super 策略
策略來源: https://tw.tradingview.com/script/vEbaMVtL-EMA-Super/
Pine Script 版本: @version=6

================================================
策略說明
================================================

## 核心概念

EMA Super 策略是一個結合多重技術指標的趨勢追蹤系統，主要使用指數移動平均線（EMA）、
Supertrend 指標和 NovaWave 風格的趨勢雲來識別市場趨勢和交易機會。

本策略的核心理念是通過多層次的技術指標交叉驗證，來提高交易信號的可靠性。策略使用
5 條不同週期的 EMA（9, 21, 50, 100, 200）來觀察短期、中期和長期趨勢，並結合
Supertrend 指標來確認趨勢方向和強度。NovaWave 趨勢雲則提供視覺化的趨勢確認。

此策略適合在趨勢明確的市場中使用，能夠捕捉到主要的趨勢轉折點，並提供清晰的進出場
信號。

## 技術指標

本策略使用以下技術指標：

- **EMA 9**: 9 期指數移動平均線（快速 EMA，用於短期趨勢判斷）
- **EMA 21**: 21 期指數移動平均線（中期趨勢參考）
- **EMA 50**: 50 期指數移動平均線（中長期趨勢支撐）
- **EMA 100**: 100 期指數移動平均線（長期趨勢參考）
- **EMA 200**: 200 期指數移動平均線（主要趨勢線）
- **Supertrend**: 超級趨勢指標（ATR 週期 10，因子 4.0）
- **NovaWave Fast EMA**: 9 期 EMA（趨勢雲上軌）
- **NovaWave Slow EMA**: 21 期 EMA（趨勢雲下軌）
- **NovaWave Signal MA**: 10 期簡單移動平均線（信號線）
- **DMA 20**: 20 期位移移動平均線
- **DMA 50**: 50 期位移移動平均線
- **DMA 200**: 200 期位移移動平均線

## 買入條件

**買入信號觸發條件**：
- 當 NovaWave Fast EMA (9 期 EMA) 向上穿越 NovaWave Slow EMA (21 期 EMA) 時產生買入信號

數學表達式：
```
buy_signal = (nw_fast[t] > nw_slow[t]) AND (nw_fast[t-1] <= nw_slow[t-1])
```

這個條件表示快速均線從下方突破慢速均線，代表短期趨勢轉強，可能是上漲趨勢的開始。

## 賣出條件

**賣出信號觸發條件**：
- 當 NovaWave Fast EMA (9 期 EMA) 向下穿越 NovaWave Slow EMA (21 期 EMA) 時產生賣出信號

數學表達式：
```
sell_signal = (nw_fast[t] < nw_slow[t]) AND (nw_fast[t-1] >= nw_slow[t-1])
```

這個條件表示快速均線從上方跌破慢速均線，代表短期趨勢轉弱，可能是下跌趨勢的開始。

## 適用場景

本策略適合以下市場環境：

1. **趨勢明確的市場**: 當市場處於明顯的上升或下降趨勢時，策略表現最佳
2. **波動適中的市場**: 過度波動可能產生較多假信號
3. **中長期交易**: 適合持倉數日到數週的交易者
4. **流動性良好的股票**: 適用於成交量充足的主流股票

不適合的場景：
- 橫盤震盪市場（可能產生頻繁的假突破）
- 極端波動市場（信號可能滯後）
- 低流動性股票（執行困難）

## 風險提示

使用本策略時請注意以下風險：

1. **滯後性**: EMA 是滯後指標，信號可能在趨勢已經發展一段時間後才出現
2. **假突破**: 在震盪市場中可能產生較多假信號，導致頻繁交易和虧損
3. **回撤風險**: 趨勢反轉時可能面臨較大回撤
4. **參數敏感性**: 指標參數的設定會影響策略表現
5. **市場環境依賴**: 策略在不同市場環境下表現差異大
6. **無止損機制**: 本策略未包含止損邏輯，需要交易者自行管理風險

**重要提醒**: 本策略僅供學術研究和教育用途，不構成投資建議。實際交易前請充分測試
並評估自身風險承受能力。

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
    'name': 'EMA Super 策略',
    'source_url': 'https://tw.tradingview.com/script/vEbaMVtL-EMA-Super/',
    'version': '@version=6'
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


def calculate_supertrend(df: pd.DataFrame, atr_period: int = 10, factor: float = 4.0) -> Tuple[pd.Series, pd.Series]:
    """
    計算 Supertrend 指標
    
    參數:
        df: 包含 high, low, close 的 DataFrame
        atr_period: ATR 計算週期
        factor: ATR 乘數因子
    
    返回:
        (supertrend, direction) 的元組
        - supertrend: Supertrend 線的值
        - direction: 趨勢方向 (1 = 下降趨勢, -1 = 上升趨勢)
    """
    # 計算 ATR
    atr = calculate_atr(df, atr_period)
    
    # 計算基本上下軌
    hl_avg = (df['high'] + df['low']) / 2
    upper_band = hl_avg + (factor * atr)
    lower_band = hl_avg - (factor * atr)
    
    # 初始化
    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=float)
    
    # 設定初始值
    supertrend.iloc[0] = upper_band.iloc[0]
    direction.iloc[0] = 1
    
    # 計算 Supertrend
    for i in range(1, len(df)):
        # 更新上下軌（考慮前一期的值）
        if lower_band.iloc[i] > supertrend.iloc[i-1] or df['close'].iloc[i-1] < supertrend.iloc[i-1]:
            current_lower = lower_band.iloc[i]
        else:
            current_lower = max(lower_band.iloc[i], supertrend.iloc[i-1])
            
        if upper_band.iloc[i] < supertrend.iloc[i-1] or df['close'].iloc[i-1] > supertrend.iloc[i-1]:
            current_upper = upper_band.iloc[i]
        else:
            current_upper = min(upper_band.iloc[i], supertrend.iloc[i-1])
        
        # 判斷趨勢方向
        if df['close'].iloc[i] <= current_upper:
            supertrend.iloc[i] = current_upper
            direction.iloc[i] = 1  # 下降趨勢
        else:
            supertrend.iloc[i] = current_lower
            direction.iloc[i] = -1  # 上升趨勢
    
    return supertrend, direction


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


# ===== 區塊 6: EMA Super 策略實現 =====
class EMASuperStrategy(BaseStrategy):
    """
    EMA Super 策略
    
    來源: https://tw.tradingview.com/script/vEbaMVtL-EMA-Super/
    
    結合多重 EMA、Supertrend 和 NovaWave 趨勢雲的綜合趨勢追蹤策略。
    買賣信號基於 NovaWave Fast EMA (9) 和 Slow EMA (21) 的交叉。
    """
    
    def __init__(self, df: pd.DataFrame):
        """初始化 EMA Super 策略"""
        super().__init__(df, "EMA Super")
        
        # 策略參數（根據 Pine Script 定義）
        # EMA 參數
        self.ema_periods = [9, 21, 50, 100, 200]
        
        # Supertrend 參數
        self.atr_period = 10
        self.st_factor = 4.0
        
        # NovaWave 參數
        self.nw_fast_len = 9
        self.nw_slow_len = 21
        self.nw_signal_len = 10
        
        # DMA 參數
        self.dma_periods = [20, 50, 200]
        self.dma_displacement = 0  # 位移量（預設為 0）
    
    def calculate_indicators(self) -> None:
        """計算策略所需的技術指標"""
        # 1. 計算 5 條 EMA
        for period in self.ema_periods:
            self.df[f'ema_{period}'] = calculate_ema(self.df['close'], period)
        
        # 2. 計算 Supertrend
        self.df['supertrend'], self.df['st_direction'] = calculate_supertrend(
            self.df, 
            self.atr_period, 
            self.st_factor
        )
        
        # 3. 計算 NovaWave 指標
        self.df['nw_fast'] = calculate_ema(self.df['close'], self.nw_fast_len)
        self.df['nw_slow'] = calculate_ema(self.df['close'], self.nw_slow_len)
        self.df['nw_signal'] = calculate_sma(self.df['close'], self.nw_signal_len)
        
        # NovaWave 趨勢判斷
        self.df['nw_bull'] = self.df['nw_fast'] > self.df['nw_slow']
        
        # 4. 計算 DMA (位移移動平均線)
        for period in self.dma_periods:
            sma = calculate_sma(self.df['close'], period)
            # 如果需要位移，使用 shift
            if self.dma_displacement != 0:
                sma = sma.shift(self.dma_displacement)
            self.df[f'dma_{period}'] = sma
    
    def generate_signals(self) -> None:
        """產生買賣信號"""
        # 買入信號: NovaWave Fast 向上穿越 Slow
        self.df['buy_signal'] = (
            (self.df['nw_fast'] > self.df['nw_slow']) & 
            (self.df['nw_fast'].shift(1) <= self.df['nw_slow'].shift(1))
        )
        
        # 賣出信號: NovaWave Fast 向下穿越 Slow
        self.df['sell_signal'] = (
            (self.df['nw_fast'] < self.df['nw_slow']) & 
            (self.df['nw_fast'].shift(1) >= self.df['nw_slow'].shift(1))
        )
        
        # 整理成標準信號表格
        signals = self.df[self.df['buy_signal'] | self.df['sell_signal']].copy()
        
        if len(signals) == 0:
            # 如果沒有信號，創建空表格
            self.signals = pd.DataFrame(columns=[
                '日期', '信號類型', '價格', 
                'EMA 9', 'EMA 21', 'EMA 50',
                'Supertrend', 'NovaWave Bull'
            ])
        else:
            self.signals = pd.DataFrame({
                '日期': signals.index,
                '信號類型': signals.apply(
                    lambda row: 'BUY' if row['buy_signal'] else 'SELL', 
                    axis=1
                ),
                '價格': signals['close'].round(2),
                'EMA 9': signals['ema_9'].round(2),
                'EMA 21': signals['ema_21'].round(2),
                'EMA 50': signals['ema_50'].round(2),
                'Supertrend': signals['supertrend'].round(2),
                'NovaWave Bull': signals['nw_bull'].map({True: '多頭', False: '空頭'})
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
        
        # 策略選擇
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
                elif len(df) < 200:
                    st.info(f"ℹ️ 數據量為 {len(df)} 筆，某些長期指標（如 EMA 200）可能不完整")
                
                # 步驟 3: 執行策略
                status.info("⚙️ 正在計算技術指標...")
                
                strategy = EMASuperStrategy(df)
                
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
            EMA Super 策略是一個結合多重技術指標的趨勢追蹤系統，主要使用指數移動平均線（EMA）、
            Supertrend 指標和 NovaWave 風格的趨勢雲來識別市場趨勢和交易機會。
            
            本策略的核心理念是通過多層次的技術指標交叉驗證，來提高交易信號的可靠性。策略使用
            5 條不同週期的 EMA（9, 21, 50, 100, 200）來觀察短期、中期和長期趨勢，並結合
            Supertrend 指標來確認趨勢方向和強度。NovaWave 趨勢雲則提供視覺化的趨勢確認。
            
            此策略適合在趨勢明確的市場中使用，能夠捕捉到主要的趨勢轉折點，並提供清晰的進出場信號。
            """)
            
            st.markdown("### 🔧 技術指標")
            st.markdown("""
            本策略使用以下技術指標：
            
            **主要 EMA 系統**：
            - **EMA 9**: 9 期指數移動平均線（快速 EMA，用於短期趨勢判斷）
            - **EMA 21**: 21 期指數移動平均線（中期趨勢參考）
            - **EMA 50**: 50 期指數移動平均線（中長期趨勢支撐）
            - **EMA 100**: 100 期指數移動平均線（長期趨勢參考）
            - **EMA 200**: 200 期指數移動平均線（主要趨勢線）
            
            **Supertrend 指標**：
            - ATR 週期: 10
            - 因子: 4.0
            - 用途: 確認趨勢方向和強度
            
            **NovaWave 趨勢雲**：
            - NovaWave Fast EMA: 9 期 EMA（趨勢雲上軌）
            - NovaWave Slow EMA: 21 期 EMA（趨勢雲下軌）
            - NovaWave Signal MA: 10 期簡單移動平均線（信號線）
            
            **位移移動平均線 (DMA)**：
            - DMA 20: 20 期位移移動平均線
            - DMA 50: 50 期位移移動平均線
            - DMA 200: 200 期位移移動平均線
            """)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📈 買入條件")
                st.success("""
                **買入信號觸發條件**：
                
                當 NovaWave Fast EMA (9 期 EMA) 向上穿越 NovaWave Slow EMA (21 期 EMA) 時產生買入信號。
                
                **數學表達式**：
                ```
                buy_signal = (nw_fast[t] > nw_slow[t]) AND 
                             (nw_fast[t-1] <= nw_slow[t-1])
                ```
                
                **意義**：快速均線從下方突破慢速均線，代表短期趨勢轉強，可能是上漲趨勢的開始。
                """)
            
            with col2:
                st.markdown("### 📉 賣出條件")
                st.error("""
                **賣出信號觸發條件**：
                
                當 NovaWave Fast EMA (9 期 EMA) 向下穿越 NovaWave Slow EMA (21 期 EMA) 時產生賣出信號。
                
                **數學表達式**：
                ```
                sell_signal = (nw_fast[t] < nw_slow[t]) AND 
                              (nw_fast[t-1] >= nw_slow[t-1])
                ```
                
                **意義**：快速均線從上方跌破慢速均線，代表短期趨勢轉弱，可能是下跌趨勢的開始。
                """)
            
            st.markdown("### 🎯 適用場景")
            st.info("""
            本策略適合以下市場環境：
            
            ✅ **適合的場景**：
            - **趨勢明確的市場**: 當市場處於明顯的上升或下降趨勢時，策略表現最佳
            - **波動適中的市場**: 過度波動可能產生較多假信號
            - **中長期交易**: 適合持倉數日到數週的交易者
            - **流動性良好的股票**: 適用於成交量充足的主流股票
            
            ❌ **不適合的場景**：
            - 橫盤震盪市場（可能產生頻繁的假突破）
            - 極端波動市場（信號可能滯後）
            - 低流動性股票（執行困難）
            """)
            
            st.markdown("### ⚠️ 風險提示")
            st.warning("""
            使用本策略時請注意以下風險：
            
            1. **滯後性**: EMA 是滯後指標，信號可能在趨勢已經發展一段時間後才出現
            2. **假突破**: 在震盪市場中可能產生較多假信號，導致頻繁交易和虧損
            3. **回撤風險**: 趨勢反轉時可能面臨較大回撤
            4. **參數敏感性**: 指標參數的設定會影響策略表現
            5. **市場環境依賴**: 策略在不同市場環境下表現差異大
            6. **無止損機制**: 本策略未包含止損邏輯，需要交易者自行管理風險
            
            **重要提醒**: 本策略僅供學術研究和教育用途，不構成投資建議。實際交易前請充分測試
            並評估自身風險承受能力。
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
                    - **日期**: {latest['日期'].strftime('%Y-%m-%d') if hasattr(latest['日期'], 'strftime') else latest['日期']}
                    - **價格**: ${latest['價格']}
                    - **EMA 9**: ${latest['EMA 9']}
                    - **EMA 21**: ${latest['EMA 21']}
                    - **趨勢**: {latest['NovaWave Bull']}
                    """)
                else:
                    st.error(f"""
                    ### 🔴 最新信號: {signal_type}
                    - **日期**: {latest['日期'].strftime('%Y-%m-%d') if hasattr(latest['日期'], 'strftime') else latest['日期']}
                    - **價格**: ${latest['價格']}
                    - **EMA 9**: ${latest['EMA 9']}
                    - **EMA 21**: ${latest['EMA 21']}
                    - **趨勢**: {latest['NovaWave Bull']}
                    """)
            else:
                st.info("📭 在選定的時間範圍內未找到任何交易信號")
            
            st.divider()
            
            # 完整信號表格
            st.markdown("### 📋 完整交易信號")
            
            if len(signals) > 0:
                # 應用顏色標記
                def highlight_signals(row):
                    if row['信號類型'] == 'BUY':
                        return ['background-color: #d4edda'] * len(row)
                    else:
                        return ['background-color: #f8d7da'] * len(row)
                
                # 格式化日期欄位
                display_signals = signals.copy()
                display_signals['日期'] = pd.to_datetime(display_signals['日期']).dt.strftime('%Y-%m-%d')
                
                styled_signals = display_signals.style.apply(highlight_signals, axis=1)
                
                st.dataframe(
                    styled_signals,
                    use_container_width=True,
                    height=400
                )
                
                # 匯出功能
                csv = signals.to_csv(index=False, encoding='utf-8-sig')
                filename = f"{st.session_state.symbol}_{STRATEGY_INFO['name'].replace(' ', '_')}_signals_{datetime.now().strftime('%Y%m%d')}.csv"
                
                st.download_button(
                    label="📥 下載信號表格 (CSV)",
                    data=csv,
                    file_name=filename,
                    mime="text/csv"
                )
            else:
                st.info("📭 沒有可顯示的交易信號")
        
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
                date_range = f"{raw_data.index[0].strftime('%Y-%m-%d')} ~ {raw_data.index[-1].strftime('%Y-%m-%d')}"
                st.metric("日期範圍", date_range)
            
            st.divider()
            
            # 顯示計算的指標欄位
            st.markdown("### 📈 技術指標總覽")
            
            indicator_cols = [col for col in raw_data.columns if col not in ['open', 'high', 'low', 'close', 'volume']]
            if indicator_cols:
                st.info(f"已計算的技術指標: {', '.join(indicator_cols)}")
            
            st.divider()
            
            # 完整數據表格
            st.markdown("### 📈 完整歷史數據（含技術指標）")
            
            # 選擇要顯示的欄位
            display_columns = st.multiselect(
                "選擇要顯示的欄位",
                options=raw_data.columns.tolist(),
                default=['open', 'high', 'low', 'close', 'volume', 'ema_9', 'ema_21', 'ema_50', 'supertrend']
            )
            
            if display_columns:
                # 格式化數據以便顯示
                display_data = raw_data[display_columns].copy()
                
                # 數值格式化為 2 位小數
                for col in display_data.columns:
                    if display_data[col].dtype in ['float64', 'float32']:
                        display_data[col] = display_data[col].round(2)
                
                st.dataframe(
                    display_data.tail(100),  # 顯示最近 100 筆
                    use_container_width=True,
                    height=400
                )
                
                st.caption(f"顯示最近 100 筆數據（共 {len(raw_data)} 筆）")
            else:
                st.warning("請至少選擇一個欄位以顯示數據")
            
            st.divider()
            
            # 匯出功能
            st.markdown("### 💾 數據匯出")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # 匯出基本 OHLCV 數據
                basic_data = raw_data[['open', 'high', 'low', 'close', 'volume']]
                csv_basic = basic_data.to_csv(encoding='utf-8-sig')
                filename_basic = f"{st.session_state.symbol}_basic_data_{datetime.now().strftime('%Y%m%d')}.csv"
                
                st.download_button(
                    label="📥 下載基本數據 (OHLCV)",
                    data=csv_basic,
                    file_name=filename_basic,
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                # 匯出完整數據（含技術指標）
                csv_full = raw_data.to_csv(encoding='utf-8-sig')
                filename_full = f"{st.session_state.symbol}_full_data_with_indicators_{datetime.now().strftime('%Y%m%d')}.csv"
                
                st.download_button(
                    label="📥 下載完整數據（含指標）",
                    data=csv_full,
                    file_name=filename_full,
                    mime="text/csv",
                    use_container_width=True
                )


if __name__ == "__main__":
    main()