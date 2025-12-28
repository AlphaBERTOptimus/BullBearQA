"""
策略生成器 - 将分析结果转化为可执行交易策略
"""

import yfinance as yf
from datetime import datetime
from typing import Dict, Optional


class StrategyGenerator:
    """
    策略生成器
    输入: Arena Judge的综合分析结果
    输出: 可执行的交易策略（买入价、目标价、止损价、仓位）
    """
    
    def __init__(self):
        self.default_risk_tolerance = 0.04  # 默认4%止损
        self.default_profit_target = 0.10   # 默认10%止盈
    
    def generate_strategy(
        self, 
        ticker: str,
        rating: str,  # "Buy" / "Hold" / "Sell"
        analysis_result: Dict,
        risk_tolerance: str = "medium"  # "low" / "medium" / "high"
    ) -> Optional[Dict]:
        """
        生成交易策略
        
        Args:
            ticker: 股票代码
            rating: 评级 (Buy/Hold/Sell)
            analysis_result: Arena Judge的分析结果
            risk_tolerance: 风险承受度
        
        Returns:
            策略字典，包含买卖价位、仓位等
        """
        # 如果是Hold，不生成策略
        if rating.upper() == "HOLD":
            return None
        
        # 获取当前价格
        try:
            stock = yf.Ticker(ticker)
            current_price = stock.info.get('currentPrice') or stock.info.get('regularMarketPrice')
            
            if not current_price:
                # 如果info获取失败，用history
                hist = stock.history(period="1d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                else:
                    return None
        except Exception as e:
            print(f"获取价格失败: {e}")
            return None
        
        # 根据评级生成策略
        if rating.upper() == "BUY":
            strategy = self._generate_buy_strategy(
                ticker, current_price, analysis_result, risk_tolerance
            )
        elif rating.upper() == "SELL":
            strategy = self._generate_sell_strategy(
                ticker, current_price, analysis_result, risk_tolerance
            )
        else:
            return None
        
        return strategy
    
    def _generate_buy_strategy(
        self, 
        ticker: str, 
        current_price: float,
        analysis: Dict,
        risk_tolerance: str
    ) -> Dict:
        """生成买入策略"""
        
        # 根据风险偏好设置参数
        risk_params = self._get_risk_parameters(risk_tolerance)
        
        # 计算止损和目标价
        stop_loss_pct = risk_params['stop_loss']
        profit_target_pct = risk_params['profit_target']
        
        # 如果分析中有技术指标，可以调整
        technical = analysis.get('technical', {})
        rsi = technical.get('rsi')
        
        # RSI低 → 超卖 → 潜在空间大
        if rsi and rsi < 30:
            profit_target_pct *= 1.5  # 目标上调50%
        
        # 计算价格
        entry_price = current_price
        target_price = round(current_price * (1 + profit_target_pct), 2)
        stop_loss = round(current_price * (1 - stop_loss_pct), 2)
        
        # 计算仓位
        position_size = self._calculate_position_size(analysis, risk_tolerance)
        
        # 计算风险回报比
        risk = stop_loss_pct * 100
        reward = profit_target_pct * 100
        risk_reward_ratio = round(reward / risk, 2) if risk > 0 else 0
        
        return {
            "action": "BUY",
            "ticker": ticker,
            "entry_price": entry_price,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "position_size": position_size,
            "time_horizon": self._estimate_time_horizon(profit_target_pct),
            "risk_reward_ratio": risk_reward_ratio,
            "expected_gain_pct": round(profit_target_pct * 100, 1),
            "max_loss_pct": round(stop_loss_pct * 100, 1),
            "reason": self._generate_reason(analysis, "BUY"),
            "confidence": self._calculate_confidence(analysis)
        }
    
    def _generate_sell_strategy(
        self, 
        ticker: str, 
        current_price: float,
        analysis: Dict,
        risk_tolerance: str
    ) -> Dict:
        """生成卖出策略（做空或止盈）"""
        
        risk_params = self._get_risk_parameters(risk_tolerance)
        
        # 卖出时，止损在上方，目标价在下方
        stop_loss_pct = risk_params['stop_loss']
        profit_target_pct = risk_params['profit_target']
        
        entry_price = current_price
        target_price = round(current_price * (1 - profit_target_pct), 2)  # 下跌目标
        stop_loss = round(current_price * (1 + stop_loss_pct), 2)        # 止损在上方
        
        position_size = self._calculate_position_size(analysis, risk_tolerance)
        
        risk = stop_loss_pct * 100
        reward = profit_target_pct * 100
        risk_reward_ratio = round(reward / risk, 2) if risk > 0 else 0
        
        return {
            "action": "SELL",
            "ticker": ticker,
            "entry_price": entry_price,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "position_size": position_size,
            "time_horizon": self._estimate_time_horizon(profit_target_pct),
            "risk_reward_ratio": risk_reward_ratio,
            "expected_gain_pct": round(profit_target_pct * 100, 1),
            "max_loss_pct": round(stop_loss_pct * 100, 1),
            "reason": self._generate_reason(analysis, "SELL"),
            "confidence": self._calculate_confidence(analysis)
        }
    
    def _get_risk_parameters(self, risk_tolerance: str) -> Dict:
        """根据风险偏好返回参数"""
        params = {
            "low": {
                "stop_loss": 0.03,      # 3%
                "profit_target": 0.08,  # 8%
            },
            "medium": {
                "stop_loss": 0.05,      # 5%
                "profit_target": 0.12,  # 12%
            },
            "high": {
                "stop_loss": 0.08,      # 8%
                "profit_target": 0.20,  # 20%
            }
        }
        return params.get(risk_tolerance.lower(), params["medium"])
    
    def _calculate_position_size(self, analysis: Dict, risk_tolerance: str) -> str:
        """计算建议仓位"""
        
        # 基础仓位
        base_position = {
            "low": "3%",
            "medium": "5%",
            "high": "8%"
        }
        
        position = base_position.get(risk_tolerance.lower(), "5%")
        
        # 根据信心度调整
        confidence = self._calculate_confidence(analysis)
        
        if confidence > 0.8:
            # 高信心 → 增加仓位
            position_map = {"3%": "5%", "5%": "8%", "8%": "10%"}
            position = position_map.get(position, position)
        elif confidence < 0.5:
            # 低信心 → 减少仓位
            position_map = {"3%": "2%", "5%": "3%", "8%": "5%"}
            position = position_map.get(position, position)
        
        return position
    
    def _estimate_time_horizon(self, profit_target_pct: float) -> str:
        """估算持仓时间"""
        if profit_target_pct < 0.08:
            return "1-2周"
        elif profit_target_pct < 0.15:
            return "1-2个月"
        else:
            return "2-6个月"
    
    def _generate_reason(self, analysis: Dict, action: str) -> str:
        """生成策略理由"""
        reasons = []
        
        # 从分析中提取关键点
        fundamental = analysis.get('fundamental', {})
        technical = analysis.get('technical', {})
        sentiment = analysis.get('sentiment', {})
        
        if action == "BUY":
            if fundamental:
                reasons.append("基本面稳健")
            if technical.get('trend') == '上涨':
                reasons.append("技术面看涨")
            if sentiment.get('score', 0) > 0.6:
                reasons.append("市场情绪积极")
        else:  # SELL
            if fundamental:
                reasons.append("估值偏高")
            if technical.get('trend') == '下跌':
                reasons.append("技术面转弱")
            if sentiment.get('score', 0) < 0.4:
                reasons.append("市场情绪转负")
        
        return " + ".join(reasons) if reasons else "综合分析显示"
    
    def _calculate_confidence(self, analysis: Dict) -> float:
        """计算信心度（0-1）"""
        
        # 简化版：如果有多个维度支持，信心度高
        scores = []
        
        if analysis.get('fundamental'):
            scores.append(0.8)
        if analysis.get('technical'):
            scores.append(0.8)
        if analysis.get('sentiment'):
            scores.append(0.7)
        
        if not scores:
            return 0.5
        
        return sum(scores) / len(scores)


# 测试代码（可选，不影响使用）
if __name__ == "__main__":
    generator = StrategyGenerator()
    
    # 模拟Arena Judge的分析结果
    mock_analysis = {
        'fundamental': {'pe': 25, 'roe': 0.15},
        'technical': {'rsi': 45, 'trend': '上涨'},
        'sentiment': {'score': 0.7}
    }
    
    strategy = generator.generate_strategy(
        ticker="AAPL",
        rating="Buy",
        analysis_result=mock_analysis,
        risk_tolerance="medium"
    )
    
    if strategy:
        print("✅ 策略生成成功!")
        for key, value in strategy.items():
            print(f"  {key}: {value}")
    else:
        print("❌ 未生成策略")
