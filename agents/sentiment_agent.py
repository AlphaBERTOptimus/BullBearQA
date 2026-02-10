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
                return "❌ 无法识别股票代码"
            
            # 使用 LLM 生成模拟的市场情绪分析
            prompt = f"""
请对 {ticker} 的市场情绪进行分析。

提供：
1. 整体市场情绪评估
2. 近期新闻热点（可以合理推测）
3. 投资者情绪倾向
4. 社交媒体讨论热度

注意：这是模拟分析，请标注"模拟分析"。
            """
            
            response = self.llm.invoke(prompt)
            return response.content
            
        except Exception as e:
            return f"❌ 情绪分析失败: {str(e)}"
    
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
        for match in matches:
            if match not in {'THE', 'VS', 'PE'}:
                return match
        return None
