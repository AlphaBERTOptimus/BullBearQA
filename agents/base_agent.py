"""基础代理类"""
from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """所有代理的基类"""
    
    def __init__(self, llm, name: str = None):
        self.llm = llm
        self.name = name or self.__class__.__name__
    
    @abstractmethod
    def run(self, query: str) -> str:
        """
        执行分析并返回文本结果
        
        Args:
            query: 用户问题
            
        Returns:
            分析结果（文本格式）
        """
        pass
