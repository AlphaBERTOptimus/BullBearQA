"""
Agent基类
"""
from typing import Any, Dict, Optional


class BaseAgent:
    """所有Agent的基类"""
    
    def __init__(self, name: str, llm=None):
        self.name = name
        self.llm = llm
    
    def analyze(self, *args, **kwargs) -> Dict[str, Any]:
        """
        分析方法，子类需实现
        """
        raise NotImplementedError("Subclass must implement analyze()")
    
    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"
