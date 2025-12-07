from .base_agent import BaseAgent
from ..tools.stock_data_tool import StockDataTool 

class FundamentalAgent(BaseAgent):
    """基本面分析 Agent"""
    
    def __init__(self, llm):
        # 创建工具
        stock_data_tool = StockDataTool()
        tools = [stock_data_tool.as_tool()]
        
        # 初始化基类
        super().__init__(llm, tools, agent_type="fundamental")
        
        # 设置专门的系统提示词
        self.system_prompt = """你是一个专业的股票基本面分析师。

你的职责：
1. 使用 stock_data 工具获取股票的基本面数据
2. 分析公司的财务健康状况、盈利能力和估值水平
3. 评估公司的行业地位和竞争优势
4. 基于基本面给出投资建议
5. 识别潜在的投资风险和机会

请始终使用工具获取实时数据，并给出专业的基本面分析。"""
