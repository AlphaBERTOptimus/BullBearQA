"""
市场情绪分析Agent
"""
from typing import Optional
from agents.base_agent import BaseAgent
from tools.news_search_tool import NewsSearchTool


class SentimentAgent(BaseAgent):
    """市场情绪分析师Agent"""
    
    def __init__(self, llm=None):
        super().__init__(name="Sentiment Analyst", llm=llm)
        self.news_tool = NewsSearchTool()
    
    def run(self, query: str) -> str:
        """
        执行市场情绪分析
        
        Args:
            query: 用户查询
            
        Returns:
            分析结果
        """
        ticker = self._extract_ticker(query)
        
        if not ticker:
            return "❌ 无法识别股票代码"
        
        # 获取新闻
        news = self.news_tool.search_news(ticker)
        
        if not news:
            return f"❌ 暂时无法获取 {ticker} 的新闻数据"
        
        return self._generate_report(ticker, news)
    
    def _extract_ticker(self, query: str) -> Optional[str]:
        """从查询中提取股票代码"""
        import re
        patterns = [
            r'\b([A-Z]{1,5})\b',
            r'([A-Z]{1,5})的',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query.upper())
            if match:
                return match.group(1)
        
        return None
    
    def _generate_report(self, ticker: str, news: list) -> str:
        """生成情绪分析报告"""
        report = f"""
## 📰 {ticker} 市场情绪分析

### 🔍 最新新闻 (最近{len(news)}条)

"""
        
        for i, item in enumerate(news[:5], 1):
            title = item.get('title', '无标题')
            source = item.get('source', '未知来源')
            date = item.get('date', '未知日期')
            
            report += f"{i}. **{title}**\n"
            report += f"   📅 {date} | 📰 {source}\n\n"
        
        # 情绪分析
        report += "### 💭 整体情绪\n"
        sentiment = self._analyze_sentiment(news)
        report += sentiment
        
        return report
    
    def _analyze_sentiment(self, news: list) -> str:
        """分析整体情绪"""
        if not news:
            return "📊 **中性** - 暂无足够数据判断\n"
        
        # 简单关键词分析
        positive_keywords = ['涨', '增长', '突破', '创新', '收购', '利好', '盈利']
        negative_keywords = ['跌', '下滑', '亏损', '裁员', '诉讼', '调查', '警告']
        
        positive_count = 0
        negative_count = 0
        
        for item in news:
            title = item.get('title', '').lower()
            for kw in positive_keywords:
                if kw in title:
                    positive_count += 1
            for kw in negative_keywords:
                if kw in title:
                    negative_count += 1
        
        if positive_count > negative_count * 1.5:
            return "🟢 **积极** - 近期新闻偏正面\n"
        elif negative_count > positive_count * 1.5:
            return "🔴 **消极** - 近期新闻偏负面\n"
        else:
            return "🟡 **中性** - 正负面新闻相当\n"
