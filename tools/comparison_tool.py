import yfinance as yf
from langchain.tools import Tool
from typing import List, Dict

class ComparisonTool:
    """股票对比工具"""
    
    def compare_stocks(self, tickers_str: str) -> str:
        """对比多只股票"""
        try:
            tickers = [t.strip().upper() for t in tickers_str.split(',')]
            
            if len(tickers) < 2:
                return "❌ 请至少提供2只股票进行对比"
            if len(tickers) > 5:
                return "❌ 最多支持对比5只股票"
            
            stocks_data = []
            for ticker in tickers:
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    stocks_data.append({
                        'ticker': ticker,
                        'name': info.get('longName', ticker),
                        'price': info.get('currentPrice', 'N/A'),
                        'marketCap': info.get('marketCap', 0),
                        'pe': info.get('trailingPE', 'N/A'),
                        'roe': info.get('returnOnEquity', 'N/A'),
                        'debtToEquity': info.get('debtToEquity', 'N/A')
                    })
                except Exception:
                    stocks_data.append({'ticker': ticker, 'error': True})
            
            result = "📊 股票对比分析\n"
            result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            for data in stocks_data:
                if data.get('error'):
                    result += f"❌ {data['ticker']}: 无法获取数据\n\n"
                    continue
                
                result += f"📈 {data['name']} ({data['ticker']})\n"
                result += f"  • 价格: ${data['price']}\n"
                result += f"  • 市盈率: {data['pe']}\n"
                result += f"  • ROE: {data['roe']}\n"
                result += f"  • 负债率: {data['debtToEquity']}\n\n"
            
            return result
            
        except Exception as e:
            return f"❌ 对比分析时出错: {str(e)}"
    
    def as_tool(self) -> Tool:
        """转换为 LangChain Tool"""
        return Tool(
            name="compare_stocks",
            description="对比多只股票的关键指标。输入格式: 'AAPL,MSFT,GOOGL' (用逗号分隔，2-5只股票)。",
            func=self.compare_stocks
        )
