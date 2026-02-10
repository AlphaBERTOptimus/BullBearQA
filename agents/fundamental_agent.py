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
            # 提取股票代码
            ticker = self._extract_ticker(query)
            if not ticker:
                return "无法识别股票代码，请提供有效的股票代码（如 AAPL、TSLA）"
            
            # 获取股票数据
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 提取关键指标
            metrics = self._extract_metrics(info)
            valuation = self._analyze_valuation(metrics)
            
            # 构建分析提示词
            analysis_prompt = self._build_analysis_prompt(ticker, info, metrics, valuation)
            
            # 调用LLM
            return self._safe_llm_invoke(analysis_prompt)
            
        except Exception as e:
            return f"基本面分析失败: {str(e)}"
    
    def _extract_ticker(self, query: str) -> str:
        """从查询中提取股票代码"""
        import re
        
        common_stocks = {
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA',
            'AMD', 'NFLX', 'BABA', 'TSM', 'V', 'JPM', 'WMT', 'JNJ', 'PG',
            'UNH', 'MA', 'HD', 'BAC', 'DIS', 'ADBE', 'CRM', 'CSCO', 'INTC'
        }
        
        query_upper = query.upper()
        
        # 优先匹配常见股票
        for stock in common_stocks:
            if stock in query_upper:
                return stock
        
        # 提取大写字母序列
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
            return "估值数据不足"
        
        if pe < 15:
            return "低估"
        elif pe > 25:
            return "高估"
        else:
            return "合理"
    
    def _build_analysis_prompt(self, ticker: str, info: dict, metrics: dict, valuation: str) -> str:
        """构建分析提示词"""
        market_cap_b = metrics.get('market_cap', 0) / 1e9
        roe_pct = metrics.get('roe', 0) * 100
        profit_margin_pct = metrics.get('profit_margin', 0) * 100
        revenue_growth_pct = metrics.get('revenue_growth', 0) * 100
        earnings_growth_pct = metrics.get('earnings_growth', 0) * 100
        dividend_yield_pct = metrics.get('dividend_yield', 0) * 100
        
        return f"""你是专业的股票基本面分析师。请对 {ticker} 进行简明扼要的分析。

公司信息:
- 名称: {info.get('longName', ticker)}
- 行业: {info.get('sector', 'N/A')} - {info.get('industry', 'N/A')}
- 市值: ${market_cap_b:.1f}B

估值指标:
- PE比率: {metrics.get('pe_ratio', 'N/A')}
- Forward PE: {metrics.get('forward_pe', 'N/A')}
- PEG比率: {metrics.get('peg_ratio', 'N/A')}
- 市净率: {metrics.get('price_to_book', 'N/A')}
- 估值评级: {valuation}

财务健康:
- ROE: {roe_pct:.1f}%
- 债务股本比: {metrics.get('debt_to_equity', 'N/A')}
- 利润率: {profit_margin_pct:.1f}%

成长性:
- 营收增长: {revenue_growth_pct:.1f}%
- 盈利增长: {earnings_growth_pct:.1f}%

股息率: {dividend_yield_pct:.2f}%

请提供简洁的分析(控制在200字以内):
1. 综合评价(2-3句)
2. 主要优势(2点)
3. 主要风险(2点)
4. 投资建议

用专业但易懂的中文回答。"""
