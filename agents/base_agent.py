"""基础代理类"""
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """所有代理的基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def analyze(self, ticker: str, **kwargs) -> Dict[str, Any]:
        """
        执行分析
        
        Args:
            ticker: 股票代码
            **kwargs: 其他参数
            
        Returns:
            分析结果字典
        """
        pass
    
    def _handle_error(self, error: Exception, ticker: str) -> Dict[str, Any]:
        """统一的错误处理"""
        return {
            "ticker": ticker,
            "error": str(error),
            "agent": self.name,
            "status": "failed"
        }
