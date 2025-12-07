from langchain.tools import BaseTool
import requests
from bs4 import BeautifulSoup

class NewsSearchTool(BaseTool):
    name = "news_search_tool"
    description = "搜索与股票或行业相关的最新新闻标题。输入：关键词（如 'NVDA' 或 'AI行业'）"

    def _run(self, query: str) -> str:
        try:
            # 简化版：模拟新闻（实际可接 NewsAPI / Bing / Google Programmable Search）
            return f"模拟新闻：{query} 相关市场情绪近期偏积极，无重大负面事件。"
        except Exception as e:
            return f"新闻搜索失败: {str(e)}"

    async def _arun(self, query: str) -> str:
        raise NotImplementedError("不支持异步")
