"""基本面分析代理"""
from typing import Dict, Any
import yfinance as yf


class FundamentalAgent:
    """基本面分析代理"""
    
    def __init__(self):
        self.name = "FundamentalAgent"
        self.description = "执行基本面分析，包括财务指标、估值等"
    
    def analyze(self, ticker: str) -> Dict[str, Any]:
        """
        执行基本面分析
        
        Args:
            ticker: 股票代码
            
        Returns:
            基本面分析结果
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 提取关键财务指标
            metrics = self._extract_metrics(info)
            
            # 估值分析
            valuation = self._analyze_valuation(metrics)
            
            return {
                "ticker": ticker,
                "company_name": info.get('longName', ticker),
                "metrics": metrics,
                "valuation": valuation,
                "summary": self._generate_summary(metrics, valuation)
            }
            
        except Exception as e:
            return {"error": f"基本面分析失败: {str(e)}"}
    
    def _extract_metrics(self, info: Dict) -> Dict[str, Any]:
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
        }
    
    def _analyze_valuation(self, metrics: Dict[str, Any]) -> str:
        """估值分析"""
        pe = metrics.get('pe_ratio')
        peg = metrics.get('peg_ratio')
        
        if not pe:
            return "估值数据不足"
        
        if pe < 15:
            valuation = "低估"
        elif pe > 25:
            valuation = "高估"
        else:
            valuation = "合理"
        
        if peg and peg < 1:
            valuation += " (相对增长率低估)"
        
        return valuation
    
    def _generate_summary(self, metrics: Dict[str, Any], valuation: str) -> str:
        """生成分析摘要"""
        summary_parts = [f"估值: {valuation}"]
        
        if metrics['pe_ratio']:
            summary_parts.append(f"PE: {metrics['pe_ratio']:.2f}")
        
        if metrics['roe']:
            summary_parts.append(f"ROE: {metrics['roe']*100:.1f}%")
        
        if metrics['dividend_yield']:
            summary_parts.append(f"股息率: {metrics['dividend_yield']*100:.2f}%")
        
        return " | ".join(summary_parts)
