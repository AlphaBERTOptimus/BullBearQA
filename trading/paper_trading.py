"""
模拟交易追踪器 - 记录策略表现
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import yfinance as yf


class PaperTradingTracker:
    """
    模拟交易追踪器
    功能：
    1. 记录交易策略
    2. 追踪策略表现
    3. 计算胜率、收益率等指标
    """
    
    def __init__(self, data_file: str = "paper_trades.json"):
        """
        初始化
        
        Args:
            data_file: 存储交易数据的JSON文件路径
        """
        self.data_file = data_file
        self.trades = self._load_trades()
    
    def _load_trades(self) -> List[Dict]:
        """从文件加载交易记录"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载交易记录失败: {e}")
                return []
        return []
    
    def _save_trades(self):
        """保存交易记录到文件"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.trades, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存交易记录失败: {e}")
    
    def add_trade(self, strategy: Dict) -> int:
        """
        添加一笔交易记录
        
        Args:
            strategy: 策略字典（来自StrategyGenerator）
        
        Returns:
            交易ID
        """
        trade_id = len(self.trades) + 1
        
        trade = {
            "id": trade_id,
            "ticker": strategy['ticker'],
            "action": strategy['action'],
            "entry_price": strategy['entry_price'],
            "target_price": strategy['target_price'],
            "stop_loss": strategy['stop_loss'],
            "position_size": strategy['position_size'],
            "entry_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "OPEN",  # OPEN / CLOSED_WIN / CLOSED_LOSS / CLOSED_BREAK_EVEN
            "exit_price": None,
            "exit_date": None,
            "pnl_pct": None,
            "reason": strategy.get('reason', ''),
            "notes": ""
        }
        
        self.trades.append(trade)
        self._save_trades()
        
        return trade_id
    
    def update_trade(self, trade_id: int, current_price: float, notes: str = "") -> Dict:
        """
        更新交易状态
        
        Args:
            trade_id: 交易ID
            current_price: 当前价格
            notes: 备注（可选）
        
        Returns:
            更新后的交易信息
        """
        if trade_id < 1 or trade_id > len(self.trades):
            return {"error": "无效的交易ID"}
        
        trade = self.trades[trade_id - 1]
        
        # 如果已经平仓，不再更新
        if trade['status'] != 'OPEN':
            return trade
        
        entry_price = trade['entry_price']
        target_price = trade['target_price']
        stop_loss = trade['stop_loss']
        action = trade['action']
        
        # 检查是否触发止盈或止损
        if action == "BUY":
            # 做多
            if current_price >= target_price:
                # 止盈
                trade['status'] = 'CLOSED_WIN'
                trade['exit_price'] = current_price
                trade['pnl_pct'] = round((current_price / entry_price - 1) * 100, 2)
            elif current_price <= stop_loss:
                # 止损
                trade['status'] = 'CLOSED_LOSS'
                trade['exit_price'] = current_price
                trade['pnl_pct'] = round((current_price / entry_price - 1) * 100, 2)
        else:  # SELL (做空)
            # 做空
            if current_price <= target_price:
                # 止盈（价格下跌）
                trade['status'] = 'CLOSED_WIN'
                trade['exit_price'] = current_price
                trade['pnl_pct'] = round((entry_price / current_price - 1) * 100, 2)
            elif current_price >= stop_loss:
                # 止损（价格上涨）
                trade['status'] = 'CLOSED_LOSS'
                trade['exit_price'] = current_price
                trade['pnl_pct'] = round((entry_price / current_price - 1) * 100, 2)
        
        # 如果状态改变，记录平仓时间
        if trade['status'] != 'OPEN':
            trade['exit_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 添加备注
        if notes:
            trade['notes'] = notes
        
        self._save_trades()
        
        return trade
    
    def manual_close_trade(
        self, 
        trade_id: int, 
        exit_price: float, 
        notes: str = ""
    ) -> Dict:
        """
        手动平仓
        
        Args:
            trade_id: 交易ID
            exit_price: 平仓价格
            notes: 备注
        
        Returns:
            平仓后的交易信息
        """
        if trade_id < 1 or trade_id > len(self.trades):
            return {"error": "无效的交易ID"}
        
        trade = self.trades[trade_id - 1]
        
        if trade['status'] != 'OPEN':
            return {"error": "交易已平仓"}
        
        entry_price = trade['entry_price']
        action = trade['action']
        
        # 计算盈亏
        if action == "BUY":
            pnl_pct = round((exit_price / entry_price - 1) * 100, 2)
        else:  # SELL
            pnl_pct = round((entry_price / exit_price - 1) * 100, 2)
        
        # 判断盈亏状态
        if pnl_pct > 0.5:
            status = 'CLOSED_WIN'
        elif pnl_pct < -0.5:
            status = 'CLOSED_LOSS'
        else:
            status = 'CLOSED_BREAK_EVEN'
        
        trade['status'] = status
        trade['exit_price'] = exit_price
        trade['exit_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        trade['pnl_pct'] = pnl_pct
        trade['notes'] = notes
        
        self._save_trades()
        
        return trade
    
    def get_all_trades(self) -> List[Dict]:
        """获取所有交易记录"""
        return self.trades
    
    def get_open_trades(self) -> List[Dict]:
        """获取所有未平仓交易"""
        return [t for t in self.trades if t['status'] == 'OPEN']
    
    def get_closed_trades(self) -> List[Dict]:
        """获取所有已平仓交易"""
        return [t for t in self.trades if t['status'] != 'OPEN']
    
    def get_performance_stats(self) -> Optional[Dict]:
        """
        计算交易表现统计
        
        Returns:
            统计字典，包含胜率、平均盈亏等
        """
        closed_trades = self.get_closed_trades()
        
        if not closed_trades:
            return None
        
        wins = [t for t in closed_trades if 'WIN' in t['status']]
        losses = [t for t in closed_trades if 'LOSS' in t['status']]
        
        total_trades = len(closed_trades)
        win_count = len(wins)
        loss_count = len(losses)
        
        win_rate = round(win_count / total_trades * 100, 1) if total_trades > 0 else 0
        
        avg_win = round(sum(t['pnl_pct'] for t in wins) / win_count, 2) if wins else 0
        avg_loss = round(sum(t['pnl_pct'] for t in losses) / loss_count, 2) if losses else 0
        
        # 最大盈利和亏损
        max_win = max((t['pnl_pct'] for t in wins), default=0)
        max_loss = min((t['pnl_pct'] for t in losses), default=0)
        
        # 盈亏比
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        return {
            "total_trades": total_trades,
            "wins": win_count,
            "losses": loss_count,
            "win_rate": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "max_win": max_win,
            "max_loss": max_loss,
            "profit_factor": round(profit_factor, 2)
        }
    
    def auto_update_all_open_trades(self):
        """自动更新所有未平仓交易的状态"""
        open_trades = self.get_open_trades()
        
        updated_count = 0
        
        for trade in open_trades:
            ticker = trade['ticker']
            
            try:
                # 获取当前价格
                stock = yf.Ticker(ticker)
                current_price = stock.info.get('currentPrice') or stock.info.get('regularMarketPrice')
                
                if not current_price:
                    hist = stock.history(period="1d")
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                    else:
                        continue
                
                # 更新状态
                result = self.update_trade(trade['id'], current_price)
                
                if result['status'] != 'OPEN':
                    updated_count += 1
            
            except Exception as e:
                print(f"更新 {ticker} 失败: {e}")
        
        return updated_count
