"""基础代理类"""
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """所有代理的基类"""
    
    def __init__(self, llm, name: str = None):
        self.llm = llm
        self.name = name or self.__class__.__name__
    
    @abstractmethod
    def run(self, query: str) -> str:
        """执行分析并返回文本结果"""
        pass
    
    def _safe_llm_invoke(self, prompt: str) -> str:
        """安全调用LLM，使用英文提示词避免编码问题"""
        try:
            # 调用 LLM（使用英文提示词）
            response = self.llm.invoke(prompt)
            
            # 提取内容
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # 确保返回字符串
            return str(content)
            
        except Exception as e:
            return f"LLM call failed: {str(e)}"
