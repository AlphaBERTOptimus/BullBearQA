# -*- coding: utf-8 -*-
# Version: 2.4.0 - Final

import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

import streamlit as st
from langchain_openai import ChatOpenAI
from agents.fundamental_agent import FundamentalAgent
from agents.technical_agent import TechnicalAgent
from agents.sentiment_agent import SentimentAgent
from agents.comparison_agent import ComparisonAgent
from router.question_router import QuestionRouter
from judge.arena_judge import ArenaJudge
import time
import traceback
import re

from trading.strategy_generator import StrategyGenerator
from trading.options_recommender import OptionsRecommender
from trading.paper_trading import PaperTradingTracker
from visualization.candlestick_chart import CandlestickChart

st.set_page_config(
    page_title="BullBearQA - 智能股票分析",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
    .main-header p {
        color: #e0e0e0;
        margin: 0.5rem 0 0 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>📊 BullBearQA</h1>
    <p>基于多Agent系统的智能股票分析平台 | Powered by DeepSeek</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🔐 配置")
    
    api_key = st.text_input(
        "DeepSeek API Key",
        type="password",
        key="api_key_input"
    )
    
    if api_key:
        st.success("✅ API Key 已设置")
    
    st.markdown("---")
    st.markdown("## 📖 使用指南")
    st.markdown("""
**● 基本面分析**
- "AAPL的PE怎么样？"
- "分析TSLA的财务状况"

**● 技术面分析**
- "NVDA的RSI是多少？"
- "MSFT的技术指标如何？"

**● 市场情绪**
- "META最近的新闻是什么？"
- "市场对GOOGL的看法"

**● 股票对比**
- "比较AAPL和MSFT"
- "NVDA vs AMD 哪个更好？"
    """)
    
    st.markdown("---")
    
    with st.expander("⚙️ 高级设置"):
        show_routing = st.checkbox("显示路由信息", value=False)
        show_timing = st.checkbox("显示执行时间", value=True)
    
    if st.button("🗑️ 清除对话历史"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 💡 投资评分")
    if 'last_score' in st.session_state:
        score_data = st.session_state.last_score
        st.metric("综合评分", f"{score_data['score']}/100", score_data['rating'])
        st.progress(score_data['score'] / 100)
    
    st.markdown("---")
    if 'paper_tracker' not in st.session_state:
        st.session_state.paper_tracker = PaperTradingTracker()

@st.cache_resource
def get_components(api_key: str):
    try:
        llm = ChatOpenAI(
            model="deepseek-chat",
            openai_api_key=api_key,
            openai_api_base="https://api.deepseek.com",
            temperature=0.7
        )
        
        return {
            'router': QuestionRouter(llm),
            'fundamental_agent': FundamentalAgent(llm),
            'technical_agent': TechnicalAgent(llm),
            'sentiment_agent': SentimentAgent(llm),
            'comparison_agent': ComparisonAgent(llm),
            'judge': ArenaJudge(llm),
            'strategy_generator': StrategyGenerator(),
            'options_recommender': OptionsRecommender()
        }
    except Exception as e:
        st.error(f"初始化失败: {str(e)}")
        return None

if 'messages' not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if api_key:
    components = get_components(api_key)
    
    if components:
        if prompt := st.chat_input("请输入你的股票分析问题..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                start_time = time.time()
                
                try:
                    routing_result = components['router'].route(prompt)
                    agent_type = routing_result['agent_type']
                    agent_outputs = {}
                    
                    selected_agent = {
                        'fundamental': components['fundamental_agent'],
                        'technical': components['technical_agent'],
                        'sentiment': components['sentiment_agent'],
                        'comparison': components['comparison_agent']
                    }.get(agent_type)
                    
                    if selected_agent:
                        output = selected_agent.run(prompt)
                        agent_outputs[agent_type] = output
                    
                    final_response = components['judge'].synthesize(prompt, agent_outputs)
                    score_data = components['judge'].create_investment_score(agent_outputs)
                    st.session_state.last_score = score_data
                    rating = score_data.get('rating', 'Hold')
                    
                    response_text = final_response
                    if show_timing:
                        response_text += f"\n\n⏱️ 执行时间: {time.time() - start_time:.2f}秒"
                    
                    message_placeholder.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                    
                    # 提取股票代码
                    display_ticker = None
                    display_tickers = routing_result.get('tickers', [])
                    
                    if not display_tickers:
                        common_stocks = {
                            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA',
                            'AMD', 'NFLX', 'MU', 'TSM', 'V', 'JPM'
                        }
                        
                        for stock in common_stocks:
                            if stock in prompt.upper():
                                display_tickers = [stock]
                                break
                    
                    if display_tickers:
                        display_ticker = display_tickers[0]
                    
                    if display_ticker or len(display_tickers) >= 2:
                        st.markdown("---")
                        chart_generator = CandlestickChart()
                        
                        if len(display_tickers) >= 2:
                            st.markdown("## 📈 股票走势对比")
                            
                            chart_period = st.selectbox(
                                "📅 选择时间周期",
                                ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
                                index=3,
                                format_func=lambda x: {"1mo": "1个月", "3mo": "3个月", "6mo": "6个月", "1y": "1年", "2y": "2年", "5y": "5年"}[x],
                                key=f"compare_{time.time()}"
                            )
                            
                            fig = chart_generator.create_comparison_chart(display_tickers, chart_period)
                            if fig:
                                st.plotly_chart(fig, use_container_width=True)
                                
                                st.markdown("### 📊 当前价格对比")
                                cols = st.columns(len(display_tickers))
                                for i, t in enumerate(display_tickers):
                                    try:
                                        price_info = chart_generator.get_price_change(t)
                                        if price_info and isinstance(price_info, dict):
                                            with cols[i]:
                                                change_color = "normal" if price_info.get('change', 0) >= 0 else "inverse"
                                                st.metric(
                                                    t,
                                                    f"${price_info.get('current_price', 0):.2f}",
                                                    delta=f"{price_info.get('change_pct', 0):+.2f}%",
                                                    delta_color=change_color
                                                )
                                    except:
                                        pass
                        
                        elif display_ticker:
                            st.markdown("## 📈 股价走势分析")
                            
                            col1, col2, col3 = st.columns([2, 1, 1])
                            
                            with col1:
                                chart_period = st.selectbox(
                                    "📅 选择时间周期",
                                    ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
                                    index=1,
                                    format_func=lambda x: {"1mo": "1个月", "3mo": "3个月", "6mo": "6个月", "1y": "1年", "2y": "2年", "5y": "5年"}[x],
                                    key=f"single_{time.time()}"
                                )
                            
                            with col2:
                                try:
                                    price_info = chart_generator.get_price_change(display_ticker)
                                    if price_info and isinstance(price_info, dict):
                                        change_color = "normal" if price_info.get('change', 0) >= 0 else "inverse"
                                        st.metric(
                                            "当前价格",
                                            f"${price_info.get('current_price', 0):.2f}",
                                            delta=f"{price_info.get('change_pct', 0):+.2f}%",
                                            delta_color=change_color
                                        )
                                except:
                                    st.caption("价格获取失败")
                            
                            with col3:
                                try:
                                    if price_info and isinstance(price_info, dict):
                                        st.metric(
                                            "52周区间",
                                            f"${price_info.get('low_52w', 0):.1f}",
                                            delta=f"${price_info.get('high_52w', 0):.1f}"
                                        )
                                except:
                                    pass
                            
                            fig = chart_generator.create_chart(display_ticker, chart_period)
                            if fig:
                                st.plotly_chart(fig, use_container_width=True)
                            
                            # 策略生成
                            if display_ticker and len(display_tickers) <= 1:
                                st.markdown("---")
                                st.subheader("📋 可执行交易策略")
                                
                                rating_emoji = {'Buy': '🟢', 'Sell': '🔴', 'Hold': '🟡'}
                                st.info(f"{rating_emoji.get(rating, '🟡')} **当前评级: {rating}**")
                                
                                risk_tolerance = st.select_slider(
                                    "风险偏好",
                                    ["low", "medium", "high"],
                                    value="medium",
                                    format_func=lambda x: {"low": "🐌 保守", "medium": "🎯 平衡", "high": "🚀 激进"}[x],
                                    key=f"risk_{time.time()}"
                                )
                                
                                strategy_rating = rating if rating in ['Buy', 'Sell'] else 'Buy'
                                strategy = components['strategy_generator'].generate_strategy(
                                    ticker=display_ticker,
                                    rating=strategy_rating,
                                    analysis_result=agent_outputs,
                                    risk_tolerance=risk_tolerance
                                )
                                
                                if strategy:
                                    if rating == 'Hold':
                                        st.warning("💡 当前评级为Hold，策略仅供参考")
                                    
                                    st.success(f"✅ 已生成 {strategy['action']} 策略")
                                    
                                    col1, col2, col3, col4 = st.columns(4)
                                    with col1:
                                        st.metric("入场价", f"${strategy['entry_price']:.2f}")
                                    with col2:
                                        gain = ((strategy['target_price']/strategy['entry_price']-1)*100)
                                        st.metric("目标价", f"${strategy['target_price']:.2f}", delta=f"+{gain:.1f}%")
                                    with col3:
                                        loss = ((1-strategy['stop_loss']/strategy['entry_price'])*100)
                                        st.metric("止损价", f"${strategy['stop_loss']:.2f}", delta=f"-{loss:.1f}%")
                                    with col4:
                                        st.metric("建议仓位", strategy['position_size'])
                                    
                                    with st.expander("📊 策略详情", expanded=True):
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.write("**风险回报比**")
                                            st.info(f"1 : {strategy['risk_reward_ratio']}")
                                        with col2:
                                            st.write("**持仓周期**")
                                            st.info(strategy['time_horizon'])
                                    
                                    st.write("**📝 交易订单**")
                                    st.code(f"""股票: {strategy['ticker']}
操作: {strategy['action']}
入场价: ${strategy['entry_price']:.2f}
目标价: ${strategy['target_price']:.2f}
止损价: ${strategy['stop_loss']:.2f}
仓位: {strategy['position_size']}
理由: {strategy['reason']}""")
                                    
                                    if st.button("💾 保存", key=f"save_{time.time()}"):
                                        trade_id = st.session_state.paper_tracker.add_trade(strategy)
                                        st.success(f"✅ 已保存 #{trade_id}")
                
                except Exception as e:
                    message_placeholder.error(f"❌ 错误: {str(e)}")
                    with st.expander("详细错误"):
                        st.code(traceback.format_exc())
else:
    st.info("👈 请输入 DeepSeek API Key")
    
    st.markdown("### 💡 示例问题")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **基本面分析**
        - AAPL的PE怎么样？
        - 分析TSLA的财务状况
        
        **技术面分析**
        - NVDA的RSI是多少？
        - MSFT的技术指标如何？
        """)
    
    with col2:
        st.markdown("""
        **市场情绪**
        - META最近的新闻是什么？
        - 市场对GOOGL的看法
        
        **股票对比**
        - 比较AAPL和MSFT
        - NVDA vs AMD 哪个更好？
        """)

st.markdown("---")
st.markdown("<div style='text-align:center;color:#666;'><p>⚠️ 免责声明：仅供参考，不构成投资建议</p></div>", unsafe_allow_html=True)
