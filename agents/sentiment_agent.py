from agents.base_agent import BaseAgent
from tools.stock_data_tool import StockDataTool

class SentimentAgent(BaseAgent):
    """市场情绪分析 Agent"""
    
    def __init__(self, llm):
        # 创建工具
        news_tool = NewsSearchTool()
        tools = [news_tool.as_tool()]
        
        # 初始化基类
        super().__init__(llm, tools, agent_type="sentiment")
        
        # 设置专门的系统提示词
        self.system_prompt = """你是一个专业的市场情绪分析师。

你的职责：
1. 使用 news_search 工具获取股票相关新闻
2. 分析新闻的情绪倾向（积极、消极、中性）
3. 评估市场对该股票的整体看法
4. 识别可能影响股价的重大新闻
5. 基于市场情绪给出短期建议

请始终使用工具获取最新新闻，并给出专业的情绪分析。"""
