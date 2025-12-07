import streamlit as st
from langchain_openai import ChatOpenAI
from agents.fundamental_agent import FundamentalAgent
from agents.technical_agent import TechnicalAgent
from agents.sentiment_agent import SentimentAgent
from agents.comparison_agent import ComparisonAgent
from router.question_router import QuestionRouter
from judge.arena_judge import ArenaJudge
import time

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
    
    return router, fundamental_agent, technical_agent, sentiment_agent, comparison_agent, judge

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
        router, fundamental_agent, technical_agent, sentiment_agent, comparison_agent, judge = get_components(api_key)
        
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
                    if 'show_routing' in locals() and show_routing:
                        st.info(router.format_routing_info(routing_result))
                    
                    # 2. 选择并执行 agent
                    agent_type = routing_result['agent_type']
                    agent_outputs = {}
                    
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
                    
                    # 计算执行时间
                    execution_time = time.time() - start_time
                    
                    # 显示最终结果
                    response_text = final_response
                    if 'show_timing' in locals() and show_timing:
                        response_text += f"\n\n⏱️ 执行时间: {execution_time:.2f}秒"
                    
                    message_placeholder.markdown(response_text)
                    
                    # 保存到对话历史
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                    
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
        
        **股票对比**
        - 比较AAPL和MSFT
        - NVDA vs AMD 哪个更好？
        """)

# 页面底部信息
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>⚠️ 免责声明：本平台提供的分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。</p>
    <p>🔗 <a href='https://github.com/xiangxiang66/BullBearQA' target='_blank'>GitHub 项目地址</a> | Powered by DeepSeek & LangChain</p>
</div>
""", unsafe_allow_html=True)
