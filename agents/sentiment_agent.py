"""情绪分析代理"""
from .base_agent import BaseAgent


class SentimentAgent(BaseAgent):
    """情绪分析代理"""
    
    def __init__(self, llm):
        super().__init__(llm, name="SentimentAgent")
    
    def run(self, query: str) -> str:
        """执行情绪分析"""
        try:
            ticker = self._extract_ticker(query)
            if not ticker:
                return "无法识别股票代码"
            
            prompt = f"""你是市场情绪分析专家。请对 {ticker} 的市场情绪进行简短分析。

提供(控制在100字以内):
1. 整体市场情绪评估
2. 投资者情绪倾向
3. 情绪对股价的可能影响

注意: 这是基于一般市场规律的模拟分析。
用简洁的中文回答。"""
            
            return self._safe_llm_invoke(prompt)
            
        except Exception as e:
            return f"情绪分析失败: {str(e)}"
    
    def _extract_ticker(self, query: str) -> str:
        """提取股票代码"""
        import re
        
        common_stocks = {
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'AMD'
        }
        
        query_upper = query.upper()
        
        for stock in common_stocks:
            if stock in query_upper:
                return stock
        
        matches = re.findall(r'\b([A-Z]{2,5})\b', query_upper)
        common_words = {'THE', 'VS', 'PE', 'NEWS', 'HOW'}
        
        for match in matches:
            if match not in common_words:
                return match
        
        return None
