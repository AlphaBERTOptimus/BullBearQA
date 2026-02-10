"""
技术指标计算工具
"""
import yfinance as yf
from functools import lru_cache
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np


class TechnicalIndicatorTool:
    """技术指标计算工具类"""
    
    def __init__(self):
        self._cache_ttl = 300
    
    @lru_cache(maxsize=100)
    def get_technical_indicators(self, ticker: str, period: str = "6mo") -> Optional[Dict[str, Any]]:
        """
        获取技术指标
        
        Args:
            ticker: 股票代码
            period: 时间周期
            
        Returns:
            技术指标字典
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            
            if hist.empty:
                return None
            
            # 计算技术指标
            indicators = {
                'ticker': ticker,
                'current_price': float(hist['Close'].iloc[-1]),
                'rsi': self._calculate_rsi(hist),
                'macd': self._calculate_macd(hist),
                'ma20': float(hist['Close'].rolling(window=20).mean().iloc[-1]),
                'ma50': float(hist['Close'].rolling(window=50).mean().iloc[-1]),
                'volume': int(hist['Volume'].iloc[-1]),
            }
            
            return indicators
            
        except Exception as e:
            print(f"Error getting technical indicators: {e}")
            return None
    
    def _calculate_rsi(self, hist: pd.DataFrame, period: int = 14) -> Dict[str, Any]:
        """计算RSI指标"""
        try:
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_value = float(rsi.iloc[-1])
            
            # 判断信号
            if rsi_value < 30:
                signal = "🟢 超卖区域，可能反弹"
            elif rsi_value > 70:
                signal = "🔴 超买区域，可能回调"
            else:
                signal = "🟡 中性区域"
            
            return {
                'value': rsi_value,
                'signal': signal
            }
        except:
            return {'value': 'N/A', 'signal': 'N/A'}
    
    def _calculate_macd(self, hist: pd.DataFrame) -> Dict[str, str]:
        """计算MACD指标"""
        try:
            exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
            exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal_line = macd.ewm(span=9, adjust=False).mean()
            
            # 判断金叉/死叉
            if macd.iloc[-1] > signal_line.iloc[-1] and macd.iloc[-2] <= signal_line.iloc[-2]:
                return {'signal': '🟢 金叉，看涨信号'}
            elif macd.iloc[-1] < signal_line.iloc[-1] and macd.iloc[-2] >= signal_line.iloc[-2]:
                return {'signal': '🔴 死叉，看跌信号'}
            elif macd.iloc[-1] > signal_line.iloc[-1]:
                return {'signal': '📊 多头排列'}
            else:
                return {'signal': '📊 空头排列'}
        except:
            return {'signal': 'N/A'}


# 函数式接口
_tool_instance = TechnicalIndicatorTool()

def get_technical_indicators(ticker: str, period: str = "6mo") -> Optional[Dict[str, Any]]:
    """函数式接口"""
    return _tool_instance.get_technical_indicators(ticker, period)
