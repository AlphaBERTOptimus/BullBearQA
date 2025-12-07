from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import os
import re

class QuestionRouter:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
            openai_api_base="https://api.deepseek.com/v1"
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
你是一个智能路由器。请根据用户问题，判断需要调用哪些分析Agent。
可选Agent: fundamental（基本面）, technical（技术面）, sentiment（情绪面）

输出格式（JSON）：
{"agents": ["fundamental", "sentiment"], "tickers": ["AAPL", "TSLA"]}

仅输出JSON，不要解释。
"""),
            ("human", "{question}")
        ])
        self.chain = self.prompt | self.llm

    def route(self, question: str) -> dict:
        # 先提取 ticker（简单正则）
        tickers = re.findall(r'\b[A-Z]{2,5}\b', question)
        try:
            response = self.chain.invoke({"question": question})
            result = eval(response.content)  # 实际项目建议用 json.loads
            result["tickers"] = list(set(tickers))
            return result
        except:
            # 默认 fallback
            return {"agents": ["fundamental", "technical", "sentiment"], "tickers": tickers}
