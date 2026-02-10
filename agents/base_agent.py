"""
Agent基类 - 修复Tool导入问题
"""
from typing import Any, Dict, Optional
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class BaseAgent:
    """所有Agent的基类"""
    
    def __init__(self, name: str, llm=None):
        self.name = name
        self.llm = llm
    
    def run(self, query: str) -> str:
        """
        执行分析（子类需实现）
        
        Args:
            query: 用户查询
            
        Returns:
            分析结果字符串
        """
        raise NotImplementedError("Subclass must implement run()")
    
    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"
