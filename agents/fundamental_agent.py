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
            # 从查询中提取股票代码
            ticker = self._extract_ticker(query)
            if not ticker:
                return "❌ 无法识别股票代码，请提供有效的股票代码（如 AAPL、TSLA）"
            
            # 获取股票数据
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 提取关键指标
            metrics = self._extract_metrics(info)
            valuation = self._analyze_valuation(metrics)
            
            # 使用 LLM 生成分析报告
            analysis_prompt = f"""
你是一位专业的股票基本面分析师。请基于以下数据对 {ticker} 进行基本面分析：

**公司信息：**
- 公司名称: {info.get('longName', ticker)}
- 行业: {info.get('sector', 'N/A')} - {info.get('industry', 'N/A')}
- 市值: ${metrics.get('market_cap', 0) / 1e9:.1f}B

**估值指标：**
- PE比率: {metrics.get('pe_ratio', 'N/A')}
- Forward PE: {metrics.get('forward_pe', 'N/A')}
- PEG比率: {metrics.get('peg_ratio', 'N/A')}
- 市净率: {metrics.get('price_to_book', 'N/A')}

**财务健康：**
- ROE: {metrics.get('roe', 0) * 100:.1f}% (如果有)
- 债务股本比: {metrics.get('debt_to_equity', 'N/A')}
- 利润率: {metrics.get('profit_margin', 0) * 100:.1f}% (如果有)

**成长性：**
- 营收增长率: {metrics.get('revenue_growth', 0) * 100:.1f}% (如果有)
- 盈利增长率: {metrics.get('earnings_growth', 0) * 100:.1f}% (如果有)

**股息：**
- 股息率: {metrics.get('dividend_yield', 0) * 100:.2f}% (如果有)

**估值评级：** {valuation}

请提供：
1. 综合评价（2-3句话）
2. 主要优势（2-3点）
3. 主要风险（2-3点）
4. 投资建议

请用清晰、专业的语言，避免过于技术化的术语。
            """
            
            response = self.llm.invoke(analysis_prompt)
            return response.content
            
        except Exception as e:
            return f"❌ 基本面分析失败: {str(e)}"
    
    def _extract_ticker(self, query: str) -> str:
        """从查询中提取股票代码"""
        import re
        # 常见股票列表
        common_stocks = {
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA',
            'AMD', 'NFLX', 'BABA', 'TSM', 'V', 'JPM', 'WMT', 'JNJ', 'PG'
        }
        
        query_upper = query.upper()
        
        # 先查找常见股票
        for stock in common_stocks:
            if stock in query_upper:
                return stock
        
        # 提取大写字母序列
        matches = re.findall(r'\b([A-Z]{2,5})\b', query_upper)
        common_words = {'THE', 'AND', 'PE', 'RSI', 'VS'}
        for match in matches:
            if match not in common_words:
                return match
        
        return None
    
    def _extract_metrics(self, info: dict) -> dict:
        """提取财务指标"""
        return {
            "market_cap": info.get('marketCap'),
            "pe_ratio": info.get('trailingPE'),
            "forward_pe": info.get('forwardPE'),
            "peg_ratio": info.get('pegRatio'),
            "price_to_book": info.get('priceToBook'),
            "debt_to_equity": info.get('debtToEquity'),
            "roe": info.get('returnOnEquity'),
            "revenue_growth": info.get('revenueGrowth'),
            "earnings_growth": info.get('earningsGrowth'),
            "profit_margin": info.get('profitMargins'),
            "dividend_yield": info.get('dividendYield'),
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
