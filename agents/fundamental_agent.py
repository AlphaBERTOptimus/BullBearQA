"""
基本面分析Agent - 修复版本
"""
from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from tools.stock_data_tool import StockDataTool


class FundamentalAgent(BaseAgent):
    """基本面分析师Agent"""
    
    def __init__(self, llm=None):
        super().__init__(name="Fundamental Analyst", llm=llm)
        self.stock_tool = StockDataTool()
    
    def run(self, query: str) -> str:
        """
        执行基本面分析
        
        Args:
            query: 用户查询（如 "AAPL的PE怎么样？"）
            
        Returns:
            分析结果的markdown格式字符串
        """
        # 从查询中提取股票代码
        ticker = self._extract_ticker(query)
        
        if not ticker:
            return "❌ 无法识别股票代码，请提供有效的股票代码（如 AAPL, TSLA）"
        
        # 获取数据
        data = self.stock_tool.get_stock_data(ticker)
        
        if not data:
            return f"❌ 无法获取 {ticker} 的数据，请检查股票代码或稍后重试"
        
        # 生成分析报告
        return self._generate_report(data)
    
    def _extract_ticker(self, query: str) -> Optional[str]:
        """从查询中提取股票代码"""
        import re
        
        # 常见股票代码模式
        patterns = [
            r'\b([A-Z]{1,5})\b',  # 1-5个大写字母
            r'([A-Z]{1,5})的',     # 中文语境
            r'分析\s*([A-Z]{1,5})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query.upper())
            if match:
                return match.group(1)
        
        return None
    
    def _generate_report(self, data: dict) -> str:
        """生成分析报告"""
        ticker = data.get('ticker', 'N/A')
        name = data.get('name', ticker)
        
        # 基本信息
        report = f"""
## 📊 {name} ({ticker}) 基本面分析

### 💰 估值指标
"""
        
        # 估值分析
        pe = data.get('pe_ratio', 'N/A')
        pb = data.get('pb_ratio', 'N/A')
        
        if pe != 'N/A' and isinstance(pe, (int, float)):
            pe_assessment = self._assess_pe(pe)
            report += f"- **市盈率 (P/E)**: {pe:.2f} {pe_assessment}\n"
        else:
            report += f"- **市盈率 (P/E)**: 数据不可用\n"
        
        if pb != 'N/A' and isinstance(pb, (int, float)):
            pb_assessment = self._assess_pb(pb)
            report += f"- **市净率 (P/B)**: {pb:.2f} {pb_assessment}\n"
        else:
            report += f"- **市净率 (P/B)**: 数据不可用\n"
        
        # 盈利能力
        report += "\n### 💪 盈利能力\n"
        
        roe = data.get('roe', 'N/A')
        if roe != 'N/A' and isinstance(roe, (int, float)):
            roe_pct = roe * 100 if roe < 1 else roe
            roe_assessment = self._assess_roe(roe_pct)
            report += f"- **净资产收益率 (ROE)**: {roe_pct:.2f}% {roe_assessment}\n"
        else:
            report += f"- **净资产收益率 (ROE)**: 数据不可用\n"
        
        profit_margin = data.get('profit_margin', 'N/A')
        if profit_margin != 'N/A' and isinstance(profit_margin, (int, float)):
            margin_pct = profit_margin * 100 if profit_margin < 1 else profit_margin
            report += f"- **利润率**: {margin_pct:.2f}%\n"
        
        # 财务健康
        report += "\n### 🏥 财务健康\n"
        
        debt_equity = data.get('debt_to_equity', 'N/A')
        if debt_equity != 'N/A' and isinstance(debt_equity, (int, float)):
            debt_assessment = self._assess_debt(debt_equity)
            report += f"- **负债权益比**: {debt_equity:.2f} {debt_assessment}\n"
        else:
            report += f"- **负债权益比**: 数据不可用\n"
        
        current_ratio = data.get('current_ratio', 'N/A')
        if current_ratio != 'N/A' and isinstance(current_ratio, (int, float)):
            report += f"- **流动比率**: {current_ratio:.2f}\n"
        
        # 市场数据
        report += "\n### 📈 市场数据\n"
        
        current_price = data.get('current_price', 'N/A')
        if current_price != 'N/A':
            report += f"- **当前价格**: ${current_price:.2f}\n"
        
        market_cap = data.get('market_cap', 'N/A')
        if market_cap != 'N/A':
            report += f"- **市值**: {self.stock_tool.format_value(market_cap)}\n"
        
        # 综合评分
        score = self._calculate_score(data)
        report += f"\n### 🎯 综合评分\n"
        report += f"**{score}/100**\n\n"
        report += self._get_score_stars(score)
        
        return report
    
    def _assess_pe(self, pe: float) -> str:
        """评估PE比率"""
        if pe < 0:
            return "⚠️ 负值（公司亏损）"
        elif pe < 15:
            return "✅ 较低，可能被低估"
        elif pe < 25:
            return "📊 合理区间"
        elif pe < 35:
            return "⚠️ 偏高"
        else:
            return "🔴 很高，需警惕泡沫"
    
    def _assess_pb(self, pb: float) -> str:
        """评估PB比率"""
        if pb < 1:
            return "✅ 低于净资产，可能存在价值机会"
        elif pb < 3:
            return "📊 合理"
        elif pb < 5:
            return "⚠️ 偏高"
        else:
            return "🔴 很高"
    
    def _assess_roe(self, roe: float) -> str:
        """评估ROE"""
        if roe > 20:
            return "✅ 优秀"
        elif roe > 15:
            return "📊 良好"
        elif roe > 10:
            return "⚠️ 一般"
        else:
            return "🔴 偏低"
    
    def _assess_debt(self, debt_equity: float) -> str:
        """评估负债率"""
        if debt_equity < 0.5:
            return "✅ 健康"
        elif debt_equity < 1.0:
            return "📊 合理"
        elif debt_equity < 2.0:
            return "⚠️ 偏高"
        else:
            return "🔴 高风险"
    
    def _calculate_score(self, data: dict) -> int:
        """计算综合评分 (0-100)"""
        score = 50  # 基础分
        
        # PE评分 (±15分)
        pe = data.get('pe_ratio', 'N/A')
        if pe != 'N/A' and isinstance(pe, (int, float)) and pe > 0:
            if pe < 15:
                score += 15
            elif pe < 25:
                score += 5
            elif pe > 35:
                score -= 10
        
        # ROE评分 (±20分)
        roe = data.get('roe', 'N/A')
        if roe != 'N/A' and isinstance(roe, (int, float)):
            roe_pct = roe * 100 if roe < 1 else roe
            if roe_pct > 20:
                score += 20
            elif roe_pct > 15:
                score += 15
            elif roe_pct < 5:
                score -= 15
        
        # 负债率评分 (±15分)
        debt_equity = data.get('debt_to_equity', 'N/A')
        if debt_equity != 'N/A' and isinstance(debt_equity, (int, float)):
            if debt_equity < 0.5:
                score += 15
            elif debt_equity < 1.0:
                score += 5
            elif debt_equity > 2.0:
                score -= 15
        
        return max(0, min(100, score))
    
    def _get_score_stars(self, score: int) -> str:
        """将评分转换为星级"""
        if score >= 80:
            return "⭐⭐⭐⭐⭐ 优秀"
        elif score >= 70:
            return "⭐⭐⭐⭐ 良好"
        elif score >= 60:
            return "⭐⭐⭐ 中等"
        elif score >= 50:
            return "⭐⭐ 一般"
        else:
            return "⭐ 较差"
