# -*- coding: utf-8 -*-
# BullBearQA - 简化版（不依赖 DeepSeek API）

import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

import streamlit as st
from agents import TechnicalAgent, FundamentalAgent, SentimentAgent, ComparisonAgent
import time
import traceback
import re

# ============================================
# 页面配置
# ============================================
st.set_page_config(
    page_title="BullBearQA - 智能股票分析",
    page_icon="📊",
    layout="wide"
)

# 自定义 CSS
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

# 页面标题
st.markdown("""
<div class="main-header">
    <h1>📊 BullBearQA</h1>
    <p>基于多Agent系统的智能股票分析平台（简化版）</p>
</div>
""", unsafe_allow_html=True)

# ============================================
# 侧边栏
# ============================================
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

# ============================================
# 初始化
# ============================================
if 'messages' not in st.session_state:
    st.session_state.messages = []

# 显示对话历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# ============================================
# 辅助函数：提取股票代码（改进版）
# ============================================
def extract_tickers(text: str) -> list:
    """从问题中提取股票代码"""
    # 常见股票代码列表（用于验证）
    common_stocks = {
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA', 
        'AMD', 'NFLX', 'BABA', 'TSM', 'V', 'JPM', 'WMT', 'JNJ', 'PG',
        'UNH', 'MA', 'HD', 'BAC', 'DIS', 'ADBE', 'CRM', 'CSCO', 'INTC',
        'PYPL', 'CMCSA', 'PEP', 'KO', 'T', 'VZ', 'NKE', 'MRK', 'ABT'
    }
    
    # 1. 先查找常见股票代码
    found_tickers = []
    text_upper = text.upper()
    for stock in common_stocks:
        if re.search(r'\b' + stock + r'\b', text_upper):
            found_tickers.append(stock)
    
    # 2. 如果没找到，再尝试提取大写字母组合
    if not found_tickers:
        matches = re.findall(r'\b([A-Z]{2,5})\b', text.upper())
        common_words = {'THE', 'AND', 'OR', 'NOT', 'FOR', 'WITH', 'VS', 'TO', 'OF', 'IN', 'ON', 'AT', 'BY', 'IS', 'ARE', 'WAS', 'WERE', 'PE', 'RSI', 'MA', 'MACD'}
        found_tickers = [t for t in matches if t not in common_words]
    
    return found_tickers

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
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 助手回复
    with st.chat_message("assistant"):
        try:
            start_time = time.time()
            
            # 1. 提取股票代码和检测问题类型
            tickers = extract_tickers(prompt)
            question_type = detect_question_type(prompt)
            
            # 调试信息
            st.caption(f"🔍 检测到股票: {tickers} | 问题类型: {question_type}")
            
            if not tickers:
                response = """
我可以帮你分析股票！请尝试以下问题：

- "分析 **AAPL** 的技术面"
- "**TSLA** 的基本面怎么样？"
- "**MSFT** 的市场情绪如何？"
- "对比 **AAPL**、**MSFT** 和 **GOOGL**"

💡 提示：请确保包含完整的股票代码（如 AAPL、TSLA 等）
                """
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            else:
                ticker = tickers[0]
                response = ""  # 初始化 response 变量
                
                # 2. 根据问题类型调用相应的 Agent
                if question_type == 'comparison' and len(tickers) >= 2:
                    with st.spinner("🔄 正在对比分析..."):
                        agent = ComparisonAgent()
                        result = agent.analyze(tickers)
                    
                    if result.get('status') == 'success':
                        response = f"""
### 🔄 股票对比分析

**{result['summary']}**

#### 📊 对比表格
"""
                        # 显示对比表格
                        if 'comparison_table' in result and not result['comparison_table'].empty:
                            st.dataframe(result['comparison_table'], use_container_width=True)
                            
                            # 排名信息
                            rankings = result.get('rankings', {})
                            response += "\n\n#### 🏆 排名\n"
                            
                            if 'PE比率排名' in rankings and rankings['PE比率排名']:
                                response += f"**PE比率排名** (从低到高): {', '.join(rankings['PE比率排名'])}\n\n"
                            
                            if 'ROE排名' in rankings and rankings['ROE排名']:
                                response += f"**ROE排名** (从高到低): {', '.join(rankings['ROE排名'])}\n"
                        else:
                            response += "\n⚠️ 暂无对比数据\n"
                        
                        st.markdown(response)
                    else:
                        response = f"❌ 对比失败: {result.get('error', '未知错误')}"
                        st.error(response)
                
                elif question_type == 'technical':
                    with st.spinner("📈 正在进行技术分析..."):
                        agent = TechnicalAgent()
                        result = agent.analyze(ticker)
                    
                    if result.get('status') == 'success':
                        indicators = result['indicators']
                        signals = result['signals']
                        
                        response = f"""
### 📈 {ticker} 技术分析

**{result['summary']}**

#### 关键指标
"""
                        # 显示指标
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("当前价格", f"${indicators['current_price']}")
                            st.metric("RSI", indicators.get('rsi', 'N/A'))
                        with col2:
                            st.metric("SMA 20", f"${indicators.get('sma_20', 'N/A')}" if indicators.get('sma_20') else 'N/A')
                            st.metric("SMA 50", f"${indicators.get('sma_50', 'N/A')}" if indicators.get('sma_50') else 'N/A')
                        with col3:
                            st.metric("趋势", signals.get('trend', 'N/A'))
                            st.metric("MACD", signals.get('macd', 'N/A'))
                        
                        response += f"""
- **RSI状态**: {signals.get('rsi', 'N/A')}
- **趋势方向**: {signals.get('trend', 'N/A')}
- **MACD信号**: {signals.get('macd', 'N/A')}
                        """
                        st.markdown(response)
                    else:
                        response = f"❌ 技术分析失败: {result.get('error', '未知错误')}"
                        st.error(response)
                
                elif question_type == 'fundamental':
                    with st.spinner("💼 正在进行基本面分析..."):
                        agent = FundamentalAgent()
                        result = agent.analyze(ticker)
                    
                    if result.get('status') == 'success':
                        metrics = result['metrics']
                        
                        response = f"""
### 💼 {ticker} 基本面分析

**公司**: {result['company_name']}  
**行业**: {result.get('sector', 'N/A')} - {result.get('industry', 'N/A')}

**{result['summary']}**

#### 关键财务指标
"""
                        # 显示指标
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
- **估值评级**: {result['valuation']}
- **市值**: ${metrics.get('market_cap', 0)/1e9:.1f}B
- **Beta**: {metrics.get('beta', 'N/A')}
                        """
                        st.markdown(response)
                    else:
                        response = f"❌ 基本面分析失败: {result.get('error', '未知错误')}"
                        st.error(response)
                
                elif question_type == 'sentiment':
                    with st.spinner("😊 正在分析市场情绪..."):
                        agent = SentimentAgent()
                        result = agent.analyze(ticker)
                    
                    if result.get('status') == 'success':
                        response = f"""
### 😊 {ticker} 市场情绪分析

**{result['summary']}**

#### 情绪指标
"""
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("情绪标签", result['sentiment_label'])
                            st.metric("情绪分数", result['sentiment_score'])
                        with col2:
                            st.metric("置信度", f"{result['confidence']*100:.0f}%")
                            st.metric("分析新闻数", result['news_count'])
                        
                        st.markdown(response)
                    else:
                        response = f"❌ 情绪分析失败: {result.get('error', '未知错误')}"
                        st.error(response)
                
                else:
                    # 通用分析：同时调用技术和基本面
                    with st.spinner("📊 正在进行综合分析..."):
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
                
                # 添加执行时间
                execution_time = time.time() - start_time
                time_info = f"⏱️ 分析耗时: {execution_time:.2f}秒"
                st.caption(time_info)
                
                # 保存到历史
                full_response = response + f"\n\n{time_info}"
                st.session_state.messages.append({"role": "assistant", "content": full_response})
        
        except Exception as e:
            error_message = f"❌ 分析过程中出现错误: {str(e)}"
            st.error(error_message)
            st.session_state.messages.append({"role": "assistant", "content": error_message})
            
            with st.expander("🔍 查看详细错误"):
                st.code(traceback.format_exc())

# 页脚
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>⚠️ 免责声明：本平台提供的分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。</p>
</div>
""", unsafe_allow_html=True)
