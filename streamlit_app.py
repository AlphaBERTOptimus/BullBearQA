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

# 自定义 CSS（保持你原来的样式）
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
    <p>基于多Agent系统的智能股票分析平台（简化版 - 无需 API Key）</p>
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
        st.markdown(message["content"])

# ============================================
# 辅助函数：提取股票代码
# ============================================
def extract_tickers(text: str) -> list:
    """从问题中提取股票代码"""
    # 查找大写字母组合（1-5个字符）
    matches = re.findall(r'\b([A-Z]{1,5})\b', text.upper())
    # 过滤掉常见英文单词
    common_words = {'THE', 'AND', 'OR', 'NOT', 'FOR', 'WITH', 'VS', 'TO', 'OF', 'IN', 'ON', 'AT', 'BY', 'IS', 'ARE', 'WAS', 'WERE'}
    tickers = [t for t in matches if t not in common_words]
    return tickers

def detect_question_type(text: str) -> str:
    """检测问题类型"""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['对比', '比较', 'vs', 'compare', '哪个更好']):
        return 'comparison'
    elif any(word in text_lower for word in ['技术', 'technical', 'rsi', 'macd', 'ma', '均线', '指标']):
        return 'technical'
    elif any(word in text_lower for word in ['基本面', 'fundamental', 'pe', 'roe', '财务', '估值', 'eps']):
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
            
            if not tickers:
                response = """
我可以帮你分析股票！请尝试以下问题：

- "分析 AAPL 的技术面"
- "TSLA 的基本面怎么样？"
- "MSFT 的市场情绪如何？"
- "对比 AAPL、MSFT 和 GOOGL"

请告诉我你想分析哪只股票？
                """
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            else:
                ticker = tickers[0]
                
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
                        st.dataframe(result['comparison_table'])
                        
                        # 排名信息
                        rankings = result['rankings']
                        response += f"""

#### 🏆 排名
**PE比率** (从低到高): {', '.join(rankings.get('PE比率排名', [])[:3])}  
**ROE** (从高到低): {', '.join(rankings.get('ROE排名', [])[:3])}
                        """
                        st.markdown(response)
                
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
                            st.metric("SMA 20", indicators.get('sma_20', 'N/A'))
                            st.metric("SMA 50", indicators.get('sma_50', 'N/A'))
                        with col3:
                            st.metric("趋势", signals.get('trend', 'N/A'))
                            st.metric("MACD", signals.get('macd', 'N/A'))
                        
                        response += f"""
- **RSI状态**: {signals.get('rsi', 'N/A')}
- **趋势方向**: {signals.get('trend', 'N/A')}
- **MACD信号**: {signals.get('macd', 'N/A')}
                        """
                        st.markdown(response)
                
                elif question_type == 'fundamental':
                    with st.spinner("💼 正在进行基本面分析..."):
                        agent = FundamentalAgent()
                        result = agent.analyze(ticker)
                    
                    if result.get('status') == 'success':
                        metrics = result['metrics']
                        
                        response = f"""
### 💼 {ticker} 基本面分析

**公司**: {result['company_name']}  
**行业**: {result.get('sector')} - {result.get('industry')}

**{result['summary']}**

#### 关键财务指标
"""
                        # 显示指标
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("PE 比率", f"{metrics.get('pe_ratio', 'N/A')}")
                            st.metric("ROE", f"{metrics.get('roe', 0)*100:.1f}%" if metrics.get('roe') else 'N/A')
                        with col2:
                            st.metric("估值", result['valuation'])
                            st.metric("股息率", f"{metrics.get('dividend_yield', 0)*100:.2f}%" if metrics.get('dividend_yield') else 'N/A')
                        
                        response += f"""
- **估值评级**: {result['valuation']}
- **市值**: ${metrics.get('market_cap', 0)/1e9:.1f}B (如果有)
- **Beta**: {metrics.get('beta', 'N/A')}
                        """
                        st.markdown(response)
                
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
                time_info = f"\n\n⏱️ 分析耗时: {execution_time:.2f}秒"
                st.caption(time_info)
                
                # 保存到历史
                full_response = response + time_info
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
