"""
问题路由器
"""
from typing import Dict, Any, List
import re


class QuestionRouter:
    """问题路由器 - 判断问题类型"""
    
    def __init__(self, llm=None):
        self.llm = llm
        
        # 关键词规则
        self.rules = {
            'fundamental': ['PE', 'PB', 'ROE', '财务', '估值', '市盈率', '市净率', '盈利'],
            'technical': ['RSI', 'MACD', '技术', '指标', '均线', 'MA', '趋势'],
            'sentiment': ['新闻', '情绪', '市场看法', '舆论', '观点'],
            'comparison': ['比较', '对比', 'vs', 'VS', '哪个好', '选哪个']
        }
    
    def route(self, question: str) -> Dict[str, Any]:
        """
        路由问题到对应的Agent
        
        Args:
            question: 用户问题
            
        Returns:
            路由结果字典
        """
        # 提取股票代码
        tickers = self._extract_tickers(question)
        
        # 规则匹配
        agent_type = self._match_by_rules(question)
        
        # 如果是多个股票，优先判断为对比
        if len(tickers) >= 2 and agent_type != 'comparison':
            agent_type = 'comparison'
        
        # 如果没有匹配到，默认为基本面
        if agent_type is None:
            agent_type = 'fundamental'
        
        return {
            'agent_type': agent_type,
            'tickers': tickers,
            'confidence': 0.8,
            'question': question
        }
    
    def _extract_tickers(self, question: str) -> List[str]:
        """提取股票代码"""
        # 匹配1-5个大写字母
        matches = re.findall(r'\b([A-Z]{1,5})\b', question.upper())
        
        # 过滤常见非股票词
        exclude = ['PE', 'PB', 'VS', 'OR', 'AND', 'THE', 'IS', 'ARE', 'MA', 'AI']
        tickers = [m for m in matches if m not in exclude]
        
        return list(set(tickers))[:5]
    
    def _match_by_rules(self, question: str) -> str:
        """基于规则匹配"""
        question_upper = question.upper()
        
        scores = {}
        for agent_type, keywords in self.rules.items():
            score = sum(1 for kw in keywords if kw.upper() in question_upper)
            if score > 0:
                scores[agent_type] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return None
    
    def format_routing_info(self, routing_result: Dict[str, Any]) -> str:
        """格式化路由信息"""
        agent_type = routing_result['agent_type']
        tickers = routing_result.get('tickers', [])
        
        agent_names = {
            'fundamental': '基本面分析',
            'technical': '技术面分析',
            'sentiment': '市场情绪分析',
            'comparison': '对比分析'
        }
        
        info = f"🎯 **路由结果**\n"
        info += f"- 分析类型: {agent_names.get(agent_type, agent_type)}\n"
        if tickers:
            info += f"- 股票代码: {', '.join(tickers)}\n"
        
        return info
