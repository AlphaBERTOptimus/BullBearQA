import yfinance as yf
from langchain.tools import Tool
from typing import Optional, Dict
import time

class StockDataTool:
    """获取股票基本面数据的工具"""
    
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 300  # 5分钟缓存
    
    def _get_cached_or_fetch(self, ticker: str) -> Optional[Dict]:
        """缓存机制"""
        current_time = time.time()
        cache_key = ticker.upper()
        
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if current_time - timestamp < self._cache_ttl:
                return data
        
        # 获取新数据
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            self._cache[cache_key] = (info, current_time)
            return info
        except Exception as e:
            return None
    
    def _format_large_number(self, num: Optional[float]) -> str:
        """格式化大数字"""
        if num is None:
            return "N/A"
        if num >= 1e12:
            return f"{num/1e12:.2f}T"
        elif num >= 1e9:
            return f"{num/1e9:.2f}B"
        elif num >= 1e6:
            return f"{num/1e6:.2f}M"
        else:
            return f"{num:,.2f}"
    
    def get_stock_data(self, ticker: str) -> str:
        """获取股票数据"""
        try:
            info = self._get_cached_or_fetch(ticker)
            
            if not info:
                return f"❌ 股票代码 '{ticker}' 不存在或数据不可用"
            
            # 基本信息
            name = info.get('longName', ticker)
            sector = info.get('sector', 'N/A')
            industry = info.get('industry', 'N/A')
            
            # 价格信息
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
            market_cap = self._format_large_number(info.get('marketCap'))
            
            # 估值指标
            pe_ratio = info.get('trailingPE', 'N/A')
            forward_pe = info.get('forwardPE', 'N/A')
            pb_ratio = info.get('priceToBook', 'N/A')
            
            # 盈利指标
            revenue = self._format_large_number(info.get('totalRevenue'))
            net_income = self._format_large_number(info.get('netIncomeToCommon'))
            profit_margin = info.get('profitMargins', 'N/A')
            if profit_margin != 'N/A':
                profit_margin = f"{profit_margin*100:.2f}%"
            
            roe = info.get('returnOnEquity', 'N/A')
            if roe != 'N/A':
                roe = f"{roe*100:.2f}%"
            
            # 财务健康
            debt_to_equity = info.get('debtToEquity', 'N/A')
            current_ratio = info.get('currentRatio', 'N/A')
            
            # 股息信息
            dividend_yield = info.get('dividendYield', 'N/A')
            if dividend_yield != 'N/A':
                dividend_yield = f"{dividend_yield*100:.2f}%"
            
            # 智能分析
            analysis = []
            if isinstance(pe_ratio, (int, float)) and pe_ratio < 15:
                analysis.append("✅ 市盈率较低，可能被低估")
            if isinstance(roe, str) and roe != 'N/A':
                roe_val = float(roe.strip('%'))
                if roe_val > 15:
                    analysis.append("✅ ROE优秀，盈利能力强")
            if isinstance(debt_to_equity, (int, float)) and debt_to_equity > 100:
                analysis.append("⚠️ 负债率较高，需关注财务风险")
            
            result = f"""
📊 {name} ({ticker})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💼 行业信息
  • 行业板块: {sector}
  • 细分行业: {industry}

💰 价格与市值
  • 当前价格: ${current_price}
  • 市值: {market_cap}

📈 估值指标
  • 市盈率(P/E): {pe_ratio}
  • 远期市盈率: {forward_pe}
  • 市净率(P/B): {pb_ratio}

💵 盈利能力
  • 营业收入: {revenue}
  • 净利润: {net_income}
  • 利润率: {profit_margin}
  • 净资产收益率(ROE): {roe}

🏦 财务健康
  • 负债权益比: {debt_to_equity}
  • 流动比率: {current_ratio}

💎 股息信息
  • 股息率: {dividend_yield}
"""
            
            if analysis:
                result += "\n🔍 智能分析\n"
                for item in analysis:
                    result += f"  {item}\n"
            
            return result
            
        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "429" in error_msg:
                return "⚠️ API 请求过于频繁，请稍后再试（建议等待 1 分钟）"
            elif "invalid" in error_msg or "not found" in error_msg:
                return f"❌ 股票代码 '{ticker}' 不存在或数据不可用"
            else:
                return f"❌ 获取数据时出错: {str(e)}"
    
    def as_tool(self) -> Tool:
        """转换为 LangChain Tool"""
        return Tool(
            name="stock_data",
            description="获取股票的基本面数据，包括价格、市值、估值指标、盈利能力和财务健康状况。输入应该是股票代码，例如 'AAPL' 或 'TSLA'。",
            func=self.get_stock_data
        )
