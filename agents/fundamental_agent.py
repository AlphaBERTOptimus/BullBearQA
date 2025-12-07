from .base_agent import BaseAgent
from tools.stock_data_tool import StockDataTool

class FundamentalAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="基本面分析师",
            role="分析公司财务指标（PE、ROE、营收、利润等），评估估值合理性。",
            tools=[StockDataTool()]
        )
