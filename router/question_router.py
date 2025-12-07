from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import re
from typing import Dict, List, Optional

class QuestionRouter:
    """混合路由器：规则 + LLM"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        
        # 关键词字典
        self.keywords = {
            'fundamental': ['基本面', '财务', '估值', '市盈率', 'PE', '市净率', 'PB', 'ROE', '营收', '利润', '负债', '现金流'],
            'technical': ['技术面', '技术指标', 'RSI', 'MACD', '均线', 'MA', '布林带', 'KDJ', '成交量', '趋势', '支撑', '阻力'],
            'sentiment': ['新闻', '舆情', '情绪', '消息', '市场看法', '分析师', '评级', '热度'],
            'comparison': ['对比', '比较', '横向', 'vs', '哪个好', '哪只', '选择']
        }
    
    def _extract_tickers(self, question: str) -> List[str]:
        """提取股票代码"""
        # 匹配美股代码（1-5个大写字母）
        pattern = r'\b[A-Z]{1,5}\b'
        tickers = re.findall(pattern, question.upper())
        # 过滤常见英文单词
        common_words = {'THE', 'AND', 'OR', 'IS', 'ARE', 'WAS', 'WERE', 'VS', 'PE', 'PB', 'ROE', 'RSI', 'MA', 'KDJ'}
        return [t for t in tickers if t not in common_words]
    
    def _rule_based_routing(self, question: str) -> Optional[Dict]:
        """基于规则的路由"""
        question_lower = question.lower()
        
        # 对比优先级最高
        if any(kw in question_lower for kw in self.keywords['comparison']):
            tickers = self._extract_tickers(question)
            if len(tickers) >= 2:
                return {
                    'agent_type': 'comparison',
                    'tickers': tickers,
                    'confidence': 'high',
                    'method': 'rule'
                }
        
        # 统计关键词命中数
        scores = {}
        for agent_type, keywords in self.keywords.items():
            if agent_type == 'comparison':
                continue
            score = sum(1 for kw in keywords if kw in question_lower)
            if score > 0:
                scores[agent_type] = score
        
        if not scores:
            return None
        
        # 选择得分最高的
        best_agent = max(scores.items(), key=lambda x: x[1])
        tickers = self._extract_tickers(question)
        
        return {
            'agent_type': best_agent[0],
            'tickers': tickers,
            'confidence': 'high' if best_agent[1] >= 2 else 'medium',
            'method': 'rule'
        }
    
    def _llm_based_routing(self, question: str) -> Dict:
        """基于 LLM 的路由（备用）"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个股票问题分类专家。请判断以下问题属于哪个类别：

1. fundamental - 基本面分析（财务数据、估值、盈利能力）
2. technical - 技术面分析（技术指标、趋势、图表）
3. sentiment - 市场情绪（新闻、舆情、分析师看法）
4. comparison - 股票对比（横向比较多只股票）

只输出类别名称，不要其他内容。"""),
            ("human", "{question}")
        ])
        
        try:
            chain = prompt | self.llm | StrOutputParser()
            result = chain.invoke({"question": question})
            agent_type = result.strip().lower()
            
            # 验证结果
            valid_types = ['fundamental', 'technical', 'sentiment', 'comparison']
            if agent_type not in valid_types:
                agent_type = 'fundamental'  # 默认
            
            tickers = self._extract_tickers(question)
            
            return {
                'agent_type': agent_type,
                'tickers': tickers,
                'confidence': 'low',
                'method': 'llm'
            }
        except Exception:
            # LLM 失败，返回默认
            return {
                'agent_type': 'fundamental',
                'tickers': self._extract_tickers(question),
                'confidence': 'low',
                'method': 'fallback'
            }
    
    def route(self, question: str) -> Dict:
        """主路由方法"""
        # 先尝试规则路由
        result = self._rule_based_routing(question)
        
        # 如果规则路由失败或置信度低，使用 LLM
        if result is None or result['confidence'] == 'low':
            llm_result = self._llm_based_routing(question)
            # 如果规则有结果但置信度低，优先使用规则结果
            if result is not None:
                return result
            return llm_result
        
        return result
    
    def format_routing_info(self, routing_result: Dict) -> str:
        """格式化路由信息"""
        agent_names = {
            'fundamental': '基本面分析',
            'technical': '技术面分析',
            'sentiment': '市场情绪',
            'comparison': '股票对比'
        }
        
        info = f"🎯 路由结果\n"
        info += f"  • Agent: {agent_names.get(routing_result['agent_type'], '未知')}\n"
        info += f"  • 股票代码: {', '.join(routing_result.get('tickers', [])) or '未识别'}\n"
        info += f"  • 置信度: {routing_result['confidence']}\n"
        info += f"  • 方法: {routing_result['method']}\n"
        
        return info
