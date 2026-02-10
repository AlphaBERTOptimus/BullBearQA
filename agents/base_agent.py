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
        """安全调用LLM，处理编码问题"""
        try:
            response = self.llm.invoke(prompt)
            # 确保返回的是字符串
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # 强制使用 UTF-8 编码
            if isinstance(content, bytes):
                return content.decode('utf-8', errors='ignore')
            return str(content)
        except Exception as e:
            return f"LLM调用失败: {str(e)}"
