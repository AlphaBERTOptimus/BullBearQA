from .base_agent import BaseAgent
from tools.comparison_tool import ComparisonTool

class ComparisonAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="对比分析师",
            role="比较多只股票的关键指标，提供横向对比和投资建议。",
            tools=[ComparisonTool()]
        )
