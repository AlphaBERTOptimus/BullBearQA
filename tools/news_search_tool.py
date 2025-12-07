from langchain.tools import BaseTool
import requests
from bs4 import BeautifulSoup
import time
from typing import Optional

class NewsSearchTool(BaseTool):
    name = "news_search_tool"
    description = "搜索与股票或行业相关的最新新闻和市场情绪。输入：股票代码或关键词"
    
    # 缓存
    _cache = {}
    _cache_ttl = 600  # 10分钟缓存（新闻更新较慢）
    
    def _get_cached_data(self, query: str) -> Optional[list]:
        if query in self._cache:
            data, timestamp = self._cache[query]
            if time.time() - timestamp < self._cache_ttl:
                return data
        return None
    
    def _set_cache(self, query: str, data: list):
        self._cache[query] = (data, time.time())
    
    def _run(self, query: str) -> str:
        try:
            query = query.strip().upper()
            
            # 检查缓存
            cached = self._get_cached_data(query)
            if cached:
                return self._format_output(query, cached, from_cache=True)
            
            # 获取新闻数据
            news_items = self._fetch_news(query)
            
            if not news_items:
                return f"⚠️ 未找到与 '{query}' 相关的近期新闻"
            
            # 存入缓存
            self._set_cache(query, news_items)
            
            return self._format_output(query, news_items)
            
        except Exception as e:
            return f"❌ 搜索新闻时出错: {str(e)}"
    
    def _fetch_news(self, query: str, max_items: int = 5) -> list:
        """
        获取新闻数据
        这里使用 Google Finance 作为免费来源
        也可以替换为 NewsAPI, Finnhub 等付费服务
        """
        news_items = []
        
        try:
            # 方法1: 使用 Google Finance (免费但可能被限流)
            url = f"https://www.google.com/finance/quote/{query}:NASDAQ"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 尝试提取新闻标题
                # 注：Google Finance 的 HTML 结构可能变化，这是一个示例
                news_sections = soup.find_all('div', class_='yY3Lee')
                
                for section in news_sections[:max_items]:
                    try:
                        title = section.get_text(strip=True)
                        if title and len(title) > 10:
                            news_items.append({
                                'title': title,
                                'source': 'Google Finance',
                                'sentiment': self._analyze_sentiment(title)
                            })
                    except:
                        continue
            
            # 如果 Google Finance 没有数据，使用备用方案
            if not news_items:
                news_items = self._get_fallback_news(query)
            
        except Exception as e:
            # 失败时返回模拟数据（实际部署时应移除）
            news_items = self._get_fallback_news(query)
        
        return news_items
    
    def _get_fallback_news(self, query: str) -> list:
        """
        备用新闻源（示例）
        实际使用时应该集成真实的 API，如：
        - NewsAPI (免费额度: 100 requests/day)
        - Finnhub (免费额度: 60 requests/min)
        - Alpha Vantage News API
        """
        # 这里返回模拟数据，提示用户配置真实API
        return [
            {
                'title': f'{query} 的新闻数据需要配置专业API',
                'source': '系统提示',
                'sentiment': 'neutral'
            },
            {
                'title': '建议集成 NewsAPI 或 Finnhub 以获取实时新闻',
                'source': '系统提示',
                'sentiment': 'neutral'
            },
            {
                'title': '当前为演示模式，使用模拟数据',
                'source': '系统提示',
                'sentiment': 'neutral'
            }
        ]
    
    def _analyze_sentiment(self, text: str) -> str:
        """
        简单的情绪分析（基于关键词）
        实际应用可使用 NLTK, TextBlob 或 FinBERT
        """
        text_lower = text.lower()
        
        # 正面词汇
        positive_words = [
            'up', 'rise', 'gain', 'profit', 'growth', 'surge', 'rally',
            'beat', 'exceed', 'record', 'high', 'strong', 'bullish',
            '上涨', '增长', '盈利', '突破', '创新高', '强劲'
        ]
        
        # 负面词汇
        negative_words = [
            'down', 'fall', 'loss', 'drop', 'decline', 'crash', 'plunge',
            'miss', 'weak', 'concern', 'risk', 'bearish', 'cut',
            '下跌', '下降', '亏损', '暴跌', '风险', '削减'
        ]
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _format_output(self, query: str, news_items: list, from_cache: bool = False) -> str:
        """格式化输出"""
        cache_note = " [缓存数据]" if from_cache else ""
        
        output = f"""
📰 **{query} 市场情绪与新闻**{cache_note}

"""
        
        # 统计情绪
        sentiments = [item['sentiment'] for item in news_items]
        positive_count = sentiments.count('positive')
        negative_count = sentiments.count('negative')
        neutral_count = sentiments.count('neutral')
        
        total = len(sentiments)
        if total > 0:
            output += f"**整体情绪分布：**\n"
            output += f"- 🟢 正面: {positive_count}/{total} ({positive_count/total*100:.0f}%)\n"
            output += f"- 🔴 负面: {negative_count}/{total} ({negative_count/total*100:.0f}%)\n"
            output += f"- 🟡 中性: {neutral_count}/{total} ({neutral_count/total*100:.0f}%)\n\n"
            
            # 综合情绪判断
            if positive_count > negative_count * 1.5:
                output += "📊 **市场情绪：** 🟢 偏乐观\n\n"
            elif negative_count > positive_count * 1.5:
                output += "📊 **市场情绪：** 🔴 偏悲观\n\n"
            else:
                output += "📊 **市场情绪：** 🟡 中性/分歧\n\n"
        
        # 显示新闻标题
        output += f"**最近新闻 (前{len(news_items)}条):**\n\n"
        
        for i, item in enumerate(news_items, 1):
            sentiment_emoji = {
                'positive': '🟢',
                'negative': '🔴',
                'neutral': '🟡'
            }
            emoji = sentiment_emoji.get(item['sentiment'], '🟡')
            
            output += f"{i}. {emoji} {item['title']}\n"
            output += f"   来源: {item['source']}\n\n"
        
        # 投资提示
        output += "💡 **投资建议：**\n"
        if positive_count > negative_count * 1.5:
            output += "- 市场情绪积极，但需结合基本面和技术面综合判断\n"
            output += "- 注意是否存在过度乐观，警惕追高风险\n"
        elif negative_count > positive_count * 1.5:
            output += "- 市场情绪偏悲观，可能存在恐慌性抛售\n"
            output += "- 若基本面良好，可能是逢低买入的机会\n"
        else:
            output += "- 市场情绪分歧，建议谨慎观望\n"
            output += "- 等待更明确的方向性信号\n"
        
        return output.strip()
    
    async def _arun(self, query: str) -> str:
        return self._run(query)
