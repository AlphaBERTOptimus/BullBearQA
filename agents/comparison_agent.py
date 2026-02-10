"""对比分析代理"""
from typing import Dict, Any, List
import yfinance as yf
import pandas as pd
from .base_agent import BaseAgent
from .technical_agent import TechnicalAgent
from .fundamental_agent import FundamentalAgent


class ComparisonAgent(BaseAgent):
    """对比分析代理 - 比较多个股票"""
    
    def __init__(self):
        super().__init__(
            name="ComparisonAgent",
            description="对比多个股票的技术面和基本面指标"
        )
        self.tech_agent = TechnicalAgent()
        self.fund_agent = FundamentalAgent()
    
    def analyze(self, tickers: List[str], **kwargs) -> Dict[str, Any]:
        """
        对比多个股票
        
        Args:
            tickers: 股票代码列表
            
        Returns:
            对比分析结果
        """
        try:
            if not tickers or len(tickers) < 2:
                return {
                    "error": "需要至少2个股票代码进行对比",
                    "agent": self.name,
                    "status": "failed"
                }
            
            # 收集所有股票数据
            comparison_data = {}
            for ticker in tickers:
                tech_data = self.tech_agent.analyze(ticker)
                fund_data = self.fund_agent.analyze(ticker)
                
                comparison_data[ticker] = {
                    "technical": tech_data,
                    "fundamental": fund_data
                }
            
            # 生成对比表
            comparison_table = self._create_comparison_table(comparison_data)
            
            # 生成排名
            rankings = self._generate_rankings(comparison_data)
            
            return {
                "tickers": tickers,
                "agent": self.name,
                "status": "success",
                "comparison_data": comparison_data,
                "comparison_table": comparison_table,
                "rankings": rankings,
                "summary": self._generate_summary(rankings)
            }
            
        except Exception as e:
            return self._handle_error(e, ", ".join(tickers))
    
    def _create_comparison_table(self, data: Dict[str, Any]) -> pd.DataFrame:
        """创建对比表格"""
        rows = []
        
        for ticker, info in data.items():
            tech = info.get('technical', {})
            fund = info.get('fundamental', {})
            
            row = {
                "股票代码": ticker,
                "公司名称": fund.get('company_name', 'N/A'),
                "当前价格": tech.get('indicators', {}).get('current_price'),
                "PE比率": fund.get('metrics', {}).get('pe_ratio'),
                "ROE": fund.get('metrics', {}).get('roe'),
                "RSI": tech.get('indicators', {}).get('rsi'),
                "趋势": tech.get('signals', {}).get('trend'),
                "估值": fund.get('valuation'),
            }
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def _generate_rankings(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """生成排名"""
        rankings = {}
        
        # 按PE比率排名（越低越好）
        pe_ranking = []
        for ticker, info in data.items():
            pe = info.get('fundamental', {}).get('metrics', {}).get('pe_ratio')
            if pe:
                pe_ranking.append((ticker, pe))
        
        pe_ranking.sort(key=lambda x: x[1])
        rankings['PE比率排名'] = [ticker for ticker, _ in pe_ranking]
        
        # 按ROE排名（越高越好）
        roe_ranking = []
        for ticker, info in data.items():
            roe = info.get('fundamental', {}).get('metrics', {}).get('roe')
            if roe:
                roe_ranking.append((ticker, roe))
        
        roe_ranking.sort(key=lambda x: x[1], reverse=True)
        rankings['ROE排名'] = [ticker for ticker, _ in roe_ranking]
        
        return rankings
    
    def _generate_summary(self, rankings: Dict[str, List[str]]) -> str:
        """生成对比摘要"""
        summary_parts = []
        
        if 'PE比率排名' in rankings and rankings['PE比率排名']:
            best_pe = rankings['PE比率排名'][0]
            summary_parts.append(f"最佳PE: {best_pe}")
        
        if 'ROE排名' in rankings and rankings['ROE排名']:
            best_roe = rankings['ROE排名'][0]
            summary_parts.append(f"最佳ROE: {best_roe}")
        
        return " | ".join(summary_parts) if summary_parts else "对比完成"
