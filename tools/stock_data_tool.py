"""
股票基本面数据获取工具
支持yfinance API，带重试和降级机制
"""
import yfinance as yf
from functools import lru_cache
import time
from typing import Dict, Optional, Any


class StockDataTool:
    """股票基本面数据获取工具类"""
    
    def __init__(self):
        self._cache_ttl = 300  # 5分钟缓存
        
    @lru_cache(maxsize=100)
    def get_stock_data(self, ticker: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        获取股票基本面数据
        
        Args:
            ticker: 股票代码 (如 'AAPL')
            max_retries: 最大重试次数
            
        Returns:
            包含股票数据的字典，失败返回None
        """
        ticker = ticker.upper().strip()
        
        for attempt in range(max_retries):
            try:
                stock = yf.Ticker(ticker)
                
                # 策略1: 尝试获取完整info
                try:
                    info = stock.info
                    if info and self._is_valid_info(info):
                        return self._parse_stock_info(info, ticker)
                except Exception as e:
                    print(f"Info fetch failed: {e}")
                
                # 策略2: 使用fast_info + history
                return self._get_fallback_data(stock, ticker)
                
            except Exception as e:
                print(f"Attempt {attempt + 1}/{max_retries} failed for {ticker}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    # 最后尝试只获取价格
                    return self._get_minimal_data(stock, ticker)
        
        return None
    
    def _is_valid_info(self, info: dict) -> bool:
        """验证info数据是否有效"""
        required_keys = ['symbol', 'currentPrice', 'regularMarketPrice']
        return any(key in info for key in required_keys) and len(info) > 5
    
    def _parse_stock_info(self, info: dict, ticker: str) -> Dict[str, Any]:
        """解析完整的stock.info数据"""
        return {
            'ticker': ticker,
            'name': info.get('longName', info.get('shortName', ticker)),
            'current_price': info.get('currentPrice', info.get('regularMarketPrice', 'N/A')),
            'market_cap': info.get('marketCap', 'N/A'),
            
            # 估值指标
            'pe_ratio': info.get('trailingPE', 'N/A'),
            'forward_pe': info.get('forwardPE', 'N/A'),
            'pb_ratio': info.get('priceToBook', 'N/A'),
            'ps_ratio': info.get('priceToSalesTrailing12Months', 'N/A'),
            
            # 盈利能力
            'roe': info.get('returnOnEquity', 'N/A'),
            'roa': info.get('returnOnAssets', 'N/A'),
            'profit_margin': info.get('profitMargins', 'N/A'),
            'operating_margin': info.get('operatingMargins', 'N/A'),
            
            # 财务健康
            'debt_to_equity': info.get('debtToEquity', 'N/A'),
            'current_ratio': info.get('currentRatio', 'N/A'),
            'quick_ratio': info.get('quickRatio', 'N/A'),
            
            # 收入与利润
            'total_revenue': info.get('totalRevenue', 'N/A'),
            'revenue_per_share': info.get('revenuePerShare', 'N/A'),
            'eps': info.get('trailingEps', 'N/A'),
            'forward_eps': info.get('forwardEps', 'N/A'),
            
            # 股息
            'dividend_yield': info.get('dividendYield', 'N/A'),
            'payout_ratio': info.get('payoutRatio', 'N/A'),
            
            # 其他
            'beta': info.get('beta', 'N/A'),
            '52_week_high': info.get('fiftyTwoWeekHigh', 'N/A'),
            '52_week_low': info.get('fiftyTwoWeekLow', 'N/A'),
            'volume': info.get('volume', 'N/A'),
            'avg_volume': info.get('averageVolume', 'N/A'),
        }
    
    def _get_fallback_data(self, stock, ticker: str) -> Optional[Dict[str, Any]]:
        """降级方案：使用fast_info + history"""
        try:
            # 获取历史价格
            hist = stock.history(period="5d")
            if hist.empty:
                return None
            
            current_price = float(hist['Close'].iloc[-1])
            volume = int(hist['Volume'].iloc[-1])
            
            # 尝试获取fast_info
            data = {
                'ticker': ticker,
                'name': ticker,
                'current_price': current_price,
                'volume': volume,
            }
            
            try:
                fast_info = stock.fast_info
                data.update({
                    'market_cap': getattr(fast_info, 'market_cap', 'N/A'),
                    'pe_ratio': getattr(fast_info, 'trailing_pe', 'N/A'),
                    '52_week_high': getattr(fast_info, 'year_high', 'N/A'),
                    '52_week_low': getattr(fast_info, 'year_low', 'N/A'),
                })
            except:
                pass
            
            # 填充缺失字段为N/A
            default_fields = [
                'forward_pe', 'pb_ratio', 'ps_ratio', 'roe', 'roa',
                'profit_margin', 'operating_margin', 'debt_to_equity',
                'current_ratio', 'quick_ratio', 'total_revenue',
                'revenue_per_share', 'eps', 'forward_eps',
                'dividend_yield', 'payout_ratio', 'beta', 'avg_volume'
            ]
            for field in default_fields:
                if field not in data:
                    data[field] = 'N/A'
            
            return data
            
        except Exception as e:
            print(f"Fallback data fetch failed: {e}")
            return None
    
    def _get_minimal_data(self, stock, ticker: str) -> Optional[Dict[str, Any]]:
        """最小数据集：仅价格"""
        try:
            hist = stock.history(period="1d")
            if hist.empty:
                return None
            
            return {
                'ticker': ticker,
                'name': ticker,
                'current_price': float(hist['Close'].iloc[-1]),
                'volume': int(hist['Volume'].iloc[-1]),
                # 其他字段全部N/A
                **{k: 'N/A' for k in [
                    'market_cap', 'pe_ratio', 'forward_pe', 'pb_ratio', 'ps_ratio',
                    'roe', 'roa', 'profit_margin', 'operating_margin',
                    'debt_to_equity', 'current_ratio', 'quick_ratio',
                    'total_revenue', 'revenue_per_share', 'eps', 'forward_eps',
                    'dividend_yield', 'payout_ratio', 'beta',
                    '52_week_high', '52_week_low', 'avg_volume'
                ]}
            }
        except Exception as e:
            print(f"Minimal data fetch failed: {e}")
            return None
    
    def get_financial_ratios(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        获取财务比率（向后兼容接口）
        
        Args:
            ticker: 股票代码
            
        Returns:
            财务比率字典
        """
        data = self.get_stock_data(ticker)
        if not data:
            return None
        
        return {
            'pe': data.get('pe_ratio', 'N/A'),
            'pb': data.get('pb_ratio', 'N/A'),
            'ps': data.get('ps_ratio', 'N/A'),
            'roe': data.get('roe', 'N/A'),
            'roa': data.get('roa', 'N/A'),
            'debt_equity': data.get('debt_to_equity', 'N/A'),
            'current_ratio': data.get('current_ratio', 'N/A'),
            'profit_margin': data.get('profit_margin', 'N/A'),
        }
    
    def format_value(self, value: Any) -> str:
        """格式化显示值"""
        if value == 'N/A' or value is None:
            return 'N/A'
        
        if isinstance(value, (int, float)):
            # 大数值格式化 (市值、收入等)
            if value > 1_000_000_000_000:
                return f"${value/1_000_000_000_000:.2f}T"
            elif value > 1_000_000_000:
                return f"${value/1_000_000_000:.2f}B"
            elif value > 1_000_000:
                return f"${value/1_000_000:.2f}M"
            elif value > 1000:
                return f"${value/1000:.2f}K"
            else:
                return f"{value:.2f}"
        
        return str(value)


# ========== 向后兼容：函数式接口 ==========

_tool_instance = StockDataTool()

def get_stock_data(ticker: str) -> Optional[Dict[str, Any]]:
    """
    函数式接口：获取股票数据
    
    Args:
        ticker: 股票代码
        
    Returns:
        股票数据字典
    """
    return _tool_instance.get_stock_data(ticker)


def get_financial_ratios(ticker: str) -> Optional[Dict[str, Any]]:
    """
    函数式接口：获取财务比率
    
    Args:
        ticker: 股票代码
        
    Returns:
        财务比率字典
    """
    return _tool_instance.get_financial_ratios(ticker)


# ========== 主程序测试 ==========

if __name__ == "__main__":
    # 测试代码
    tool = StockDataTool()
    
    test_tickers = ['AAPL', 'TSLA', 'MSFT']
    
    for ticker in test_tickers:
        print(f"\n{'='*50}")
        print(f"Testing {ticker}")
        print('='*50)
        
        data = tool.get_stock_data(ticker)
        
        if data:
            print(f"✅ 成功获取 {ticker} 数据")
            print(f"当前价格: {tool.format_value(data.get('current_price'))}")
            print(f"市盈率: {data.get('pe_ratio')}")
            print(f"ROE: {data.get('roe')}")
            print(f"市值: {tool.format_value(data.get('market_cap'))}")
        else:
            print(f"❌ 获取 {ticker} 数据失败")
