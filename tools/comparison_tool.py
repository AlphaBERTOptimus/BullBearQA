from langchain.tools import BaseTool
import yfinance as yf
import pandas as pd
from typing import List, Dict
import time

class ComparisonTool(BaseTool):
    name = "comparison_tool"
    description = "比较多只股票的关键指标。输入：用逗号分隔的股票代码列表，如 'AAPL,MSFT,GOOGL'"
    
    # 缓存
    _cache = {}
    _cache_ttl = 300
    
    def _run(self, tickers_str: str) -> str:
        try:
            # 解析股票代码
            tickers = [t.strip().upper() for t in tickers_str.split(',')]
            
            if len(tickers) < 2:
                return "❌ 请至少提供2只股票进行比较"
            
            if len(tickers) > 5:
                return "⚠️ 最多支持同时比较5只股票，已自动截取前5只"
                tickers = tickers[:5]
            
            # 获取所有股票数据
            comparison_data = []
            
            for ticker in tickers:
                data = self._get_stock_metrics(ticker)
                if data:
                    comparison_data.append(data)
                else:
                    comparison_data.append({'ticker': ticker, 'error': True})
            
            # 格式化输出
            return self._format_comparison(comparison_data)
            
        except Exception as e:
            return f"❌ 比较股票时出错: {str(e)}"
    
    def _get_stock_metrics(self, ticker: str) -> Dict:
        """获取单只股票的关键指标"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info or 'symbol' not in info:
                return None
            
            # 提取关键指标
            metrics = {
                'ticker': ticker,
                'name': info.get('shortName', 'N/A'),
                'price': info.get('currentPrice', info.get('regularMarketPrice', 'N/A')),
                'market_cap': info.get('marketCap', 'N/A'),
                'pe': info.get('trailingPE', info.get('forwardPE', 'N/A')),
                'pb': info.get('priceToBook', 'N/A'),
                'roe': info.get('returnOnEquity', 'N/A'),
                'profit_margin': info.get('profitMargins', 'N/A'),
                'revenue_growth': info.get('revenueGrowth', 'N/A'),
                'debt_to_equity': info.get('debtToEquity', 'N/A'),
                'dividend_yield': info.get('dividendYield', 'N/A'),
                'beta': info.get('beta', 'N/A'),
                'error': False
            }
            
            # 计算简单的技术指标
            try:
                hist = stock.history(period="1mo")
                if not hist.empty:
                    # 月度涨跌幅
                    month_return = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
                    metrics['month_return'] = month_return
                else:
                    metrics['month_return'] = 'N/A'
            except:
                metrics['month_return'] = 'N/A'
            
            return metrics
            
        except Exception as e:
            return None
    
    def _format_comparison(self, data: List[Dict]) -> str:
        """格式化对比输出"""
        
        valid_data = [d for d in data if not d.get('error')]
        error_tickers = [d['ticker'] for d in data if d.get('error')]
        
        if not valid_data:
            return "❌ 无法获取任何股票的有效数据"
        
        output = "📊 **股票对比分析**\n\n"
        
        # 基本信息对比
        output += "**基本信息：**\n\n"
        output += "| 股票代码 | 公司名称 | 当前价格 | 市值 |\n"
        output += "|---------|---------|---------|------|\n"
        
        for d in valid_data:
            price = f"${d['price']:.2f}" if isinstance(d['price'], (int, float)) else d['price']
            market_cap = self._format_large_number(d['market_cap'])
            output += f"| {d['ticker']} | {d['name'][:15]} | {price} | {market_cap} |\n"
        
        output += "\n"
        
        # 估值指标对比
        output += "**估值指标：**\n\n"
        output += "| 股票 | P/E | P/B | 股息率 | Beta |\n"
        output += "|-----|-----|-----|--------|------|\n"
        
        for d in valid_data:
            pe = f"{d['pe']:.2f}" if isinstance(d['pe'], (int, float)) else "N/A"
            pb = f"{d['pb']:.2f}" if isinstance(d['pb'], (int, float)) else "N/A"
            div_yield = f"{d['dividend_yield']*100:.2f}%" if isinstance(d['dividend_yield'], (int, float)) else "N/A"
            beta = f"{d['beta']:.2f}" if isinstance(d['beta'], (int, float)) else "N/A"
            
            output += f"| {d['ticker']} | {pe} | {pb} | {div_yield} | {beta} |\n"
        
        output += "\n"
        
        # 盈利能力对比
        output += "**盈利能力：**\n\n"
        output += "| 股票 | ROE | 利润率 | 营收增长率 | 月度涨跌 |\n"
        output += "|-----|-----|--------|-----------|----------|\n"
        
        for d in valid_data:
            roe = f"{d['roe']*100:.2f}%" if isinstance(d['roe'], (int, float)) else "N/A"
            margin = f"{d['profit_margin']*100:.2f}%" if isinstance(d['profit_margin'], (int, float)) else "N/A"
            growth = f"{d['revenue_growth']*100:.2f}%" if isinstance(d['revenue_growth'], (int, float)) else "N/A"
            month_ret = f"{d['month_return']:+.2f}%" if isinstance(d['month_return'], (int, float)) else "N/A"
            
            output += f"| {d['ticker']} | {roe} | {margin} | {growth} | {month_ret} |\n"
        
        output += "\n"
        
        # 财务健康对比
        output += "**财务健康：**\n\n"
        output += "| 股票 | 资产负债率 (D/E) |\n"
        output += "|-----|------------------|\n"
        
        for d in valid_data:
            de = f"{d['debt_to_equity']:.2f}" if isinstance(d['debt_to_equity'], (int, float)) else "N/A"
            output += f"| {d['ticker']} | {de} |\n"
        
        output += "\n"
        
        # 智能分析
        output += "💡 **对比分析：**\n\n"
        
        # 找出最佳指标
        best_pe = self._find_best(valid_data, 'pe', lower_is_better=True)
        best_roe = self._find_best(valid_data, 'roe', lower_is_better=False)
        best_growth = self._find_best(valid_data, 'revenue_growth', lower_is_better=False)
        best_margin = self._find_best(valid_data, 'profit_margin', lower_is_better=False)
        best_month = self._find_best(valid_data, 'month_return', lower_is_better=False)
        
        if best_pe:
            output += f"- **估值最低 (P/E):** {best_pe['ticker']} ({best_pe['pe']:.2f})\n"
        if best_roe:
            output += f"- **盈利能力最强 (ROE):** {best_roe['ticker']} ({best_roe['roe']*100:.2f}%)\n"
        if best_growth:
            output += f"- **增长最快 (营收):** {best_growth['ticker']} ({best_growth['revenue_growth']*100:.2f}%)\n"
        if best_margin:
            output += f"- **利润率最高:** {best_margin['ticker']} ({best_margin['profit_margin']*100:.2f}%)\n"
        if best_month:
            output += f"- **近期表现最佳:** {best_month['ticker']} ({best_month['month_return']:+.2f}%)\n"
        
        # 综合评分（简化版）
        output += "\n**综合建议：**\n"
        scores = self._calculate_scores(valid_data)
        
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        for rank, (ticker, score) in enumerate(sorted_scores, 1):
            stars = "⭐" * min(5, int(score/20))
            output += f"{rank}. {ticker}: {stars} ({score:.0f}分)\n"
        
        if error_tickers:
            output += f"\n⚠️ 以下股票数据获取失败: {', '.join(error_tickers)}\n"
        
        return output.strip()
    
    def _format_large_number(self, value) -> str:
        """格式化大数字"""
        if value == 'N/A' or value is None:
            return 'N/A'
        try:
            value = float(value)
            if value >= 1e12:
                return f"${value/1e12:.2f}T"
            elif value >= 1e9:
                return f"${value/1e9:.2f}B"
            elif value >= 1e6:
                return f"${value/1e6:.2f}M"
            return f"${value:,.0f}"
        except:
            return str(value)
    
    def _find_best(self, data: List[Dict], metric: str, lower_is_better: bool = False) -> Dict:
        """找出某个指标最佳的股票"""
        valid = [d for d in data if isinstance(d.get(metric), (int, float)) and d.get(metric) != 'N/A']
        
        if not valid:
            return None
        
        if lower_is_better:
            return min(valid, key=lambda x: x[metric])
        else:
            return max(valid, key=lambda x: x[metric])
    
    def _calculate_scores(self, data: List[Dict]) -> Dict[str, float]:
        """计算综合评分（简化版）"""
        scores = {}
        
        metrics = {
            'pe': {'weight': 15, 'lower_is_better': True},
            'roe': {'weight': 25, 'lower_is_better': False},
            'profit_margin': {'weight': 20, 'lower_is_better': False},
            'revenue_growth': {'weight': 20, 'lower_is_better': False},
            'month_return': {'weight': 20, 'lower_is_better': False}
        }
        
        for d in data:
            ticker = d['ticker']
            score = 0
            
            for metric, config in metrics.items():
                value = d.get(metric)
                if isinstance(value, (int, float)) and value != 'N/A':
                    # 归一化分数（0-100）
                    all_values = [x.get(metric) for x in data if isinstance(x.get(metric), (int, float))]
                    
                    if all_values:
                        if config['lower_is_better']:
                            normalized = 100 * (1 - (value - min(all_values)) / (max(all_values) - min(all_values) + 0.001))
                        else:
                            normalized = 100 * (value - min(all_values)) / (max(all_values) - min(all_values) + 0.001)
                        
                        score += normalized * config['weight'] / 100
            
            scores[ticker] = score
        
        return scores
    
    async def _arun(self, tickers_str: str) -> str:
        return self._run(tickers_str)
