from langchain.tools import BaseTool
import yfinance as yf

class StockDataTool(BaseTool):
    name = "stock_data_tool"
    description = "获取股票基本面数据，如PE、ROE、市值、营收等。输入：股票代码（如 'AAPL'）"

    def _run(self, ticker: str) -> str:
        try:
            stock = yf.Ticker(ticker.strip().upper())
            info = stock.info
            pe = info.get('trailingPE', 'N/A')
            roe = info.get('returnOnEquity', 'N/A')
            if roe != 'N/A':
                roe = round(roe * 100, 2)
            market_cap = info.get('marketCap', 'N/A')
            if market_cap != 'N/A':
                market_cap = f"{market_cap / 1e9:.2f}B"
            return f"股票 {ticker}: PE={pe}, ROE={roe}%, 市值={market_cap}"
        except Exception as e:
            return f"获取 {ticker} 基本面数据失败: {str(e)}"

    async def _arun(self, ticker: str) -> str:
        raise NotImplementedError("不支持异步")
