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
                return "❌ 无法识别股票代码"
            
            # 获取历史数据
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            
            if df.empty:
                return f"❌ 无法获取 {ticker} 的历史数据"
            
            # 计算技术指标
            indicators = self._calculate_indicators(df)
            signals = self._generate_signals(indicators)
            
            # 使用 LLM 生成分析
            analysis_prompt = f"""
你是一位专业的技术分析师。请基于以下技术指标对 {ticker} 进行分析：

**价格信息：**
- 当前价格: ${indicators['current_price']:.2f}
- 20日均线: ${indicators.get('sma_20', 'N/A')}
- 50日均线: ${indicators.get('sma_50', 'N/A')}
- 200日均线: ${indicators.get('sma_200', 'N/A')}

**动量指标：**
- RSI(14): {indicators.get('rsi', 'N/A')} - {signals.get('rsi', 'N/A')}
- MACD: {indicators.get('macd', 'N/A')} - {signals.get('macd', 'N/A')}

**趋势信号：**
- 整体趋势: {signals.get('trend', 'N/A')}

**布林带：**
- 上轨: ${indicators.get('bb_upper', 'N/A')}
- 下轨: ${indicators.get('bb_lower', 'N/A')}

请提供：
1. 技术面综合评价
2. 短期走势预判
3. 关键支撑位和阻力位
4. 交易建议

保持专业但易懂的语言。
            """
            
            response = self.llm.invoke(analysis_prompt)
            return response.content
            
        except Exception as e:
            return f"❌ 技术分析失败: {str(e)}"
    
    def _extract_ticker(self, query: str) -> str:
        """提取股票代码"""
        import re
        common_stocks = {
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA',
            'AMD', 'NFLX', 'TSM', 'V', 'JPM'
        }
        
        query_upper = query.upper()
        for stock in common_stocks:
            if stock in query_upper:
                return stock
        
        matches = re.findall(r'\b([A-Z]{2,5})\b', query_upper)
        common_words = {'THE', 'RSI', 'PE', 'VS'}
        for match in matches:
            if match not in common_words:
                return match
        return None
    
    def _calculate_indicators(self, df: pd.DataFrame) -> dict:
        """计算技术指标"""
        close = df['Close']
        
        # 移动平均
        sma_20 = close.rolling(20).mean()
        sma_50 = close.rolling(50).mean()
        sma_200 = close.rolling(200).mean()
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = close.ewm(span=12).mean()
        ema_26 = close.ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9).mean()
        
        # 布林带
        bb_middle = close.rolling(20).mean()
        bb_std = close.rolling(20).std()
        bb_upper = bb_middle + (2 * bb_std)
        bb_lower = bb_middle - (2 * bb_std)
        
        return {
            "current_price": close.iloc[-1],
            "sma_20": sma_20.iloc[-1] if not pd.isna(sma_20.iloc[-1]) else None,
            "sma_50": sma_50.iloc[-1] if not pd.isna(sma_50.iloc[-1]) else None,
            "sma_200": sma_200.iloc[-1] if not pd.isna(sma_200.iloc[-1]) else None,
            "rsi": rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else None,
            "macd": macd.iloc[-1] if not pd.isna(macd.iloc[-1]) else None,
            "macd_signal": signal.iloc[-1] if not pd.isna(signal.iloc[-1]) else None,
            "bb_upper": bb_upper.iloc[-1] if not pd.isna(bb_upper.iloc[-1]) else None,
            "bb_lower": bb_lower.iloc[-1] if not pd.isna(bb_lower.iloc[-1]) else None,
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
