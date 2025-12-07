import streamlit as st
from langchain_openai import ChatOpenAI
from agents.fundamental_agent import FundamentalAgent
from agents.technical_agent import TechnicalAgent
from agents.sentiment_agent import SentimentAgent
from agents.comparison_agent import ComparisonAgent
from router.question_router import QuestionRouter
from judge.arena_judge import ArenaJudge
import time
import os

# =====================================================
# 页面配置
# =====================================================
st.set_page_config(
    page_title="BullBearQA - 智能股票分析",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# 自定义CSS样式
# =====================================================
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #1e3a8a, #059669);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================
# 侧边栏 - API Key 输入
# =====================================================
with st.sidebar:
    st.title("🔐 配置")
    
    api_key = st.text_input(
        "DeepSeek API Key",
        type="password",
        help="从 https://platform.deepseek.com 获取"
    )
    
    if api_key:
        os.environ["DEEPSEEK_API_KEY"] = api_key
        st.success("✅ API Key 已设置")
    else:
        st.warning("⚠️ 请输入 API Key")
    
    st.divider()
    
    st.subheader("📖 使用指南")
    st.markdown("""
    **BullBearQA** 支持以下类型的问题：
    
    🔹 **基本面分析**
    - "AAPL的PE怎么样？"
    - "分析TSLA的财务状况"
    
    🔹 **技术面分析**
    - "NVDA的RSI是多少？"
    - "MSFT的技术指标如何？"
    
    🔹 **市场情绪**
    - "最近GOOGL的新闻如何？"
    - "市场对META的看法"
    
    🔹 **股票对比**
    - "比较AAPL和MSFT"
    - "NVDA vs AMD 哪个更好？"
    """)
    
    st.divider()
    
    st.subheader("⚙️ 高级设置")
    
    show_routing = st.checkbox("显示路由信息", value=True)
    show_timing = st.checkbox("显示执行时间", value=True)
    
    st.divider()
    
    if st.button("🗑️ 清空对话历史"):
        st.session_state.messages = []
        st.rerun()

# =====================================================
# 主页面
# =====================================================
st.markdown('<div class="main-header">📊 BullBearQA</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">基于多Agent系统的智能股票分析平台 | Powered by DeepSeek & LangChain</div>',
    unsafe_allow_html=True
)

# =====================================================
# 初始化组件（使用缓存）
# =====================================================
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
    
    # 初始化所有 agents（传入 llm 参数）
    fundamental_agent = FundamentalAgent(llm)
    technical_agent = TechnicalAgent(llm)
    sentiment_agent = SentimentAgent(llm)
    comparison_agent = ComparisonAgent(llm)
    
    # 初始化 Arena Judge
    judge = ArenaJudge(llm)
    
    return router, fundamental_agent, technical_agent, sentiment_agent, comparison_agent, judge
# 获取组件
if api_key:
    router, fundamental_agent, technical_agent, sentiment_agent, comparison_agent, judge = get_components(api_key)
else:
    router = None

# ==========
