# ============================================
# AI 投資日誌分析系統
# ============================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from openai import OpenAI
from datetime import timedelta

# ============================================
# 頁面設定
# ============================================

st.set_page_config(
    page_title="AI 投資日誌分析系統",
    page_icon="📊",
    layout="wide"
)

# ============================================
# 工具函數區
# ============================================

# CSV 驗證函數
def validate_trading_journal(df):
    """
    驗證投資日誌格式
    返回：(is_valid, error_messages, warnings)
    """
    errors = []
    warnings = []
    
    # 1. 必要欄位檢查
    required_columns = ['Date', 'Type', 'Symbol', 'Name', 'Price', 'Quantity', 'Reason']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        errors.append(f"❌ 缺少必要欄位: {', '.join(missing_cols)}")
        return False, errors, warnings
    
    # 2. 資料型態驗證
    try:
        df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors='coerce')
        if df['Date'].isna().any():
            errors.append("❌ Date 欄位格式錯誤，應為 YYYY-MM-DD")
    except:
        errors.append("❌ Date 欄位格式錯誤，應為 YYYY-MM-DD")
    
    # 3. Type 欄位驗證
    invalid_types = df[~df['Type'].isin(['Buy', 'Sell'])]
    if not invalid_types.empty:
        errors.append(f"❌ Type 欄位只能是 'Buy' 或 'Sell'，發現錯誤: {invalid_types['Type'].unique().tolist()}")
    
    # 4. 數值驗證
    try:
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
        df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
        
        if df['Price'].isna().any() or df['Quantity'].isna().any():
            errors.append("❌ Price 和 Quantity 必須是有效數字")
        elif (df['Price'] <= 0).any():
            errors.append("❌ Price 必須大於 0")
        elif (df['Quantity'] <= 0).any():
            errors.append("❌ Quantity 必須大於 0")
    except:
        errors.append("❌ Price 和 Quantity 必須是數字")
    
    # 5. Symbol 驗證
    if df['Symbol'].str.contains(r'[^A-Z0-9\.\-]', regex=True, na=False).any():
        warnings.append("⚠️ 股票代碼包含特殊字元，請確認是否正確")
    
    # 6. 日期邏輯驗證
    if not errors:
        future_dates = df[df['Date'] > pd.Timestamp.now()]
        if not future_dates.empty:
            warnings.append(f"⚠️ 發現 {len(future_dates)} 筆未來日期的交易")
    
    # 7. 庫存邏輯驗證（FIFO 模擬）
    if not errors:
        inventory = {}
        for idx, row in df.sort_values('Date').iterrows():
            symbol = row['Symbol']
            if symbol not in inventory:
                inventory[symbol] = 0
            
            if row['Type'] == 'Buy':
                inventory[symbol] += row['Quantity']
            else:  # Sell
                inventory[symbol] -= row['Quantity']
                if inventory[symbol] < -0.001:  # 容許浮點數誤差
                    warnings.append(f"⚠️ {symbol} 在 {row['Date'].strftime('%Y-%m-%d')} 賣出數量超過持有數量")
    
    is_valid = len(errors) == 0
    return is_valid, errors, warnings

# FIFO 績效計算函數
def calculate_fifo_performance(df, current_prices):
    """
    使用 FIFO 規則計算投資績效
    current_prices: dict {symbol: current_price}
    """
    df = df.sort_values('Date').copy()
    
    # 初始化
    holdings = {}  # {symbol: [{'date': ..., 'price': ..., 'quantity': ...}, ...]}
    trade_history = {}
    realized_pnl = {}
    trade_details = []
    
    for idx, row in df.iterrows():
        symbol = row['Symbol']
        
        if symbol not in holdings:
            holdings[symbol] = []
            trade_history[symbol] = []
            realized_pnl[symbol] = 0
        
        if row['Type'] == 'Buy':
            # 記錄買入
            holdings[symbol].append({
                'date': row['Date'],
                'price': row['Price'],
                'quantity': row['Quantity']
            })
            
            trade_history[symbol].append({
                'date': row['Date'],
                'type': 'Buy',
                'price': row['Price'],
                'quantity': row['Quantity'],
                'reason': row['Reason']
            })
        
        else:  # Sell
            # FIFO 計算已實現損益
            sell_quantity = row['Quantity']
            sell_price = row['Price']
            trade_pnl = 0
            weighted_cost = 0
            total_sold = 0
            
            while sell_quantity > 0 and holdings[symbol]:
                oldest_buy = holdings[symbol][0]
                
                if oldest_buy['quantity'] <= sell_quantity:
                    # 完全賣出這批買入
                    pnl = (sell_price - oldest_buy['price']) * oldest_buy['quantity']
                    trade_pnl += pnl
                    weighted_cost += oldest_buy['price'] * oldest_buy['quantity']
                    total_sold += oldest_buy['quantity']
                    sell_quantity -= oldest_buy['quantity']
                    holdings[symbol].pop(0)
                else:
                    # 部分賣出
                    pnl = (sell_price - oldest_buy['price']) * sell_quantity
                    trade_pnl += pnl
                    weighted_cost += oldest_buy['price'] * sell_quantity
                    total_sold += sell_quantity
                    oldest_buy['quantity'] -= sell_quantity
                    sell_quantity = 0
            
            avg_cost = weighted_cost / total_sold if total_sold > 0 else 0
            return_pct = ((sell_price - avg_cost) / avg_cost * 100) if avg_cost > 0 else 0
            
            realized_pnl[symbol] += trade_pnl
            
            trade_history[symbol].append({
                'date': row['Date'],
                'type': 'Sell',
                'price': sell_price,
                'quantity': row['Quantity'],
                'avg_cost': avg_cost,
                'pnl': trade_pnl,
                'return_pct': return_pct,
                'reason': row['Reason']
            })
    
    # 計算當前持倉
    current_holdings = []
    total_cost = 0
    total_market_value = 0
    total_realized_pnl = sum(realized_pnl.values())
    
    for symbol, holding_list in holdings.items():
        if holding_list:
            total_quantity = sum(h['quantity'] for h in holding_list)
            total_cost_basis = sum(h['price'] * h['quantity'] for h in holding_list)
            avg_cost = total_cost_basis / total_quantity if total_quantity > 0 else 0
            
            current_price = current_prices.get(symbol, 0)
            market_value = current_price * total_quantity
            unrealized_pnl = market_value - total_cost_basis
            unrealized_pnl_pct = (unrealized_pnl / total_cost_basis * 100) if total_cost_basis > 0 else 0
            
            current_holdings.append({
                'symbol': symbol,
                'name': df[df['Symbol'] == symbol]['Name'].iloc[0],
                'quantity': total_quantity,
                'avg_cost': avg_cost,
                'current_price': current_price,
                'cost_basis': total_cost_basis,
                'market_value': market_value,
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pnl_pct': unrealized_pnl_pct
            })
            
            total_cost += total_cost_basis
            total_market_value += market_value
    
    # 計算總投入（包含已賣出的）
    all_buys = df[df['Type'] == 'Buy']
    total_investment = (all_buys['Price'] * all_buys['Quantity']).sum()
    
    # 總體績效
    total_unrealized_pnl = total_market_value - total_cost
    total_pnl = total_realized_pnl + total_unrealized_pnl
    total_return_pct = (total_pnl / total_investment * 100) if total_investment > 0 else 0
    
    return {
        'current_holdings': current_holdings,
        'trade_history': trade_history,
        'realized_pnl': realized_pnl,
        'total_realized_pnl': total_realized_pnl,
        'total_unrealized_pnl': total_unrealized_pnl,
        'total_investment': total_investment,
        'total_cost': total_cost,
        'total_market_value': total_market_value,
        'total_pnl': total_pnl,
        'total_return_pct': total_return_pct
    }

# FMP API 函數
@st.cache_data(ttl=3600)
def get_fmp_historical_price(symbol, api_key, start_date, end_date):
    """獲取歷史股價"""
    try:
        url = f"https://financialmodelingprep.com/stable/historical-price-eod/full"
        params = {
            'symbol': symbol,
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'apikey': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list):
            if not data:  # 空陣列
                return None
            df = pd.DataFrame(data)
        elif isinstance(data, dict) and 'historical' in data:
            # 相容舊格式
            df = pd.DataFrame(data['historical'])
        else:
            return None
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        return df
        
    except requests.exceptions.Timeout:
        st.error(f"⏱️ FMP API 請求超時: {symbol}")
        return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            st.error("❌ FMP API Key 無效，請檢查")
        elif e.response.status_code == 429:
            st.warning("⚠️ FMP API 請求次數超過限制")
        else:
            st.error(f"❌ FMP API 錯誤: {e}")
        return None
    except Exception as e:
        st.error(f"❌ 獲取 {symbol} 歷史股價失敗: {str(e)}")
        return None

@st.cache_data(ttl=300)
def get_fmp_quote(symbol, api_key):
    """獲取當前報價"""
    try:
        url = f"https://financialmodelingprep.com/stable/quote"
        params = {
            'symbol': symbol,
            'apikey': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data and len(data) > 0:
            return data[0].get('price', 0)
        return 0
        
    except Exception as e:
        st.warning(f"⚠️ 無法獲取 {symbol} 當前報價")
        return 0

@st.cache_data(ttl=3600)
def get_fmp_profile(symbol, api_key):
    """獲取公司資料"""
    try:
        url = f"https://financialmodelingprep.com/stable/profile"
        params = {
            'symbol': symbol,
            'apikey': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data and len(data) > 0:
            return data[0]
        return {}
        
    except Exception as e:
        return {}

@st.cache_data(ttl=3600)
def get_fmp_key_metrics(symbol, api_key):
    """獲取關鍵指標"""
    try:
        url = f"https://financialmodelingprep.com/stable/key-metrics"
        params = {
            'symbol': symbol,
            'limit': 4,
            'apikey': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return data if data else []
        
    except Exception as e:
        return []

@st.cache_data(ttl=3600)
def get_fmp_ratios(symbol, api_key):
    """獲取財務比率"""
    try:
        url = f"https://financialmodelingprep.com/stable/ratios"
        params = {
            'symbol': symbol,
            'limit': 4,
            'apikey': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return data if data else []
        
    except Exception as e:
        return []

# Alpha Vantage API
def get_alpha_vantage_news(symbol, api_key):
    """
    獲取新聞情緒（選配）
    返回：(news_data, error_message)
    - news_data: 新聞列表或 None
    - error_message: 錯誤訊息或 None
    """
    if not api_key:
        return None, None

    try:
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'NEWS_SENTIMENT',
            'tickers': symbol,
            'apikey': api_key
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # 檢查 API 回傳的錯誤訊息
        if "Error Message" in data:
            return None, f"❌ API 錯誤: {data['Error Message']}"

        if "Note" in data:
            # API 呼叫頻率限制
            return None, "⚠️ API 呼叫頻率超過限制，請稍後再試（Alpha Vantage 免費版每分鐘限制 5 次呼叫）"

        if "Information" in data:
            # API 額度用完
            return None, "⚠️ API 每日額度已用完，請明天再試或升級方案"

        # 檢查是否有新聞資料
        if 'feed' in data and data['feed']:
            return data['feed'][:10], None  # 只取前 10 則新聞

        return None, "ℹ️ 目前沒有相關新聞資料"

    except requests.exceptions.Timeout:
        return None, "⚠️ 網路請求逾時，請檢查網路連線"
    except requests.exceptions.ConnectionError:
        return None, "⚠️ 無法連線到 Alpha Vantage 伺服器，請檢查網路連線"
    except requests.exceptions.HTTPError as e:
        return None, f"❌ HTTP 錯誤: {e}"
    except Exception as e:
        return None, f"❌ 未預期的錯誤: {str(e)}"

# AI 分析相關函數
def prepare_ai_analysis_data(df, performance, fmp_data, news_data, symbol):
    """準備 AI 分析資料"""
    
    # 1. 該股票的交易記錄
    symbol_trades = df[df['Symbol'] == symbol].sort_values('Date').to_dict('records')
    
    # 2. 績效統計
    trade_hist = performance['trade_history'].get(symbol, [])
    buy_count = sum(1 for t in trade_hist if t['type'] == 'Buy')
    sell_count = sum(1 for t in trade_hist if t['type'] == 'Sell')
    
    completed_trades = [t for t in trade_hist if t['type'] == 'Sell']
    win_count = sum(1 for t in completed_trades if t.get('pnl', 0) > 0)
    win_rate = (win_count / len(completed_trades) * 100) if completed_trades else 0
    
    avg_holding_days = 0
    if len(completed_trades) > 0:
        # 簡化計算：假設平均持有時間
        first_buy = df[(df['Symbol'] == symbol) & (df['Type'] == 'Buy')]['Date'].min()
        last_sell = df[(df['Symbol'] == symbol) & (df['Type'] == 'Sell')]['Date'].max()
        if pd.notna(first_buy) and pd.notna(last_sell):
            avg_holding_days = (last_sell - first_buy).days / len(completed_trades)
    
    current_holding = next((h for h in performance['current_holdings'] if h['symbol'] == symbol), None)
    
    perf_data = {
        'total_trades': len(symbol_trades),
        'buy_count': buy_count,
        'sell_count': sell_count,
        'realized_pnl': performance['realized_pnl'].get(symbol, 0),
        'win_rate': win_rate,
        'avg_holding_days': int(avg_holding_days),
        'current_holding': current_holding
    }
    
    # 3. 股價背景
    price_data = fmp_data.get('historical')
    price_context = {}
    
    if price_data is not None and not price_data.empty:
        price_context = {
            'first_price': price_data['close'].iloc[0],
            'last_price': price_data['close'].iloc[-1],
            'period_high': price_data['high'].max(),
            'period_low': price_data['low'].min(),
            'overall_change_pct': ((price_data['close'].iloc[-1] - price_data['close'].iloc[0]) / price_data['close'].iloc[0] * 100)
        }
    
    # 4. 公司資料
    profile = fmp_data.get('profile', {})
    company_info = {
        'name': profile.get('companyName', symbol),
        'sector': profile.get('sector', 'N/A'),
        'industry': profile.get('industry', 'N/A'),
        'market_cap': profile.get('marketCap', 0)
    }
    
    # 5. 關鍵指標
    metrics = fmp_data.get('key_metrics', [])
    key_metrics_summary = {}
    if metrics and len(metrics) > 0:
        latest = metrics[0] if isinstance(metrics, list) else metrics
        if isinstance(latest, dict):
            key_metrics_summary = {
                'returnOnEquity': latest.get('returnOnEquity', 0),
                'returnOnAssets': latest.get('returnOnAssets', 0),
                'returnOnInvestedCapital': latest.get('returnOnInvestedCapital', 0),
                'freeCashFlowYield': latest.get('freeCashFlowYield', 0),
                'currentRatio': latest.get('currentRatio', 0),
                'netDebtToEBITDA': latest.get('netDebtToEBITDA', 0)
            }
    
    # 6. 新聞摘要
    news_summary = None
    if news_data:
        bullish = sum(1 for n in news_data if 'Bullish' in str(n.get('overall_sentiment_label', '')))
        bearish = sum(1 for n in news_data if 'Bearish' in str(n.get('overall_sentiment_label', '')))
        neutral = len(news_data) - bullish - bearish
        
        news_summary = {
            'total': len(news_data),
            'bullish_pct': (bullish / len(news_data) * 100) if news_data else 0,
            'neutral_pct': (neutral / len(news_data) * 100) if news_data else 0,
            'bearish_pct': (bearish / len(news_data) * 100) if news_data else 0,
            'top_headlines': [n.get('title', '') for n in news_data[:3]]
        }
    
    return {
        'symbol': symbol,
        'trades': symbol_trades,
        'performance': perf_data,
        'price_context': price_context,
        'company_info': company_info,
        'key_metrics': key_metrics_summary,
        'news_summary': news_summary
    }

def generate_ai_analysis_prompt(analysis_data):
    """生成 AI Prompt"""
    
    symbol = analysis_data['symbol']
    trades = analysis_data['trades']
    perf = analysis_data['performance']
    price_ctx = analysis_data['price_context']
    company = analysis_data['company_info']
    metrics = analysis_data['key_metrics']
    news = analysis_data['news_summary']
    
    # 構建交易歷史文本
    trades_text = ""
    for i, trade in enumerate(trades, 1):
        date_str = trade['Date'].strftime('%Y-%m-%d') if isinstance(trade['Date'], pd.Timestamp) else str(trade['Date'])
        trades_text += f"\n交易 {i}:\n"
        trades_text += f"- 日期: {date_str}\n"
        trades_text += f"- 類型: {trade['Type']}\n"
        trades_text += f"- 價格: ${trade['Price']:.2f}\n"
        trades_text += f"- 數量: {trade['Quantity']} 股\n"
        trades_text += f"- 理由: {trade['Reason']}\n"
    
    # 構建績效文本
    perf_text = f"""
- 總交易次數: {perf['total_trades']}
- 買入次數: {perf['buy_count']}
- 賣出次數: {perf['sell_count']}
- 已實現損益: ${perf['realized_pnl']:,.2f}
- 勝率: {perf['win_rate']:.1f}%
- 平均持有天數: {perf['avg_holding_days']} 天
"""
    
    if perf['current_holding']:
        perf_text += f"- 當前持倉: {perf['current_holding']['quantity']} 股 @ 平均成本 ${perf['current_holding']['avg_cost']:.2f}\n"
        perf_text += f"- 未實現損益: ${perf['current_holding']['unrealized_pnl']:,.2f} ({perf['current_holding']['unrealized_pnl_pct']:.2f}%)\n"
    else:
        perf_text += "- 當前無持倉\n"
    
    # 構建股價背景文本
    price_text = ""
    if price_ctx:
        price_text = f"""
在交易期間，{symbol} 的股價從 ${price_ctx.get('first_price', 0):.2f} 變動到 ${price_ctx.get('last_price', 0):.2f}
期間最高價: ${price_ctx.get('period_high', 0):.2f}
期間最低價: ${price_ctx.get('period_low', 0):.2f}
整體漲跌幅: {price_ctx.get('overall_change_pct', 0):.2f}%
"""
    
    # 構建公司背景文本
    company_text = f"""
公司名稱: {company.get('name', symbol)}
產業: {company.get('sector', 'N/A')} - {company.get('industry', 'N/A')}
市值: ${company.get('market_cap', 0):,.0f}
"""
    
    # 構建財務指標文本
    metrics_text = ""
    if metrics and isinstance(metrics, dict):
        roe = metrics.get('returnOnEquity', 0)
        roa = metrics.get('returnOnAssets', 0)
        roic = metrics.get('returnOnInvestedCapital', 0)
        fcf_yield = metrics.get('freeCashFlowYield', 0)
        current_ratio = metrics.get('currentRatio', 0)
        debt_to_ebitda = metrics.get('netDebtToEBITDA', 0)

        metrics_text = f"""
ROE (股東權益報酬率): {f'{roe*100:.2f}%' if roe else 'N/A'}
ROA (資產報酬率): {f'{roa*100:.2f}%' if roa else 'N/A'}
ROIC (投入資本報酬率): {f'{roic*100:.2f}%' if roic else 'N/A'}
自由現金流殖利率: {f'{fcf_yield*100:.2f}%' if fcf_yield else 'N/A'}
流動比率: {f'{current_ratio:.2f}' if current_ratio else 'N/A'}
淨負債/EBITDA: {f'{debt_to_ebitda:.2f}' if debt_to_ebitda else 'N/A'}
"""
    
    # 構建新聞文本
    news_text = ""
    if news:
        news_text = f"""
## 新聞情緒分析
分析期間共 {news['total']} 則相關新聞
- 看多 (Bullish): {news['bullish_pct']:.1f}%
- 中性 (Neutral): {news['neutral_pct']:.1f}%
- 看空 (Bearish): {news['bearish_pct']:.1f}%

重點新聞標題:
"""
        for i, headline in enumerate(news['top_headlines'], 1):
            news_text += f"{i}. {headline}\n"
    
    # 完整 Prompt
    prompt = f"""
你是一位資深的投資交易分析專家，具備技術分析、基本面分析和投資心理學的專業知識。

請根據以下使用者的 {symbol} 交易日誌，進行多維度客觀評估。

## 評估維度與權重
1. 交易執行評估 (40%) - 買賣時機、價格合理性
2. 決策品質評估 (30%) - 理由邏輯、策略一致性
3. 市場環境對比 (20%) - 與大盤/基本面的比較
4. 心理因素觀察 (10%) - 作為輔助參考

---

## 交易記錄
{trades_text}

## 績效統計
{perf_text}

## 股價背景
{price_text}

## 公司基本資料
{company_text}

## 財務指標
{metrics_text}

{news_text}

---

請用 Markdown 格式輸出完整分析報告，包含以下章節：

# {symbol} 投資分析報告

## 一、交易執行評估

### 1.1 買入時機分析
[請分析每次買入的價格位置是否合理，對比當時的股價區間和技術面位置]

### 1.2 賣出時機分析
[請分析每次賣出是否過早或過晚，賣出後股價走勢如何]

### 1.3 持倉管理
[分析持有時間是否合理，加碼減碼時機]

## 二、決策品質評估

### 2.1 理由合理性
[分析每次進場理由是否有依據，邏輯是否清晰]

### 2.2 策略一致性
[觀察是否有明確的投資策略，執行是否一致]

### 2.3 風險意識
[評估風險控制意識，是否設定停損等]

## 三、市場環境對比

### 3.1 相對績效
[比較使用者的報酬率與股票本身的漲跌幅]

### 3.2 基本面匹配度
[評估交易時機是否與公司基本面相符]

### 3.3 市場時機
[是否抓住關鍵機會或避開風險]

## 四、心理因素觀察

### 4.1 情緒化交易
[從交易理由中觀察到的心理狀態變化]

### 4.2 壓力下決策
[市場波動時的反應與決策品質]

## 五、綜合建議

### ✅ 優勢清單
[列出 3-5 個具體做得好的地方]

### 📈 改進方向
[列出 3-5 個具體可執行的改進建議]

"""

    print("\n" + "=" * 60)
    print("AI 分析提示語 (Prompt):")
    print("=" * 60)
    print(prompt)
    print("=" * 60 + "\n")

    return prompt

def call_openai_api(prompt, openai_key):
    """呼叫 OpenAI API"""
    try:
        print("\n" + "=" * 60)
        print("正在使用 AI 進行分析...")
        print("=" * 60 + "\n")

        client = OpenAI(api_key=openai_key)

        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "你是一位專業且富有同理心的投資交易分析師，擅長從交易記錄中發現模式並給予建設性建議。"},
                {"role": "user", "content": prompt}
            ]
        )
        
        print("\n" + "=" * 60)
        print("✅ API 呼叫成功")
        print("=" * 60 + "\n")

        return response.choices[0].message.content

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ AI 模型 API 呼叫失敗: {str(e)}")
        print("=" * 60 + "\n")
        return f"❌ AI 分析生成失敗: {str(e)}\n\n請檢查 OpenAI API Key 是否正確，或稍後再試。"

# 視覺化函數
def create_candlestick_chart(symbol, price_data, trades_data):
    """創建 K 線圖"""
    
    # 創建子圖：K線圖 + 成交量
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=(f'{symbol} 股價走勢', '成交量')
    )
    
    # 添加 K 線圖
    fig.add_trace(
        go.Candlestick(
            x=price_data['date'],
            open=price_data['open'],
            high=price_data['high'],
            low=price_data['low'],
            close=price_data['close'],
            name='K線圖',
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350'
        ),
        row=1, col=1
    )
    
    # 計算移動平均線
    price_data['MA5'] = price_data['close'].rolling(window=5).mean()
    price_data['MA10'] = price_data['close'].rolling(window=10).mean()
    price_data['MA20'] = price_data['close'].rolling(window=20).mean()
    price_data['MA60'] = price_data['close'].rolling(window=60).mean()
    
    # 添加移動平均線
    fig.add_trace(
        go.Scatter(x=price_data['date'], y=price_data['MA5'], 
                   mode='lines', name='MA5',
                   line=dict(color='orange', width=1)),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=price_data['date'], y=price_data['MA10'], 
                   mode='lines', name='MA10',
                   line=dict(color='blue', width=1)),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=price_data['date'], y=price_data['MA20'], 
                   mode='lines', name='MA20',
                   line=dict(color='red', width=1)),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=price_data['date'], y=price_data['MA60'], 
                   mode='lines', name='MA60',
                   line=dict(color='purple', width=1)),
        row=1, col=1
    )
    
    # 添加買入標記
    buy_trades = [t for t in trades_data if t['type'] == 'Buy']
    if buy_trades:
        buy_dates = [t['date'] for t in buy_trades]
        buy_prices = [t['price'] for t in buy_trades]
        buy_texts = [f"買入<br>數量: {t['quantity']}<br>理由: {t['reason'][:50]}..." for t in buy_trades]
        
        fig.add_trace(
            go.Scatter(
                x=buy_dates,
                y=buy_prices,
                mode='markers+text',
                marker=dict(size=15, color='green', symbol='triangle-up', line=dict(width=2, color='darkgreen')),
                text=['▲'] * len(buy_trades),
                textposition='top center',
                textfont=dict(size=20),
                name='買入',
                hovertext=buy_texts,
                hoverinfo='text'
            ),
            row=1, col=1
        )
    
    # 添加賣出標記
    sell_trades = [t for t in trades_data if t['type'] == 'Sell']
    if sell_trades:
        sell_dates = [t['date'] for t in sell_trades]
        sell_prices = [t['price'] for t in sell_trades]
        sell_texts = []
        for t in sell_trades:
            pnl_text = f"<br>損益: ${t.get('pnl', 0):,.2f} ({t.get('return_pct', 0):.2f}%)" if 'pnl' in t else ""
            sell_texts.append(f"賣出<br>數量: {t['quantity']}{pnl_text}<br>理由: {t['reason'][:50]}...")
        
        fig.add_trace(
            go.Scatter(
                x=sell_dates,
                y=sell_prices,
                mode='markers+text',
                marker=dict(size=15, color='red', symbol='triangle-down', line=dict(width=2, color='darkred')),
                text=['▼'] * len(sell_trades),
                textposition='bottom center',
                textfont=dict(size=20),
                name='賣出',
                hovertext=sell_texts,
                hoverinfo='text'
            ),
            row=1, col=1
        )
    
    # 添加成交量
    colors = ['red' if close < open else 'green' 
              for close, open in zip(price_data['close'], price_data['open'])]
    
    fig.add_trace(
        go.Bar(
            x=price_data['date'],
            y=price_data['volume'],
            name='成交量',
            marker_color=colors,
            showlegend=False
        ),
        row=2, col=1
    )
    
    # 更新布局
    fig.update_layout(
        title=f'{symbol} 股價走勢與交易記錄',
        xaxis_title='日期',
        yaxis_title='價格 (USD)',
        xaxis_rangeslider_visible=False,
        height=800,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    fig.update_xaxes(title_text="日期", row=2, col=1)
    fig.update_yaxes(title_text="價格", row=1, col=1)
    fig.update_yaxes(title_text="成交量", row=2, col=1)
    
    return fig

# ============================================
# 側邊欄
# ============================================

st.sidebar.header("📊 AI 投資日誌分析系統", divider="rainbow")

# API Keys 輸入
fmp_api_key = st.sidebar.text_input("🔑 FMP API Key", type="password", help="從 https://financialmodelingprep.com 取得")
openai_api_key = st.sidebar.text_input("🤖 OpenAI API Key", type="password", help="從 https://platform.openai.com 取得")
alpha_api_key = st.sidebar.text_input("📰 Alpha Vantage API Key (選填)", type="password", help="從 https://www.alphavantage.co 取得，用於新聞分析")

st.sidebar.divider()

# CSV 上傳
uploaded_file = st.sidebar.file_uploader("📤 上傳投資日誌 CSV", type=['csv'])

# 驗證結果顯示
validation_status = st.sidebar.empty()
validation_details = st.sidebar.empty()

csv_valid = False
df_validated = None

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        is_valid, errors, warnings = validate_trading_journal(df)

        if is_valid:
            csv_valid = True
            df_validated = df

            # 清空舊的 AI 分析報告（每次上傳檔案都清空）
            keys_to_remove = [key for key in st.session_state.keys() if key.startswith('ai_report_')]
            for key in keys_to_remove:
                del st.session_state[key]
            if keys_to_remove:
                st.sidebar.info("🔄 已清空舊的 AI 分析結果")

            validation_status.success("✅ CSV 格式驗證通過")
            
            # 顯示統計資訊
            symbols = df['Symbol'].unique()
            date_range = f"{df['Date'].min()} 至 {df['Date'].max()}"
            
            validation_details.info(f"""
📊 **交易統計**
- 總交易筆數: {len(df)}
- 涉及股票: {len(symbols)} 檔 ({', '.join(symbols)})
- 時間範圍: {date_range}
            """)
            
            # 顯示警告
            if warnings:
                for warning in warnings:
                    st.sidebar.warning(warning)
        else:
            csv_valid = False
            validation_status.error("❌ CSV 格式驗證失敗")
            for error in errors:
                validation_details.error(error)
            
            st.sidebar.info("💡 請修正 CSV 檔案後重新上傳")
            
    except Exception as e:
        validation_status.error(f"❌ 讀取 CSV 失敗: {str(e)}")

st.sidebar.divider()

# AI 分析選項
enable_ai = st.sidebar.checkbox("啟用 AI 深度分析", value=True, disabled=not csv_valid, 
                                 help="使用 AI 進行深度交易分析")

st.sidebar.divider()

# 分析按鈕
analyze_button = st.sidebar.button("🚀 開始分析", type="primary",
                                   disabled=not (csv_valid and fmp_api_key and (openai_api_key if enable_ai else True)),
                                   use_container_width=True)

st.sidebar.divider()

# 下載範本
sample_csv = """Date,Type,Symbol,Name,Price,Quantity,Reason
2025-01-15,Buy,NVDA,NVIDIA Corporation,136.24,50,看好AI晶片需求持續增長，Q4財報即將公布預期會超出市場預期。技術面突破135美元關鍵壓力位。"""

st.sidebar.download_button(
    label="📥 下載 CSV 範本",
    data=sample_csv,
    file_name="trading_journal_template.csv",
    mime="text/csv",
    use_container_width=True
)

st.sidebar.divider()

# 免責聲明
st.sidebar.markdown("""
### 📢 免責聲明
本系統僅供學術研究與教育用途，AI 提供的數據與分析結果僅供參考，**不構成投資建議或財務建議**。

請使用者自行判斷投資決策，並承擔相關風險。本系統作者不對任何投資行為負責，亦不承擔任何損失責任。
""")

# ============================================
# 主畫面
# ============================================

st.header("📊 AI 投資日誌分析系統", divider="rainbow")

# 未上傳檔案時的歡迎畫面
if uploaded_file is None:
    st.markdown("""
    # 🎯 歡迎使用 AI 投資日誌分析系統

    ## 📖 使用步驟

    ### 1. 準備 API Keys
    - 註冊 [FMP API](https://financialmodelingprep.com/developer/docs) **(必要)** - 用於獲取股價資料
    - 註冊 [OpenAI API](https://platform.openai.com/) **(必要)** - 用於 AI 分析
    - 註冊 [Alpha Vantage API](https://www.alphavantage.co/) **(選配)** - 用於新聞情緒分析

    ### 2. 準備投資日誌 CSV
    請確保你的 CSV 檔案包含以下欄位：
    
    | 欄位 | 說明 | 範例 |
    |------|------|------|
    | Date | 交易日期 (YYYY-MM-DD) | 2025-01-15 |
    | Type | 交易類型 (Buy/Sell) | Buy |
    | Symbol | 股票代碼 | NVDA |
    | Name | 股票名稱 | NVIDIA Corporation |
    | Price | 成交價格 | 136.24 |
    | Quantity | 股數 | 50 |
    | Reason | 進場理由 | 看好AI晶片需求... |

    💡 **提示**: 可點擊左側「下載 CSV 範本」按鈕獲取範例檔案

    ### 3. 上傳與分析
    - 在左側欄輸入 API Keys
    - 上傳你的 CSV 檔案
    - 系統會自動驗證格式
    - 勾選「啟用 AI 分析」可獲得深度建議
    - 點擊「開始分析」按鈕

    ---

    ## 🔍 系統功能

    ### 📊 基本分析
    - ✅ 投資績效總覽（總報酬率、已實現/未實現損益）
    - ✅ 當前持倉狀況明細
    - ✅ 股價 K 線圖 + 交易標記
    - ✅ 技術指標（MA5/10/20/60、成交量）

    ### 🤖 AI 深度分析
    - 📈 **交易執行評估 (40%)** - 買賣時機、價格合理性、持倉管理
    - 🎯 **決策品質評估 (30%)** - 理由邏輯、策略一致性、風險意識
    - 📊 **市場環境對比 (20%)** - 相對績效、基本面匹配度、市場時機
    - 🧠 **心理因素觀察 (10%)** - 情緒化交易、壓力下決策

    ---

    ## ⚠️ 重要提醒

    - 本系統僅供學習與自我反思使用
    - AI 分析結果僅供參考，不構成投資建議
    - 請勿依賴系統結果做出實際投資決策
    - 所有投資均有風險，請謹慎評估
    """)

# 分析流程
elif analyze_button and csv_valid and fmp_api_key and (openai_api_key if enable_ai else True):
    
    df = df_validated.copy()
    
    # ===== 階段 1: 獲取股票當前報價 =====
    st.subheader("📡 正在獲取股票資料...")
    
    symbols = df['Symbol'].unique().tolist()
    current_prices = {}
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, symbol in enumerate(symbols):
        status_text.text(f"正在獲取 {symbol} 當前報價... ({i+1}/{len(symbols)})")
        price = get_fmp_quote(symbol, fmp_api_key)
        if price:
            current_prices[symbol] = price
        progress_bar.progress((i + 1) / len(symbols))
    
    progress_bar.empty()
    status_text.empty()
    
    if not current_prices:
        st.error("❌ 無法獲取任何股票報價，請檢查 FMP API Key 是否正確")
        st.stop()
    
    st.success(f"✅ 成功獲取 {len(current_prices)} 檔股票報價")
    
    # ===== 階段 2: 計算投資績效 =====
    with st.spinner("💰 正在計算投資績效..."):
        performance = calculate_fifo_performance(df, current_prices)
    
    st.success("✅ 績效計算完成")
    
    # ===== 顯示區塊 1: 績效儀表板 =====
    st.header("📊 投資績效總覽", divider="rainbow")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("💰 總投入金額", f"${performance['total_investment']:,.2f}")
    
    with col2:
        st.metric("📊 當前市值", f"${performance['total_market_value']:,.2f}")
    
    with col3:
        delta_color = "normal" if performance['total_return_pct'] >= 0 else "inverse"
        st.metric(
            "📈 總報酬率", 
            f"{performance['total_return_pct']:.2f}%",
            delta=f"${performance['total_pnl']:,.2f}"
        )
    
    with col4:
        st.metric("✅ 已實現損益", f"${performance['total_realized_pnl']:,.2f}")
    
    with col5:
        st.metric("⏳ 未實現損益", f"${performance['total_unrealized_pnl']:,.2f}")
    
    # ===== 顯示區塊 2: 當前持倉 =====
    st.header("📋 當前持倉狀況", divider="rainbow")
    
    if performance['current_holdings']:
        holdings_df = pd.DataFrame(performance['current_holdings'])
        
        # 格式化 DataFrame
        display_df = holdings_df.copy()
        display_df.columns = ['股票代碼', '股票名稱', '持有數量', '平均成本', '當前價格', '總成本', '當前市值', '未實現損益', '報酬率%']
        
        # 使用 Streamlit 的表格顯示
        st.dataframe(
            display_df.style.format({
                '平均成本': '${:.2f}',
                '當前價格': '${:.2f}',
                '總成本': '${:,.2f}',
                '當前市值': '${:,.2f}',
                '未實現損益': '${:,.2f}',
                '報酬率%': '{:.2f}%'
            }).applymap(
                lambda x: 'color: green' if x > 0 else ('color: red' if x < 0 else ''),
                subset=['未實現損益', '報酬率%']
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("ℹ️ 目前無持倉")
    
    # ===== 階段 3: 獲取詳細資料並繪製圖表 =====
    st.header("📈 股價走勢與交易記錄", divider="rainbow")
    
    # 為每檔股票獲取資料
    all_stock_data = {}
    
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    for i, symbol in enumerate(symbols):
        status_text.text(f"正在獲取 {symbol} 詳細資料... ({i+1}/{len(symbols)})")
        
        # 確定日期範圍
        symbol_trades = df[df['Symbol'] == symbol]
        start_date = symbol_trades['Date'].min() - timedelta(days=120)  # 提前120天顯示背景
        end_date = pd.Timestamp.now()
        
        # 獲取各項資料
        historical = get_fmp_historical_price(symbol, fmp_api_key, start_date, end_date)
        profile = get_fmp_profile(symbol, fmp_api_key)
        key_metrics = get_fmp_key_metrics(symbol, fmp_api_key)
        ratios = get_fmp_ratios(symbol, fmp_api_key)
        
        all_stock_data[symbol] = {
            'historical': historical,
            'profile': profile,
            'key_metrics': key_metrics,
            'ratios': ratios
        }
        
        progress_bar.progress((i + 1) / len(symbols))
    
    progress_bar.empty()
    status_text.empty()
    
    # 使用 Tabs 顯示每檔股票
    tabs = st.tabs([f"📊 {symbol}" for symbol in symbols])
    
    for tab, symbol in zip(tabs, symbols):
        with tab:
            stock_data = all_stock_data[symbol]
            historical_data = stock_data.get('historical')
            
            # 修正判斷邏輯：檢查 historical_data 是否為有效的 DataFrame
            if historical_data is not None and isinstance(historical_data, pd.DataFrame) and not historical_data.empty:
                # 獲取該股票的交易記錄
                symbol_trade_history = performance['trade_history'].get(symbol, [])
                
                # 繪製 K 線圖
                fig = create_candlestick_chart(symbol, historical_data, symbol_trade_history)
                st.plotly_chart(fig, use_container_width=True)
                
                # 顯示交易歷史詳情
                with st.expander(f"📜 查看 {symbol} 交易歷史詳情"):
                    symbol_trades = df[df['Symbol'] == symbol].sort_values('Date', ascending=False)
                    
                    for idx, trade in symbol_trades.iterrows():
                        emoji = "🟢" if trade['Type'] == 'Buy' else "🔴"
                        date_str = trade['Date'].strftime('%Y-%m-%d') if isinstance(trade['Date'], pd.Timestamp) else str(trade['Date'])
                        
                        st.markdown(f"""
                        {emoji} **{trade['Type']}** - {date_str}
                        - 💵 價格: ${trade['Price']:.2f}
                        - 📊 數量: {trade['Quantity']} 股
                        - 📝 理由: {trade['Reason']}
                        """)
                        
                        # 如果是賣出，顯示損益
                        if trade['Type'] == 'Sell':
                            matching_trade = next((t for t in symbol_trade_history 
                                                  if t['type'] == 'Sell' and 
                                                  t['date'] == trade['Date'] and 
                                                  t['price'] == trade['Price']), None)
                            if matching_trade and 'pnl' in matching_trade:
                                pnl_color = "green" if matching_trade['pnl'] > 0 else "red"
                                st.markdown(f"""
                                - 💰 已實現損益: <span style='color:{pnl_color}'>${matching_trade['pnl']:,.2f} ({matching_trade['return_pct']:.2f}%)</span>
                                """, unsafe_allow_html=True)
                        
                        st.divider()
            else:
                st.error(f"❌ 無法獲取 {symbol} 的歷史股價資料")
    
    # ===== AI 分析準備 (背景執行) =====
    if enable_ai and openai_api_key:
        # 在背景準備 AI 分析，不在此處顯示（將在每個股票詳細區塊中顯示）
        for symbol in symbols:
            # 只有當 session_state 中沒有報告時才執行分析
            if f"ai_report_{symbol}" not in st.session_state:
                with st.spinner(f"🧠 正在分析 {symbol} 的交易記錄..."):
                    # 嘗試獲取新聞（選配）
                    news_data = None
                    if alpha_api_key:
                        news_data, error_msg = get_alpha_vantage_news(symbol, alpha_api_key)
                        if error_msg:
                            st.warning(f"📰 {symbol} 新聞獲取: {error_msg}")

                    # 準備 AI 分析資料
                    analysis_data = prepare_ai_analysis_data(
                        df,
                        performance,
                        all_stock_data[symbol],
                        news_data,
                        symbol
                    )

                    # 生成 AI Prompt
                    prompt = generate_ai_analysis_prompt(analysis_data)

                    # 呼叫 OpenAI API
                    ai_report = call_openai_api(prompt, openai_api_key)

                    # 儲存報告到 session_state
                    st.session_state[f"ai_report_{symbol}"] = ai_report
    
    # ===== 階段 3: 獲取詳細資料並繪製圖表 =====
    st.header("📈 股價走勢與交易記錄", divider="rainbow")
    
    # 為每檔股票獲取資料
    all_stock_data = {}
    
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    for i, symbol in enumerate(symbols):
        status_text.text(f"正在獲取 {symbol} 詳細資料... ({i+1}/{len(symbols)})")
        
        # 確定日期範圍
        symbol_trades = df[df['Symbol'] == symbol]
        start_date = symbol_trades['Date'].min() - timedelta(days=120)  
        end_date = pd.Timestamp.now()
        
        # 獲取各項資料
        historical = get_fmp_historical_price(symbol, fmp_api_key, start_date, end_date)
        profile = get_fmp_profile(symbol, fmp_api_key)
        key_metrics = get_fmp_key_metrics(symbol, fmp_api_key)
        ratios = get_fmp_ratios(symbol, fmp_api_key)
        
        all_stock_data[symbol] = {
            'historical': historical,
            'profile': profile,
            'key_metrics': key_metrics,
            'ratios': ratios
        }
        
        progress_bar.progress((i + 1) / len(symbols))
    
    # 清除進度條
    status_text.empty()
    progress_bar.empty()
    
    # 為每檔股票創建圖表和分析
    for symbol in symbols:
        st.subheader(f"📊 {symbol} 詳細分析", divider="rainbow")
        
        stock_data = all_stock_data[symbol]
        historical = stock_data['historical']
        profile = stock_data['profile']
        key_metrics = stock_data['key_metrics']
        ratios = stock_data['ratios']
        
        if historical is not None and not historical.empty:
            # 創建股價走勢圖
            fig = go.Figure()
            
            # 添加股價線
            fig.add_trace(go.Scatter(
                x=historical['date'],
                y=historical['close'],
                mode='lines',
                name='收盤價',
                line=dict(color='#1f77b4', width=2)
            ))
            
            # 添加交易記錄
            symbol_trades = df[df['Symbol'] == symbol].copy()
            symbol_trades = symbol_trades.sort_values('Date')
            
            # 買入點
            buy_trades = symbol_trades[symbol_trades['Type'] == 'Buy']
            if not buy_trades.empty:
                fig.add_trace(go.Scatter(
                    x=buy_trades['Date'],
                    y=buy_trades['Price'],
                    mode='markers',
                    name='買入',
                    marker=dict(color='green', size=10, symbol='triangle-up')
                ))
            
            # 賣出點
            sell_trades = symbol_trades[symbol_trades['Type'] == 'Sell']
            if not sell_trades.empty:
                fig.add_trace(go.Scatter(
                    x=sell_trades['Date'],
                    y=sell_trades['Price'],
                    mode='markers',
                    name='賣出',
                    marker=dict(color='red', size=10, symbol='triangle-down')
                ))
            
            fig.update_layout(
                title=f"{symbol} 股價走勢與交易記錄",
                xaxis_title="日期",
                yaxis_title="價格 (USD)",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 顯示交易記錄表格
            st.subheader("📋 交易記錄")
            display_trades = symbol_trades[['Date', 'Type', 'Quantity', 'Price']].copy()
            display_trades['Date'] = display_trades['Date'].dt.strftime('%Y-%m-%d')
            display_trades.columns = ['日期', '動作', '數量', '價格']
            
            st.dataframe(display_trades, use_container_width=True, hide_index=True)
            
            # 顯示基本資料
            if profile:
                st.subheader("🏢 公司基本資料")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("公司名稱", profile.get('companyName', 'N/A'))
                    st.metric("產業", profile.get('sector', 'N/A'))
                    st.metric("行業", profile.get('industry', 'N/A'))

                with col2:
                    market_cap = profile.get('marketCap', 0)
                    st.metric("市值", f"${market_cap:,.0f}" if market_cap else 'N/A')
                    st.metric("Beta", f"{profile.get('beta', 'N/A')}")
                    st.metric("員工人數", f"{int(profile.get('fullTimeEmployees', 0)):,}" if profile.get('fullTimeEmployees') else 'N/A')

                with col3:
                    price = profile.get('price', 0)
                    st.metric("股價", f"${price:.2f}" if price else 'N/A')
                    st.metric("52週區間", profile.get('range', 'N/A'))
                    st.metric("交易所", profile.get('exchange', 'N/A'))
            
            # 顯示關鍵指標
            if key_metrics:
                # 如果 key_metrics 是 list，取第一個元素
                metrics_data = key_metrics[0] if isinstance(key_metrics, list) and len(key_metrics) > 0 else key_metrics

                if isinstance(metrics_data, dict):
                    st.subheader("📈 關鍵財務指標")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        roe = metrics_data.get('returnOnEquity', 0)
                        st.metric("ROE", f"{roe*100:.2f}%" if roe else 'N/A')
                        roa = metrics_data.get('returnOnAssets', 0)
                        st.metric("ROA", f"{roa*100:.2f}%" if roa else 'N/A')

                    with col2:
                        debt_to_ebitda = metrics_data.get('netDebtToEBITDA', 0)
                        st.metric("淨負債/EBITDA", f"{debt_to_ebitda:.2f}" if debt_to_ebitda else 'N/A')
                        current_ratio = metrics_data.get('currentRatio', 0)
                        st.metric("流動比率", f"{current_ratio:.2f}" if current_ratio else 'N/A')

                    with col3:
                        fcf_yield = metrics_data.get('freeCashFlowYield', 0)
                        st.metric("自由現金流殖利率", f"{fcf_yield*100:.2f}%" if fcf_yield else 'N/A')
                        roic = metrics_data.get('returnOnInvestedCapital', 0)
                        st.metric("ROIC", f"{roic*100:.2f}%" if roic else 'N/A')
            
            # AI 分析
            if enable_ai and openai_api_key:
                st.subheader("🤖 AI 深度分析")

                # 顯示 AI 分析報告
                if f"ai_report_{symbol}" in st.session_state:
                    st.markdown(st.session_state[f"ai_report_{symbol}"])
                else:
                    st.warning("⚠️ AI 分析報告尚未生成，請稍候...")

                st.divider()
    
    st.success("✅ 所有分析完成！")

elif not csv_valid and uploaded_file is not None:
    st.warning("⚠️ 請修正 CSV 格式錯誤後重新上傳")

else:
    st.info("👈 請在左側欄位填寫 API Keys 並上傳投資日誌 CSV 檔案以開始分析")
