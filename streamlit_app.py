import streamlit as st
from router.question_router import QuestionRouter
from agents.fundamental_agent import FundamentalAgent
from agents.technical_agent import TechnicalAgent
from agents.sentiment_agent import SentimentAgent
from judge.arena_judge import ArenaJudge

# ==============================
# 安全提示：API Key 由用户输入，不存储、不提交
# ==============================

st.set_page_config(page_title="BullBearQA", page_icon="🧠", layout="wide")
st.title("🧠 BullBearQA - AI金融问答系统")
st.caption("🔒 您的 API Key 仅在本次会话中使用，不会被保存或上传")

# ==============================
# 侧边栏：API Key 输入
# ==============================
with st.sidebar:
    st.header("🔑 API 配置")
    api_key = st.text_input(
        "请输入 DeepSeek API Key",
        type="password",
        placeholder="sk-...",
        help="从 https://platform.deepseek.com 获取"
    )
    if api_key:
        st.success("✅ Key 已输入")
    else:
        st.warning("⚠️ 请输入 API Key")

    st.markdown("---")
    st.info("""
    **说明**：
    - Key 仅用于本次会话
    - 不会保存到服务器或 GitHub
    - 刷新页面后需重新输入
    """)

# ==============================
# 主界面：问答
# ==============================
if not api_key:
    st.info("👈 请在左侧侧边栏输入 DeepSeek API Key 后开始提问")
    st.stop()

# 初始化组件（带 API Key）
@st.cache_resource
def get_components(_api_key: str):
    # 注入 API Key 到所有组件
    import os
    os.environ["DEEPSEEK_API_KEY"] = _api_key  # 用于后续 LLM 初始化

    router = QuestionRouter()
    judge = ArenaJudge()
    agents = {
        "fundamental": FundamentalAgent(),
        "technical": TechnicalAgent(),
        "sentiment": SentimentAgent()
    }
    return router, judge, agents

# 使用 _api_key 避免缓存依赖（但内容不变，可安全缓存）
router, judge, agents = get_components(api_key)

# 聊天历史
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("例如：MU的PE怎么样？或比较NVDA和AMD的基本面"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.spinner("AI正在思考..."):
        try:
            route_result = router.route(prompt)
            needed_agents = route_result.get("agents", ["fundamental"])
            agent_outputs = []

            for agent_name in needed_agents:
                if agent_name in agents:
                    res = agents[agent_name].run(prompt)
                    agent_outputs.append(f"【{agent_name}】: {res['output']}")

            full_input = "\n".join(agent_outputs)
            final_answer = judge.judge(full_input)

            st.session_state.messages.append({"role": "assistant", "content": final_answer})
            st.chat_message("assistant").write(final_answer)
        except Exception as e:
            st.error(f"❌ 分析出错: {str(e)}")
            st.chat_message("assistant").error(f"分析失败: {str(e)}")
