"""技术分析代理"""
from typing import Dict, Any
import yfinance as yf
import pandas as pd
from .base_agent import BaseAgent


class TechnicalAgent(BaseAgent):
    """技术分析代理"""
    
    def __init__(self):
        super().__init__(
            name="TechnicalAgent",
            description="执行技术指标分析，包括趋势、动量、波动率等"
        )
    
    def analyze(self, ticker: str, period: str = "1y") -> Dict[str, Any]:
        """执行技术分析"""
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)
            
            if df.empty:
                return {"error": f"无法获取 {ticker} 的数据", "ticker": ticker}
            
            indicators = self._calculate_indicators(df)
            signals = self._generate_signals(indicators)
            
            return {
                "ticker": ticker,
                "agent": self.name,
                "status": "success",
                "indicators": indicators,
                "signals": signals,
                "summary": self._generate_summary(indicators, signals)
            }
            
        except Exception as e:
            return self._handle_error(e, ticker)
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算技术指标"""
        close = df['Close']
        
        # 移动平均线
        sma_20 = close.rolling(window=20).mean()
        sma_50 = close.rolling(window=50).mean()
        sma_200 = close.rolling(window=200).mean()
        
        # RSI
        rsi = self._calculate_rsi(close)
        
        # MACD
        macd, signal, hist = self._calculate_macd(close)
        
        # 布林带
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(close)
        
        current_price = close.iloc[-1]
        
        return {
            "current_price": round(current_price, 2),
            "sma_20": round(sma_20.iloc[-1], 2) if not pd.isna(sma_20.iloc[-1]) else None,
            "sma_50": round(sma_50.iloc[-1], 2) if not pd.isna(sma_50.iloc[-1]) else None,
            "sma_200": round(sma_200.iloc[-1], 2) if not pd.isna(sma_200.iloc[-1]) else None,
            "rsi": round(rsi.iloc[-1], 2) if not pd.isna(rsi.iloc[-1]) else None,
            "macd": round(macd.iloc[-1], 2) if not pd.isna(macd.iloc[-1]) else None,
            "macd_signal": round(signal.iloc[-1], 2) if not pd.isna(signal.iloc[-1]) else None,
            "bb_upper": round(bb_upper.iloc[-1], 2) if not pd.isna(bb_upper.iloc[-1]) else None,
            "bb_lower": round(bb_lower.iloc[-1], 2) if not pd.isna(bb_lower.iloc[-1]) else None,
        }
    
    def _calculate_rsi(self, close: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI"""
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, close: pd.Series, fast=12, slow=26, signal=9):
        """计算MACD"""
        ema_fast = close.ewm(span=fast).mean()
        ema_slow = close.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    
    def _calculate_bollinger_bands(self, close: pd.Series, period=20, std=2):
        """计算布林带"""
        middle = close.rolling(window=period).mean()
        std_dev = close.rolling(window=period).std()
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        return upper, middle, lower
    
    def _generate_signals(self, indicators: Dict[str, Any]) -> Dict[str, str]:
        """生成交易信号"""
        signals = {}
        
        if indicators['rsi']:
            if indicators['rsi'] > 70:
                signals['rsi'] = "超买"
            elif indicators['rsi'] < 30:
                signals['rsi'] = "超卖"
            else:
                signals['rsi'] = "中性"
        
        if indicators['sma_50'] and indicators['sma_200']:
            if indicators['sma_50'] > indicators['sma_200']:
                signals['trend'] = "多头"
            else:
                signals['trend'] = "空头"
        
        if indicators['macd'] and indicators['macd_signal']:
            if indicators['macd'] > indicators['macd_signal']:
                signals['macd'] = "看涨"
            else:
                signals['macd'] = "看跌"
        
        return signals
    
    def _generate_summary(self, indicators: Dict[str, Any], signals: Dict[str, str]) -> str:
        """生成分析摘要"""
        summary_parts = []
        
        if indicators['current_price']:
            summary_parts.append(f"价格: ${indicators['current_price']}")
        
        if 'rsi' in signals:
            summary_parts.append(f"RSI {signals['rsi']}")
        
        if 'trend' in signals:
            summary_parts.append(f"趋势: {signals['trend']}")
        
        if 'macd' in signals:
            summary_parts.append(f"MACD {signals['macd']}")
        
        return " | ".join(summary_parts)
