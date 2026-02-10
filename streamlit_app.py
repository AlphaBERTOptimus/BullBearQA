"""技术分析代理"""
import yfinance as yf
import pandas as pd
from .base_agent import BaseAgent


class TechnicalAgent(BaseAgent):
    """技术分析代理"""
    
    def __init__(self, llm):
        super().__init__(llm, name="TechnicalAgent")
    
    def run(self, query: str) -> str:
        """执行技术分析"""
        try:
            ticker = self._extract_ticker(query)
            if not ticker:
                return "无法识别股票代码"
            
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            
            if df.empty:
                return f"无法获取 {ticker} 的历史数据"
            
            indicators = self._calculate_indicators(df)
            signals = self._generate_signals(indicators)
            
            prompt = self._build_english_prompt(ticker, indicators, signals)
            
            result = self._safe_llm_invoke(prompt)
            
            if "LLM call failed" in result:
                return self._fallback_analysis(ticker, indicators, signals)
            
            return result
            
        except Exception as e:
            return f"技术分析失败: {str(e)}"
    
    def _build_english_prompt(self, ticker: str, indicators: dict, signals: dict) -> str:
        """构建英文提示词 - 完全修复版"""
        # 提取指标值
        current_price = indicators.get('current_price', 0)
        sma_20 = indicators.get('sma_20')
        sma_50 = indicators.get('sma_50')
        sma_200 = indicators.get('sma_200')
        rsi = indicators.get('rsi')
        bb_upper = indicators.get('bb_upper')
        bb_lower = indicators.get('bb_lower')
        
        # 安全格式化（分别处理每个值）
        def format_price(val):
            return f"${val:.2f}" if val is not None else 'N/A'
        
        def format_number(val):
            return f"{val:.1f}" if val is not None else 'N/A'
        
        return f"""You are a professional technical analyst. Provide a concise technical analysis of {ticker} in Chinese.

Price Info:
- Current Price: {format_price(current_price)}
- SMA 20: {format_price(sma_20)}
- SMA 50: {format_price(sma_50)}
- SMA 200: {format_price(sma_200)}

Momentum Indicators:
- RSI(14): {format_number(rsi)} - {signals.get('rsi', 'N/A')}
- MACD: {signals.get('macd', 'N/A')}

Trend: {signals.get('trend', 'N/A')}

Bollinger Bands:
- Upper: {format_price(bb_upper)}
- Lower: {format_price(bb_lower)}

Please provide in Chinese (within 150 characters):
1. Technical overview
2. Short-term trend forecast
3. Key support and resistance levels
4. Trading recommendation

Respond in professional but easy-to-understand Chinese."""
    
    def _fallback_analysis(self, ticker: str, indicators: dict, signals: dict) -> str:
        """备用分析"""
        current_price = indicators.get('current_price', 0)
        rsi = indicators.get('rsi')
        rsi_str = f"{rsi:.1f}" if rsi is not None else 'N/A'
        
        return f"""【技术分析 - {ticker}】

当前价格: ${current_price:.2f}

技术指标:
- RSI: {rsi_str} ({signals.get('rsi', 'N/A')})
- 趋势: {signals.get('trend', 'N/A')}
- MACD: {signals.get('macd', 'N/A')}

综合评价: 短期{'超买，建议观望' if signals.get('rsi') == '超买' else '超卖，可能反弹' if signals.get('rsi') == '超卖' else '震荡中'}，整体趋势{signals.get('trend', 'N/A')}。"""
    
    def _extract_ticker(self, query: str) -> str:
        """提取股票代码"""
        import re
        
        common_stocks = {
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA',
            'AMD', 'NFLX', 'TSM', 'V', 'JPM', 'BABA', 'MU'
        }
        
        query_upper = query.upper()
        
        for stock in common_stocks:
            if stock in query_upper:
                return stock
        
        matches = re.findall(r'\b([A-Z]{2,5})\b', query_upper)
        common_words = {'THE', 'RSI', 'PE', 'VS', 'HOW', 'WHAT'}
        
        for match in matches:
            if match not in common_words:
                return match
        
        return None
    
    def _calculate_indicators(self, df: pd.DataFrame) -> dict:
        """计算技术指标"""
        close = df['Close']
        
        sma_20 = close.rolling(20).mean()
        sma_50 = close.rolling(50).mean()
        sma_200 = close.rolling(200).mean()
        
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        ema_12 = close.ewm(span=12).mean()
        ema_26 = close.ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9).mean()
        
        bb_middle = close.rolling(20).mean()
        bb_std = close.rolling(20).std()
        bb_upper = bb_middle + (2 * bb_std)
        bb_lower = bb_middle - (2 * bb_std)
        
        return {
            "current_price": float(close.iloc[-1]),
            "sma_20": float(sma_20.iloc[-1]) if not pd.isna(sma_20.iloc[-1]) else None,
            "sma_50": float(sma_50.iloc[-1]) if not pd.isna(sma_50.iloc[-1]) else None,
            "sma_200": float(sma_200.iloc[-1]) if not pd.isna(sma_200.iloc[-1]) else None,
            "rsi": float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None,
            "macd": float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else None,
            "macd_signal": float(signal.iloc[-1]) if not pd.isna(signal.iloc[-1]) else None,
            "bb_upper": float(bb_upper.iloc[-1]) if not pd.isna(bb_upper.iloc[-1]) else None,
            "bb_lower": float(bb_lower.iloc[-1]) if not pd.isna(bb_lower.iloc[-1]) else None,
        }
    
    def _generate_signals(self, indicators: dict) -> dict:
        """生成交易信号"""
        signals = {}
        
        rsi = indicators.get('rsi')
        if rsi:
            if rsi > 70:
                signals['rsi'] = "超买"
            elif rsi < 30:
                signals['rsi'] = "超卖"
            else:
                signals['rsi'] = "中性"
        
        sma_50 = indicators.get('sma_50')
        sma_200 = indicators.get('sma_200')
        if sma_50 and sma_200:
            signals['trend'] = "多头" if sma_50 > sma_200 else "空头"
        
        macd = indicators.get('macd')
        macd_signal = indicators.get('macd_signal')
        if macd and macd_signal:
            signals['macd'] = "看涨" if macd > macd_signal else "看跌"
        
        return signals
