from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
import os

class BaseAgent:
    def __init__(self, name: str, role: str, tools: list, model_name: str = "deepseek-chat"):
        self.name = name
        self.role = role
        self.tools = tools

        # 使用 DeepSeek API（LangChain 支持 OpenAI 兼容接口）
        self.llm = ChatOpenAI(
            model=model_name,
            openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
            openai_api_base="https://api.deepseek.com/v1"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", f"你是一位专业的{role}。请严谨、专业地回答问题。"),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad")
        ])

        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        self.executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

    def run(self, input: str) -> dict:
        return self.executor.invoke({"input": input})
