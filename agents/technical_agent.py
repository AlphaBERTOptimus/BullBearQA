from .base_agent import BaseAgent
from tools.technical_indicator_tool import TechnicalIndicatorTool

class TechnicalAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="技术面分析师",
            role="分析价格走势、技术指标（RSI、MACD、均线等），判断买卖信号。",
            tools=[TechnicalIndicatorTool()]
        )
