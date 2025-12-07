from .base_agent import BaseAgent
from tools.news_search_tool import NewsSearchTool

class SentimentAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="情绪面分析师",
            role="分析新闻、社交媒体、市场情绪，识别热点和风险。",
            tools=[NewsSearchTool()]
        )
