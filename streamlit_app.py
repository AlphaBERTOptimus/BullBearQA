import streamlit as st
from langchain_openai import ChatOpenAI
from agents.fundamental_agent import FundamentalAgent
from agents.technical_agent import TechnicalAgent
from agents.sentiment_agent import SentimentAgent
from agents.comparison_agent import ComparisonAgent
from router.question_router import QuestionRouter
from judge.arena_judge import ArenaJudge
import time

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

**💡 自动生成交易策略**
- 任何股票查询都会生成可执行策略
- 支持保存到模拟盘追踪盈亏
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
        st.sidebar.info("还没有交易记录\n试试生成策略并保存！")
    
    # 查看所有交易
    if st.sidebar.checkbox("查看交易记录"):
        all_trades = tracker.get_all_trades()
        if all_trades:
            for trade in reversed(all_trades[-5:]):  # 显示最近5条
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
    # ========================================

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
                    agent_outputs = {}
                    
                    # 提取ticker信息（用于后续策略生成）
                    tickers = routing_result.get('tickers', [])
                    ticker = tickers[0] if tickers else None
                    
                    # 根据类型选择 agent
                    agents_map = {
                        'fundamental': fundamental_agent,
                        'technical': technical_agent,
                        'sentiment': sentiment_agent,
                        'comparison': comparison_agent
                    }
                    
                    selected_agent = agents_map.get(agent_type)
                    
                    if selected_agent:
                        # 显示进度
                        progress_text = f"📊 正在执行{agent_type}分析..."
                        with st.spinner(progress_text):
                            output = selected_agent.run(prompt)
                            agent_out
