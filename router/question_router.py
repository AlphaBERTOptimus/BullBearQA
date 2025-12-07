from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import os
import re
from typing import List, Dict

class QuestionRouter:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
            openai_api_base="https://api.deepseek.com/v1",
            temperature=0
        )
        
        # 关键词规则库（快速匹配，避免每次都调用LLM）
        self.keywords = {
            'fundamental': [
                'pe', 'p/e', '市盈率', 'pb', 'p/b', '市净率', 'roe', '净资产收益率',
                '营收', '利润', '盈利', '估值', '财务', '基本面', '市值', 
                '资产负债率', 'd/e', 'debt', '股息', 'dividend'
            ],
            'technical': [
                'rsi', 'macd', '均线', 'ma', 'moving average', '技术', '技术面',
                '趋势', '支撑', '压力', '突破', '布林带', 'bollinger', '成交量',
                '涨跌', '回调', '反弹', '图表', 'chart'
            ],
            'sentiment': [
                '新闻', 'news', '情绪', 'sentiment', '舆论', '热度', '讨论',
                '社交', 'social', '消息', '传闻', '分析师', '机构', '看涨', '看跌',
                '市场观点', '投资者情绪'
            ],
            'comparison': [
                '比较', '对比', 'vs', 'versus', 'compare', '哪个', '哪只',
                '更好', 'better', '差异', 'difference'
            ]
        }
    
    def route(self, question: str) -> Dict[str, any]:
        """
        路由问题到相应的Agent
        返回: {
            'agents': ['fundamental', 'technical', ...],
            'tickers': ['AAPL', 'MSFT', ...],
            'method': 'rule' or 'llm'
        }
        """
        question_lower = question.lower()
        
        # 1. 提取股票代码（通用）
        tickers = self._extract_tickers(question)
        
        # 2. 尝试规则匹配（快速）
        rule_result = self._rule_based_routing(question_lower)
        
        if rule_result['confidence'] == 'high':
            return {
                'agents': rule_result['agents'],
                'tickers': tickers,
                'method': 'rule',
                'confidence': 'high'
            }
        
        # 3. 使用LLM路由（精确但较慢）
        llm_result = self._llm_based_routing(question)
        
        return {
            'agents': llm_result['agents'],
            'tickers': tickers,
            'method': 'llm',
            'confidence': llm_result['confidence']
        }
    
    def _extract_tickers(self, text: str) -> List[str]:
        """提取股票代码"""
        # 匹配1-5个大写字母的股票代码
        # 例如: AAPL, MSFT, TSLA, NVDA
        pattern = r'\b[A-Z]{1,5}\b'
        tickers = list(set(re.findall(pattern, text)))
        
        # 过滤常见非股票代码的词
        exclude_words = {'PE', 'PB', 'ROE', 'RSI', 'MA', 'VS', 'AI', 'DE', 'US', 'USD'}
        tickers = [t for t in tickers if t not in exclude_words]
        
        return tickers
    
    def _rule_based_routing(self, question: str) -> Dict[str, any]:
        """基于关键词的快速路由"""
        matched_agents = set()
        
        # 检查每个Agent的关键词
        for agent_type, keywords in self.keywords.items():
            for keyword in keywords:
                if keyword in question:
                    matched_agents.add(agent_type)
                    break
        
        # 判断置信度
        if len(matched_agents) == 1:
            # 明确匹配单个类型
            return {
                'agents': list(matched_agents),
                'confidence': 'high'
            }
        elif len(matched_agents) > 1:
            # 匹配多个类型（可能是复合问题）
            # 如果包含"比较"，优先使用comparison
            if 'comparison' in matched_agents:
                return {
                    'agents': ['comparison'],
                    'confidence': 'high'
                }
            return {
                'agents': list(matched_agents),
                'confidence': 'medium'
            }
        else:
            # 无匹配，需要LLM判断
            return {
                'agents': [],
                'confidence': 'low'
            }
    
    def _llm_based_routing(self, question: str) -> Dict[str, any]:
        """使用LLM进行精确路由"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个问题路由专家，负责将用户的股票相关问题分配给合适的分析师。

可用的分析师类型：
1. fundamental - 基本面分析师：回答关于财务指标、估值、盈利能力的问题（如PE、ROE、营收、利润等）
2. technical - 技术面分析师：回答关于价格走势、技术指标的问题（如RSI、MACD、均线、趋势等）
3. sentiment - 情绪面分析师：回答关于市场情绪、新闻、舆论的问题
4. comparison - 对比分析师：回答比较多只股票的问题

规则：
- 如果问题涉及多个维度，返回多个分析师（用逗号分隔）
- 如果问题明确是比较类（如"比较AAPL和MSFT"），只返回comparison
- 如果无法判断，返回fundamental作为默认

请只返回分析师类型（用逗号分隔），不要有其他解释。"""),
            ("user", "{question}")
        ])
        
        try:
            chain = prompt | self.llm
            result = chain.invoke({"question": question})
            
            # 解析结果
            content = result.content.strip().lower()
            
            # 提取Agent列表
            agents = []
            if 'comparison' in content:
                agents.append('comparison')
            else:
                if 'fundamental' in content:
                    agents.append('fundamental')
                if 'technical' in content:
                    agents.append('technical')
                if 'sentiment' in content:
                    agents.append('sentiment')
            
            # 如果为空，默认使用fundamental
            if not agents:
                agents = ['fundamental']
            
            return {
                'agents': agents,
                'confidence': 'high' if len(agents) <= 2 else 'medium'
            }
            
        except Exception as e:
            # LLM失败时的降级策略
            print(f"LLM路由失败: {e}")
            return {
                'agents': ['fundamental'],  # 默认使用基本面分析
                'confidence': 'low'
            }
    
    def format_routing_info(self, routing_result: Dict) -> str:
        """格式化路由信息（用于调试）"""
        agents_cn = {
            'fundamental': '基本面分析师',
            'technical': '技术面分析师',
            'sentiment': '情绪面分析师',
            'comparison': '对比分析师'
        }
        
        agent_names = [agents_cn.get(a, a) for a in routing_result['agents']]
        tickers = routing_result.get('tickers', [])
        method = routing_result.get('method', 'unknown')
        
        info = f"🎯 路由结果: {', '.join(agent_names)}"
        if tickers:
            info += f" | 股票: {', '.join(tickers)}"
        info += f" | 方法: {'规则匹配' if method == 'rule' else 'AI判断'}"
        
        return info
