from langchain.tools import BaseTool
import yfinance as yf
import pandas as pd

def calculate_rsi(prices, window=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def check_macd_cross(prices):
    exp1 = prices.ewm(span=12).mean()
    exp2 = prices.ewm(span=26).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9).mean()
    prev_diff = macd.iloc[-2] - signal.iloc[-2]
    curr_diff = macd.iloc[-1] - signal.iloc[-1]
    if prev_diff < 0 and curr_diff > 0:
        return "金叉"
    elif prev_diff > 0 and curr_diff < 0:
        return "死叉"
    else:
        return "无交叉"

class TechnicalIndicatorTool(BaseTool):
    name = "technical_indicator_tool"
    description = "获取股票技术指标，如RSI、MACD金叉死叉等。输入：股票代码（如 'TSLA'）"

    def _run(self, ticker: str) -> str:
        try:
            data = yf.download(ticker.strip().upper(), period="3mo")
            if data.empty:
                return f"{ticker} 无足够价格数据"
            close = data['Close']
            rsi = calculate_rsi(close)
            macd_status = check_macd_cross(close)
            return f"股票 {ticker}: RSI={rsi:.2f}, MACD={macd_status}"
        except Exception as e:
            return f"计算 {ticker} 技术指标失败: {str(e)}"

    async def _arun(self, ticker: str) -> str:
        raise NotImplementedError("不支持异步")
