from .base_agent import BaseAgent
from tools.technical_indicator_tool import TechnicalIndicatorTool

class TechnicalAgent(BaseAgent):
    """技术分析 Agent"""
    
    def __init__(self, llm):
        # 创建工具
        technical_tool = TechnicalIndicatorTool()
        tools = [technical_tool.as_tool()]
        
        # 初始化基类
        super().__init__(llm, tools, agent_type="technical")
        
        # 设置专门的系统提示词
        self.system_prompt = """你是一个专业的股票技术分析师。

你的职责：
1. 使用 technical_indicators 工具获取股票的技术指标数据
2. 解读 RSI、MACD、移动平均线、布林带和成交量
3. 基于技术指标给出买卖时机建议
4. 识别技术形态和趋势
5. 提供短期交易建议

请始终使用工具获取实时数据，并给出专业的技术分析。"""
