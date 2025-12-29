# -*- coding: utf-8 -*-
from agents.base_agent import BaseAgent
from tools.comparison_tool import ComparisonTool

class ComparisonAgent(BaseAgent):
    """股票对比分析 Agent"""
    
    def __init__(self, llm):
        # 创建工具
        comparison_tool = ComparisonTool()
        tools = [comparison_tool.as_tool()]
        
        # 初始化基类
        super().__init__(llm, tools, agent_type="comparison")
        
        # 设置专门的系统提示词
        self.system_prompt = """你是一个专业的股票对比分析师。

你的职责：
1. 使用 compare_stocks 工具对比多只股票
2. 横向比较各项关键指标
3. 识别各股票的优势和劣势
4. 基于对比结果给出投资建议
5. 为不同风险偏好的投资者推荐合适的标的

请始终使用工具获取对比数据，并给出专业的对比分析。"""
