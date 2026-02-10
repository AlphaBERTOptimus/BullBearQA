"""
股票对比分析Agent
"""
from typing import List, Optional
from agents.base_agent import BaseAgent
from tools.stock_data_tool import StockDataTool


class ComparisonAgent(BaseAgent):
    """股票对比分析师Agent"""
    
    def __init__(self, llm=None):
        super().__init__(name="Comparison Analyst", llm=llm)
        self.stock_tool = StockDataTool()
    
    def run(self, query: str) -> str:
        """
        执行对比分析
        
        Args:
            query: 用户查询
            
        Returns:
            对比分析结果
        """
        tickers = self._extract_tickers(query)
        
        if len(tickers) < 2:
            return "❌ 需要至少两个股票代码进行对比"
        
        # 获取所有股票数据
        stocks_data = {}
        for ticker in tickers:
            data = self.stock_tool.get_stock_data(ticker)
            if data:
                stocks_data[ticker] = data
        
        if len(stocks_data) < 2:
            return "❌ 无法获取足够的股票数据进行对比"
        
        return self._generate_comparison_report(stocks_data)
    
    def _extract_tickers(self, query: str) -> List[str]:
        """从查询中提取多个股票代码"""
        import re
        
        # 匹配所有大写字母组合
        matches = re.findall(r'\b([A-Z]{1,5})\b', query.upper())
        
        # 过滤常见非股票代码词
        exclude = ['VS', 'OR', 'AND', 'THE', 'IS', 'ARE', 'COMPARE']
        tickers = [m for m in matches if m not in exclude]
        
        return list(set(tickers))[:5]  # 最多5个
    
    def _generate_comparison_report(self, stocks_data: dict) -> str:
        """生成对比报告"""
        tickers = list(stocks_data.keys())
        
        report = f"""
## ⚖️ 股票对比分析

对比股票: {', '.join(tickers)}

### 📊 估值对比

| 指标 | {' | '.join(tickers)} |
|------|{'|'.join(['----' for _ in tickers])}|
"""
        
        # PE对比
        pe_row = "| P/E比率 |"
        for ticker in tickers:
            pe = stocks_data[ticker].get('pe_ratio', 'N/A')
            pe_str = f"{pe:.2f}" if pe != 'N/A' and isinstance(pe, (int, float)) else 'N/A'
            pe_row += f" {pe_str} |"
        report += pe_row + "\n"
        
        # ROE对比
        roe_row = "| ROE |"
        for ticker in tickers:
            roe = stocks_data[ticker].get('roe', 'N/A')
            if roe != 'N/A' and isinstance(roe, (int, float)):
                roe_pct = roe * 100 if roe < 1 else roe
                roe_str = f"{roe_pct:.2f}%"
            else:
                roe_str = 'N/A'
            roe_row += f" {roe_str} |"
        report += roe_row + "\n"
        
        # 市值对比
        mcap_row = "| 市值 |"
        for ticker in tickers:
            mcap = stocks_data[ticker].get('market_cap', 'N/A')
            mcap_str = self.stock_tool.format_value(mcap) if mcap != 'N/A' else 'N/A'
            mcap_row += f" {mcap_str} |"
        report += mcap_row + "\n"
        
        # 综合评分
        report += "\n### 🎯 综合评分\n\n"
        
        scores = {}
        for ticker in tickers:
            score = self._calculate_score(stocks_data[ticker])
            scores[ticker] = score
            stars = self._get_stars(score)
            report += f"- **{ticker}**: {score}/100 {stars}\n"
        
        # 推荐
        report += "\n### 💡 投资建议\n\n"
        best_ticker = max(scores, key=scores.get)
        report += f"综合评分最高: **{best_ticker}** ({scores[best_ticker]}/100)\n"
        
        return report
    
    def _calculate_score(self, data: dict) -> int:
        """计算评分"""
        score = 50
        
        pe = data.get('pe_ratio', 'N/A')
        if pe != 'N/A' and isinstance(pe, (int, float)) and pe > 0:
            if pe < 15:
                score += 15
            elif pe > 35:
                score -= 10
        
        roe = data.get('roe', 'N/A')
        if roe != 'N/A' and isinstance(roe, (int, float)):
            roe_pct = roe * 100 if roe < 1 else roe
            if roe_pct > 20:
                score += 20
            elif roe_pct < 5:
                score -= 15
        
        return max(0, min(100, score))
    
    def _get_stars(self, score: int) -> str:
        """转换为星级"""
        if score >= 80:
            return "⭐⭐⭐⭐⭐"
        elif score >= 70:
            return "⭐⭐⭐⭐"
        elif score >= 60:
            return "⭐⭐⭐"
        elif score >= 50:
            return "⭐⭐"
        else:
            return "⭐"
