"""基本面分析代理"""
import yfinance as yf
from .base_agent import BaseAgent


class FundamentalAgent(BaseAgent):
    """基本面分析代理"""
    
    def __init__(self, llm):
        super().__init__(llm, name="FundamentalAgent")
    
    def run(self, query: str) -> str:
        """执行基本面分析"""
        try:
            ticker = self._extract_ticker(query)
            if not ticker:
                return "无法识别股票代码，请提供有效的股票代码（如 AAPL、TSLA）"
            
            stock = yf.Ticker(ticker)
            info = stock.info
            
            metrics = self._extract_metrics(info)
            valuation = self._analyze_valuation(metrics)
            
            # 使用英文提示词让LLM用中文回答（避免编码问题）
            analysis_prompt = self._build_english_prompt(ticker, info, metrics, valuation)
            
            result = self._safe_llm_invoke(analysis_prompt)
            
            # 如果LLM调用失败，使用备用方案
            if "LLM call failed" in result:
                return self._fallback_analysis(ticker, info, metrics, valuation)
            
            return result
            
        except Exception as e:
            return f"基本面分析失败: {str(e)}"
    
    def _build_english_prompt(self, ticker: str, info: dict, metrics: dict, valuation: str) -> str:
        """构建英文提示词（避免编码问题）"""
        market_cap_b = metrics.get('market_cap', 0) / 1e9
        roe_pct = metrics.get('roe', 0) * 100
        profit_margin_pct = metrics.get('profit_margin', 0) * 100
        revenue_growth_pct = metrics.get('revenue_growth', 0) * 100
        earnings_growth_pct = metrics.get('earnings_growth', 0) * 100
        dividend_yield_pct = metrics.get('dividend_yield', 0) * 100
        
        return f"""You are a professional stock fundamental analyst. Provide a concise analysis of {ticker} in Chinese.

Company Info:
- Name: {info.get('longName', ticker)}
- Sector: {info.get('sector', 'N/A')} - {info.get('industry', 'N/A')}
- Market Cap: ${market_cap_b:.1f}B

Valuation Metrics:
- P/E Ratio: {metrics.get('pe_ratio', 'N/A')}
- Forward P/E: {metrics.get('forward_pe', 'N/A')}
- PEG Ratio: {metrics.get('peg_ratio', 'N/A')}
- Valuation: {valuation}

Financial Health:
- ROE: {roe_pct:.1f}%
- Profit Margin: {profit_margin_pct:.1f}%

Growth:
- Revenue Growth: {revenue_growth_pct:.1f}%
- Earnings Growth: {earnings_growth_pct:.1f}%

Dividend Yield: {dividend_yield_pct:.2f}%

Please provide in Chinese (within 200 characters):
1. Overall assessment (2-3 sentences)
2. Key strengths (2 points)
3. Key risks (2 points)
4. Investment recommendation

Respond in professional but easy-to-understand Chinese."""
    
    def _fallback_analysis(self, ticker: str, info: dict, metrics: dict, valuation: str) -> str:
        """备用分析（当LLM调用失败时）"""
        pe = metrics.get('pe_ratio', 'N/A')
        roe = metrics.get('roe', 0) * 100
        market_cap_b = metrics.get('market_cap', 0) / 1e9
        
        return f"""【基本面分析 - {ticker}】

公司: {info.get('longName', ticker)}
行业: {info.get('sector', 'N/A')}

估值评级: {valuation}
- PE比率: {pe}
- ROE: {roe:.1f}%
- 市值: ${market_cap_b:.1f}B

综合评价: 该股票估值{valuation}，ROE为{roe:.1f}%，显示{'较好' if roe > 15 else '一般'}的盈利能力。

投资建议: 基于当前估值{'偏高' if valuation == 'Overvalued' else '合理' if valuation == 'Fair' else '偏低'}，建议{'谨慎' if valuation == 'Overvalued' else '关注' if valuation == 'Fair' else '重点关注'}。"""
    
    def _extract_ticker(self, query: str) -> str:
        """提取股票代码"""
        import re
        
        common_stocks = {
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA',
            'AMD', 'NFLX', 'BABA', 'TSM', 'V', 'JPM', 'WMT', 'JNJ', 'PG',
            'UNH', 'MA', 'HD', 'BAC', 'DIS', 'ADBE', 'CRM', 'CSCO', 'INTC'
        }
        
        query_upper = query.upper()
        
        for stock in common_stocks:
            if stock in query_upper:
                return stock
        
        matches = re.findall(r'\b([A-Z]{2,5})\b', query_upper)
        common_words = {'THE', 'AND', 'PE', 'RSI', 'VS', 'HOW', 'WHAT'}
        
        for match in matches:
            if match not in common_words:
                return match
        
        return None
    
    def _extract_metrics(self, info: dict) -> dict:
        """提取财务指标"""
        return {
            "market_cap": info.get('marketCap', 0),
            "pe_ratio": info.get('trailingPE'),
            "forward_pe": info.get('forwardPE'),
            "peg_ratio": info.get('pegRatio'),
            "price_to_book": info.get('priceToBook'),
            "debt_to_equity": info.get('debtToEquity'),
            "roe": info.get('returnOnEquity', 0),
            "revenue_growth": info.get('revenueGrowth', 0),
            "earnings_growth": info.get('earningsGrowth', 0),
            "profit_margin": info.get('profitMargins', 0),
            "dividend_yield": info.get('dividendYield', 0),
            "beta": info.get('beta'),
        }
    
    def _analyze_valuation(self, metrics: dict) -> str:
        """估值分析"""
        pe = metrics.get('pe_ratio')
        if not pe:
            return "Data Insufficient"
        
        if pe < 15:
            return "Undervalued"
        elif pe > 25:
            return "Overvalued"
        else:
            return "Fair"
