# tools/stock_data_tool.py
import yfinance as yf
import time
from functools import lru_cache

@lru_cache(maxsize=100)
def get_stock_data(ticker: str, max_retries=3):
    """获取股票基本面数据,带重试机制"""
    for attempt in range(max_retries):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 验证数据是否有效
            if info and 'currentPrice' in info:
                return {
                    'pe_ratio': info.get('trailingPE', 'N/A'),
                    'forward_pe': info.get('forwardPE', 'N/A'),
                    'pb_ratio': info.get('priceToBook', 'N/A'),
                    'roe': info.get('returnOnEquity', 'N/A'),
                    'profit_margin': info.get('profitMargins', 'N/A'),
                    'market_cap': info.get('marketCap', 'N/A'),
                    'current_price': info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
                }
            else:
                # 如果info不完整,尝试用替代方法
                return get_stock_data_alternative(ticker)
                
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
                continue
            else:
                # 最后一次尝试失败,使用备用数据源
                return get_stock_data_alternative(ticker)
    
    return None

def get_stock_data_alternative(ticker: str):
    """备用数据获取方法"""
    try:
        stock = yf.Ticker(ticker)
        
        # 方法1: 使用fast_info(更稳定)
        try:
            fast_info = stock.fast_info
            hist = stock.history(period="5d")
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                return {
                    'pe_ratio': fast_info.get('trailing_pe', 'N/A'),
                    'forward_pe': fast_info.get('forward_pe', 'N/A'),
                    'market_cap': fast_info.get('market_cap', 'N/A'),
                    'current_price': current_price,
                    'pb_ratio': 'N/A',  # fast_info不提供
                    'roe': 'N/A',
                    'profit_margin': 'N/A'
                }
        except:
            pass
        
        # 方法2: 最小化数据集
        hist = stock.history(period="1d")
        if not hist.empty:
            return {
                'current_price': hist['Close'].iloc[-1],
                'pe_ratio': 'N/A',
                'forward_pe': 'N/A',
                'pb_ratio': 'N/A',
                'roe': 'N/A',
                'profit_margin': 'N/A',
                'market_cap': 'N/A'
            }
            
    except Exception as e:
        print(f"Alternative method failed: {e}")
    
    return None
