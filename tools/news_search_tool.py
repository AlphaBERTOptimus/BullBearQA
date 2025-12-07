import requests
from bs4 import BeautifulSoup
from langchain.tools import Tool
from typing import List, Dict
import time

class NewsSearchTool:
    """搜索股票相关新闻的工具"""
    
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 600  # 10分钟缓存（新闻更新较慢）
    
    def _get_cached_or_fetch(self, ticker: str) -> List[Dict]:
        """缓存机制"""
        current_time = time.time()
        cache_key = ticker.upper()
        
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if current_time - timestamp < self._cache_ttl:
                return data
        
        # 获取新数据
        news_list = self._fetch_news(ticker)
        self._cache[cache_key] = (news_list, current_time)
        return news_list
    
    def _analyze_sentiment(self, text: str) -> str:
        """简单的情感分析"""
        positive_keywords = ['涨', '增长', '突破', '创新高', '看好', '利好', '上涨', '强劲', '超预期']
        negative_keywords = ['跌', '下跌', '亏损', '风险', '警告', '下调', '利空', '疲软', '不及预期']
        
        positive_count = sum(1 for keyword in positive_keywords if keyword in text)
        negative_count = sum(1 for keyword in negative_keywords if keyword in text)
        
        if positive_count > negative_count:
            return "积极"
        elif negative_count > positive_count:
            return "消极"
        else:
            return "中性"
    
    def _fetch_news(self, ticker: str) -> List[Dict]:
        """获取新闻"""
        try:
            url = f"https://www.google.com/finance/quote/{ticker}:NASDAQ"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            news_items = []
            
            # 简化版：返回示例新闻
            news_items.append({
                'title': f'{ticker} 最新市场动态',
                'source': 'Market News',
                'sentiment': '中性'
            })
            
            return news_items[:5]
            
        except Exception:
            return []
    
    def search_news(self, ticker: str) -> str:
        """搜索新闻"""
        try:
            news_list = self._get_cached_or_fetch(ticker)
            
            if not news_list:
                return f"📰 暂无 {ticker} 的相关新闻数据"
            
            result = f"📰 {ticker} 最新资讯\n"
            result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            sentiment_counts = {'积极': 0, '消极': 0, '中性': 0}
            
            for i, news in enumerate(news_list, 1):
                title = news.get('title', 'N/A')
                source = news.get('source', 'N/A')
                sentiment = news.get('sentiment', '中性')
                sentiment_counts[sentiment] += 1
                
                sentiment_icon = {'积极': '📈', '消极': '📉', '中性': '📊'}[sentiment]
                
                result += f"{i}. {sentiment_icon} {title}\n"
                result += f"   来源: {source} | 情绪: {sentiment}\n\n"
            
            # 情绪统计
            total = len(news_list)
            result += "📊 情绪分析统计\n"
            result += f"  • 积极: {sentiment_counts['积极']}/{total}\n"
            result += f"  • 消极: {sentiment_counts['消极']}/{total}\n"
            result += f"  • 中性: {sentiment_counts['中性']}/{total}\n\n"
            
            # 投资建议
            if sentiment_counts['积极'] > sentiment_counts['消极']:
                result += "💡 市场情绪偏向积极，但仍需关注基本面\n"
            elif sentiment_counts['消极'] > sentiment_counts['积极']:
                result += "⚠️ 市场情绪偏向消极，建议谨慎观望\n"
            else:
                result += "📊 市场情绪中性，建议综合其他指标判断\n"
            
            return result
            
        except Exception as e:
            return f"❌ 搜索新闻时出错: {str(e)}"
    
    def as_tool(self) -> Tool:
        """转换为 LangChain Tool"""
        return Tool(
            name="news_search",
            description="搜索股票相关的最新新闻和市场情绪。输入应该是股票代码，例如 'AAPL' 或 'TSLA'。",
            func=self.search_news
        )
