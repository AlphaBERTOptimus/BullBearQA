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

# 这是extract_rating_from_text函数的完整替换版本
# 复制这个函数替换你的streamlit_app.py中的同名函数（第71-150行）

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
        if buy_score > 0 and buy_score >= hold_score * 0.5:  # 买入只需达到持有的一半
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
        # ========== Phase 1: 新增组件返回 ==========
        'strategy_generator': strategy_generator,
        'options_recommender': options_recommender
        # =========================================
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
                            agent_outputs[agent_type] = output
                    
                    # 3. 如果是对比，可能需要多个 agent
                    if agent_type == 'comparison' and len(routing_result.get('tickers', [])) >= 2:
                        # 对比分析已经在 comparison_agent 中完成
                        pass
                    
                    # 4. Arena Judge 综合
                    with st.spinner("🤔 正在生成综合分析..."):
                        final_response = judge.synthesize(prompt, agent_outputs)
                    
                    # 5. 创建投资评分
                    score_data = judge.create_investment_score(agent_outputs)
                    st.session_state.last_score = score_data
                    
                    # 🆕 使用增强的文本提取
                    rating = extract_rating_from_text(final_response)
                    
                    # 计算执行时间
                    execution_time = time.time() - start_time
                    
                    # 显示最终结果
                    response_text = final_response
                    if show_timing:
                        response_text += f"\n\n⏱️ 执行时间: {execution_time:.2f}秒"
                    
                    message_placeholder.markdown(response_text)
                    
                    # 保存到对话历史
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                    
                    # ========== Phase 1: 策略生成与期权推荐 ==========
                    
                    # 1. 策略生成功能（只对Buy和Sell）
                    if ticker and rating in ['Buy', 'Sell']:
                        st.markdown("---")
                        st.subheader("📋 可执行交易策略")
                        
                        # 用户选择风险偏好
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            risk_tolerance = st.select_slider(
                                "风险偏好",
                                options=["low", "medium", "high"],
                                value="medium",
                                format_func=lambda x: {"low": "🐌 保守", "medium": "🎯 平衡", "high": "🚀 激进"}[x],
                                key=f"risk_{ticker}_{time.time()}"
                            )
                        
                        # 生成策略
                        strategy = components['strategy_generator'].generate_strategy(
                            ticker=ticker,
                            rating=rating,
                            analysis_result=agent_outputs,
                            risk_tolerance=risk_tolerance
                        )
                        
                        if strategy:
                            # 显示策略
                            st.success(f"✅ 已生成 {strategy['action']} 策略")
                            
                            # 关键指标
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("入场价", f"${strategy['entry_price']:.2f}")
                            with col2:
                                gain = ((strategy['target_price']/strategy['entry_price']-1)*100)
                                st.metric("目标价", f"${strategy['target_price']:.2f}", 
                                         delta=f"+{gain:.1f}%", delta_color="normal")
                            with col3:
                                loss = ((1-strategy['stop_loss']/strategy['entry_price'])*100)
                                st.metric("止损价", f"${strategy['stop_loss']:.2f}", 
                                         delta=f"-{loss:.1f}%", delta_color="inverse")
                            with col4:
                                st.metric("建议仓位", strategy['position_size'])
                            
                            # 策略详情
                            with st.expander("📊 策略详情", expanded=True):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write("**风险回报比**")
                                    st.info(f"1 : {strategy['risk_reward_ratio']}")
                                    
                                    st.write("**持仓周期**")
                                    st.info(strategy['time_horizon'])
                                
                                with col2:
                                    st.write("**策略理由**")
                                    st.info(strategy['reason'])
                                    
                                    st.write("**信心度**")
                                    confidence = strategy['confidence']
                                    st.progress(confidence)
                                    st.caption(f"{confidence*100:.0f}%")
                            
                            # 可复制的交易订单
                            st.write("**📝 交易订单（可复制）**")
                            order_text = f"""
交易订单
━━━━━━━━━━━━━━━━━━
股票代码: {strategy['ticker']}
操作: {strategy['action']}

入场价: ${strategy['entry_price']:.2f}
目标价: ${strategy['target_price']:.2f} (+{strategy['expected_gain_pct']}%)
止损价: ${strategy['stop_loss']:.2f} (-{strategy['max_loss_pct']}%)

建议仓位: {strategy['position_size']}
风险回报比: 1:{strategy['risk_reward_ratio']}
持仓周期: {strategy['time_horizon']}

理由: {strategy['reason']}
                            """
                            st.code(order_text, language="text")
                            
                            # 保存到模拟盘
                            col1, col2 = st.columns([1, 3])
                            with col1:
                                if st.button("💾 保存到模拟盘", type="primary", key=f"save_{ticker}_{time.time()}"):
                                    trade_id = tracker.add_trade(strategy)
                                    st.success(f"✅ 已保存（编号 #{trade_id}）")
                                    st.balloons()
                            with col2:
                                st.caption("💡 保存后可在侧边栏查看交易记录")
                        else:
                            st.warning("⚠️ 策略生成失败，可能是获取价格数据失败，请稍后重试")
                    
                    elif ticker and rating == 'Hold':
                        # Hold评级的特殊提示
                        st.markdown("---")
                        st.info(f"""
💡 **当前建议: {rating} (持有/观望)**

由于当前评级为Hold，暂不生成买入/卖出策略。

**你可以**：
- 📊 查看下方的期权策略（增强收益）
- 🔔 添加到监控列表，等待更好时机
- 📈 继续跟踪基本面和技术面变化
                        """)
                    
                    # 2. 期权策略推荐（所有评级都显示）
                    if ticker:
                        st.markdown("---")
                        st.subheader("📊 期权策略推荐（进阶）")
                        
                        # 根据评级给出提示
                        if rating == 'Hold':
                            st.caption("💡 虽然当前建议持有，但如果你已持有股票，可以考虑备兑开仓等策略增强收益")
                        else:
                            st.caption("💡 如果你了解期权，可以考虑以下策略")
                        
                        # 用户选择波动率
                        volatility = st.select_slider(
                            "当前波动率",
                            options=["low", "medium", "high"],
                            value="medium",
                            format_func=lambda x: {"low": "📉 低波动", "medium": "📊 中等", "high": "📈 高波动"}[x],
                            key=f"vol_{ticker}_{time.time()}"
                        )
                        
                        # 推荐策略
                        options_strategies = components['options_recommender'].recommend_strategies(
                            ticker=ticker,
                            rating=rating,
                            volatility=volatility
                        )
                        
                        # 显示策略
                        for i, strategy_opt in enumerate(options_strategies, 1):
                            with st.expander(f"{strategy_opt['name']} - 复杂度: {strategy_opt['complexity']}", expanded=(i==1 and rating=='Hold')):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write("**基本信息**")
                                    st.write(f"适合场景: {strategy_opt['适合场景']}")
                                    st.write(f"风险: {strategy_opt['风险']}")
                                    st.write(f"收益: {strategy_opt['收益']}")
                                    st.write(f"成本: {strategy_opt['成本']}")
                                
                                with col2:
                                    st.write("**推荐度**")
                                    st.write(strategy_opt['推荐度'])
                                    
                                    if '⚠️ 风险提示' in strategy_opt:
                                        st.warning(strategy_opt['⚠️ 风险提示'])
                                    elif '💡 提示' in strategy_opt:
                                        st.info(strategy_opt['💡 提示'])
                                
                                st.write("**策略说明**")
                                st.info(strategy_opt['说明'])
                                
                                if strategy_opt.get('优点'):
                                    st.write("**优点**")
                                    for pro in strategy_opt['优点']:
                                        st.write(f"✅ {pro}")
                                
                                if strategy_opt.get('缺点'):
                                    st.write("**缺点**")
                                    for con in strategy_opt['缺点']:
                                        st.write(f"⚠️ {con}")
                    
                    # ========== Phase 1 功能结束 ==========
                    
                    # 触发侧边栏更新
                    st.rerun()
                    
                except Exception as e:
                    error_message = f"❌ 处理过程中出现错误: {str(e)}"
                    message_placeholder.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
    
    except Exception as e:
        st.error(f"❌ 初始化组件失败: {str(e)}")
        st.info("💡 请检查 API Key 是否正确，或稍后重试。")

else:
    # 未设置 API Key 的提示
    st.info("👈 请在左侧侧边栏输入你的 DeepSeek API Key 以开始使用")
    
    # 示例问题
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
        - 最近GOOGL的新闻如何？
        - 市场对META的看法
        
        **投资决策（生成策略）**
        - NVDA值得买入吗？
        - 苹果股票现在可以买吗？
        """)

# 页面底部信息
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>⚠️ 免责声明：本平台提供的分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。</p>
    <p>🔗 <a href='https://github.com/xiangxiang66/BullBearQA' target='_blank'>GitHub 项目地址</a> | Powered by DeepSeek & LangChain</p>
</div>
""", unsafe_allow_html=True)
