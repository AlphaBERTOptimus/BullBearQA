from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain_openai import ChatOpenAI
import os

class BaseAgent:
    def __init__(self, name: str, role: str, tools: list, model_name: str = "deepseek-chat"):
        self.name = name
        self.role = role
        self.tools = tools
        
        # 初始化 LLM
        self.llm = ChatOpenAI(
            model=model_name,
            openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
            openai_api_base="https://api.deepseek.com/v1",
            temperature=0
        )
        
        # 创建 Prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", f"""你是 {name}，角色是：{role}

重要规则：
1. 使用提供的工具获取数据
2. 数据分析要专业、客观
3. 给出明确的结论和建议
4. 如果数据不足，明确说明
5. 避免过度乐观或悲观

请基于工具返回的数据进行专业分析。"""),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # 创建 Agent
        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        
        # 创建 AgentExecutor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=3
        )
    
    def run(self, question: str) -> str:
        """执行分析"""
        try:
            result = self.agent_executor.invoke({"input": question})
            return result['output']
        except Exception as e:
            return f"❌ {self.name} 执行出错: {str(e)}"
