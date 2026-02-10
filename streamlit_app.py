import streamlit as st
from agents import TechnicalAgent, FundamentalAgent, SentimentAgent, ComparisonAgent

st.title("🐂🐻 BullBearQA - 股票分析系统")

# 侧边栏选择功能
analysis_type = st.sidebar.selectbox(
    "选择分析类型",
    ["技术分析", "基本面分析", "情绪分析", "对比分析"]
)

if analysis_type == "技术分析":
    st.header("📈 技术分析")
    ticker = st.text_input("输入股票代码", value="AAPL")
    
    if st.button("开始分析"):
        with st.spinner("分析中..."):
            tech_agent = TechnicalAgent()
            result = tech_agent.analyze(ticker)
            
            if result.get('status') == 'success':
                st.success(result['summary'])
                
                # 显示指标
                st.subheader("技术指标")
                col1, col2, col3 = st.columns(3)
                
                indicators = result['indicators']
                with col1:
                    st.metric("当前价格", f"${indicators.get('current_price', 'N/A')}")
                    st.metric("RSI", indicators.get('rsi', 'N/A'))
                
                with col2:
                    st.metric("SMA 20", indicators.get('sma_20', 'N/A'))
                    st.metric("SMA 50", indicators.get('sma_50', 'N/A'))
                
                with col3:
                    st.metric("MACD", indicators.get('macd', 'N/A'))
                    st.metric("趋势", result['signals'].get('trend', 'N/A'))
            else:
                st.error(f"分析失败: {result.get('error')}")

elif analysis_type == "基本面分析":
    st.header("💼 基本面分析")
    ticker = st.text_input("输入股票代码", value="AAPL")
    
    if st.button("开始分析"):
        with st.spinner("分析中..."):
            fund_agent = FundamentalAgent()
            result = fund_agent.analyze(ticker)
            
            if result.get('status') == 'success':
                st.success(result['summary'])
                
                st.subheader(f"{result['company_name']}")
                st.write(f"**行业**: {result.get('sector')} - {result.get('industry')}")
                st.write(f"**估值**: {result['valuation']}")
                
                # 显示财务指标
                metrics = result['metrics']
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("PE 比率", f"{metrics.get('pe_ratio', 'N/A')}")
                    st.metric("ROE", f"{metrics.get('roe', 0)*100:.1f}%" if metrics.get('roe') else 'N/A')
                
                with col2:
                    st.metric("PEG 比率", metrics.get('peg_ratio', 'N/A'))
                    st.metric("股息率", f"{metrics.get('dividend_yield', 0)*100:.2f}%" if metrics.get('dividend_yield') else 'N/A')
            else:
                st.error(f"分析失败: {result.get('error')}")

elif analysis_type == "情绪分析":
    st.header("😊 情绪分析")
    ticker = st.text_input("输入股票代码", value="AAPL")
    
    if st.button("开始分析"):
        with st.spinner("分析中..."):
            sent_agent = SentimentAgent()
            result = sent_agent.analyze(ticker)
            
            if result.get('status') == 'success':
                st.success(result['summary'])
                
                # 显示情绪指标
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("情绪标签", result['sentiment_label'])
                    st.metric("情绪分数", result['sentiment_score'])
                
                with col2:
                    st.metric("置信度", f"{result['confidence']*100:.0f}%")
                    st.metric("新闻数量", result['news_count'])
            else:
                st.error(f"分析失败: {result.get('error')}")

elif analysis_type == "对比分析":
    st.header("🔄 对比分析")
    
    # 输入多个股票代码
    tickers_input = st.text_input(
        "输入股票代码（用逗号分隔）", 
        value="AAPL,MSFT,GOOGL"
    )
    
    if st.button("开始对比"):
        tickers = [t.strip().upper() for t in tickers_input.split(',')]
        
        if len(tickers) < 2:
            st.warning("请至少输入2个股票代码")
        else:
            with st.spinner("对比分析中..."):
                comp_agent = ComparisonAgent()
                result = comp_agent.analyze(tickers)
                
                if result.get('status') == 'success':
                    st.success(result['summary'])
                    
                    # 显示对比表格
                    st.subheader("📊 对比表格")
                    st.dataframe(result['comparison_table'])
                    
                    # 显示排名
                    st.subheader("🏆 排名")
                    rankings = result['rankings']
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**PE比率排名**（从低到高）")
                        for i, ticker in enumerate(rankings.get('PE比率排名', []), 1):
                            st.write(f"{i}. {ticker}")
                    
                    with col2:
                        st.write("**ROE排名**（从高到低）")
                        for i, ticker in enumerate(rankings.get('ROE排名', []), 1):
                            st.write(f"{i}. {ticker}")
                else:
                    st.error(f"对比失败: {result.get('error')}")
