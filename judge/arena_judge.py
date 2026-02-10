"""
Arena Judge - 综合分析裁判
"""
from typing import Dict, Any


class ArenaJudge:
    """Arena Judge - 整合多个Agent的输出"""
    
    def __init__(self, llm=None):
        self.llm = llm
    
    def synthesize(self, question: str, agent_outputs: Dict[str, str]) -> str:
        """
        综合多个Agent的分析结果
        
        Args:
            question: 原始问题
            agent_outputs: 各Agent的输出
            
        Returns:
            综合分析结果
        """
        if not agent_outputs:
            return "❌ 没有收到任何分析结果"
        
        # 简单拼接各Agent的输出
        result = "# 🏆 Arena Judge 综合分析\n\n"
        
        for agent_type, output in agent_outputs.items():
            result += f"{output}\n\n"
        
        # 添加投资建议
        score_data = self.create_investment_score(agent_outputs)
        result += self._format_investment_advice(score_data)
        
        return result
    
    def create_investment_score(self, agent_outputs: Dict[str, str]) -> Dict[str, Any]:
        """
        创建投资评分
        
        Args:
            agent_outputs: 各Agent的输出
            
        Returns:
            评分数据
        """
        # 简单评分逻辑
        score = 50
        breakdown = {}
        
        # 基本面评分
        fundamental = agent_outputs.get('fundamental', '')
        if '✅' in fundamental:
            score += 15
            breakdown['基本面'] = +15
        elif '🔴' in fundamental:
            score -= 15
            breakdown['基本面'] = -15
        
        # 技术面评分
        technical = agent_outputs.get('technical', '')
        if '买入' in technical:
            score += 15
            breakdown['技术面'] = +15
        elif '卖出' in technical:
            score -= 15
            breakdown['技术面'] = -15
        
        # 情绪评分
        sentiment = agent_outputs.get('sentiment', '')
        if '🟢' in sentiment or '积极' in sentiment:
            score += 10
            breakdown['市场情绪'] = +10
        elif '🔴' in sentiment or '消极' in sentiment:
            score -= 10
            breakdown['市场情绪'] = -10
        
        # 确保分数在0-100之间
        score = max(0, min(100, score))
        
        # 评级
        if score >= 70:
            rating = 'Buy'
        elif score >= 50:
            rating = 'Hold'
        else:
            rating = 'Sell'
        
        return {
            'score': score,
            'rating': rating,
            'breakdown': breakdown
        }
    
    def _format_investment_advice(self, score_data: Dict[str, Any]) -> str:
        """格式化投资建议"""
        score = score_data['score']
        rating = score_data['rating']
        
        advice = "## 💡 投资建议\n\n"
        
        rating_emoji = {
            'Buy': '🟢',
            'Hold': '🟡',
            'Sell': '🔴'
        }
        
        advice += f"**评级**: {rating_emoji.get(rating, '🟡')} {rating}\n"
        advice += f"**综合评分**: {score}/100\n\n"
        
        if score >= 70:
            advice += "✅ 建议买入 - 多项指标表现良好\n"
        elif score >= 50:
            advice += "⚠️ 建议持有 - 指标喜忧参半，观望为主\n"
        else:
            advice += "🔴 建议卖出 - 多项指标显示风险\n"
        
        return advice
