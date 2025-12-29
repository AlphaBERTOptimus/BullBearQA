"""
K线图可视化模块
提供交互式股价图表、对比图表等功能
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

class CandlestickChart:
    """交互式K线图生成器"""
    
    def __init__(self):
        self.colors = {
            'background': '#0e1117',
            'grid': '#2d3436',
            'up': '#26a69a',      # 绿色（涨）
            'down': '#ef5350',    # 红色（跌）
            'ma20': '#ffa726',    # 橙色
            'ma50': '#ab47bc',    # 紫色
            'volume': 'rgba(100,149,237,0.5)'
        }
    
    def create_chart(self, ticker: str, period: str = "3mo"):
        """
        生成完整的K线图（包含成交量和均线）
        
        Args:
            ticker: 股票代码（如 'AAPL', 'NVDA'）
            period: 时间周期
                - 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        
        Returns:
            plotly.graph_objects.Figure 或 None（如果数据获取失败）
        """
        try:
            # 获取股票数据
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)
            
            if df.empty:
                print(f"[ERROR] 无法获取 {ticker} 的数据")
                return None
            
            # 计算技术指标
            df = self._calculate_indicators(df)
            
            # 创建子图（K线图 + 成交量）
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.7, 0.3],
                subplot_titles=(f'{ticker} 股价走势', '成交量')
            )
            
            # 1. 添加K线图
            fig.add_trace(
                go.Candlestick(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name=ticker,
                    increasing_line_color=self.colors['up'],
                    decreasing_line_color=self.colors['down']
                ),
                row=1, col=1
            )
            
            # 2. 添加20日均线
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['MA20'],
                    name='MA20',
                    line=dict(color=self.colors['ma20'], width=1.5),
                    opacity=0.8
                ),
                row=1, col=1
            )
            
            # 3. 添加50日均线
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['MA50'],
                    name='MA50',
                    line=dict(color=self.colors['ma50'], width=1.5),
                    opacity=0.8
                ),
                row=1, col=1
            )
            
            # 4. 添加成交量柱状图
            colors = [self.colors['up'] if row['Close'] >= row['Open'] 
                     else self.colors['down'] for _, row in df.iterrows()]
            
            fig.add_trace(
                go.Bar(
                    x=df.index,
                    y=df['Volume'],
                    name='Volume',
                    marker_color=colors,
                    opacity=0.5
                ),
                row=2, col=1
            )
            
            # 5. 布局设置
            fig.update_layout(
                title={
                    'text': f'<b>{ticker}</b> - 股价走势分析',
                    'font': {'size': 24, 'color': 'white'}
                },
                template='plotly_dark',
                height=700,
                xaxis_rangeslider_visible=False,
                hovermode='x unified',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    bgcolor='rgba(0,0,0,0.5)'
                ),
                plot_bgcolor=self.colors['background'],
                paper_bgcolor=self.colors['background']
            )
            
            # 6. Y轴设置
            fig.update_yaxes(title_text="价格 (USD)", row=1, col=1)
            fig.update_yaxes(title_text="成交量", row=2, col=1)
            
            # 7. X轴设置
            fig.update_xaxes(
                title_text="日期",
                row=2, col=1,
                gridcolor=self.colors['grid']
            )
            
            return fig
            
        except Exception as e:
            print(f"[ERROR] 生成K线图失败: {str(e)}")
            return None
    
    def create_comparison_chart(self, tickers: list, period: str = "1y"):
        """
        生成多股票对比图（归一化）
        
        Args:
            tickers: 股票代码列表（如 ['AAPL', 'MSFT', 'GOOGL']）
            period: 时间周期
        
        Returns:
            plotly.graph_objects.Figure 或 None
        """
        try:
            fig = go.Figure()
            
            # 预定义颜色
            colors = ['#00d4ff', '#ff6b6b', '#4ecdc4', '#ffe66d', '#a8dadc']
            
            for i, ticker in enumerate(tickers):
                stock = yf.Ticker(ticker)
                df = stock.history(period=period)
                
                if not df.empty:
                    # 归一化（以第一天为基准100）
                    normalized = (df['Close'] / df['Close'].iloc[0]) * 100
                    
                    fig.add_trace(go.Scatter(
                        x=df.index,
                        y=normalized,
                        name=ticker,
                        mode='lines',
                        line=dict(width=2.5, color=colors[i % len(colors)]),
                        hovertemplate=f'<b>{ticker}</b><br>日期: %{{x}}<br>涨跌: %{{y:.2f}}%<extra></extra>'
                    ))
            
            # 添加基准线（100%）
            if fig.data:
                x_range = [fig.data[0].x[0], fig.data[0].x[-1]]
                fig.add_trace(go.Scatter(
                    x=x_range,
                    y=[100, 100],
                    name='基准线',
                    line=dict(color='gray', width=1, dash='dash'),
                    showlegend=False
                ))
            
            fig.update_layout(
                title={
                    'text': '<b>股票走势对比</b>（归一化）',
                    'font': {'size': 20, 'color': 'white'}
                },
                yaxis_title='相对涨跌幅 (%)',
                xaxis_title='日期',
                template='plotly_dark',
                height=550,
                hovermode='x unified',
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    bgcolor='rgba(0,0,0,0.5)'
                ),
                plot_bgcolor=self.colors['background'],
                paper_bgcolor=self.colors['background']
            )
            
            return fig
            
        except Exception as e:
            print(f"[ERROR] 生成对比图失败: {str(e)}")
            return None
    
    def create_mini_chart(self, ticker: str, period: str = "1mo"):
        """
        生成简化版K线图（用于侧边栏或小卡片）
        
        Args:
            ticker: 股票代码
            period: 时间周期
        
        Returns:
            plotly.graph_objects.Figure 或 None
        """
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)
            
            if df.empty:
                return None
            
            # 只显示收盘价曲线
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['Close'],
                mode='lines',
                line=dict(color='cyan', width=2),
                fill='tozeroy',
                fillcolor='rgba(0,212,255,0.1)',
                name=ticker
            ))
            
            fig.update_layout(
                template='plotly_dark',
                height=200,
                margin=dict(l=0, r=0, t=30, b=0),
                showlegend=False,
                plot_bgcolor=self.colors['background'],
                paper_bgcolor=self.colors['background'],
                xaxis=dict(visible=False),
                yaxis=dict(visible=True, side='right')
            )
            
            return fig
            
        except Exception as e:
            print(f"[ERROR] 生成迷你图失败: {str(e)}")
            return None
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标
        
        Args:
            df: 股票数据DataFrame
        
        Returns:
            添加了技术指标的DataFrame
        """
        # 计算移动平均线
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA50'] = df['Close'].rolling(window=50).mean()
        
        # 可以添加更多指标
        # df['RSI'] = self._calculate_rsi(df['Close'])
        # df['MACD'] = ...
        
        return df
    
    def get_price_change(self, ticker: str) -> dict:
        """
        获取价格变动信息
        
        Args:
            ticker: 股票代码
        
        Returns:
            包含价格信息的字典
        """
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="5d")
            
            if df.empty or len(df) < 2:
                return None
            
            current_price = df['Close'].iloc[-1]
            previous_close = df['Close'].iloc[-2]
            change = current_price - previous_close
            change_pct = (change / previous_close) * 100
            
            return {
                'current_price': current_price,
                'previous_close': previous_close,
                'change': change,
                'change_pct': change_pct,
                'high_52w': df['High'].max(),
                'low_52w': df['Low'].min()
            }
            
        except Exception as e:
            print(f"[ERROR] 获取价格失败: {str(e)}")
            return None
