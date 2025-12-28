import streamlit as st
from langchain_openai import ChatOpenAI
from agents.fundamental_agent import FundamentalAgent
from agents.technical_agent import TechnicalAgent
from agents.sentiment_agent import SentimentAgent
from agents.comparison_agent import ComparisonAgent
from router.question_router import QuestionRouter
from judge.arena_judge import ArenaJudge
import time
import re

# ========== Phase 1: 新增导入 ==========
from trading.strategy_generator import StrategyGenerator
from trading.options_recommender import OptionsRecommender
from trading.paper_trading import PaperTradingTracker
# ========================================

# 页面配置
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
    .stButton>button {
        width: 100%;
        background-color: #1e3c72;
        color: white;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
</style>
""", unsafe_allow_html=True)

# 页面标题
st.markdown("""
<div class="main-header">
    <h1>📊 BullBearQA</h1>
    <p>基于多Agent系统的智能股票分析平台 | Powered by DeepSeek & LangChain</p>
</div>
""", unsafe_allow_html=True)

def extract_rating_from_text(text: str) -> str:
    """
    从Arena Judge的文本中智能提取评级
    超强版本 - 100%识别买入表达
    """
    text_lower = text.lower()
    
    buy_patterns = [
        r'建议.*?买入', r'推荐.*?买入', r'适合.*?买入', r'可以.*?买入',
        r'谨慎.*?买入', r'分批.*?买入', r'逢低.*?买入', r'积极.*?买入',
        r'值得.*?买入', r'买入', r'建议.*?配置', r'适合.*?配置',
        r'逢低.*?配置', r'分批.*?配置', r'配置', r'建议.*?布局',
        r'适合.*?布局', r'逢低.*?布局', r'分批.*?布局', r'布局', r'建仓',
    ]
    
    sell_patterns = [
        r'建议.*?卖出', r'推荐.*?卖出', r'应该.*?卖出', r'卖出',
        r'建议.*?减仓', r'减仓',
    ]
    
    hold_patterns = [
        r'暂不建议.*?买', r'不建议.*?买', r'谨慎.*?持有',
        r'建议.*?观望', r'观望', r'等待', r'持有',
    ]
    
    advice_section = ""
    if "投资建议" in text:
        start = text.find("投资建议")
        end = text.find("⚠️", start)
        if end == -1: end = text.find("✨", start)
        if end == -1: end = start + 500
        advice_section = text[start:end]
    
    def calc_score(patterns, text_to_check):
        score = 0
        for pattern in patterns:
            matches = re.findall(pattern, text_to_check)
            score += len(matches) * 3
        return score
    
    if advice_section:
        buy_score = calc_score(buy_patterns, advice_section)
        sell_score = calc_score(sell_patterns, advice_section)
        hold_score = calc_score(hold_patterns, advice_section)
        if buy_score > 0: return 'Buy'
        elif sell_score > buy_score and sell_score > hold_score: return 'Sell'
    
    buy_score_full = calc_score(buy_patterns, text_lower)
    sell_score_full = calc_score(sell_patterns, text_lower)
    hold_score_full = calc_score(hold_patterns, text_lower)
    
    if buy_score_full > 0 and buy_score_full > sell_score_full: return 'Buy'
    elif sell_score_full > buy_score_full and sell_score_full > hold_score_full: return 'Sell'
    
    return 'Hold'

# 侧边栏
with st.sidebar:
    st.markdown("## 🔐 配置")
    api_key = st.text_input("DeepSeek API Key", type="password", key="api_key_input")
    if api_key: st.success("✅ API Key 已设置")
    
    st.markdown("---")
    st.markdown("## 📖 使用指南")
    st.markdown("（内容省略...）")
    
    # 初始化tracker
    if 'paper_tracker' not in st.session_state:
        st.session_state.paper_tracker = PaperTradingTracker()
    
    tracker = st.session_state.paper_tracker
    stats = tracker.get_performance_stats()
    if stats:
        col1, col2 = st.sidebar.columns(2)
        with col1: st.metric("胜率", f"{stats['win_rate']}%")
        with col2: st.metric("总交易", stats['total_trades'])

# 组件初始化
@st.cache_resource
def get_components(api_key: str):
    llm = ChatOpenAI(model="deepseek-chat", openai_api_key=api_key, openai_api_base="https://api.deepseek.com", temperature=0.7)
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

if 'messages' not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if api_key:
    try:
        components = get_components(api_key)
        router = components['router']
        judge = components['judge']
        
        if prompt := st.chat_input("请输入你的股票分析问题..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                start_time = time.time()
                
                routing_result = router.route(prompt)
                agent_type = routing_result['agent_type']
                tickers = routing_result.get('tickers', [])
                ticker = tickers[0] if tickers else None
                
                agent_outputs = {}
                selected_agent = components.get(f'{agent_type}_agent')
                if selected_agent:
                    agent_outputs[agent_type] = selected_agent.run(prompt)
                
                final_response = judge.synthesize(prompt, agent_outputs)
                rating = extract_rating_from_text(final_response)
                
                execution_time = time.time() - start_time
                response_text = final_response + f"\n\n⏱️ 执行时间: {execution_time:.2f}秒"
                message_placeholder.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                
                if ticker and rating in ['Buy', 'Sell']:
                    st.markdown("---")
                    st.subheader("📋 可执行交易策略")
                    strategy = components['strategy_generator'].generate_strategy(ticker, rating, agent_outputs)
                    if strategy:
                        st.success(f"✅ 已生成 {strategy['action']} 策略")
                        st.json(strategy) # 简易展示策略内容内容数据

    except Exception as e:
        st.error(f"❌ 运行出错: {str(e)}")
else:
    st.info("👈 请在左侧侧边栏输入你的 DeepSeek API Key 以开始使用")

# 底部免责声明
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>⚠️ 免责声明：投资有风险，入市需谨慎。</div>", unsafe_allow_html=True)
