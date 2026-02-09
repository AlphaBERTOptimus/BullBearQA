# -*- coding: utf-8 -*-
import sys
import io

# ============================================
# 强制设置 UTF-8 编码（必须在最开头）
# ============================================
if sys.version_info[0] >= 3:
    # 重新包装 stdout 和 stderr
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, 
            encoding='utf-8', 
            errors='replace',
            line_buffering=True
        )
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, 
            encoding='utf-8', 
            errors='replace',
            line_buffering=True
        )

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
            # 确保输入是正确的字符串
            if isinstance(question, bytes):
                question = question.decode('utf-8', errors='replace')
            
            result = self.agent_executor.invoke({
                "input": question,
                "chat_history": []
            })
            
            # 安全地获取输出
            output = result.get("output", "抱歉，无法生成回答。")
            
            # 确保输出是字符串并正确编码
            if isinstance(output, bytes):
                output = output.decode('utf-8', errors='replace')
            
            return str(output)
            
        except Exception as e:
            # 安全地处理异常
            return self._safe_error_message(e)
    
    def _safe_error_message(self, error) -> str:
        """安全地生成错误消息（避免编码问题）"""
        try:
            error_str = str(error)
        except:
            try:
                error_str = repr(error)
            except:
                error_str = "未知错误"
        
        # 检查错误类型
        error_lower = error_str.lower()
        
        if "rate limit" in error_lower:
            msg = "API 请求过于频繁，请稍后再试（建议等待 1 分钟）"
        elif "invalid" in error_lower or "not found" in error_lower:
            msg = f"遇到错误：{error_str}"
        else:
            msg = f"处理过程中出现错误：{error_str}"
        
        # 使用 ASCII 安全的前缀
        try:
            return f"⚠️ {msg}"
        except:
            # 如果连 emoji 都有问题，使用纯文本
            return f"[错误] {msg}"
