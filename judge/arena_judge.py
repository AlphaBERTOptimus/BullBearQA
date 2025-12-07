from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Dict, List

class ArenaJudge:
    """Arena Judge - 综合多个 agent 的输出"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
    
    def synthesize(self, question: str, agent_outputs: Dict[str, str]) -> str:
        """综合多个 agent 的输出"""
        
        # 构建输入内容
        analysis_content = ""
        for agent_type, output in agent_outputs.items():
            agent_names = {
                'fundamental': '基本面分析',
                'technical': '技术面分析',
                'sentiment': '市场情绪',
                'comparison': '股票对比'
            }
            agent_name = agent_names.get(agent_type, agent_type)
            analysis_content += f"\n\n【{agent_name}】\n{output}"
        
        # 创建综合分析的 prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个资深的投资顾问，需要综合多个分析师的报告，给出最终的投资建议。

请按照以下结构输出：

📊 综合分析摘要
[用2-3句话总结关键发现]

💡 投资建议
[明确的买入/持有/卖出建议，并说明理由]

⚠️ 主要风险
[列出2-3个关键风险点]

✨ 投资机会
[列出1-2个潜在机会]

🎯 最终结论
[一句话总结]

请保持客观、专业，避免过度承诺。"""),
            ("human", """用户问题：{question}

各分析师报告：
{analysis_content}

请给出你的综合分析：""")
        ])
        
        try:
            chain = prompt | self.llm | StrOutputParser()
            result = chain.invoke({
                "question": question,
                "analysis_content": analysis_content
            })
            return result
        except Exception as e:
            # 如果 LLM 调用失败，返回简单的拼接结果
            fallback = "📊 综合分析报告\n"
            fallback += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            fallback += analysis_content
            fallback += "\n\n⚠️ 注意：由于 API 调用失败，以上为原始分析报告。"
            return fallback
    
    def create_investment_score(self, agent_outputs: Dict[str, str]) -> Dict:
        """创建投资评分（0-100）"""
        
        # 简化版评分逻辑
        score = 50  # 基准分
        breakdown = {
            'fundamental': 0,
            'technical': 0,
            'sentiment': 0
        }
        
        # 基本面评分
        if 'fundamental' in agent_outputs:
            output = agent_outputs['fundamental'].lower()
            if '被低估' in output or 'roe优秀' in output:
                breakdown['fundamental'] = 20
            elif '负债高' in output:
                breakdown['fundamental'] = -10
            else:
                breakdown['fundamental'] = 10
        
        # 技术面评分
        if 'technical' in agent_outputs:
            output = agent_outputs['technical'].lower()
            bullish_count = output.count('看涨') + output.count('上涨')
            bearish_count = output.count('看跌') + output.count('下跌')
            breakdown['technical'] = (bullish_count - bearish_count) * 5
        
        # 情绪评分
        if 'sentiment' in agent_outputs:
            output = agent_outputs['sentiment'].lower()
            if '积极' in output:
                breakdown['sentiment'] = 10
            elif '消极' in output:
                breakdown['sentiment'] = -10
            else:
                breakdown['sentiment'] = 0
        
        # 计算总分
        total_score = score + sum(breakdown.values())
        total_score = max(0, min(100, total_score))  # 限制在 0-100
        
        # 评级
        if total_score >= 80:
            rating = "Strong Buy"
        elif total_score >= 60:
            rating = "Buy"
        elif total_score >= 40:
            rating = "Hold"
        elif total_score >= 20:
            rating = "Sell"
        else:
            rating = "Strong Sell"
        
        return {
            'score': total_score,
            'rating': rating,
            'breakdown': breakdown
        }
