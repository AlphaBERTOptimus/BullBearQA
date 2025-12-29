# -*- coding: utf-8 -*-
"""
Arena Judge - 综合分析裁判
整合多个Agent的分析结果，给出最终投资建议
"""

class ArenaJudge:
    def __init__(self, llm):
        self.llm = llm
    
    def synthesize(self, question: str, agent_outputs: dict) -> str:
        """
        综合多个Agent的分析结果
        
        Args:
            question: 用户问题
            agent_outputs: {agent_type: output_text} 字典
        
        Returns:
            综合分析报告
        """
        try:
            # 确保输入是UTF-8编码
            question = str(question).encode('utf-8', errors='ignore').decode('utf-8')
            
            # 构建综合分析提示词
            prompt = f"""
你是一位资深的金融分析师，请综合以下多个维度的分析结果，给出专业的投资建议。

用户问题：{question}

分析结果：
"""
            
            # 添加各Agent的分析结果
            agent_name_map = {
                'fundamental': '【基本面分析】',
                'technical': '【技术面分析】',
                'sentiment': '【市场情绪】',
                'comparison': '【股票对比】'
            }
            
            for agent_type, output in agent_outputs.items():
                agent_name = agent_name_map.get(agent_type, f'【{agent_type}】')
                # 确保输出是UTF-8编码
                output_str = str(output).encode('utf-8', errors='ignore').decode('utf-8')
                prompt += f"\n{agent_name}\n{output_str}\n"
            
            # 添加输出格式要求
            prompt += """

请按以下格式输出综合分析报告：

📊 综合分析摘要
[用2-3句话总结关键发现]

💡 投资建议
[明确的投资建议：买入/持有/卖出，并说明理由]

⚠️ 主要风险
[列出2-3个关键风险点]

✨ 投资机会
[列出2-3个投资机会]

🎯 最终结论
[用1-2句话给出最终结论]
"""
            
            # 调用LLM生成综合分析
            response = self.llm.invoke(prompt)
            
            # 确保响应是UTF-8编码
            result = response.content.encode('utf-8', errors='ignore').decode('utf-8')
            
            return result
            
        except Exception as e:
            # 返回友好的错误信息（UTF-8编码）
            error_msg = f"""
📊 综合分析报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{agent_name_map.get(list(agent_outputs.keys())[0], '【分析】') if agent_outputs else '【分析】'}
❌ 处理过程中出现错误：{str(e)}

⚠️ 注意：由于 API 调用失败，以上为原始分析报告。
"""
            return error_msg.encode('utf-8', errors='ignore').decode('utf-8')
    
    def create_investment_score(self, agent_outputs: dict) -> dict:
        """
        创建投资评分
        
        Args:
            agent_outputs: {agent_type: output_text} 字典
        
        Returns:
            {
                'score': int (0-100),
                'rating': str ('Buy', 'Hold', 'Sell'),
                'breakdown': dict
            }
        """
        try:
            # 默认值
            default_score = {
                'score': 50,
                'rating': 'Hold',
                'breakdown': {
                    '基本面': 0,
                    '技术面': 0,
                    '市场情绪': 0
                }
            }
            
            # 检查输入类型
            if not isinstance(agent_outputs, dict):
                print(f"[WARNING] agent_outputs 类型错误: {type(agent_outputs)}")
                return default_score
            
            if not agent_outputs:
                return default_score
            
            # 初始化评分
            scores = {
                'fundamental': 50,
                'technical': 50,
                'sentiment': 50
            }
            
            # 简单评分逻辑（基于关键词）
            for agent_type, output in agent_outputs.items():
                if not isinstance(output, str):
                    continue
                
                output_lower = output.lower()
                
                # 正面关键词
                positive_keywords = ['优秀', '强劲', '看涨', '买入', '上涨', '增长', '超预期', '积极', '利好']
                # 负面关键词
                negative_keywords = ['疲软', '看跌', '卖出', '下跌', '风险', '担忧', '不及预期', '消极', '利空']
                
                pos_count = sum(1 for kw in positive_keywords if kw in output_lower)
                neg_count = sum(1 for kw in negative_keywords if kw in output_lower)
                
                # 根据关键词调整分数
                if pos_count > neg_count:
                    scores[agent_type] = min(85, 50 + (pos_count - neg_count) * 10)
                elif neg_count > pos_count:
                    scores[agent_type] = max(15, 50 - (neg_count - pos_count) * 10)
            
            # 计算综合分数（加权平均）
            weights = {
                'fundamental': 0.4,
                'technical': 0.3,
                'sentiment': 0.3
            }
            
            total_score = 0
            total_weight = 0
            
            for agent_type, weight in weights.items():
                if agent_type in scores:
                    total_score += scores[agent_type] * weight
                    total_weight += weight
            
            final_score = int(total_score / total_weight) if total_weight > 0 else 50
            
            # 确定评级
            if final_score >= 70:
                rating = 'Buy'
            elif final_score >= 40:
                rating = 'Hold'
            else:
                rating = 'Sell'
            
            # 构建分解
            breakdown = {}
            agent_name_map = {
                'fundamental': '基本面',
                'technical': '技术面',
                'sentiment': '市场情绪'
            }
            
            for agent_type, score in scores.items():
                cn_name = agent_name_map.get(agent_type, agent_type)
                breakdown[cn_name] = score - 50  # 显示相对于50的差值
            
            return {
                'score': final_score,
                'rating': rating,
                'breakdown': breakdown
            }
            
        except Exception as e:
            print(f"[ERROR] create_investment_score 失败: {str(e)}")
            # 返回默认值
            return {
                'score': 50,
                'rating': 'Hold',
                'breakdown': {}
            }
