from langchain.tools import BaseTool
import yfinance as yf
import pandas as pd
import time
from typing import Optional

class TechnicalIndicatorTool(BaseTool):
    name = "technical_indicator_tool"
    description = "计算技术指标（RSI、MACD、均线等）。输入：股票代码（如 'TSLA'）"
    
    # 缓存
    _cache = {}
    _cache_ttl = 300  # 5分钟
    
    def _get_cached_data(self, ticker: str) -> Optional[dict]:
        if ticker in self._cache:
            data, timestamp = self._cache[ticker]
            if time.time() - timestamp < self._cache_ttl:
                return data
        return None
    
    def _set_cache(self, ticker: str, data: dict):
        self._cache[ticker] = (data, time.time())
    
    def _run(self, ticker: str) -> str:
        try:
            ticker = ticker.strip().upper()
            
            # 检查缓存
            cached = self._get_cached_data(ticker)
            if cached:
                return self._format_output(ticker, cached, from_cache=True)
            
            # 获取历史数据（最近90天）
            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo")
            
            if hist.empty:
                return f"❌ 无法获取 {ticker} 的历史数据"
            
            # 计算技术指标
            indicators = self._calculate_indicators(hist)
            
            # 获取当前价格
            current_price = hist['Close'].iloc[-1]
            indicators['current_price'] = current_price
            
            # 存入缓存
            self._set_cache(ticker, indicators)
            
            return self._format_output(ticker, indicators)
            
        except Exception as e:
            if "rate limit" in str(e).lower():
                return f"⚠️ API 请求过于频繁，请稍后再试"
            return f"❌ 计算 {ticker} 技术指标时出错: {str(e)}"
    
    def _calculate_indicators(self, hist: pd.DataFrame) -> dict:
        """计算各类技术指标"""
        close = hist['Close']
        
        indicators = {}
        
        # 1. RSI (14日)
        try:
            indicators['rsi'] = self._calculate_rsi(close, 14)
        except:
            indicators['rsi'] = None
        
        # 2. MACD
        try:
            macd_data = self._calculate_macd(close)
            indicators['macd'] = macd_data['macd']
            indicators['macd_signal'] = macd_data['signal']
            indicators['macd_hist'] = macd_data['histogram']
        except:
            indicators['macd'] = None
            indicators['macd_signal'] = None
            indicators['macd_hist'] = None
        
        # 3. 移动平均线
        try:
            indicators['ma20'] = close.rolling(window=20).mean().iloc[-1]
            indicators['ma50'] = close.rolling(window=50).mean().iloc[-1]
        except:
            indicators['ma20'] = None
            indicators['ma50'] = None
        
        # 4. 布林带
        try:
            bollinger = self._calculate_bollinger(close)
            indicators['bb_upper'] = bollinger['upper']
            indicators['bb_middle'] = bollinger['middle']
            indicators['bb_lower'] = bollinger['lower']
        except:
            indicators['bb_upper'] = None
            indicators['bb_middle'] = None
            indicators['bb_lower'] = None
        
        # 5. 成交量分析
        try:
            volume = hist['Volume']
            indicators['avg_volume'] = volume.tail(20).mean()
            indicators['volume_trend'] = "增加" if volume.iloc[-1] > indicators['avg_volume'] else "减少"
        except:
            indicators['avg_volume'] = None
            indicators['volume_trend'] = None
        
        return indicators
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> float:
        """计算 RSI"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=window).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=window).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]
    
    def _calculate_macd(self, prices: pd.Series) -> dict:
        """计算 MACD"""
        exp1 = prices.ewm(span=12, adjust=False).mean()
        exp2 = prices.ewm(span=26, adjust=False).mean()
        
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        
        return {
            'macd': macd.iloc[-1],
            'signal': signal.iloc[-1],
            'histogram': histogram.iloc[-1]
        }
    
    def _calculate_bollinger(self, prices: pd.Series, window: int = 20) -> dict:
        """计算布林带"""
        middle = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        
        upper = middle + (std * 2)
        lower = middle - (std * 2)
        
        return {
            'upper': upper.iloc[-1],
            'middle': middle.iloc[-1],
            'lower': lower.iloc[-1]
        }
    
    def _format_output(self, ticker: str, indicators: dict, from_cache: bool = False) -> str:
        """格式化输出"""
        try:
            cache_note = " [缓存数据]" if from_cache else ""
            current_price = indicators.get('current_price', 'N/A')
            
            output = f"""
📈 **{ticker} 技术分析**{cache_note}

**当前价格:** ${current_price:.2f}

**动量指标：**
"""
            
            # RSI 分析
            rsi = indicators.get('rsi')
            if rsi is not None:
                rsi_s
