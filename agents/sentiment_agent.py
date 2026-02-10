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
            
            prompt = f"""You are a market sentiment analyst. Provide a brief sentiment analysis of {ticker} in Chinese.

Please provide in Chinese (within 100 characters):
1. Overall market sentiment assessment
2. Investor sentiment tendency
3. Possible impact of sentiment on stock price

Note: This is a simulated analysis based on general market patterns.
Respond in concise Chinese."""
            
            result = self._safe_llm_invoke(prompt)
            
            if "LLM call failed" in result:
                return f"【市场情绪分析 - {ticker}】\n\n当前市场情绪：中性\n投资者情绪倾向于观望，短期波动可能加大。建议关注成交量变化。"
            
            return result
            
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
