from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

class BaseAgent:
    """Agent 基类"""
    
    def __init__(self, llm, tools, agent_type="base"):
        self.llm = llm
        self.tools = tools
        self.agent_type = agent_type
        
        # 设置系统提示词
        self.system_prompt = """你是一个专业的股票分析助手。

请遵循以下规则：
1. 必须使用提供的工具来获取实时数据
2. 基于工具返回的数据进行专业分析
3. 给出清晰的结论和建议
4. 如果数据不完整，请明确说明
5. 保持客观，避免过度承诺

请根据用户的问题，使用合适的工具获取数据并进行分析。"""
        
        # 创建 agent
        self.agent_executor = self._create_agent()
    
    def _create_agent(self):
        """创建 agent"""
        # 创建 prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # 创建 tool calling agent
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # 创建 executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=3,
            handle_parsing_errors=True
        )
        
        return agent_executor
    
    def run(self, question: str) -> str:
        """运行 agent"""
        try:
            result = self.agent_executor.invoke({
                "input": question,
                "chat_history": []
            })
            return result.get("output", "抱歉，无法生成回答。")
        except Exception as e:
            error_msg = str(e)
            if "rate limit" in error_msg.lower():
                return "⚠️ API 请求过于频繁，请稍后再试（建议等待 1 分钟）"
            elif "invalid" in error_msg.lower() or "not found" in error_msg.lower():
                return f"❌ 遇到错误：{error_msg}"
            else:
                return f"❌ 处理过程中出现错误：{error_msg}"
