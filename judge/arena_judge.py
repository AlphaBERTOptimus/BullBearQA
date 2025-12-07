from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import os

class ArenaJudge:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
            openai_api_base="https://api.deepseek.com/v1"
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一位投资裁判（Arena Judge）。请综合以下各Agent的分析，给出清晰、专业的最终建议。"),
            ("human", "各Agent分析结果如下：\n{agent_results}\n\n请输出：1. 摘要 2. 最终建议（BUY/HOLD/SELL）3. 风险提示")
        ])
        self.chain = self.prompt | self.llm

    def judge(self, agent_results: str) -> str:
        return self.chain.invoke({"agent_results": agent_results}).content
