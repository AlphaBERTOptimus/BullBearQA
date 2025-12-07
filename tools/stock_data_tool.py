from langchain.tools import BaseTool
import yfinance as yf
from typing import Optional
import time

class StockDataTool(BaseTool):
    name = "stock_data_tool"
    description = "获取股票基本面数据，如PE、ROE、市值、营收等。输入：股票代码（如 'AAPL'）"
    
    # 简单的内存缓存
    _cache = {}
    _cache_ttl = 300  # 5分钟缓存
    
    def _get_cached_data(self, ticker: str) -> Optional[dict]:
        """检查缓存"""
        if ticker in self._cache:
            data, timestamp = self._cache[ticker]
            if time.time() - timestamp < self._cache_ttl:
                return data
        return None
    
    def _set_cache(self, ticker: str, data: dict):
        """设置缓存"""
        self._cache[ticker] = (data, time.time())
    
    def _run(self, ticker: str) -> str:
        try:
            ticker = ticker.strip().upper()
            
            # 检查缓存
            cached = self._get_cached_data(ticker)
            if cached:
                return self._format_output(cached, from_cache=True)
            
            # 获取数据
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 验证数据有效性
            if not info or 'symbol' not in info:
                return f"❌ 错误：股票代码 '{ticker}' 不存在或数据不可用"
            
            # 存入缓存
            self._set_cache(ticker, info)
            
            return self._format_output(info)
            
        except Exception as e:
            if "rate limit" in str(e).lower():
                return f"⚠️ API 请求过于频繁，请稍后再试（建议等待 1 分钟）"
            return f"❌ 获取 {ticker} 数据时出错: {str(e)}"
    
    def _format_output(self, info: dict, from_cache: bool = False) -> str:
        """格式化输出"""
        try:
            ticker = info.get('symbol', 'N/A')
            name = info.get('longName', info.get('shortName', 'N/A'))
            
            # 提取关键指标
            pe = info.get('trailingPE', info.get('forwardPE', 'N/A'))
            pb = info.get('priceToBook', 'N/A')
            roe = info.get('returnOnEquity', 'N/A')
            market_cap = info.get('marketCap', 'N/A')
            revenue = info.get('totalRevenue', 'N/A')
            profit_margin = info.get('profitMargins', 'N/A')
            debt_to_equity = info.get('debtToEquity', 'N/A')
            
            # 格式化数字
            def format_number(value, is_percentage=False, is_currency=False):
                if value == 'N/A' or value is None:
                    return 'N/A'
                try:
