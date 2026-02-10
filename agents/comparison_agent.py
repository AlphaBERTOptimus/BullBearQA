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
            
            prompt = self._build_english_prompt(comparison_data)
            
            result = self._safe_llm_invoke(prompt)
            
            if "LLM call failed" in result:
                return self._fallback_comparison(comparison_data)
            
            return result
            
        except Exception as e:
            return f"对比分析失败: {str(e)}"
    
    def _build_english_prompt(self, data: dict) -> str:
        """构建英文提示词"""
        lines = ["Please provide a concise comparison of the following stocks in Chinese:\n"]
        
        for ticker, info in data.items():
            lines.append(f"\n{ticker} ({info['name']})")
            
            pe = info['pe']
            lines.append(f"- P/E: {pe:.2f}" if pe else "- P/E: N/A")
            
            roe = info['roe']
            lines.append(f"- ROE: {roe*100:.1f}%" if roe else "- ROE: N/A")
            
            mcap = info['market_cap']
            lines.append(f"- Market Cap: ${mcap/1e9:.1f}B" if mcap else "- Market Cap: N/A")
        
        lines.append("\n\nPlease provide in Chinese (within 150 characters):")
        lines.append("1. Core advantages of each stock")
        lines.append("2. Valuation comparison")
        lines.append("3. Investment recommendation")
        lines.append("\nRespond in concise Chinese.")
        
        return "\n".join(lines)
    
    def _fallback_comparison(self, data: dict) -> str:
        """备用对比分析"""
        lines = ["【股票对比分析】\n"]
        
        for ticker, info in data.items():
            pe = info['pe']
            roe = info['roe']
            lines.append(f"\n{ticker}:")
            lines.append(f"- PE: {pe:.2f}" if pe else "- PE: N/A")
            lines.append(f"- ROE: {roe*100:.1f}%" if roe else "- ROE: N/A")
        
        lines.append("\n综合评价: 建议根据个人风险偏好和投资目标选择。")
        
        return "\n".join(lines)
    
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
        
        return list(dict.fromkeys(found))
