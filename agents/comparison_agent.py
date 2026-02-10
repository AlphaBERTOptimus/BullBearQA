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
                return "需要至少2个股票代码进行对比"
            
            # 获取数据
            comparison_data = {}
            for ticker in tickers:
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    comparison_data[ticker] = {
                        'name': info.get('longName', ticker),
                        'pe': info.get('trailingPE'),
                        'roe': info.get('returnOnEquity', 0),
                        'market_cap': info.get('marketCap', 0),
                        'beta': info.get('beta'),
                        'div_yield': info.get('dividendYield', 0)
                    }
                except:
                    comparison_data[ticker] = {
                        'name': ticker,
                        'pe': None,
                        'roe': 0,
                        'market_cap': 0,
                        'beta': None,
                        'div_yield': 0
                    }
            
            # 构建提示词
            prompt = self._build_comparison_prompt(comparison_data)
            
            # 调用LLM
            return self._safe_llm_invoke(prompt)
            
        except Exception as e:
            return f"对比分析失败: {str(e)}"
    
    def _extract_tickers(self, query: str) -> list:
        """提取多个股票代码"""
        import re
        
        common_stocks = {
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'AMD',
            'NFLX', 'TSM', 'V', 'JPM'
        }
        
        found = []
        query_upper = query.upper()
        
        for stock in common_stocks:
            if stock in query_upper:
                found.append(stock)
        
        if not found:
            matches = re.findall(r'\b([A-Z]{2,5})\b', query_upper)
            common_words = {'VS', 'THE', 'PE', 'AND', 'OR'}
            for match in matches:
                if match not in common_words:
                    found.append(match)
        
        return list(dict.fromkeys(found))  # 去重
    
    def _build_comparison_prompt(self, data: dict) -> str:
        """构建对比提示词"""
        lines = ["请对以下股票进行简明对比:\n"]
        
        for ticker, info in data.items():
            lines.append(f"\n{ticker} ({info['name']})")
            
            pe = info['pe']
            lines.append(f"- PE: {pe:.2f}" if pe else "- PE: N/A")
            
            roe = info['roe']
            lines.append(f"- ROE: {roe*100:.1f}%" if roe else "- ROE: N/A")
            
            mcap = info['market_cap']
            lines.append(f"- 市值: ${mcap/1e9:.1f}B" if mcap else "- 市值: N/A")
        
        lines.append("\n\n请提供简洁对比(控制在150字以内):")
        lines.append("1. 各股核心优势")
        lines.append("2. 估值对比")
        lines.append("3. 投资建议")
        lines.append("\n用简洁的中文回答。")
        
        return "\n".join(lines)
