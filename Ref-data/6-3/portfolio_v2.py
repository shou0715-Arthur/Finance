import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import matplotlib.pyplot as plt
import time
from datetime import datetime, timedelta
import matplotlib

# 設定matplotlib中文字體支援
matplotlib.rcParams['font.family'] = ['DejaVu Sans']  # 使用預設字體
matplotlib.rcParams['axes.unicode_minus'] = False  # 解決負號顯示問題

# 設置頁面配置
st.set_page_config(page_title="Code Gym | AI 投資組合風險分析系統", layout="wide")

# 應用標題與描述
st.title("投資組合風險分析系統")
st.markdown("本系統協助分析您的投資組合是否符合風險屬性，僅供教育學習用途，非投資建議。")

# 側邊欄設置
with st.sidebar:
    st.header("基本資料設定")
    
    # API金鑰設置
    perplexity_api_key = st.text_input("Perplexity API Key", type="password", value='')
    fmp_api_key = st.text_input("FMP API Key", type="password", value='')
    
    # Beta值分析選項
    use_beta_analysis = st.checkbox("取得公司Beta值進行進階分析", value=False, 
                                   help="勾選此選項將使用FMP付費API獲取Beta值進行更深入的風險分析")
    
    # 風險屬性設定
    risk_profile_options = {
        "Conservative": "Conservative",
        "Moderate": "Moderate", 
        "Balanced": "Balanced",
        "Growth-oriented": "Growth-oriented",
        "Aggressive": "Aggressive"
    }
    
    risk_profile = st.selectbox(
        "風險屬性",
        options=list(risk_profile_options.keys())
    )
    
    risk_score = st.slider("總風險分數", 0, 100, 50)
    capital = st.number_input("可投資資金 (USD)", min_value=1000, value=100000, step=1000)
    
    st.subheader("風險構成評分")
    financial_status = st.slider("財務狀況", 0, 100, 50)
    investment_experience = st.slider("投資經驗", 0, 100, 50)
    investment_goal = st.slider("投資目標明確性", 0, 100, 50)
    risk_tolerance = st.slider("風險承受度", 0, 100, 50)

# 函數：取得FMP股價歷史資料
def get_fmp_historical_data(symbol, api_key):
    """從FMP API取得股票歷史價格資料（半年內）"""
    try:
        # 檢查是否為現金
        if symbol.upper() == "CASH":
            return {"is_cash": True}
            
        # 計算日期範圍（一年）
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        # 格式化日期
        from_date = start_date.strftime('%Y-%m-%d')
        to_date = end_date.strftime('%Y-%m-%d')
        
        # 構建API URL
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
        params = {
            'from': from_date,
            'to': to_date,
            'apikey': api_key
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if 'historical' in data and data['historical']:
                return {"data": data, "is_cash": False}
            else:
                return {"error": f"無法獲取{symbol}的歷史數據"}
        else:
            return {"error": f"API請求失敗，狀態碼: {response.status_code}"}
            
    except Exception as e:
        return {"error": f"取得{symbol}資料時發生錯誤: {str(e)}"}

# 函數：取得FMP公司Beta值資料
def get_fmp_company_data(symbol, api_key):
    """從FMP API取得公司Beta值等基本資料"""
    try:
        print(f"[DEBUG] 開始獲取 {symbol} 的公司資料")
        url = f"https://financialmodelingprep.com/stable/search-exchange-variants"
        params = {
            'symbol': symbol,
            'apikey': api_key
        }
        
        print(f"[DEBUG] API URL: {url}")
        print(f"[DEBUG] API 參數: {params}")
        
        response = requests.get(url, params=params)
        print(f"[DEBUG] API 回應狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[DEBUG] API 回應資料類型: {type(data)}, 長度: {len(data) if isinstance(data, list) else 'N/A'}")
            print(f"[DEBUG] API 回應資料: {data}")
            
            if isinstance(data, list) and len(data) > 0:
                company_info = data[0]
                beta_value = company_info.get("beta")
                print(f"[DEBUG] {symbol} 的 Beta 值: {beta_value} (類型: {type(beta_value)})")
                
                result = {
                    "symbol": company_info.get("symbol", symbol),
                    "company_name": company_info.get("companyName", symbol),
                    "beta": beta_value,
                    "sector": company_info.get("sector", "Unknown"),
                    "industry": company_info.get("industry", "Unknown"),
                    "market_cap": company_info.get("mktCap", None),
                    "price": company_info.get("price", None),
                    "exchange": company_info.get("exchangeShortName", "Unknown")
                }
                print(f"[DEBUG] {symbol} 公司資料解析完成: {result}")
                return result
            elif isinstance(data, dict):
                # 處理單一對象回應的情況
                print(f"[DEBUG] API 回應是單一對象，直接使用")
                beta_value = data.get("beta")
                print(f"[DEBUG] {symbol} 的 Beta 值: {beta_value} (類型: {type(beta_value)})")
                
                result = {
                    "symbol": data.get("symbol", symbol),
                    "company_name": data.get("companyName", symbol),
                    "beta": beta_value,
                    "sector": data.get("sector", "Unknown"),
                    "industry": data.get("industry", "Unknown"),
                    "market_cap": data.get("mktCap", None),
                    "price": data.get("price", None),
                    "exchange": data.get("exchangeShortName", "Unknown")
                }
                print(f"[DEBUG] {symbol} 公司資料解析完成: {result}")
                return result
            else:
                error_msg = f"找不到{symbol}的公司資料，API回應為空或格式異常"
                print(f"[DEBUG] 錯誤: {error_msg}")
                return {"error": error_msg}
        else:
            error_msg = f"API請求失敗，狀態碼: {response.status_code}"
            print(f"[DEBUG] 錯誤: {error_msg}")
            print(f"[DEBUG] 回應內容: {response.text}")
            return {"error": error_msg}
            
    except Exception as e:
        import traceback
        error_msg = f"取得{symbol}公司資料時發生錯誤: {str(e)}"
        print(f"[DEBUG] 異常錯誤: {error_msg}")
        print(f"[DEBUG] 錯誤詳細資訊: {traceback.format_exc()}")
        return {"error": error_msg}

# 函數：計算股票風險指標
def calculate_stock_metrics(historical_data):
    """計算股票的波動性和年回報率"""
    try:
        # 提取歷史數據
        prices = []
        for record in historical_data['historical']:
            prices.append(record['close'])
        
        # 反轉列表使其按時間順序排列
        prices = prices[::-1]
        
        if len(prices) < 2:
            return {"error": "歷史數據不足"}
        
        # 計算年回報率
        if len(prices) >= 252:  # 一年交易日
            start_price = prices[-252]
            end_price = prices[-1]
        else:
            start_price = prices[0] 
            end_price = prices[-1]
            
        annual_return = ((end_price - start_price) / start_price) * 100
        
        # 計算每日回報率
        daily_returns = []
        for i in range(1, len(prices)):
            daily_return = (prices[i] - prices[i-1]) / prices[i-1]
            daily_returns.append(daily_return)
        
        # 計算年化波動率
        daily_volatility = np.std(daily_returns)
        annual_volatility = daily_volatility * np.sqrt(252) * 100
        
        # 分類波動性
        if annual_volatility < 20:
            volatility_level = "Low"
        elif annual_volatility < 35:
            volatility_level = "Medium"
        else:
            volatility_level = "High"
            
        # 計算最大回撤
        peak = prices[0]
        max_drawdown = 0
        for price in prices:
            if price > peak:
                peak = price
            drawdown = (price - peak) / peak
            if drawdown < max_drawdown:
                max_drawdown = drawdown
                
        return {
            "annual_return": f"{annual_return:.1f}%",
            "volatility": volatility_level,
            "annual_volatility": annual_volatility,
            "max_drawdown": f"{max_drawdown * 100:.1f}%"
        }
        
    except Exception as e:
        return {"error": f"計算指標時發生錯誤: {str(e)}"}

# 函數：解析股票資料
def parse_stock_summary(symbol, historical_data, company_data=None):
    """解析股票資料為摘要格式"""
    try:
        print(f"[DEBUG] 開始解析 {symbol} 的資料")
        
        # 處理現金部位
        if symbol.upper() == "CASH":
            print(f"[DEBUG] {symbol} 是現金部位，返回現金摘要")
            return {
                "symbol": "CASH",
                "company_name": "Cash Position",
                "asset_type": "Cash",
                "price_data": {
                    "annual_return": "0.0%",
                    "max_drawdown": "0.0%", 
                    "volatility": "Very Low",
                    "annual_volatility": 0
                },
                "beta": None,
                "beta_risk_level": "無市場風險"
            }
        
        # 計算風險指標
        print(f"[DEBUG] 開始計算 {symbol} 的風險指標")
        metrics = calculate_stock_metrics(historical_data)
        
        if "error" in metrics:
            print(f"[DEBUG] {symbol} 風險指標計算錯誤: {metrics['error']}")
            return {"error": metrics["error"]}
        
        print(f"[DEBUG] {symbol} 風險指標計算完成: {metrics}")
        
        # 準備基本資料
        result = {
            "symbol": symbol,
            "company_name": company_data.get("company_name", symbol) if company_data else symbol,
            "asset_type": "Stock",
            "price_data": {
                "annual_return": metrics["annual_return"],
                "max_drawdown": metrics["max_drawdown"],
                "volatility": metrics["volatility"],
                "annual_volatility": metrics.get("annual_volatility", 30)
            }
        }
        
        print(f"[DEBUG] {symbol} 基本資料準備完成")
        
        # 添加Beta值資料（如果有）
        if company_data:
            print(f"[DEBUG] {symbol} 有公司資料，開始處理Beta值")
            beta_value = company_data.get("beta")
            print(f"[DEBUG] {symbol} Beta值: {beta_value} (類型: {type(beta_value)})")
            
            result["beta"] = beta_value
            
            # Beta值風險分級 - 加強錯誤處理
            if beta_value is not None:
                try:
                    beta_float = float(beta_value)
                    print(f"[DEBUG] {symbol} Beta值轉換為float: {beta_float}")
                    
                    if beta_float > 1.2:
                        result["beta_risk_level"] = "高系統性風險"
                    elif beta_float > 0.8:
                        result["beta_risk_level"] = "中等系統性風險"
                    else:
                        result["beta_risk_level"] = "低系統性風險"
                        
                    print(f"[DEBUG] {symbol} Beta風險等級: {result['beta_risk_level']}")
                except (ValueError, TypeError) as e:
                    print(f"[DEBUG] {symbol} Beta值轉換錯誤: {e}")
                    result["beta_risk_level"] = "Beta值無效"
            else:
                print(f"[DEBUG] {symbol} Beta值為None")
                result["beta_risk_level"] = "無Beta數據"
        else:
            print(f"[DEBUG] {symbol} 無公司資料")
            result["beta"] = None
            result["beta_risk_level"] = "無Beta數據"
            
        print(f"[DEBUG] {symbol} 資料解析完成: {result}")
        return result
        
    except Exception as e:
        import traceback
        error_msg = f"解析{symbol}資料時發生錯誤: {str(e)}"
        print(f"[DEBUG] 異常錯誤: {error_msg}")
        print(f"[DEBUG] 錯誤詳細資訊: {traceback.format_exc()}")
        return {"error": error_msg}

# 函數：計算綜合風險分數
def calculate_comprehensive_risk_score(asset_summary):
    """計算包含Beta值的綜合風險分數"""
    try:
        print(f"[DEBUG] 開始計算 {asset_summary.get('symbol', 'Unknown')} 的綜合風險分數")
        
        # 基礎波動性分數
        volatility_map = {"Very Low": 10, "Low": 30, "Medium": 60, "High": 90}
        volatility = asset_summary.get("price_data", {}).get("volatility", "Medium")
        volatility_score = volatility_map.get(volatility, 50)
        
        print(f"[DEBUG] 波動性: {volatility}, 波動性分數: {volatility_score}")
        
        # 檢查是否有Beta值
        beta_value = asset_summary.get("beta")
        print(f"[DEBUG] Beta值: {beta_value} (類型: {type(beta_value)})")
        
        # 如果有有效的Beta值，進行綜合計算
        if beta_value is not None:
            try:
                beta_float = float(beta_value)
                print(f"[DEBUG] Beta值轉換為float: {beta_float}")
                
                # 將Beta值標準化到0-100範圍 (Beta=2對應100分)
                beta_score = min(beta_float * 50, 100)
                print(f"[DEBUG] Beta分數: {beta_score}")
                
                # 綜合風險分數：波動性70% + Beta值30%
                comprehensive_score = (volatility_score * 0.7) + (beta_score * 0.3)
                print(f"[DEBUG] 綜合風險分數 = ({volatility_score} * 0.7) + ({beta_score} * 0.3) = {comprehensive_score}")
                
            except (ValueError, TypeError) as e:
                print(f"[DEBUG] Beta值轉換錯誤，使用純波動性分數: {e}")
                comprehensive_score = volatility_score
        else:
            # 沒有Beta值時使用原有邏輯
            print(f"[DEBUG] 沒有Beta值，使用純波動性分數")
            comprehensive_score = volatility_score
        
        print(f"[DEBUG] 最終綜合風險分數: {comprehensive_score}")
        return comprehensive_score
        
    except Exception as e:
        import traceback
        print(f"[DEBUG] 計算綜合風險分數時發生錯誤: {str(e)}")
        print(f"[DEBUG] 錯誤詳細資訊: {traceback.format_exc()}")
        # 發生錯誤時返回預設中等風險分數
        return 50

# 主界面：投資組合輸入
st.header("投資組合設置")

# 使用session_state來保存投資組合數據
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = [{"symbol": "", "allocation": 0}]

# 現金部位設置
col1, col2 = st.columns([1, 3])
with col1:
    st.write("現金部位 (%)")
with col2:
    cash_position = st.number_input("現金配置比例", min_value=0, max_value=100, value=10, step=1, label_visibility="collapsed", key="cash_position")

# 設置按鈕來增加或減少投資组合中的资产項
col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    if st.button("➕ 新增資產", type="primary", width="content"):
        st.session_state.portfolio.append({"symbol": "", "allocation": 0})
        
with col2:
    if st.button("➖ 刪除資產", type="secondary", width="content") and len(st.session_state.portfolio) > 1:
        st.session_state.portfolio.pop()

# 建立投資組合輸入表單
portfolio_data = []
remaining_allocation = 100 - cash_position

for i, item in enumerate(st.session_state.portfolio):
    col1, col2 = st.columns([1, 3])
    
    with col1:
        symbol = st.text_input(f"股票代碼 #{i+1}", value=item["symbol"], key=f"symbol_{i}")
    
    with col2:
        allocation = st.number_input(
            f"配置比例 % #{i+1}", 
            min_value=0, 
            max_value=remaining_allocation,
            value=min(item["allocation"], remaining_allocation), 
            step=1,
            key=f"allocation_{i}"
        )
    
    # 更新session_state
    st.session_state.portfolio[i]["symbol"] = symbol
    st.session_state.portfolio[i]["allocation"] = allocation
    
    if symbol and allocation > 0:
        portfolio_data.append({"symbol": symbol, "allocation": allocation})

# 加入現金部位
if cash_position > 0:
    portfolio_data.append({"symbol": "CASH", "allocation": cash_position})

# 計算總分配比例
total_allocation = cash_position + sum(item["allocation"] for item in st.session_state.portfolio)

# 顯示分配比例檢查
st.subheader("投資組合分配比例")
if total_allocation != 100:
    st.error(f"目前分配比例總計 {total_allocation}%，必須為100%")
else:
    st.success("分配比例總計 100%")

# 顯示投資組合配置
if portfolio_data:
    st.subheader("投資組合資產配置")
    
    # 使用表格顯示配置，避免中文字體問題
    config_data = []
    for item in portfolio_data:
        if item["allocation"] > 0:
            config_data.append({
                "Asset Symbol": item['symbol'],
                "Allocation %": f"{item['allocation']}%"
            })
    
    if config_data:
        config_df = pd.DataFrame(config_data)
        st.dataframe(config_df, width="stretch", hide_index=True)
        
        # 如果想要圓餅圖，可以使用 Plotly 替代 matplotlib
        try:
            import plotly.express as px
            fig = px.pie(
                values=[item["allocation"] for item in portfolio_data if item["allocation"] > 0],
                names=[f"{item['symbol']} ({item['allocation']}%)" for item in portfolio_data if item["allocation"] > 0],
                title="Portfolio Asset Allocation"
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, width="stretch")
        except ImportError:
            st.info("Portfolio allocation chart requires plotly. Showing table view instead.")

# 創建一個容器來顯示分析結果
analysis_container = st.container()

# 開始分析按鈕
if st.button("開始分析投資組合", type="primary", width="stretch"):
    print(f"[DEBUG] 分析按鈕被點擊")
    print(f"[DEBUG] total_allocation: {total_allocation}")
    print(f"[DEBUG] perplexity_api_key 長度: {len(perplexity_api_key) if perplexity_api_key else 0}")
    print(f"[DEBUG] fmp_api_key 長度: {len(fmp_api_key) if fmp_api_key else 0}")
    
    if total_allocation != 100:
        st.error(f"投資組合配置必須為100%，目前為{total_allocation}%")
    elif not perplexity_api_key or not fmp_api_key:
        st.error("請提供Perplexity和FMP的API金鑰")
        print(f"[DEBUG] API金鑰檢查失敗 - Perplexity: {bool(perplexity_api_key)}, FMP: {bool(fmp_api_key)}")
    else:
        print(f"[DEBUG] 開始執行分析邏輯")
        
        # 創建進度條
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 初始化投資組合摘要
            portfolio_summary = []
            beta_data = []  # 儲存Beta值資料
            
            # 處理每個資產
            total_assets = len(portfolio_data)
            for i, asset in enumerate(portfolio_data):
                symbol = asset["symbol"]
                allocation = asset["allocation"]
                
                # 更新進度
                progress = (i + 1) / (total_assets + 1)
                progress_bar.progress(progress)
                status_text.text(f"正在分析 {symbol}... ({i+1}/{total_assets})")
                
                # 如果是現金，直接添加現金摘要
                if symbol.upper() == "CASH":
                    cash_summary = parse_stock_summary("CASH", None, None)
                    cash_summary["allocation"] = allocation
                    portfolio_summary.append(cash_summary)
                    continue
                
                # 獲取FMP歷史股價資料
                historical_result = get_fmp_historical_data(symbol, fmp_api_key)
                
                if "error" in historical_result:
                    st.error(f"{symbol}: {historical_result['error']}")
                    continue
                
                # 獲取公司Beta值資料（如果勾選）
                company_data = None
                if use_beta_analysis:
                    print(f"[DEBUG] 開始獲取 {symbol} 的Beta值資料")
                    company_result = get_fmp_company_data(symbol, fmp_api_key)
                    
                    if "error" not in company_result:
                        company_data = company_result
                        print(f"[DEBUG] {symbol} 公司資料獲取成功")
                        
                        # 安全地構建beta_data
                        try:
                            beta_value = company_data.get("beta")
                            print(f"[DEBUG] 準備添加 {symbol} 到beta_data, Beta值: {beta_value}")
                            
                            # 安全的Beta風險等級計算
                            if beta_value is not None:
                                try:
                                    beta_float = float(beta_value)
                                    if beta_float > 1.2:
                                        beta_risk_level = "高系統性風險"
                                    elif beta_float > 0.8:
                                        beta_risk_level = "中等系統性風險"
                                    else:
                                        beta_risk_level = "低系統性風險"
                                except (ValueError, TypeError):
                                    beta_risk_level = "Beta值無效"
                            else:
                                beta_risk_level = "無Beta數據"
                            
                            beta_data.append({
                                "symbol": symbol,
                                "company_name": company_data.get("company_name", symbol),
                                "beta": beta_value,
                                "beta_risk_level": beta_risk_level,
                                "allocation": allocation
                            })
                            print(f"[DEBUG] {symbol} 成功添加到beta_data")
                            
                        except Exception as e:
                            print(f"[DEBUG] 處理 {symbol} 的beta_data時發生錯誤: {e}")
                            import traceback
                            print(f"[DEBUG] 錯誤詳細資訊: {traceback.format_exc()}")
                    else:
                        print(f"[DEBUG] {symbol} 公司資料獲取失敗: {company_result.get('error', '未知錯誤')}")
                else:
                    print(f"[DEBUG] 未勾選Beta分析，跳過 {symbol} 的Beta值獲取")
                
                # 解析資料
                print(f"[DEBUG] 開始解析 {symbol} 的資料摘要")
                asset_summary = parse_stock_summary(symbol, historical_result["data"], company_data)
                
                # 檢查是否有錯誤
                if "error" in asset_summary:
                    st.error(f"{symbol}: {asset_summary['error']}")
                    continue
                
                # 添加分配比例
                asset_summary["allocation"] = allocation
                
                # 添加到投資組合摘要
                portfolio_summary.append(asset_summary)
                print(f"[DEBUG] {symbol} 已添加到portfolio_summary，Beta值: {asset_summary.get('beta')}")
                
                # API限制，避免過快請求
                time.sleep(0.3)
            
            # 更新進度
            progress_bar.progress(0.9)
            status_text.text("正在生成分析報告...")
            
            # 調試：檢查最終的portfolio_summary內容
            print(f"[DEBUG] 最終portfolio_summary內容:")
            for asset in portfolio_summary:
                print(f"[DEBUG] - {asset.get('symbol')}: Beta={asset.get('beta')}, Beta風險={asset.get('beta_risk_level')}, 資產類型={asset.get('asset_type')}")
            
            print(f"[DEBUG] beta_data內容: {beta_data}")
            print(f"[DEBUG] use_beta_analysis狀態: {use_beta_analysis}")
            
            # 準備風險屬性資料
            risk_profile_data = {
                "level": risk_profile_options[risk_profile],
                "score": risk_score,
                "capital": capital,
                "scores": {
                    "financial_status": financial_status,
                    "investment_experience": investment_experience,
                    "investment_goal": investment_goal,
                    "risk_tolerance": risk_tolerance
                }
            }
            
            # 計算投資組合整體風險
            print(f"[DEBUG] 開始計算投資組合整體風險")
            portfolio_risk_score = 0
            
            for asset in portfolio_summary:
                try:
                    print(f"[DEBUG] 處理資產: {asset.get('symbol', 'Unknown')}")
                    
                    if asset.get("asset_type") != "Cash":
                        print(f"[DEBUG] {asset.get('symbol')} 不是現金，開始計算風險分數")
                        risk_score_individual = calculate_comprehensive_risk_score(asset)
                        allocation = asset.get("allocation", 0)
                        weighted_risk = (risk_score_individual * allocation) / 100
                        portfolio_risk_score += weighted_risk
                        
                        print(f"[DEBUG] {asset.get('symbol')} - 個別風險分數: {risk_score_individual}, 配置: {allocation}%, 加權風險: {weighted_risk}")
                    else:
                        print(f"[DEBUG] {asset.get('symbol')} 是現金部位，跳過風險計算")
                        
                except Exception as e:
                    print(f"[DEBUG] 計算 {asset.get('symbol', 'Unknown')} 風險時發生錯誤: {e}")
                    import traceback
                    print(f"[DEBUG] 錯誤詳細資訊: {traceback.format_exc()}")
                    continue
            
            print(f"[DEBUG] 投資組合整體風險分數: {portfolio_risk_score}")
            
            # 準備AI分析的數據
            input_data = {
                "risk_profile": risk_profile_data,
                "portfolio": portfolio_summary,
                "portfolio_risk_score": portfolio_risk_score
            }
            
            # 構建基礎提示語
            system_message = """你是一位專業的投資風險教育顧問，專精於投資組合風險分析。你的職責包括：

1. 客觀分析投資組合的風險水準和資產配置合理性
2. 評估投資組合是否符合用戶的風險承受度
3. 提供純教育性的資產配置建議方向
4. 強調風險意識和理性投資思維
5. 專注於股票型投資組合分析，不推薦債券、ETF等其他資產類型
6. 在資產配置調整建議中，以不同風險特性的股票類型作為主要方向

重要原則：
- 僅提供教育性分析，絕不提供具體投資建議
- 保持完全客觀中立的分析態度
- 使用專業術語但保持易懂
- 所有分析僅供教育和研究目的
- 強調投資風險和市場不確定性
- 使用繁體中文回答

嚴格的表達方式要求：
- 使用「歷史數據顯示」、「技術指標反映」、「組合特性呈現」等客觀描述
- 避免「建議」、「可能性」、「預期」、「關注」等暗示性用詞
- 禁用「如果...則...」的假設句型
- 不提供具體股票推薦，僅提及資產類型方向
- 強調「歷史表現不代表未來結果」
- 避免任何可能被解讀為投資指引的表達"""
            
            # 基礎用戶提示語
            user_prompt = f"""請基於以下投資組合數據進行專業風險分析：

**分析範圍說明**：本分析專注於股票型投資組合的風險評估，所有配置建議均以股票類型為主要考量方向。

### 用戶風險屬性
- 風險類型：{risk_profile}
- 風險評分：{risk_score}/100
- 可投資資金：${capital:,}
- 詳細評分：
  - 財務狀況：{financial_status}/100
  - 投資經驗：{investment_experience}/100
  - 投資目標明確性：{investment_goal}/100
  - 風險承受度：{risk_tolerance}/100

### 投資組合資產配置
{json.dumps(portfolio_summary, indent=2, ensure_ascii=False)}

### 投資組合風險指標
- 綜合風險評分：{portfolio_risk_score:.1f}/100

### 產業配置分析框架
請運用GICS產業分類系統評估投資組合的產業分散程度：
- 分析目前產業配置的集中度
- 評估產業間的相關性和風險特性
- 識別產業配置的潛在風險點

### 分析要求
請從以下五個面向進行專業分析：

#### 1. 投資組合整體風險水準評估
- 基於歷史波動性數據分析組合風險
- 評估資產配置的風險分散效果
- 計算組合的綜合風險評分

#### 2. 投資組合集中度分析
- 分析單一資產配置比例是否過高
- 評估資產類型的分散程度
- 識別潛在的集中風險點

#### 3. 風險適配性評估
- 比較組合風險與用戶風險承受度
- 分析是否符合投資經驗和財務狀況
- 評估風險與投資目標的一致性

#### 4. 資產配置優化方向
- 指出需要調整的產業配置方向
- 基於GICS產業分類系統與多維度風險特性分析，提供配置參考方向：

### 產業多維度風險特性分析框架

#### 防禦型產業組合
- **醫療保健(Health Care)**：低週期性、高防禦性、低利率敏感度、中等創新驅動
- **必需消費品(Consumer Staples)**：低週期性、高防禦性、低通膨敏感度、低區域依賴性
- **公用事業(Utilities)**：低週期性、高防禦性、高利率敏感度、低地緣政治風險

#### 週期敏感型產業組合
- **能源(Energy)**：高週期性、低防禦性、高通膨受益、高地緣政治敏感度
- **材料(Materials)**：高週期性、中等防禦性、高通膨敏感度、中等區域依賴性
- **工業(Industrials)**：高週期性、中等防禦性、中等利率敏感度、高資本密集度

#### 成長驅動型產業組合
- **資訊科技(Information Technology)**：中等週期性、中等防禦性、極高創新驅動、高地緣政治敏感度
- **通訊服務(Communication Services)**：低週期性、中等防禦性、高創新驅動、中等區域依賴性

#### 利率敏感型產業組合
- **金融(Financials)**：高週期性、低防禦性、極高利率敏感度、低創新驅動
- **房地產(Real Estate)**：中等週期性、中等防禦性、極高利率敏感度、低創新驅動

#### 消費週期型產業
- **非必需消費品(Consumer Discretionary)**：高週期性、低防禦性、高利率敏感度、中等創新驅動

### 多維度市場環境適應策略
- **升息環境**：增加金融股、減少成長股和房地產股配置
- **通膨環境**：配置能源、材料等通膨受益產業，避免利率敏感產業
- **經濟衰退**：提高防禦型產業比重（醫療、必需消費品、公用事業）
- **地緣風險升高**：降低高地緣政治敏感產業（科技、能源）比重
- **創新週期**：平衡高創新驅動產業與傳統穩定產業

### 產業相關性與分散效果評估
- 分析產業間的週期性相關度和利率敏感度關聯性
- 評估地緣政治風險對不同產業集群的影響
- 檢視ESG永續趨勢對傳統產業的長期影響

### 動態配置調整原則
- 基於宏觀經濟指標變化調整產業權重
- 監控產業輪動週期和最佳投資時機
- 平衡短期防禦需求與長期成長潛力

#### 5. 風險管理教育要點
- 強調投資風險和市場不確定性
- 提醒市場波動對組合的影響
- 說明風險管理的重要原則
- 強調基本面分析與風險指標分析的重要性
- 說明個股選擇應基於深入研究而非單一指標"""
            
            # 如果有Beta值數據，增加Beta分析
            if use_beta_analysis and beta_data:
                # 檢查portfolio_summary中是否真的有Beta值
                has_valid_beta = any(
                    asset.get("beta") is not None and asset.get("asset_type") != "Cash"
                    for asset in portfolio_summary
                )
                
                print(f"[DEBUG] Beta分析狀態檢查:")
                print(f"[DEBUG] - use_beta_analysis: {use_beta_analysis}")
                print(f"[DEBUG] - beta_data長度: {len(beta_data)}")
                print(f"[DEBUG] - portfolio中有有效Beta: {has_valid_beta}")
                
                # 詳細檢查每個資產的Beta狀況
                for asset in portfolio_summary:
                    if asset.get("asset_type") != "Cash":
                        print(f"[DEBUG] - {asset.get('symbol')}: Beta值={asset.get('beta')} (類型:{type(asset.get('beta'))}), 是否有效={asset.get('beta') is not None}")
                
                if has_valid_beta:
                    print(f"[DEBUG] 開始構建Beta分析章節")
                    beta_section = f"""

### Beta值系統性風險分析
以下是投資組合中各資產的Beta值詳細資料：

**Beta值數據摘要：**
"""
                    # 從portfolio_summary中提取Beta資料，確保數據一致性
                    beta_assets_count = 0
                    for asset in portfolio_summary:
                        if asset.get("asset_type") != "Cash" and asset.get("beta") is not None:
                            beta_assets_count += 1
                            beta_section += f"""
- {asset['symbol']} ({asset['company_name']}):
  - Beta值: {asset['beta']}
  - Beta風險等級: {asset['beta_risk_level']}
  - 投資組合配置: {asset['allocation']}%
"""
                            print(f"[DEBUG] 添加 {asset['symbol']} 到Beta分析章節")
                    
                    print(f"[DEBUG] 總共有 {beta_assets_count} 個資產有Beta值")
                    
                    beta_section += f"""
**Beta值解讀說明**：
- Beta > 1：表示該資產對市場波動的敏感度較高，當市場上漲或下跌時，該資產的價格波動幅度通常會大於市場整體表現，屬於高系統性風險
- Beta < 1：表示該資產對市場波動的敏感度較低，價格波動相對市場較為穩定，屬於低系統性風險
- Beta = 1：表示該資產的價格波動與市場整體同步

**重要提醒**：Beta值僅反映歷史價格與市場的相關性，不代表投資報酬的高低。個股實際表現仍主要取決於公司基本面、產業前景、市場情緒等多重因素。

#### 6. Beta值系統性風險深度分析
請基於以上Beta值數據進行以下分析：
- 分析各資產的Beta值特性及其對投資組合的影響
- 評估組合整體的系統性風險暴露程度
- 結合GICS產業分類，解讀不同產業的Beta值特性
- 提供基於產業分散和Beta值的風險平衡教育要點
- 說明Beta值在不同市場環境和產業週期下的表現特性"""
                    
                    user_prompt += beta_section
                    print(f"[DEBUG] 已添加Beta分析章節到提示語")
                else:
                    print(f"[DEBUG] 雖然勾選Beta分析，但portfolio_summary中沒有有效的Beta值")
                    user_prompt += """

### Beta值分析狀態
雖然啟用了Beta值分析，但所分析的資產中沒有獲得有效的Beta值數據。請在分析中說明這種情況，並解釋可能的原因（如：新上市股票、資料來源限制等）。"""
            elif use_beta_analysis and not beta_data:
                print(f"[DEBUG] 勾選了Beta分析但beta_data為空")
                user_prompt += """

### Beta值分析狀態
雖然啟用了Beta值分析，但未能從API獲取到任何Beta值數據。請在分析中說明這種情況。"""
            else:
                print(f"[DEBUG] 未啟用Beta分析或無Beta數據")
                print(f"[DEBUG] - use_beta_analysis: {use_beta_analysis}")
                print(f"[DEBUG] - beta_data: {beta_data}")
            
            user_prompt += "\n\n請使用markdown格式呈現分析結果，保持客觀專業的教育導向。"
            
            # 列印完整的提示語內容供除錯
            print(f"[DEBUG] ==================== 完整提示語內容 ====================")
            print(f"[DEBUG] System Message:")
            print(system_message)
            print(f"[DEBUG] ==================== 分隔線 ====================")
            print(f"[DEBUG] User Prompt:")
            print(user_prompt)
            print(f"[DEBUG] ==================== 提示語結束 ====================")
            
            # 調用Perplexity API
            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                "accept": "application/json",
                "authorization": f"Bearer {perplexity_api_key}",
                "content-type": "application/json"
            }
            payload = {
                "model": "sonar-reasoning",
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False,
                "search_mode": "sec",
                "search_after_date_filter": "1/1/2023"
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                analysis_result = response.json()['choices'][0]['message']['content']
            else:
                analysis_result = f"分析請求失敗，狀態碼: {response.status_code}"
            
            # 完成進度
            progress_bar.progress(1.0)
            status_text.text("分析完成！")
            
            # 在分析容器中顯示結果
            with analysis_container:
                st.header("投資組合分析結果")
                st.markdown(analysis_result)
                
                # 生成資產分配表格
                st.subheader("投資組合資產明細")
                
                # 準備表格數據
                table_data = []
                for asset in portfolio_summary:
                    asset_type = asset.get("asset_type", "Unknown")
                    volatility = asset.get("price_data", {}).get("volatility", "N/A")
                    annual_return = asset.get("price_data", {}).get("annual_return", "N/A")
                    beta_info = f"{asset.get('beta', 'N/A')}" if asset.get('beta') is not None else "N/A"
                    beta_risk = asset.get("beta_risk_level", "N/A")
                    
                    table_data.append({
                        "資產": f"{asset['symbol']} ({asset['company_name']})",
                        "類型": asset_type,
                        "配置比例": f"{asset['allocation']}%",
                        "波動性": volatility,
                        "年回報": annual_return,
                        "Beta值": beta_info,
                        "Beta風險": beta_risk
                    })
                
                # 顯示表格
                st.table(pd.DataFrame(table_data))
                
                # 添加風險評估與風險偏好比較
                st.subheader("風險評估與風險偏好比較")
                
                # 建立兩個欄
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 您的風險屬性")
                    st.info(f"""
                    **風險類型**: {risk_profile} ({risk_profile_options[risk_profile]})
                    **風險評分**: {risk_score}/100
                    **財務狀況**: {financial_status}/100
                    **投資經驗**: {investment_experience}/100
                    **投資目標明確性**: {investment_goal}/100
                    **風險承受度**: {risk_tolerance}/100
                    """)
                
                with col2:
                    st.markdown("#### 投資組合特性")
                    
                    # 計算現金比例
                    cash_percentage = 0
                    for asset in portfolio_summary:
                        if asset.get("asset_type") == "Cash":
                            cash_percentage += asset.get("allocation", 0)
                    
                    # 顯示投資組合風險指標
                    st.info(f"""
                    **綜合風險水平**: {portfolio_risk_score:.1f}/100
                    **現金部位**: {cash_percentage}%
                    **風險資產部位**: {100-cash_percentage}%
                    **Beta分析**: {"已啟用" if use_beta_analysis else "未啟用"}
                    """)
            
        except Exception as e:
            import traceback
            error_msg = f"分析過程中發生錯誤: {str(e)}"
            print(f"[DEBUG] 主要錯誤: {error_msg}")
            print(f"[DEBUG] 完整錯誤追蹤: {traceback.format_exc()}")
            st.error(error_msg)
            st.error("詳細錯誤資訊已輸出到控制台，請檢查終端機或命令提示字元的輸出。")

# 頁面底部免責聲明
st.markdown("---")
st.caption("""
**免責聲明**: 本系統僅供教育和學習目的，不構成投資建議。市場有風險，投資需謹慎。
系統分析基於有限資料和模型，實際投資決策應考慮個人情況並諮詢專業投資顧問。
""")