"""
技术面分析Agent
"""
from typing import Optional
from agents.base_agent import BaseAgent
from tools.technical_indicator_tool import TechnicalIndicatorTool


class TechnicalAgent(BaseAgent):
    """技术面分析师Agent"""
    
    def __init__(self, llm=None):
        super().__init__(name="Technical Analyst", llm=llm)
        self.tech_tool = TechnicalIndicatorTool()
    
    def run(self, query: str) -> str:
        """
        执行技术面分析
        
        Args:
            query: 用户查询
            
        Returns:
            分析结果
        """
        ticker = self._extract_ticker(query)
        
        if not ticker:
            return "❌ 无法识别股票代码"
        
        # 获取技术指标
        indicators = self.tech_tool.get_technical_indicators(ticker)
        
        if not indicators:
            return f"❌ 无法获取 {ticker} 的技术指标数据"
        
        return self._generate_report(ticker, indicators)
    
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
    
    def _generate_report(self, ticker: str, indicators: dict) -> str:
        """生成技术分析报告"""
        report = f"""
## 📈 {ticker} 技术面分析

### 📊 动量指标
"""
        
        # RSI分析
        rsi = indicators.get('rsi', {}).get('value', 'N/A')
        if rsi != 'N/A':
            rsi_signal = indicators.get('rsi', {}).get('signal', '')
            report += f"- **RSI(14)**: {rsi:.2f} {rsi_signal}\n"
        
        # MACD分析
        macd_signal = indicators.get('macd', {}).get('signal', 'N/A')
        if macd_signal != 'N/A':
            report += f"- **MACD**: {macd_signal}\n"
        
        # 趋势指标
        report += "\n### 📉 趋势指标\n"
        
        ma20 = indicators.get('ma20', 'N/A')
        ma50 = indicators.get('ma50', 'N/A')
        current_price = indicators.get('current_price', 'N/A')
        
        if ma20 != 'N/A':
            report += f"- **MA20**: ${ma20:.2f}\n"
        if ma50 != 'N/A':
            report += f"- **MA50**: ${ma50:.2f}\n"
        if current_price != 'N/A':
            report += f"- **当前价格**: ${current_price:.2f}\n"
        
        # 趋势判断
        if all(x != 'N/A' for x in [current_price, ma20, ma50]):
            if current_price > ma20 > ma50:
                report += "\n✅ **强势上涨趋势**：价格位于MA20和MA50之上\n"
            elif current_price < ma20 < ma50:
                report += "\n⚠️ **弱势下跌趋势**：价格位于MA20和MA50之下\n"
            else:
                report += "\n📊 **震荡行情**：均线交织\n"
        
        # 综合信号
        report += "\n### 🎯 综合交易信号\n"
        signal = self._generate_signal(indicators)
        report += signal
        
        return report
    
    def _generate_signal(self, indicators: dict) -> str:
        """生成综合交易信号"""
        signals = []
        
        # RSI信号
        rsi = indicators.get('rsi', {}).get('value')
        if rsi:
            if rsi < 30:
                signals.append("买入")
            elif rsi > 70:
                signals.append("卖出")
        
        # MACD信号
        macd_signal = indicators.get('macd', {}).get('signal', '')
        if '看涨' in macd_signal or '金叉' in macd_signal:
            signals.append("买入")
        elif '看跌' in macd_signal or '死叉' in macd_signal:
            signals.append("卖出")
        
        # 综合判断
        if signals.count("买入") >= 2:
            return "🟢 **建议买入**"
        elif signals.count("卖出") >= 2:
            return "🔴 **建议卖出**"
        else:
            return "🟡 **建议持有/观望**"
