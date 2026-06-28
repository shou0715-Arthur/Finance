import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import json
from datetime import datetime
import numpy as np
from openai import OpenAI
import time

st.set_page_config(
    page_title="AI 投資理財分析系統",
    page_icon="📊",
    layout="wide"
)

# 定義函數從 Alpha Vantage 獲取股價數據
def get_stock_data(symbol, api_key):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    
    # 確認 API 響應包含股價數據
    if "Time Series (Daily)" not in data:
        st.error(f"無法獲取 {symbol} 的股價數據。可能是 API 金鑰無效、股票代號錯誤或已達到 API 請求限制。")
        st.json(data)  # 顯示 API 響應以便調試
        return None
    
    # 解析股價數據
    time_series = data["Time Series (Daily)"]
    df = pd.DataFrame(time_series).T
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    
    # 轉換數據類型
    for col in df.columns:
        df[col] = pd.to_numeric(df[col])
    
    # 重命名列
    df.columns = ['開盤價', '最高價', '最低價', '收盤價', '成交量']
    
    # 添加日期列用於繪圖
    df['date'] = df.index
    
    # 只返回最近60天的數據以便計算更多移動平均線
    return df.tail(60)

# 【新增】計算 topic 加權分數的輔助函數
def calculate_topic_weighted_score(topic_relevance, ticker_relevance):
    """
    計算 topic 的加權分數
    topic_relevance: topic 與文章的相關性分數
    ticker_relevance: 文章與 ticker 的相關性分數
    """
    return float(topic_relevance) * float(ticker_relevance)

# 【新增】將加權分數轉換為文字描述的輔助函數
def get_topic_relevance_label(weighted_score):
    """
    根據加權分數返回文字描述
    """
    if weighted_score >= 0.6:
        return "高度相關"
    elif weighted_score >= 0.3:
        return "中度相關"
    else:
        return "低度相關"

# 【修改】定義函數從 Alpha Vantage 獲取新聞情緒數據
def get_news_sentiment(symbol, api_key):
    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    
    # 確認 API 響應包含新聞數據
    if "feed" not in data:
        st.error(f"無法獲取 {symbol} 的新聞情緒數據。可能是 API 金鑰無效或已達到 API 請求限制。")
        st.json(data)  # 顯示 API 響應以便調試
        return None
    
    news_items = []
    
    # 解析新聞數據
    for item in data["feed"]:
        # 確認此新聞與股票相關
        ticker_sentiments = [ts for ts in item.get("ticker_sentiment", []) if ts.get("ticker") == symbol]
        
        if ticker_sentiments:
            sentiment_data = ticker_sentiments[0]
            
            # 提取股票特定情緒數據
            ticker_sentiment_score = sentiment_data.get("ticker_sentiment_score", "0")
            if isinstance(ticker_sentiment_score, str):
                try:
                    ticker_sentiment_score = float(ticker_sentiment_score)
                except ValueError:
                    ticker_sentiment_score = 0.0
            elif ticker_sentiment_score is None:
                ticker_sentiment_score = 0.0
            else:
                ticker_sentiment_score = float(ticker_sentiment_score)
            
            # 提取文章整體情緒數據
            overall_sentiment_score = item.get("overall_sentiment_score", 0)
            if isinstance(overall_sentiment_score, str):
                try:
                    overall_sentiment_score = float(overall_sentiment_score)
                except ValueError:
                    overall_sentiment_score = 0.0
            elif overall_sentiment_score is None:
                overall_sentiment_score = 0.0
            else:
                overall_sentiment_score = float(overall_sentiment_score)
            
            # 提取相關性分數
            relevance_score = sentiment_data.get("relevance_score", "0")
            if isinstance(relevance_score, str):
                try:
                    relevance_score = float(relevance_score)
                except ValueError:
                    relevance_score = 0.0
            elif relevance_score is None:
                relevance_score = 0.0
            else:
                relevance_score = float(relevance_score)
            
            # 【新增】處理 topics 資訊
            topics_list = []
            raw_topics = item.get("topics", [])
            
            for topic in raw_topics:
                topic_name = topic.get("topic", "Unknown")
                topic_relevance = topic.get("relevance_score", "0")
                
                # 轉換 topic_relevance 為 float
                if isinstance(topic_relevance, str):
                    try:
                        topic_relevance = float(topic_relevance)
                    except ValueError:
                        topic_relevance = 0.0
                elif topic_relevance is None:
                    topic_relevance = 0.0
                else:
                    topic_relevance = float(topic_relevance)
                
                # 過濾: 只保留 topic 原始相關性 > 0.2 的主題
                if topic_relevance > 0.2:
                    # 計算加權分數
                    weighted_score = calculate_topic_weighted_score(topic_relevance, relevance_score)
                    
                    topics_list.append({
                        "topic": topic_name,
                        "topic_relevance": topic_relevance,
                        "weighted_score": weighted_score,
                        "label": get_topic_relevance_label(weighted_score)
                    })
            
            # 依照加權分數排序 topics
            topics_list = sorted(topics_list, key=lambda x: x["weighted_score"], reverse=True)
            
            news_items.append({
                "title": item.get("title", "無標題"),
                "published_time": item.get("time_published", ""),
                "summary": item.get("summary", "無摘要"),
                "url": item.get("url", "#"),
                # 股票特定情緒
                "ticker_sentiment": sentiment_data.get("ticker_sentiment_label", "Neutral"),
                "ticker_sentiment_score": ticker_sentiment_score,
                # 文章整體情緒
                "overall_sentiment": item.get("overall_sentiment_label", "Neutral"),
                "overall_sentiment_score": overall_sentiment_score,
                # 相關性
                "relevance_score": relevance_score,
                # 【新增】Topics
                "topics": topics_list
            })
    
    # 按相關性分數和股票情緒分數排序，取前10則
    if news_items:
        news_items = sorted(news_items, key=lambda x: (x["relevance_score"], abs(x["ticker_sentiment_score"])), reverse=True)
        return news_items[:10]
    else:
        return []

# 【修改】使用 OpenAI GPT 分析市場情緒
def analyze_market_sentiment(news_items, openai_api_key):
    if not news_items:
        return "無法獲取足夠的新聞數據來分析市場情緒。"
    
    client = OpenAI(api_key=openai_api_key)
    
    # 準備新聞摘要文本
    news_text = ""
    for i, item in enumerate(news_items, 1):
        news_text += f"新聞 {i}:\n"
        news_text += f"標題: {item['title']}\n"
        news_text += f"摘要: {item['summary']}\n"
        news_text += f"股票情緒: {item['ticker_sentiment']} (分數: {item['ticker_sentiment_score']})\n"
        news_text += f"文章情緒: {item['overall_sentiment']} (分數: {item['overall_sentiment_score']})\n"
        news_text += f"相關性: {item['relevance_score']}\n"
        
        # 【新增】加入 topics 資訊 (使用文字描述)
        if item.get('topics'):
            topics_str = ", ".join([f"{t['topic']} ({t['label']})" for t in item['topics'][:3]])  # 只顯示前3個
            news_text += f"相關主題: {topics_str}\n"
        
        news_text += "\n"
    
    # 準備 prompt
    prompt = f"""
    你是一位專業的金融市場分析師。請根據以下新聞和情緒數據，分析目前市場對該股票的情緒狀態。
    提供一個簡短但全面的市場情緒總結（3-5句話）。
    
    {news_text}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"分析市場情緒時出錯: {str(e)}"

# 生成情緒統計摘要的函數
def generate_sentiment_summary(news_items):
    if not news_items:
        return None
    
    # 統計股票情緒分布
    ticker_sentiments = [item['ticker_sentiment'] for item in news_items]
    ticker_sentiment_counts = {}
    for sentiment in ticker_sentiments:
        ticker_sentiment_counts[sentiment] = ticker_sentiment_counts.get(sentiment, 0) + 1
    
    # 統計文章情緒分布
    overall_sentiments = [item['overall_sentiment'] for item in news_items]
    overall_sentiment_counts = {}
    for sentiment in overall_sentiments:
        overall_sentiment_counts[sentiment] = overall_sentiment_counts.get(sentiment, 0) + 1
    
    # 計算平均分數
    avg_ticker_score = np.mean([item['ticker_sentiment_score'] for item in news_items])
    avg_overall_score = np.mean([item['overall_sentiment_score'] for item in news_items])
    avg_relevance_score = np.mean([item['relevance_score'] for item in news_items])
    
    return {
        'ticker_sentiment_counts': ticker_sentiment_counts,
        'overall_sentiment_counts': overall_sentiment_counts,
        'avg_ticker_score': avg_ticker_score,
        'avg_overall_score': avg_overall_score,
        'avg_relevance_score': avg_relevance_score,
        'total_news': len(news_items)
    }

# 【修改】使用 OpenAI GPT 生成投資建議
def generate_investment_advice(stock_data, news_items, symbol, openai_api_key):
    if stock_data is None or not news_items:
        return "無法獲取足夠的數據來生成投資建議。"
    
    client = OpenAI(api_key=openai_api_key)
    
    # 準備股價數據
    stock_data_text = stock_data[['收盤價']].tail(30).to_string()
    
    # 準備新聞摘要文本
    news_text = ""
    for i, item in enumerate(news_items, 1):
        news_text += f"新聞 {i}:\n"
        news_text += f"標題: {item['title']}\n"
        news_text += f"摘要: {item['summary']}\n"
        news_text += f"股票情緒: {item['ticker_sentiment']} (分數: {item['ticker_sentiment_score']})\n"
        news_text += f"文章情緒: {item['overall_sentiment']} (分數: {item['overall_sentiment_score']})\n"
        news_text += f"相關性: {item['relevance_score']}\n"
        
        # 【新增】加入 topics 資訊 (使用文字描述)
        if item.get('topics'):
            topics_str = ", ".join([f"{t['topic']} ({t['label']})" for t in item['topics'][:3]])  # 只顯示前3個
            news_text += f"相關主題: {topics_str}\n"
        
        news_text += "\n"
    
    # 準備 prompt
    prompt = f"""
    你是一位熟悉金融市場的分析師，請根據以下資訊，給出一份具結構的分析報告，包含：股價走勢分析、媒體情緒總結、技術面觀察，以及短期與中長期的分析結果。

    最近30天的 {symbol} 股價資料如下：
    {stock_data_text}

    近期新聞與情緒摘要如下：
    {news_text}

    輸出結果，包含以下標題：

    ## 分析總結

    ## 媒體情緒觀察(請依據標題和摘要簡單提出分析論述)

    ## 綜合分析結果（短期與中長期）
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"生成投資建議時出錯: {str(e)}"

# 獲取情緒顏色的輔助函數
def get_sentiment_color(sentiment_label):
    sentiment_lower = sentiment_label.lower()
    if "bullish" in sentiment_lower:
        if "somewhat" in sentiment_lower:
            return "🟢", "#90EE90"  # 淺綠色
        else:
            return "🟢", "#008000"  # 深綠色
    elif "bearish" in sentiment_lower:
        if "somewhat" in sentiment_lower:
            return "🔴", "#FFB6C1"  # 淺紅色
        else:
            return "🔴", "#FF0000"  # 深紅色
    else:
        return "⚪", "#808080"  # 灰色

# 【新增】獲取相關性標籤和顏色的輔助函數
def get_relevance_label(score):
    """
    將相關性分數轉換為直觀的標籤和顏色
    """
    if score >= 0.8:
        return "🔥 高度相關", "#FF4500"
    elif score >= 0.5:
        return "✅ 相關", "#FFA500"
    elif score >= 0.3:
        return "⚡ 中度相關", "#FFD700"
    else:
        return "❓ 低度相關", "#808080"

# Streamlit 側邊欄 - 用戶輸入
st.sidebar.header("AI 市場情緒分析助理", divider="rainbow")

symbol = st.sidebar.text_input("股票代號 (例如: AAPL, MSFT)", "AAPL")
alpha_vantage_api_key = st.sidebar.text_input("Alpha Vantage API Key", type="password")
openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")

# 添加分析按鈕
analyze_button = st.sidebar.button("開始分析")
st.sidebar.markdown("""
### 📢 免責聲明
本系統僅供學術研究與教育用途，AI 提供的數據與分析結果僅供參考，**不構成投資建議或財務建議**。
請使用者自行判斷投資決策，並承擔相關風險。本系統作者不對任何投資行為負責，亦不承擔任何損失責任。
""")

# 主頁面
st.header("Code Gym | AI 市場情緒分析助理", divider="rainbow")

# 只有在按下分析按鈕且提供了必要的 API 金鑰時才執行分析
if analyze_button and alpha_vantage_api_key and openai_api_key:
    # 顯示加載中的消息
    with st.spinner("正在獲取股價數據..."):
        stock_data = get_stock_data(symbol, alpha_vantage_api_key)
    
    if stock_data is not None:
        # 股價趨勢圖
        st.header("一、股價趨勢圖")
        
        # 計算移動平均線
        stock_data['MA5'] = stock_data['收盤價'].rolling(window=5).mean()
        stock_data['MA10'] = stock_data['收盤價'].rolling(window=10).mean()
        stock_data['MA20'] = stock_data['收盤價'].rolling(window=20).mean()
        stock_data['MA60'] = stock_data['收盤價'].rolling(window=60).mean()
        
        # 取最近30天用於顯示
        display_data = stock_data.tail(30).copy()
        
        # 繪製K線圖
        fig = go.Figure()
        
        # 添加K線圖
        fig.add_trace(go.Candlestick(
            x=display_data.index,
            open=display_data["開盤價"],
            high=display_data["最高價"],
            low=display_data["最低價"],
            close=display_data["收盤價"],
            name="K線圖"
        ))
        
        # 添加移動平均線
        fig.add_trace(go.Scatter(
            x=display_data.index, 
            y=display_data["MA5"], 
            mode="lines", 
            name="MA5",
            line=dict(color='orange', width=1)
        ))
        fig.add_trace(go.Scatter(
            x=display_data.index, 
            y=display_data["MA10"], 
            mode="lines", 
            name="MA10",
            line=dict(color='blue', width=1)
        ))
        fig.add_trace(go.Scatter(
            x=display_data.index, 
            y=display_data["MA20"], 
            mode="lines", 
            name="MA20",
            line=dict(color='red', width=1)
        ))
        fig.add_trace(go.Scatter(
            x=display_data.index, 
            y=display_data["MA60"], 
            mode="lines", 
            name="MA60",
            line=dict(color='purple', width=1)
        ))
        
        # 改進圖表設定
        start_date = display_data.index.min()
        end_date = display_data.index.max()
        
        fig.update_layout(
            title=f"{symbol} 股價走勢 ({start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')})",
            xaxis_title="日期",
            yaxis_title="價格",
            xaxis_rangeslider_visible=False,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 表格顯示數據
        with st.expander("查看股價數據"):
            st.dataframe(display_data[['開盤價', '最高價', '最低價', '收盤價', '成交量', 'MA5', 'MA10', 'MA20', 'MA60']])
        
        # 情緒新聞摘要
        st.header("二、情緒新聞摘要")
        
        with st.spinner("正在獲取新聞情緒數據..."):
            news_items = get_news_sentiment(symbol, alpha_vantage_api_key)
        
        if news_items:
            # 生成統計摘要
            sentiment_summary = generate_sentiment_summary(news_items)
            
            # 統計摘要區塊
            st.subheader("📊 情緒統計總覽")
            
            # 使用三欄布局
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                st.markdown("**📈 股票情緒分布**")
                if sentiment_summary['ticker_sentiment_counts']:
                    # 創建股票情緒餅圖
                    labels = list(sentiment_summary['ticker_sentiment_counts'].keys())
                    values = list(sentiment_summary['ticker_sentiment_counts'].values())
                    
                    fig_ticker = go.Figure(data=[go.Pie(
                        labels=labels,
                        values=values,
                        hole=0.3,
                        textinfo='label+percent'
                    )])
                    fig_ticker.update_layout(
                        title="股票情緒分布",
                        height=300,
                        showlegend=True
                    )
                    st.plotly_chart(fig_ticker, use_container_width=True)
            
            with col2:
                st.markdown("**📰 文章情緒分布**")
                if sentiment_summary['overall_sentiment_counts']:
                    # 創建文章情緒餅圖
                    labels = list(sentiment_summary['overall_sentiment_counts'].keys())
                    values = list(sentiment_summary['overall_sentiment_counts'].values())
                    
                    fig_overall = go.Figure(data=[go.Pie(
                        labels=labels,
                        values=values,
                        hole=0.3,
                        textinfo='label+percent'
                    )])
                    fig_overall.update_layout(
                        title="文章情緒分布",
                        height=300,
                        showlegend=True
                    )
                    st.plotly_chart(fig_overall, use_container_width=True)
            
            with col3:
                st.markdown("**📈 關鍵指標**")
                st.metric("新聞總數", sentiment_summary['total_news'])
                st.metric("平均股票情緒分數", f"{sentiment_summary['avg_ticker_score']:.3f}")
                st.metric("平均文章情緒分數", f"{sentiment_summary['avg_overall_score']:.3f}")
                st.metric("平均相關性分數", f"{sentiment_summary['avg_relevance_score']:.3f}")
            
            st.divider()
            
            # 【修改】詳細新聞列表
            st.subheader("📝 詳細新聞列表")

            # 【新增】情緒與相關性分數說明
            with st.expander("ℹ️ 如何解讀情緒分數與相關性分數?", expanded=False):
                st.markdown("""
                ### 📊 情緒分數說明
                情緒分數反映新聞內容對股票的正面或負面態度,範圍從 **-1 (極度看空)** 到 **+1 (極度看多)**:
                
                - **🟢 Bullish (看多)**: ≥ 0.35,新聞內容明顯正面,可能推升股價
                - **🟢 Somewhat-Bullish (偏看多)**: 0.15 ~ 0.35,新聞內容偏正面
                - **⚪ Neutral (中性)**: -0.15 ~ 0.15,新聞內容中立,無明顯傾向
                - **🔴 Somewhat-Bearish (偏看空)**: -0.35 ~ -0.15,新聞內容偏負面
                - **🔴 Bearish (看空)**: ≤ -0.35,新聞內容明顯負面,可能打壓股價
                
                ---
                
                ### 🎯 相關性分數說明
                相關性分數衡量新聞與該股票的關聯程度,範圍從 **0 (無關)** 到 **1 (高度相關)**:
                
                - **🔥 高度相關** (≥ 0.8): 新聞主要討論該股票
                - **✅ 相關** (0.5 ~ 0.8): 新聞明確提及該股票
                - **⚡ 中度相關** (0.3 ~ 0.5): 新聞有提到該股票但非重點
                - **❓ 低度相關** (< 0.3): 新聞僅略微提及該股票
                
                💡 **建議**: 優先關注「高相關性」且「情緒明確」的新聞,對股價影響較大。
                """)

            st.divider()

            for i, item in enumerate(news_items, 1):
                # 獲取情緒顏色和圖示
                ticker_icon, ticker_color = get_sentiment_color(item["ticker_sentiment"])
                overall_icon, overall_color = get_sentiment_color(item["overall_sentiment"])
                
                # 【新增】獲取相關性標籤
                relevance_label, relevance_color = get_relevance_label(item["relevance_score"])
                
                
                with st.expander(f"{i}. {item['title']}", expanded=False):
                    
                    try:
                        published_time = datetime.strptime(item["published_time"], "%Y%m%dT%H%M%S").strftime("%Y-%m-%d %H:%M:%S") if item["published_time"] else "未知時間"
                    except:
                        published_time = "未知時間"
                    
                    st.caption(f"🕐 發布時間: {published_time}")
                    
                    st.divider()
                    
                    # 【修改】重新設計資訊布局 - 更清晰的分區
                    # 第一區: 情緒分析
                    st.markdown("### 📈 情緒分析")
                    col_sentiment_1, col_sentiment_2 = st.columns(2)
                    
                    with col_sentiment_1:
                        st.markdown(f"**針對 {symbol} 的情緒**")
                        st.markdown(f"{ticker_icon} **{item['ticker_sentiment']}**")
                        st.caption(f"分數: {item['ticker_sentiment_score']:.3f}")
                    
                    with col_sentiment_2:
                        st.markdown(f"**文章整體情緒**")
                        st.markdown(f"{overall_icon} **{item['overall_sentiment']}**")
                        st.caption(f"分數: {item['overall_sentiment_score']:.3f}")
                    
                    st.divider()
                    
                    # 第二區: 相關性與主題
                    st.markdown("### 🎯 相關性與主題")
                    
                    # 相關性分數
                    st.markdown(f"**新聞相關性:** {relevance_label}")
                    st.caption(f"相關性分數: {item['relevance_score']:.3f}")
                    
                    # 【保持】顯示 Topics 資訊
                    if item.get('topics'):
                        st.markdown("**📌 涵蓋主題:**")
                        topics_display = []
                        for topic in item['topics']:
                            # 根據加權分數顯示不同圖示
                            if topic['weighted_score'] >= 0.6:
                                icon = "🔥"
                            elif topic['weighted_score'] >= 0.3:
                                icon = "✅"
                            else:
                                icon = "⚡"
                            
                            topics_display.append(
                                f"{icon} **{topic['topic']}** ({topic['label']})"
                            )
                        
                        # 使用更清晰的顯示方式
                        for topic_str in topics_display:
                            st.markdown(f"- {topic_str}")
                    
                    st.divider()
                    
                    # 第三區: 新聞摘要
                    st.markdown("### 📄 新聞摘要")
                    st.write(item['summary'])
                    
                    # 原文連結
                    if item['url'] != "#":
                        st.markdown(f"🔗 [閱讀完整新聞內容]({item['url']})")
        else:
            st.info("無法獲取相關新聞。")
        
        # 市場情緒總結
        st.header("三、市場情緒總結")
        
        with st.spinner("正在分析市場情緒..."):
            sentiment_analysis = analyze_market_sentiment(news_items, openai_api_key)
            st.write(sentiment_analysis)
        
        # AI 投資建議
        st.header("四、AI 分析結果")
        
        with st.spinner("正在生成投資建議..."):
            investment_advice = generate_investment_advice(stock_data, news_items, symbol, openai_api_key)
            st.markdown(investment_advice)

elif analyze_button:
    st.warning("請填寫所有必要的 API 金鑰再開始分析。")