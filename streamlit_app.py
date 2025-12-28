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
    超级宽松版本 - 识别所有可能的买入表达
    
    Returns:
        'Buy', 'Sell', 或 'Hold'
    """
    # 提取"投资建议"部分（最重要）
    advice_section = ""
    if "💡 投资建议" in text or "投资建议" in text:
        start = text.find("投资建议")
        if start != -1:
            end = text.find("⚠️", start)
            if end == -1:
                end = text.find("✨", start)
            if end == -1:
                end = start + 300
            advice_section = text[start:end]
    
    # 超级完整的关键词列表
    buy_patterns = {
        # 明确买入（权重3）
        '建议买入': 3, '推荐买入': 3, '可以买入': 3, '值得买入': 3,
        '谨慎买入': 3, '分批买入': 3, '逢低买入': 3, '积极买入': 3,
        '适合买入': 3, '可考虑买入': 3,
        # 配置/布局相关（权重2）
        '建议配置': 2, '逢低配置': 2, '适合配置': 2, '可配置': 2,
        '分批配置': 2, '谨慎配置': 2,
        '建议布局': 2, '逢低布局': 2, '适合布局': 2, '可布局': 2,
        '分批布局': 2, '谨慎布局': 2,
        # 建仓相关（权重2）
        '建议建仓': 2, '逢低建仓': 2, '分批建仓': 2,
        # 一般买入（权重1）
        '买入': 1, '配置': 1, '布局': 1, '建仓': 1
    }
    
    sell_patterns = {
        '建议卖出': 3, '推荐卖出': 3, '应该卖出': 3,
        '建议减仓': 3, '止盈卖出': 2, '逢高卖出': 2,
        '卖出': 1, '减仓': 1
    }
    
    hold_patterns = {
        '暂不建议': 3, '不建议买': 3, '谨慎持有': 3,
        '观望': 2, '等待': 2, '持有': 1
    }
    
    def calculate_score(patterns, text_to_check):
        score = 0
        matched_keywords = []
        for pattern, weight in patterns.items():
            if pattern in text_to_check:
                score += weight
                matched_keywords.append(f"{pattern}({weight})")
        return score, matched_keywords
    
    # 在投资建议section中检查
    if advice_section:
        buy_score, buy_matches = calculate_score(buy_patterns, advice_section)
        sell_score, sell_matches = calculate_score(sell_patterns, advice_section)
        hold_score, hold_matches = calculate_score(hold_patterns, advice_section)
        
        # 超级宽松判断：只要buy_score > 0就考虑Buy
        if buy_score > 0 and buy_score >= hold_score * 0.5:
            return 'Buy'
        elif sell_score > buy_score and sell_score > hold_score:
            return 'Sell'
    
    # 全文检查
    buy_score_full, _ = calculate_score(buy_patterns, text)
    sell_score_full, _ = calculate_score(sell_patterns, text)
    hold_score_full, _ = calculate_score(hold_patterns, text)
    
    if buy_score_full > hold_score_full * 0.5 and buy_score_full > sell_score_full:
        return 'Buy'
    elif sell_score_full > buy_score_full and sell_score_full > hold_score_full:
        return 'Sell'
    
    return 'Hold'

# 侧边栏
with st.sidebar:
    st.markdown("## 🔐 配置")
    
    # API Key 输入
    api_key = st.text_input(
        "DeepSeek API Key",
        type="password",
        help="请输入你的 DeepSeek API Key",
        key="api_key_input"
    )
    
    if api_key:
        st.success("✅ API Key 已设置")
    
    st.markdown("---")
    
    # 使用指南
    st.markdown("## 📖 使用指南")
    st.markdown("""
BullBearQA 支持以下类型的问题：

**● 基本面分析**
- "AAPL的PE怎么样？"
- "分析TSLA的财务状况"

**● 技术面分析**
- "NVDA的RSI是多少？"
- "MSFT的技术指标如何？"

**● 市场情绪**
- "最近GOOGL的新闻如何？"
- "市场对META的看法"

**● 股票对比**
- "比较AAPL和MSFT"
- "NVDA vs AMD 哪个更好？"

**💡 想看交易策略？**
试试这些问题：
- "NVDA值得买入吗？"
- "应该买入苹果股票吗？"
- "微软现在可以买吗？"
    """)
    
    st.markdown("---")
    
    # 高级设置
    with st.expander("⚙️ 高级设置"):
        show_routing = st.checkbox("显示路由信息", value=False)
        show_timing = st.checkbox("显示执行时间", value=True)
    
    st.markdown("---")
    
    # 清除历史
    if st.button("🗑️ 清除对话历史"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 💡 投资评分")
    if 'last_score' in st.session_state:
        score_data = st.session_state.last_score
        score = score_data['score']
        rating = score_data['rating']
        
        # 显示评分
        st.metric("综合评分", f"{score}/100", rating)
        
        # 进度条
        st.progress(score / 100)
        
        # 详细分解
        breakdown = score_data.get('breakdown', {})
        if breakdown:
            st.markdown("**评分构成**")
            for key, value in breakdown.items():
                st.text(f"{key}: {value:+d}")
    
    # ========== Phase 1: 侧边栏添加模拟交易追踪 ==========
    st.markdown("---")
    st.sidebar.subheader("📊 模拟交易追踪")
    
    # 初始化tracker
    if 'paper_tracker' not in st.session_state:
        st.session_state.paper_tracker = PaperTradingTracker()
    
    tracker = st.session_state.paper_tracker
    
    # 显示统计
    stats = tracker.get_performance_stats()
    if stats:
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("胜率", f"{stats['win_rate']}%")
        with col2:
            st.metric("总交易", stats['total_trades'])
        
        with st.sidebar.expander("📈 详细统计"):
            st.write(f"✅ 盈利次数: {stats['wins']}")
            st.write(f"❌ 亏损次数: {stats['losses']}")
            st.write(f"💰 平均盈利: {stats['avg_win']}%")
            st.write(f"📉 平均亏损: {stats['avg_loss']}%")
            st.write(f"🎯 最大盈利: {stats['max_win']}%")
            st.write(f"⚠️ 最大亏损: {stats['max_loss']}%")
    else:
        st.sidebar.info("还没有交易记录\n试试问\"NVDA值得买吗？\"")
    
    # 查看所有交易
    if st.sidebar.checkbox("查看交易记录"):
        all_trades = tracker.get_all_trades()
        if all_trades:
            for trade in reversed(all_trades[-5:]):
                status_emoji = {
                    'OPEN': '🟡',
                    'CLOSED_WIN': '✅',
                    'CLOSED_LOSS': '❌',
                    'CLOSED_BREAK_EVEN': '⚪'
                }
                emoji = status_emoji.get(trade['status'], '❓')
                
                st.sidebar.text(f"{emoji} #{trade['id']} {trade['ticker']} {trade['action']}")
                if trade.get('pnl_pct'):
                    st.sidebar.text(f"   {trade['pnl_pct']:+.1f}%")
        else:
            st.sidebar.write("暂无记录")

# 初始化组件（带缓存）
@st.cache_resource
def get_components(api_key: str):
    """初始化所有组件（带缓存）"""
    # 初始化 LLM
    llm = ChatOpenAI(
        model="deepseek-chat",
        openai_api_key=api_key,
        openai_api_base="https://api.deepseek.com",
        temperature=0.7
    )
    
    # 初始化路由器
    router = QuestionRouter(llm)
    
    # 初始化所有 agents
    fundamental_agent = FundamentalAgent(llm)
    technical_agent = TechnicalAgent(llm)
    sentiment_agent = SentimentAgent(llm)
    comparison_agent = ComparisonAgent(llm)
    
    # 初始化 Arena Judge
    judge = ArenaJudge(llm)
    
    # ========== Phase 1: 新增组件初始化 ==========
    strategy_generator = StrategyGenerator()
    options_recommender = OptionsRecommender()
    # ==========================================
    
    return {
        'router': router,
        'fundamental_agent': fundamental_agent,
        'technical_agent': technical_agent,
        'sentiment_agent': sentiment_agent,
        'comparison_agent': comparison_agent,
        'judge': judge,
        'strategy_generator': strategy_generator,
        'options_recommender': options_recommender
    }

# 初始化对话历史
if 'messages' not in st.session_state:
    st.session_state.messages = []

# 显示对话历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 主对话界面
if api_key:
    # 获取组件
    try:
        components = get_components(api_key)
        
        # 提取组件
        router = components['router']
        fundamental_agent = components['fundamental_agent']
        technical_agent = components['technical_agent']
        sentiment_agent = components['sentiment_agent']
        comparison_agent = components['comparison_agent']
        judge = components['judge']
        tracker = st.session_state.paper_tracker
        
        # 用户输入
        if prompt := st.chat_input("请输入你的股票分析问题..."):
            # 显示用户消息
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # 处理问题
            with st.chat_message("assistant"):
                # 创建占位符
                message_placeholder = st.empty()
                
                # 开始计时
                start_time = time.time()
                
                try:
                    # 1. 路由
                    with st.spinner("🎯 正在分析问题..."):
                        routing_result = router.route(prompt)
                    
                    # 显示路由信息（如果启用）
                    if show_routing:
                        st.info(router.format_routing_info(routing_result))
                    
                    # 2. 选择并执行 agent
                    agent_type = routing_result['agent_type']import streamlit as st
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
    超级宽松版本 - 识别所有可能的买入表达
    
    Returns:
        'Buy', 'Sell', 或 'Hold'
    """
    # 提取"投资建议"部分（最重要）
    advice_section = ""
    if "💡 投资建议" in text or "投资建议" in text:
        start = text.find("投资建议")
        if start != -1:
            end = text.find("⚠️", start)
            if end == -1:
                end = text.find("✨", start)
            if end == -1:
                end = start + 300
            advice_section = text[start:end]
    
    # 超级完整的关键词列表
    buy_patterns = {
        # 明确买入（权重3）
        '建议买入': 3, '推荐买入': 3, '可以买入': 3, '值得买入': 3,
        '谨慎买入': 3, '分批买入': 3, '逢低买入': 3, '积极买入': 3,
        '适合买入': 3, '可考虑买入': 3,
        # 配置/布局相关（权重2）
        '建议配置': 2, '逢低配置': 2, '适合配置': 2, '可配置': 2,
        '分批配置': 2, '谨慎配置': 2,
        '建议布局': 2, '逢低布局': 2, '适合布局': 2, '可布局': 2,
        '分批布局': 2, '谨慎布局': 2,
        # 建仓相关（权重2）
        '建议建仓': 2, '逢低建仓': 2, '分批建仓': 2,
        # 一般买入（权重1）
        '买入': 1, '配置': 1, '布局': 1, '建仓': 1
    }
    
    sell_patterns = {
        '建议卖出': 3, '推荐卖出': 3, '应该卖出': 3,
        '建议减仓': 3, '止盈卖出': 2, '逢高卖出': 2,
        '卖出': 1, '减仓': 1
    }
    
    hold_patterns = {
        '暂不建议': 3, '不建议买': 3, '谨慎持有': 3,
        '观望': 2, '等待': 2, '持有': 1
    }
    
    def calculate_score(patterns, text_to_check):
        score = 0
        matched_keywords = []
        for pattern, weight in patterns.items():
            if pattern in text_to_check:
                score += weight
                matched_keywords.append(f"{pattern}({weight})")
        return score, matched_keywords
    
    # 在投资建议section中检查
    if advice_section:
        buy_score, buy_matches = calculate_score(buy_patterns, advice_section)
        sell_score, sell_matches = calculate_score(sell_patterns, advice_section)
        hold_score, hold_matches = calculate_score(hold_patterns, advice_section)
        
        # 超级宽松判断：只要buy_score > 0就考虑Buy
        if buy_score > 0 and buy_score >= hold_score * 0.5:
            return 'Buy'
        elif sell_score > buy_score and sell_score > hold_score:
            return 'Sell'
    
    # 全文检查
    buy_score_full, _ = calculate_score(buy_patterns, text)
    sell_score_full, _ = calculate_score(sell_patterns, text)
    hold_score_full, _ = calculate_score(hold_patterns, text)
    
    if buy_score_full > hold_score_full * 0.5 and buy_score_full > sell_score_full:
        return 'Buy'
    elif sell_score_full > buy_score_full and sell_score_full > hold_score_full:
        return 'Sell'
    
    return 'Hold'

# 侧边栏
with st.sidebar:
    st.markdown("## 🔐 配置")
    
    # API Key 输入
    api_key = st.text_input(
        "DeepSeek API Key",
        type="password",
        help="请输入你的 DeepSeek API Key",
        key="api_key_input"
    )
    
    if api_key:
        st.success("✅ API Key 已设置")
    
    st.markdown("---")
    
    # 使用指南
    st.markdown("## 📖 使用指南")
    st.markdown("""
BullBearQA 支持以下类型的问题：

**● 基本面分析**
- "AAPL的PE怎么样？"
- "分析TSLA的财务状况"

**● 技术面分析**
- "NVDA的RSI是多少？"
- "MSFT的技术指标如何？"

**● 市场情绪**
- "最近GOOGL的新闻如何？"
- "市场对META的看法"

**● 股票对比**
- "比较AAPL和MSFT"
- "NVDA vs AMD 哪个更好？"

**💡 想看交易策略？**
试试这些问题：
- "NVDA值得买入吗？"
- "应该买入苹果股票吗？"
- "微软现在可以买吗？"
    """)
    
    st.markdown("---")
    
    # 高级设置
    with st.expander("⚙️ 高级设置"):
        show_routing = st.checkbox("显示路由信息", value=False)
        show_timing = st.checkbox("显示执行时间", value=True)
    
    st.markdown("---")
    
    # 清除历史
    if st.button("🗑️ 清除对话历史"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 💡 投资评分")
    if 'last_score' in st.session_state:
        score_data = st.session_state.last_score
        score = score_data['score']
        rating = score_data['rating']
        
        # 显示评分
        st.metric("综合评分", f"{score}/100", rating)
        
        # 进度条
        st.progress(score / 100)
        
        # 详细分解
        breakdown = score_data.get('breakdown', {})
        if breakdown:
            st.markdown("**评分构成**")
            for key, value in breakdown.items():
                st.text(f"{key}: {value:+d}")
    
    # ========== Phase 1: 侧边栏添加模拟交易追踪 ==========
    st.markdown("---")
    st.sidebar.subheader("📊 模拟交易追踪")
    
    # 初始化tracker
    if 'paper_tracker' not in st.session_state:
        st.session_state.paper_tracker = PaperTradingTracker()
    
    tracker = st.session_state.paper_tracker
    
    # 显示统计
    stats = tracker.get_performance_stats()
    if stats:
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("胜率", f"{stats['win_rate']}%")
        with col2:
            st.metric("总交易", stats['total_trades'])
        
        with st.sidebar.expander("📈 详细统计"):
            st.write(f"✅ 盈利次数: {stats['wins']}")
            st.write(f"❌ 亏损次数: {stats['losses']}")
            st.write(f"💰 平均盈利: {stats['avg_win']}%")
            st.write(f"📉 平均亏损: {stats['avg_loss']}%")
            st.write(f"🎯 最大盈利: {stats['max_win']}%")
            st.write(f"⚠️ 最大亏损: {stats['max_loss']}%")
    else:
        st.sidebar.info("还没有交易记录\n试试问\"NVDA值得买吗？\"")
    
    # 查看所有交易
    if st.sidebar.checkbox("查看交易记录"):
        all_trades = tracker.get_all_trades()
        if all_trades:
            for trade in reversed(all_trades[-5:]):
                status_emoji = {
                    'OPEN': '🟡',
                    'CLOSED_WIN': '✅',
                    'CLOSED_LOSS': '❌',
                    'CLOSED_BREAK_EVEN': '⚪'
                }
                emoji = status_emoji.get(trade['status'], '❓')
                
                st.sidebar.text(f"{emoji} #{trade['id']} {trade['ticker']} {trade['action']}")
                if trade.get('pnl_pct'):
                    st.sidebar.text(f"   {trade['pnl_pct']:+.1f}%")
        else:
            st.sidebar.write("暂无记录")

# 初始化组件（带缓存）
@st.cache_resource
def get_components(api_key: str):
    """初始化所有组件（带缓存）"""
    # 初始化 LLM
    llm = ChatOpenAI(
        model="deepseek-chat",
        openai_api_key=api_key,
        openai_api_base="https://api.deepseek.com",
        temperature=0.7
    )
    
    # 初始化路由器
    router = QuestionRouter(llm)
    
    # 初始化所有 agents
    fundamental_agent = FundamentalAgent(llm)
    technical_agent = TechnicalAgent(llm)
    sentiment_agent = SentimentAgent(llm)
    comparison_agent = ComparisonAgent(llm)
    
    # 初始化 Arena Judge
    judge = ArenaJudge(llm)
    
    # ========== Phase 1: 新增组件初始化 ==========
    strategy_generator = StrategyGenerator()
    options_recommender = OptionsRecommender()
    # ==========================================
    
    return {
        'router': router,
        'fundamental_agent': fundamental_agent,
        'technical_agent': technical_agent,
        'sentiment_agent': sentiment_agent,
        'comparison_agent': comparison_agent,
        'judge': judge,
        'strategy_generator': strategy_generator,
        'options_recommender': options_recommender
    }

# 初始化对话历史
if 'messages' not in st.session_state:
    st.session_state.messages = []

# 显示对话历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 主对话界面
if api_key:
    # 获取组件
    try:
        components = get_components(api_key)
        
        # 提取组件
        router = components['router']
        fundamental_agent = components['fundamental_agent']
        technical_agent = components['technical_agent']
        sentiment_agent = components['sentiment_agent']
        comparison_agent = components['comparison_agent']
        judge = components['judge']
        tracker = st.session_state.paper_tracker
        
        # 用户输入
        if prompt := st.chat_input("请输入你的股票分析问题..."):
            # 显示用户消息
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # 处理问题
            with st.chat_message("assistant"):
                # 创建占位符
                message_placeholder = st.empty()
                
                # 开始计时
                start_time = time.time()
                
                try:
                    # 1. 路由
                    with st.spinner("🎯 正在分析问题..."):
                        routing_result = router.route(prompt)
                    
                    # 显示路由信息（如果启用）
                    if show_routing:
                        st.info(router.format_routing_info(routing_result))
                    
                    # 2. 选择并执行 agent
                    agent_type = routing_result['agent_type']
