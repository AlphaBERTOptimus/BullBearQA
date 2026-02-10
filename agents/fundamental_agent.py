"""
基本面分析Agent
"""
from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from tools.stock_data_tool import StockDataTool


class FundamentalAgent(BaseAgent):
    """基本面分析师Agent"""
    
    def __init__(self, llm=None):
        super().__init__(name="Fundamental Analyst", llm=llm)
        self.stock_tool = StockDataTool()
    
    def analyze(self, ticker: str) -> Dict[str, Any]:
        """
        执行基本面分析
        
        Args:
            ticker: 股票代码
            
        Returns:
            分析结果字典
        """
        # 获取数据
        data = self.stock_tool.get_stock_data(ticker)
        
        if not data:
            return {
                'success': False,
                'error': f'无法获取 {ticker} 的数据',
                'ticker': ticker
            }
        
        # 分析估值
        valuation_analysis = self._analyze_valuation(data)
        
        # 分析盈利能力
        profitability_analysis = self._analyze_profitability(data)
        
        # 分析财务健康
        financial_health = self._analyze_financial_health(data)
        
        # 综合评分
        score = self._calculate_score(data)
        
        # 生成投资建议
        recommendation = self._generate_recommendation(score, data)
        
        return {
            'success': True,
            'ticker': ticker,
            'data': data,
            'valuation': valuation_analysis,
            'profitability': profitability_analysis,
            'financial_health': financial_health,
            'score': score,
            'recommendation': recommendation,
            'summary': self._generate_summary(data, score, recommendation)
        }
    
    def _analyze_valuation(self, data: dict) -> dict:
        """分析估值指标"""
        pe = data.get('pe_ratio', 'N/A')
        pb = data.get('pb_ratio', 'N/A')
        
        analysis = {
            'pe_ratio': pe,
            'pb_ratio': pb,
            'assessment': []
        }
        
        # PE分析
        if pe != 'N/A' and isinstance(pe, (int, float)):
            if pe < 15:
                analysis['assessment'].append('✅ PE较低，可能被低估')
            elif pe > 30:
                analysis['assessment'].append('⚠️ PE较高，估值偏贵')
            else:
                analysis['assessment'].append('📊 PE处于合理区间')
        else:
            analysis['assessment'].append('❓ PE数据不可用')
        
        # PB分析
        if pb != 'N/A' and isinstance(pb, (int, float)):
            if pb < 1:
                analysis['assessment'].append('✅ PB<1，可能存在价值投资机会')
            elif pb > 5:
                analysis['assessment'].append('⚠️ PB较高，需关注泡沫风险')
        
        return analysis
    
    def _analyze_profitability(self, data: dict) -> dict:
        """分析盈利能力"""
        roe = data.get('roe', 'N/A')
        profit_margin = data.get('profit_margin', 'N/A')
        
        analysis = {
            'roe': roe,
            'profit_margin': profit_margin,
            'assessment': []
        }
        
        # ROE分析
        if roe != 'N/A' and isinstance(roe, (int, float)):
            roe_pct = roe * 100 if roe < 1 else roe
            if roe_pct > 15:
                analysis['assessment'].append(f'✅ ROE优秀 ({roe_pct:.1f}%)')
            elif roe_pct > 10:
                analysis['assessment'].append(f'📊 ROE良好 ({roe_pct:.1f}%)')
            else:
                analysis['assessment'].append(f'⚠️ ROE偏低 ({roe_pct:.1f}%)')
        else:
            analysis['assessment'].append('❓ ROE数据不可用')
        
        return analysis
    
    def _analyze_financial_health(self, data: dict) -> dict:
        """分析财务健康度"""
        debt_equity = data.get('debt_to_equity', 'N/A')
        current_ratio = data.get('current_ratio', 'N/A')
        
        analysis = {
            'debt_to_equity': debt_equity,
            'current_ratio': current_ratio,
            'assessment': []
        }
        
        # 负债率分析
        if debt_equity != 'N/A' and isinstance(debt_equity, (int, float)):
            if debt_equity < 50:
                analysis['assessment'].append('✅ 负债水平健康')
            elif debt_equity > 100:
                analysis['assessment'].append('⚠️ 负债率偏高，需关注财务风险')
        
        return analysis
    
    def _calculate_score(self, data: dict) -> int:
        """计算综合评分 (0-100)"""
        score = 50  # 基础分
        
        # PE评分
        pe = data.get('pe_ratio', 'N/A')
        if pe != 'N/A' and isinstance(pe, (int, float)):
            if pe < 15:
                score += 10
            elif pe > 30:
                score -= 10
        
        # ROE评分
        roe = data.get('roe', 'N/A')
        if roe != 'N/A' and isinstance(roe, (int, float)):
            roe_pct = roe * 100 if roe < 1 else roe
            if roe_pct > 15:
                score += 15
            elif roe_pct < 5:
                score -= 10
        
        # 负债率评分
        debt_equity = data.get('debt_to_equity', 'N/A')
        if debt_equity != 'N/A' and isinstance(debt_equity, (int, float)):
            if debt_equity < 50:
                score += 10
            elif debt_equity > 100:
                score -= 15
        
        return max(0, min(100, score))
    
    def _generate_recommendation(self, score: int, data: dict) -> str:
        """生成投资建议"""
        if score >= 70:
            return "Buy"
        elif score >= 50:
            return "Hold"
        else:
            return "Sell"
    
    def _generate_summary(self, data: dict, score: int, recommendation: str) -> str:
        """生成分析摘要"""
        ticker = data.get('ticker', 'N/A')
        price = self.stock_tool.format_value(data.get('current_price'))
        
        summary = f"""
📊 {ticker} 基本面分析
━━━━━━━━━━━━━━━━━━━━━━━━
当前价格: {price}
综合评分: {score}/100
投资建议: {recommendation}
━━━━━━━━━━━━━━━━━━━━━━━━
        """.strip()
        
        return summary
