import yfinance as yf
from langchain.tools import Tool
from typing import Optional, Dict
import time

class TechnicalIndicatorTool:
    """获取股票技术指标的工具"""
    
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 300  # 5分钟缓存
    
    def _get_cached_or_fetch(self, ticker: str):
        """缓存机制"""
        current_time = time.time()
        cache_key = ticker.upper()
        
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if current_time - timestamp < self._cache_ttl:
                return data
        
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo")
            if hist.empty:
                return None
            self._cache[cache_key] = (hist, current_time)
            return hist
        except Exception:
            return None
    
    def get_technical_indicators(self, ticker: str) -> str:
        """获取技术指标"""
        try:
            hist = self._get_cached_or_fetch(ticker)
            
            if hist is None or hist.empty:
                return f"❌ 无法获取 '{ticker}' 的历史数据"
            
            # 计算技术指标
            close = hist['Close']
            
            # 1. RSI (相对强弱指标)
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # RSI 解读
            if current_rsi < 30:
                rsi_signal = "超卖，可能反弹"
            elif current_rsi > 70:
                rsi_signal = "超买，可能回调"
            else:
                rsi_signal = "中性"
            
            # 2. MACD
            exp1 = close.ewm(span=12, adjust=False).mean()
            exp2 = close.ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            histogram = macd - signal
            
            current_macd = macd.iloc[-1]
            current_signal = signal.iloc[-1]
            current_histogram = histogram.iloc[-1]
            
            # MACD 解读
            if current_histogram > 0:
                macd_signal = "看涨"
            else:
                macd_signal = "看跌"
            
            # 3. 移动平均线
            ma20 = close.rolling(window=20).mean().iloc[-1]
            ma50 = close.rolling(window=50).mean().iloc[-1]
            current_price = close.iloc[-1]
            
            # MA 解读
            if current_price > ma20 > ma50:
                ma_signal = "强势上涨趋势"
            elif current_price < ma20 < ma50:
                ma_signal = "弱势下跌趋势"
            else:
                ma_signal = "震荡整理"
            
            # 4. 布林带
            ma = close.rolling(window=20).mean()
            std = close.rolling(window=20).std()
            upper_band = ma + (std * 2)
            lower_band = ma - (std * 2)
            
            current_upper = upper_band.iloc[-1]
            current_lower = lower_band.iloc[-1]
            
            # 布林带解读
            if current_price > current_upper:
                bollinger_signal = "突破上轨，超买"
            elif current_price < current_lower:
                bollinger_signal = "跌破下轨，超卖"
            else:
                position = (current_price - current_lower) / (current_upper - current_lower) * 100
                bollinger_signal = f"位于布林带内 ({position:.1f}%)"
            
            # 5. 成交量分析
            volume = hist['Volume']
            avg_volume = volume.rolling(window=20).mean().iloc[-1]
            current_volume = volume.iloc[-1]
            volume_ratio = (current_volume / avg_volume) * 100
            
            if volume_ratio > 150:
                volume_signal = "放量明显"
            elif volume_ratio < 50:
                volume_signal = "缩量明显"
            else:
                volume_signal = "正常"
            
            result = f"""
📈 {ticker} 技术指标分析
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 当前价格: ${current_price:.2f}

🔴 RSI (相对强弱指标)
  • 当前值: {current_rsi:.2f}
  • 信号: {rsi_signal}

📉 MACD (指数平滑异同移动平均线)
  • MACD: {current_macd:.2f}
  • 信号线: {current_signal:.2f}
  • 柱状图: {current_histogram:.2f}
  • 信号: {macd_signal}

📊 移动平均线
  • MA20: ${ma20:.2f}
  • MA50: ${ma50:.2f}
  • 信号: {ma_signal}

🎯 布林带
  • 上轨: ${current_upper:.2f}
  • 下轨: ${current_lower:.2f}
  • 信号: {bollinger_signal}

📦 成交量
  • 当前成交量: {current_volume:,.0f}
  • 20日平均: {avg_volume:,.0f}
  • 量比: {volume_ratio:.1f}%
  • 信号: {volume_signal}
"""
            return result
            
        except Exception as e:
            return f"❌ 计算技术指标时出错: {str(e)}"
    
    def as_tool(self) -> Tool:
        """转换为 LangChain Tool"""
        return Tool(
            name="technical_indicators",
            description="获取股票的技术指标，包括RSI、MACD、移动平均线、布林带和成交量分析。输入应该是股票代码，例如 'AAPL' 或 'TSLA'。",
            func=self.get_technical_indicators
        )
