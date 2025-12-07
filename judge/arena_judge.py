from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import os
from typing import List, Dict

class ArenaJudge:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
            openai_api_base="https://api.deepseek.com/v1",
            temperature=0.3
        )
    
    def synthesize(self, question: str, agent_outputs: List[Dict]) -> str:
        """
        综合多个Agent的输出，生成最终建议
        
        Args:
            question: 用户原始问题
            agent_outputs: [
                {'agent': 'fundamental', 'output': '...'},
                {'agent': 'technical', 'output': '...'},
                ...
            ]
        """
        # 如果只有一个Agent的输出，直接返回
        if len(agent_outputs) == 1:
            return self._format_single_output(agent_outputs[0])
        
        # 多个Agent输出，需要综合
        return self._synthesize_multiple_outputs(question, agent_outputs)
    
    def _format_single_output(self, agent_output: Dict) -> str:
        """格式化单个Agent的输出"""
        agent_name = {
            'fundamental': '📊 基本面分析',
            'technical': '📈 技术面分析',
            'sentiment': '📰 市场情绪',
            'comparison': '⚖️ 对比分析'
        }.get(agent_output['agent'], '分析结果')
        
        return f"""
{agent_name}

{agent_output['output']}
"""
    
    def _synthesize_multiple_outputs(self, question: str, agent_outputs: List[Dict]) -> str:
        """综合多个Agent的输出"""
        
        # 构建综合分析的输入
        agents_info = []
        for item in agent_outputs:
            agent_name = {
                'fundamental': '基本面分析师',
                'technical': '技术面分析师',
                'sentiment': '情绪分析师',
                'comparison': '对比分析师'
            }.get(item['agent'], item['agent'])
            
            agents_info.append(f"""
【{agent_name}的分析】
{item['output']}
""")
        
        combined_analysis = "\n\n".join(agents_info)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是 BullBear Arena 的首席分析师（Arena Judge），负责综合多位专业分析师的意见，给出最终的投资建议。

你的任务：
1. 整合各位分析师的观点，识别一致性和分歧
2. 给出明确的投资建议（买入/持有/卖出/观望）
3. 列出关键风险和机会
4. 保持客观中立，避免过度乐观或悲观

输出格式：
📊 综合分析摘要
[2-3句话总结各维度的核心观点]

💡 投资建议
- 评级: [买入/持有/卖出/观望]
- 理由: [简明扼要的理由]

⚠️ 关键风险
- [风险1]
- [风险2]

✅ 投资机会
- [机会1]
- [机会2]

📝 结论
[1-2句话的最终建议]
"""),
            ("user", """用户问题: {question}

各位分析师的意见:
{analysis}

请综合以上分析，给出你的最终判断。""")
        ])
        
        try:
            chain = prompt | self.llm
            result = chain.invoke({
                "question": question,
                "analysis": combined_analysis
            })
            
            # 在最终输出前加上各Agent的详细分析
            detailed_output = "═" * 50 + "\n"
            detailed_output += "🔍 **详细分析报告**\n"
            detailed_output += "═" * 50 + "\n\n"
            
            for item in agent_outputs:
                agent_emoji = {
                    'fundamental': '📊',
                    'technical': '📈',
                    'sentiment': '📰',
                    'comparison': '⚖️'
                }.get(item['agent'], '📋')
                
                agent_name = {
                    'fundamental': '基本面分析',
                    'technical': '技术面分析',
                    'sentiment': '市场情绪',
                    'comparison': '对比分析'
                }.get(item['agent'], '分析结果')
                
                detailed_output += f"{agent_emoji} **{agent_name}**\n\n"
                detailed_output += f"{item['output']}\n\n"
                detailed_output += "─" * 50 + "\n\n"
            
            # 添加最终综合建议
            detailed_output += "═" * 50 + "\n"
            detailed_output += "🏆 **Arena Judge 最终裁决**\n"
            detailed_output += "═" * 50 + "\n\n"
            detailed_output += result.content
            
            return detailed_output
            
        except Exception as e:
            # 如果LLM综合失败，直接拼接各Agent输出
            fallback = "⚠️ 综合分析暂时不可用，以下是各维度的独立分析：\n\n"
            
            for item in agent_outputs:
                agent_name = {
                    'fundamental': '📊 基本面分析',
                    'technical': '📈 技术面分析',
                    'sentiment': '📰 市场情绪',
                    'comparison': '⚖️ 对比分析'
                }.get(item['agent'], '分析结果')
                
                fallback += f"{agent_name}\n\n{item['output']}\n\n"
                fallback += "─" * 50 + "\n\n"
            
            return fallback
    
    def create_investment_score(self, agent_outputs: List[Dict]) -> Dict:
        """
        基于各Agent输出计算简单的投资评分
        返回: {
            'score': 0-100,
            'rating': 'Strong Buy' | 'Buy' | 'Hold' | 'Sell' | 'Strong Sell'
        }
        """
        scores = {
            'fundamental': 0,
            'technical': 0,
            'sentiment': 0
        }
        
        # 简化的评分逻辑（可以根据实际需求优化）
        for item in agent_outputs:
            agent = item['agent']
            output = item['output'].lower()
            
            # 基本面评分
            if agent == 'fundamental':
                if 'pe较低' in output or 'roe优秀' in output:
                    scores['fundamental'] += 30
                elif 'pe较高' in output or 'roe偏低' in output:
                    scores['fundamental'] -= 20
                else:
                    scores['fundamental'] += 10
            
            # 技术面评分
            elif agent == 'technical':
                if '看涨' in output or '超卖' in output:
                    scores['technical'] += 30
                elif '看跌' in output or '超买' in output:
                    scores['technical'] -= 20
                else:
                    scores['technical'] += 10
            
            # 情绪面评分
            elif agent == 'sentiment':
                if '偏乐观' in output or '正面' in output:
                    scores['sentiment'] += 20
                elif '偏悲观' in output or '负面' in output:
                    scores['sentiment'] -= 10
                else:
                    scores['sentiment'] += 5
        
        # 计算总分（0-100）
        total_score = sum(scores.values())
        normalized_score = min(100, max(0, 50 + total_score))
        
        # 评级
        if normalized_score >= 80:
            rating = "Strong Buy"
        elif normalized_score >= 60:
            rating = "Buy"
        elif normalized_score >= 40:
            rating = "Hold"
        elif normalized_score >= 20:
            rating = "Sell"
        else:
            rating = "Strong Sell"
        
        return {
            'score': normalized_score,
            'rating': rating,
            'breakdown': scores
        }
