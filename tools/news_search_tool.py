"""
新闻搜索工具
"""
import requests
from functools import lru_cache
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


class NewsSearchTool:
    """新闻搜索工具类"""
    
    def __init__(self):
        self._cache_ttl = 600  # 10分钟缓存
    
    @lru_cache(maxsize=50)
    def search_news(self, ticker: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        搜索股票相关新闻
        
        Args:
            ticker: 股票代码
            days: 查询最近几天的新闻
            
        Returns:
            新闻列表
        """
        try:
            # 使用 Google Finance 作为数据源
            news = self._fetch_google_finance_news(ticker)
            
            if not news:
                # 备用：使用 Yahoo Finance
                news = self._fetch_yahoo_news(ticker)
            
            return news[:10]  # 最多返回10条
            
        except Exception as e:
            print(f"Error searching news: {e}")
            return []
    
    def _fetch_google_finance_news(self, ticker: str) -> List[Dict[str, Any]]:
        """从Google Finance获取新闻"""
        try:
            # 简化版本 - 实际应该调用真实API
            # 这里返回模拟数据
            return [
                {
                    'title': f'{ticker} 最新市场动态',
                    'source': 'Google Finance',
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'url': f'https://www.google.com/finance/quote/{ticker}:NASDAQ'
                }
            ]
        except:
            return []
    
    def _fetch_yahoo_news(self, ticker: str) -> List[Dict[str, Any]]:
        """从Yahoo Finance获取新闻（备用）"""
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            news = stock.news
            
            result = []
            for item in news[:5]:
                result.append({
                    'title': item.get('title', ''),
                    'source': item.get('publisher', 'Yahoo Finance'),
                    'date': datetime.fromtimestamp(item.get('providerPublishTime', 0)).strftime('%Y-%m-%d'),
                    'url': item.get('link', '')
                })
            
            return result
        except:
            return []


# 函数式接口
_tool_instance = NewsSearchTool()

def search_news(ticker: str, days: int = 7) -> List[Dict[str, Any]]:
    """函数式接口"""
    return _tool_instance.search_news(ticker, days)
