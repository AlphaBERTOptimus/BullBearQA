"""交易策略生成器"""
import yfinance as yf
from typing import Dict, Any


class StrategyGenerator:
    """交易策略生成器"""
    
    def __init__(self):
        self.risk_params = {
            'low': {'stop_loss': 0.03, 'position': '3-5%', 'target_multiplier': 2.0},
            'medium': {'stop_loss': 0.05, 'position': '5-10%', 'target_multiplier': 2.4},
            'high': {'stop_loss': 0.08, 'position': '10-15%', 'target_multiplier': 3.0}
        }
    
    def generate_strategy(
        self,
        ticker: str,
        rating: str,
        analysis_result: Dict[str, Any],
        risk_tolerance: str = 'medium'
    ) -> Dict[str, Any]:
        """生成交易策略"""
        try:
            stock = yf.Ticker(ticker)
            current_price = stock.info.get('currentPrice') or stock.info.get('regularMarketPrice')
            
            if not current_price:
                hist = stock.history(period='1d')
                if not hist.empty:
                    current_price = float(hist['Close'].iloc[-1])
            
            if not current_price:
                return None
            
            if rating == 'Buy':
                return self._generate_buy_strategy(ticker, current_price, analysis_result, risk_tolerance)
            elif rating == 'Sell':
                return self._generate_sell_strategy(ticker, current_price, analysis_result, risk_tolerance)
            else:
                return self._generate_buy_strategy(ticker, current_price, analysis_result, risk_tolerance)
                
        except Exception as e:
            print(f"策略生成失败: {str(e)}")
            return None
    
    def _generate_buy_strategy(
        self,
        ticker: str,
        current_price: float,
        analysis: Dict[str, Any],
        risk_tolerance: str
    ) -> Dict[str, Any]:
        """生成买入策略"""
        params = self.risk_params[risk_tolerance]
        
        stop_loss = current_price * (1 - params['stop_loss'])
        target_price = current_price * (1 + params['stop_loss'] * params['target_multiplier'])
        
        expected_gain = ((target_price / current_price) - 1) * 100
        max_loss = ((current_price / stop_loss) - 1) * 100
        
        return {
            'ticker': ticker,
            'action': 'BUY',
            'entry_price': current_price,
            'target_price': target_price,
            'stop_loss': stop_loss,
            'position_size': params['position'],
            'risk_reward_ratio': round(params['target_multiplier'], 1),
            'expected_gain_pct': f"{expected_gain:.1f}",
            'max_loss_pct': f"{max_loss:.1f}",
            'time_horizon': self._get_time_horizon(risk_tolerance),
            'reason': self._generate_reason(analysis, 'BUY'),
            'confidence': self._calculate_confidence(analysis, risk_tolerance)
        }
    
    def _generate_sell_strategy(
        self,
        ticker: str,
        current_price: float,
        analysis: Dict[str, Any],
        risk_tolerance: str
    ) -> Dict[str, Any]:
        """生成卖出策略"""
        params = self.risk_params[risk_tolerance]
        
        stop_loss = current_price * (1 + params['stop_loss'])
        target_price = current_price * (1 - params['stop_loss'] * params['target_multiplier'])
        
        expected_gain = ((current_price / target_price) - 1) * 100
        max_loss = ((stop_loss / current_price) - 1) * 100
        
        return {
            'ticker': ticker,
            'action': 'SELL',
            'entry_price': current_price,
            'target_price': target_price,
            'stop_loss': stop_loss,
            'position_size': params['position'],
            'risk_reward_ratio': round(params['target_multiplier'], 1),
            'expected_gain_pct': f"{expected_gain:.1f}",
            'max_loss_pct': f"{max_loss:.1f}",
            'time_horizon': self._get_time_horizon(risk_tolerance),
            'reason': self._generate_reason(analysis, 'SELL'),
            'confidence': self._calculate_confidence(analysis, risk_tolerance)
        }
    
    def _get_time_horizon(self, risk_tolerance: str) -> str:
        """获取持仓周期"""
        horizons = {
            'low': '3-6个月',
            'medium': '1-2个月',
            'high': '1-2周'
        }
        return horizons.get(risk_tolerance, '1-2个月')
    
    def _generate_reason(self, analysis: Dict[str, Any], action: str) -> str:
        """生成策略理由（修复版 - 处理字符串）"""
        reasons = []
        
        # 安全提取分析结果
        fundamental = analysis.get('fundamental', '')
        technical = analysis.get('technical', '')
        sentiment = analysis.get('sentiment', '')
        
        # 处理基本面（可能是字符串或字典）
        if isinstance(fundamental, str):
            if 'ROE' in fundamental or '盈利' in fundamental:
                reasons.append("基本面稳健")
        elif isinstance(fundamental, dict):
            if fundamental.get('roe', 0) > 0.15:
                reasons.append("盈利能力强")
        
        # 处理技术面（可能是字符串或字典）
        if isinstance(technical, str):
            if 'RSI' in technical:
                if '超卖' in technical and action == 'BUY':
                    reasons.append("技术面超卖")
                elif '超买' in technical and action == 'SELL':
                    reasons.append("技术面超买")
            if '多头' in technical and action == 'BUY':
                reasons.append("趋势向上")
        elif isinstance(technical, dict):
            rsi = technical.get('rsi', 50)
            if rsi < 30 and action == 'BUY':
                reasons.append("技术面超卖")
            elif rsi > 70 and action == 'SELL':
                reasons.append("技术面超买")
        
        # 处理情绪（可能是字符串或字典）
        if isinstance(sentiment, str):
            if '积极' in sentiment or '看好' in sentiment:
                reasons.append("市场情绪积极")
        elif isinstance(sentiment, dict):
            if sentiment.get('score', 0) > 0.6:
                reasons.append("市场情绪积极")
        
        # 如果没有提取到任何理由，使用默认
        if not reasons:
            reasons.append("综合分析显示" if action == 'BUY' else "风险控制考虑")
        
        return "，".join(reasons)
    
    def _calculate_confidence(self, analysis: Dict[str, Any], risk_tolerance: str) -> float:
        """计算策略信心度"""
        base_confidence = {
            'low': 0.6,
            'medium': 0.75,
            'high': 0.85
        }
        
        confidence = base_confidence.get(risk_tolerance, 0.75)
        
        # 根据分析结果调整（简化版，只检查是否有内容）
        if analysis.get('fundamental'):
            confidence += 0.05
        if analysis.get('technical'):
            confidence += 0.05
        if analysis.get('sentiment'):
            confidence += 0.05
        
        return min(confidence, 0.95)
