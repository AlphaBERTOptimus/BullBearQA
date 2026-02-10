# -*- coding: utf-8 -*-
# BullBearQA - 简化版

import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

import streamlit as st
from agents import TechnicalAgent, FundamentalAgent, SentimentAgent, ComparisonAgent
import time
import traceback
import re

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
    <p>基于多Agent系统的智能股票分析平台</p>
</div>
""", unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.markdown("## 📖 使用指南")
    st.markdown("""
**● 基本面分析**
- "AAPL的PE怎么样？"
- "分析TSLA的财务状况"

**● 技术面分析**
- "NVDA的RSI是多少？"
- "MSFT的技术指标如何？"

**● 市场情绪**
- "最近GOOGL的新闻如何？"

**● 股票对比**
- "比较AAPL和MSFT"
- "NVDA vs AMD 哪个更好？"
    """)
    
    st.markdown("---")
    
    if st.button("🗑️ 清除对话历史"):
        st.session_state.messages = []
        st.rerun()

if 'messages' not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# ============================================
# 辅助函数
# ============================================
def extract_tickers(text: str) -> list:
    """从问题中提取股票代码（修复版）"""
    common_stocks = {
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA', 
        'AMD', 'NFLX', 'BABA', 'TSM', 'V', 'JPM', 'WMT', 'JNJ', 'PG',
        'UNH', 'MA', 'HD', 'BAC', 'DIS', 'ADBE', 'CRM', 'CSCO', 'INTC',
        'PYPL', 'CMCSA', 'PEP', 'KO', 'T', 'VZ', 'NKE', 'MRK', 'ABT'
    }
    
    found_tickers = []
    text_upper = text.upper()
    
    # 直接查找常见股票（不用正则边界）
    for stock in common_stocks:
        if stock in text_upper:
            found_tickers.append(stock)
    
    # 如果没找到，提取大写字母序列
    if not found_tickers:
        matches = re.findall(r'([A-Z]{2,5})', text_upper)
        common_words = {'THE', 'AND', 'OR', 'NOT', 'FOR', 'WITH', 'VS', 'TO', 'OF', 'IN', 'ON', 'AT', 'BY', 'IS', 'ARE', 'WAS', 'WERE', 'PE', 'RSI', 'MA', 'MACD', 'ROE'}
        found_tickers = [t for t in matches if t not in common_words]
    
    # 去重
    seen = set()
    result = []
    for ticker in found_tickers:
        if ticker not in seen:
            seen.add(ticker)
            result.append(ticker)
    
    return result

def detect_question_type(text: str) -> str:
    """检测问题类型"""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['对比', '比较', 'vs', 'compare', '哪个更好', '哪个好']):
        return 'comparison'
    elif any(word in text_lower for word in ['技术', 'technical', 'rsi', 'macd', 'ma', '均线', '指标', '技术面']):
        return 'technical'
    elif any(word in text_lower for word in ['基本面', 'fundamental', 'pe', 'roe', '财务', '估值', 'eps', '市盈率']):
        return 'fundamental'
    elif any(word in text_lower for word in ['情绪', 'sentiment', '新闻', 'news', '市场看法']):
        return 'sentiment'
    else:
        return 'general'

# ============================================
# 主对话界面
# ============================================
if prompt := st.chat_input("请输入你的股票分析问题..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        try:
            start_time = time.time()
            
            tickers = extract_tickers(prompt)
            question_type = detect_question_type(prompt)
            
            # 调试信息
            st.caption(f"🔍 检测: 股票={tickers}, 类型={question_type}")
            
            if not tickers:
                response = """
我可以帮你分析股票！请尝试：

- "**AAPL** 的PE怎么样？"
- "分析 **TSLA** 的财务状况"
- "**NVDA** 的RSI是多少？"
- "对比 **AAPL** 和 **MSFT**"

💡 请确保包含股票代码（如 AAPL、TSLA 等）
                """
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            else:
                ticker = tickers[0]
                response = ""
                
                # 对比分析
                if question_type == 'comparison' and len(tickers) >= 2:
                    with st.spinner("🔄 对比分析中..."):
                        agent = ComparisonAgent()
                        result = agent.analyze(tickers)
                    
                    if result.get('status') == 'success':
                        response = f"### 🔄 股票对比分析\n\n**{result['summary']}**\n\n"
                        
                        if 'comparison_table' in result and not result['comparison_table'].empty:
                            st.dataframe(result['comparison_table'], use_container_width=True)
                            
                            rankings = result.get('rankings', {})
                            response += "#### 🏆 排名\n"
                            
                            if rankings.get('PE比率排名'):
                                response += f"**PE比率** (低→高): {', '.join(rankings['PE比率排名'])}\n\n"
                            if rankings.get('ROE排名'):
                                response += f"**ROE** (高→低): {', '.join(rankings['ROE排名'])}\n"
                        
                        st.markdown(response)
                    else:
                        st.error(f"❌ {result.get('error')}")
                
                # 技术分析
                elif question_type == 'technical':
                    with st.spinner("📈 技术分析中..."):
                        agent = TechnicalAgent()
                        result = agent.analyze(ticker)
                    
                    if result.get('status') == 'success':
                        indicators = result['indicators']
                        signals = result['signals']
                        
                        response = f"### 📈 {ticker} 技术分析\n\n**{result['summary']}**\n\n"
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("当前价格", f"${indicators['current_price']}")
                            st.metric("RSI", indicators.get('rsi', 'N/A'))
                        with col2:
                            sma20 = indicators.get('sma_20')
                            st.metric("SMA 20", f"${sma20:.2f}" if sma20 else 'N/A')
                            sma50 = indicators.get('sma_50')
                            st.metric("SMA 50", f"${sma50:.2f}" if sma50 else 'N/A')
                        with col3:
                            st.metric("趋势", signals.get('trend', 'N/A'))
                            st.metric("MACD", signals.get('macd', 'N/A'))
                        
                        response += f"""
**信号解读：**
- RSI: {signals.get('rsi', 'N/A')}
- 趋势: {signals.get('trend', 'N/A')}
- MACD: {signals.get('macd', 'N/A')}
                        """
                        st.markdown(response)
                    else:
                        st.error(f"❌ {result.get('error')}")
                
                # 基本面分析
                elif question_type == 'fundamental':
                    with st.spinner("💼 基本面分析中..."):
                        agent = FundamentalAgent()
                        result = agent.analyze(ticker)
                    
                    if result.get('status') == 'success':
                        metrics = result['metrics']
                        
                        response = f"""### 💼 {ticker} 基本面分析

**公司**: {result['company_name']}  
**行业**: {result.get('sector', 'N/A')} - {result.get('industry', 'N/A')}

**{result['summary']}**

"""
                        col1, col2 = st.columns(2)
                        with col1:
                            pe = metrics.get('pe_ratio')
                            st.metric("PE 比率", f"{pe:.2f}" if pe else 'N/A')
                            roe = metrics.get('roe')
                            st.metric("ROE", f"{roe*100:.1f}%" if roe else 'N/A')
                        with col2:
                            st.metric("估值", result['valuation'])
                            div_yield = metrics.get('dividend_yield')
                            st.metric("股息率", f"{div_yield*100:.2f}%" if div_yield else 'N/A')
                        
                        response += f"""
**关键指标：**
- 估值: {result['valuation']}
- 市值: ${metrics.get('market_cap', 0)/1e9:.1f}B
- Beta: {metrics.get('beta', 'N/A')}
                        """
                        st.markdown(response)
                    else:
                        st.error(f"❌ {result.get('error')}")
                
                # 情绪分析
                elif question_type == 'sentiment':
                    with st.spinner("😊 情绪分析中..."):
                        agent = SentimentAgent()
                        result = agent.analyze(ticker)
                    
                    if result.get('status') == 'success':
                        response = f"### 😊 {ticker} 市场情绪\n\n**{result['summary']}**\n\n"
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("情绪", result['sentiment_label'])
                            st.metric("分数", result['sentiment_score'])
                        with col2:
                            st.metric("置信度", f"{result['confidence']*100:.0f}%")
                            st.metric("新闻数", result['news_count'])
                        
                        st.markdown(response)
                    else:
                        st.error(f"❌ {result.get('error')}")
                
                # 综合分析
                else:
                    with st.spinner("📊 综合分析中..."):
                        tech_agent = TechnicalAgent()
                        fund_agent = FundamentalAgent()
                        
                        tech_result = tech_agent.analyze(ticker)
                        fund_result = fund_agent.analyze(ticker)
                    
                    response = f"### 📊 {ticker} 综合分析\n\n"
                    
                    if tech_result.get('status') == 'success':
                        response += f"**技术面**: {tech_result['summary']}\n\n"
                    
                    if fund_result.get('status') == 'success':
                        response += f"**基本面**: {fund_result['summary']}\n\n"
                        response += f"**估值**: {fund_result['valuation']}\n"
                    
                    st.markdown(response)
                
                # 执行时间
                execution_time = time.time() - start_time
                st.caption(f"⏱️ 耗时: {execution_time:.2f}秒")
                
                full_response = response + f"\n\n⏱️ {execution_time:.2f}秒"
                st.session_state.messages.append({"role": "assistant", "content": full_response})
        
        except Exception as e:
            error_msg = f"❌ 错误: {str(e)}"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            
            with st.expander("🔍 详细错误"):
                st.code(traceback.format_exc())

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>⚠️ 免责声明：本平台提供的分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。</p>
</div>
""", unsafe_allow_html=True)
