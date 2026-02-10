"""对比分析代理"""
import yfinance as yf
from .base_agent import BaseAgent


class ComparisonAgent(BaseAgent):
    """对比分析代理"""
    
    def __init__(self, llm):
        super().__init__(llm, name="ComparisonAgent")
    
    def run(self, query: str) -> str:
        """执行对比分析"""
        try:
            tickers = self._extract_tickers(query)
            if len(tickers) < 2:
                return "❌ 需要至少2个股票代码进行对比"
            
            # 获取数据
            comparison_data = {}
            for ticker in tickers:
                stock = yf.Ticker(ticker)
                info = stock.info
                comparison_data[ticker] = {
                    'name': info.get('longName', ticker),
                    'pe': info.get('trailingPE'),
                    'roe': info.get('returnOnEquity'),
                    'market_cap': info.get('marketCap'),
                    'beta': info.get('beta'),
                    'div_yield': info.get('dividendYield')
                }
            
            # 使用 LLM 生成对比分析
            prompt = f"""
请对以下股票进行对比分析：

{self._format_comparison_data(comparison_data)}

提供：
1. 各股票的核心优势
2. 估值对比分析
3. 风险对比
4. 投资建议（哪个更适合什么类型的投资者）

保持客观、专业。
            """
            
            response = self.llm.invoke(prompt)
            return response.content
            
        except Exception as e:
            return f"❌ 对比分析失败: {str(e)}"
    
    def _extract_tickers(self, query: str) -> list:
        """提取多个股票代码"""
        import re
        common_stocks = {
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'AMD'
        }
        
        found = []
        query_upper = query.upper()
        
        for stock in common_stocks:
            if stock in query_upper:
                found.append(stock)
        
        if not found:
            matches = re.findall(r'\b([A-Z]{2,5})\b', query_upper)
            for match in matches:
                if match not in {'VS', 'THE', 'PE'}:
                    found.append(match)
        
        return list(dict.fromkeys(found))  # 去重
    
    def _format_comparison_data(self, data: dict) -> str:
        """格式化对比数据"""
        lines = []
        for ticker, info in data.items():
            lines.append(f"\n**{ticker} ({info['name']})**")
            lines.append(f"- PE比率: {info['pe']:.2f}" if info['pe'] else "- PE比率: N/A")
            lines.append(f"- ROE: {info['roe']*100:.1f}%" if info['roe'] else "- ROE: N/A")
            lines.append(f"- 市值: ${info['market_cap']/1e9:.1f}B" if info['market_cap'] else "- 市值: N/A")
        return "\n".join(lines)
