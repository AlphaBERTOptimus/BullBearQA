# -*- coding: utf-8 -*-
"""
智能问题路由器：规则匹配 + LLM备用
支持提取多个股票代码，适用于对比分析
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import re
from typing import Dict, List, Optional

class QuestionRouter:
    """混合路由器：规则 + LLM"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        
        # 关键词字典（用于规则匹配）
        self.keywords = {
            'fundamental': ['基本面', '财务', '估值', '市盈率', 'PE', '市净率', 'PB', 'ROE', '营收', '利润', '负债', '现金流', '资产', '收益'],
            'technical': ['技术面', '技术指标', 'RSI', 'MACD', '均线', 'MA', '布林带', 'KDJ', '成交量', '趋势', '支撑', '阻力', '突破'],
            'sentiment': ['新闻', '舆情', '情绪', '消息', '市场看法', '分析师', '评级', '热度', '关注', '舆论'],
            'comparison': ['对比', '比较', '横向', 'vs', 'versus', '哪个好', '哪只', '选择', '和', '还是']
        }
        
        # 美股常见股票代码库（扩展版）
        self.common_tickers = {
            # 科技股
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'NVDA', 'AMD', 'INTC', 'TSLA',
            'NFLX', 'ADBE', 'CRM', 'ORCL', 'CSCO', 'IBM', 'QCOM', 'AVGO', 'TXN', 'NOW',
            # 金融股
            'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'BLK', 'SCHW', 'AXP', 'V', 'MA', 'PYPL',
            # 消费股
            'WMT', 'HD', 'NKE', 'MCD', 'SBUX', 'TGT', 'COST', 'LOW', 'DIS', 'CMCSA',
            # 医药股
            'JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'ABT', 'LLY', 'MRK', 'DHR', 'BMY',
            # 工业股
            'BA', 'CAT', 'GE', 'HON', 'MMM', 'UPS', 'FDX', 'RTX', 'LMT', 'DE',
            # 能源股
            'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'PXD', 'MPC', 'PSX', 'VLO', 'OXY',
            # 消费品
            'PG', 'KO', 'PEP', 'PM', 'MO', 'CL', 'EL', 'MDLZ', 'KHC', 'GIS',
            # 中概股
            'BABA', 'JD', 'PDD', 'NIO', 'XPEV', 'LI', 'BILI', 'IQ', 'BIDU', 'TME',
            # 新兴科技
            'UBER', 'LYFT', 'ABNB', 'COIN', 'SHOP', 'SQ', 'RBLX', 'U', 'SNOW', 'PLTR',
            # 通信
            'T', 'VZ', 'TMUS', 'CHTR',
            # 汽车
            'GM', 'F', 'RIVN', 'LCID'
        }
        
        # 中文到英文的映射
        self.cn_to_en = {
            '苹果': 'AAPL', '微软': 'MSFT', '谷歌': 'GOOGL', '亚马逊': 'AMZN',
            '英伟达': 'NVDA', '脸书': 'META', 'facebook': 'META', '特斯拉': 'TSLA',
            '阿里巴巴': 'BABA', '阿里': 'BABA', '京东': 'JD', '拼多多': 'PDD',
            '蔚来': 'NIO', '小鹏': 'XPEV', '理想': 'LI', '奈飞': 'NFLX',
            '迪士尼': 'DIS', '英特尔': 'INTC', '超微': 'AMD', '超威': 'AMD',
            '可口可乐': 'KO', '百事': 'PEP', '麦当劳': 'MCD', '星巴克': 'SBUX',
            '沃尔玛': 'WMT', '耐克': 'NKE', '波音': 'BA', '通用': 'GM', '福特': 'F'
        }
    
    def _extract_tickers(self, question: str) -> List[str]:
        """
        从问题中提取股票代码（增强版）
        支持：
        1. 直接匹配大写代码（如 AAPL）
        2. 中文公司名映射（如 苹果 → AAPL）
        3. 特殊模式识别（如 "AAPL的PE"）
        """
        tickers = []
        question_upper = question.upper()
        
        # 方法1: 匹配所有可能的股票代码（1-5个大写字母）
        potential_tickers = re.findall(r'\b([A-Z]{1,5})\b', question_upper)
        
        # 过滤：必须在常见ticker列表中
        for ticker in potential_tickers:
            # 排除常见英文单词
            excluded_words = {
                'THE', 'AND', 'OR', 'IS', 'ARE', 'WAS', 'WERE', 'VS', 'VERSUS',
                'PE', 'PB', 'ROE', 'RSI', 'MA', 'KDJ', 'MACD', 'A', 'I', 'IN', 'ON', 'AT'
            }
            if ticker not in excluded_words and ticker in self.common_tickers:
                if ticker not in tickers:
                    tickers.append(ticker)
        
        # 方法2: 匹配中文公司名
        for cn_name, en_ticker in self.cn_to_en.items():
            if cn_name in question:
                if en_ticker not in tickers:
                    tickers.append(en_ticker)
        
        # 方法3: 特殊模式（针对"AAPL的PE"这类问题）
        # 匹配 "XXX的" 或 "分析XXX" 或 "XXX怎么样"
        special_patterns = [
            r'([A-Z]{2,5})(?:的|股票|如何|怎么样)',
            r'(?:分析|看看|查询)([A-Z]{2,5})',
            r'([A-Z]{2,5})(?:\s+|$)'
        ]
        for pattern in special_patterns:
            matches = re.findall(pattern, question_upper)
            for match in matches:
                ticker = match.strip()
                if ticker in self.common_tickers and ticker not in tickers:
                    tickers.append(ticker)
        
        return tickers
    
    def _rule_based_routing(self, question: str) -> Optional[Dict]:
        """
        基于规则的路由（优先级最高）
        返回 None 表示规则匹配失败，需要LLM
        """
        question_lower = question.lower()
        
        # 提取股票代码（所有情况都提取）
        tickers = self._extract_tickers(question)
        
        # 规则1: 对比分析（优先级最高）
        comparison_keywords = ['对比', '比较', '横向', 'vs', 'versus', '哪个好', '哪只', '选择', '还是']
        if any(kw in question_lower for kw in comparison_keywords):
            # 对比至少需要2个ticker
            if len(tickers) >= 2:
                return {
                    'agent_type': 'comparison',
                    'tickers': tickers,
                    'confidence': 'high',
                    'method': 'rule'
                }
            # 如果只有1个ticker但有对比关键词，可能是语言问题（如"比较AAPL和微软"）
            # 尝试更激进的提取
            elif len(tickers) == 1:
                # 检查是否有"和"字连接两个名称
                if '和' in question or 'and' in question_lower:
                    return {
                        'agent_type': 'comparison',
                        'tickers': tickers,  # 至少返回1个ticker
                        'confidence': 'medium',
                        'method': 'rule'
                    }
        
        # 规则2-4: 其他类型分析（统计关键词命中数）
        scores = {}
        for agent_type, keywords in self.keywords.items():
            if agent_type == 'comparison':
                continue
            score = sum(1 for kw in keywords if kw in question_lower)
            if score > 0:
                scores[agent_type] = score
        
        # 如果没有任何关键词命中，返回None让LLM判断
        if not scores:
            # 但如果提取到了ticker，默认为基本面分析
            if tickers:
                return {
                    'agent_type': 'fundamental',
                    'tickers': tickers,
                    'confidence': 'medium',
                    'method': 'rule'
                }
            return None
        
        # 选择得分最高的agent类型
        best_agent = max(scores.items(), key=lambda x: x[1])
        
        return {
            'agent_type': best_agent[0],
            'tickers': tickers,
            'confidence': 'high' if best_agent[1] >= 2 else 'medium',
            'method': 'rule'
        }
    
    def _llm_based_routing(self, question: str) -> Dict:
        """
        基于 LLM 的路由（备用方案）
        当规则匹配失败或置信度低时使用
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个股票问题分类专家。请判断以下问题属于哪个类别：

1. fundamental - 基本面分析（财务数据、估值、盈利能力、市盈率PE、ROE等）
2. technical - 技术面分析（技术指标、趋势、图表、RSI、MACD、均线等）
3. sentiment - 市场情绪（新闻、舆情、分析师看法、市场热度等）
4. comparison - 股票对比（横向比较多只股票）

只输出类别名称（fundamental/technical/sentiment/comparison），不要其他内容。"""),
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
        except Exception as e:
            # LLM 失败，返回默认值
            print(f"[WARNING] LLM路由失败: {str(e)}")
            return {
                'agent_type': 'fundamental',
                'tickers': self._extract_tickers(question),
                'confidence': 'low',
                'method': 'fallback'
            }
    
    def route(self, question: str) -> Dict:
        """
        主路由方法
        优先使用规则路由，失败时使用LLM
        
        Returns:
            {
                'agent_type': str,  # 'fundamental', 'technical', 'sentiment', 'comparison'
                'tickers': List[str],  # 提取到的股票代码
                'confidence': str,  # 'high', 'medium', 'low'
                'method': str  # 'rule', 'llm', 'fallback'
            }
        """
        # 先尝试规则路由
        result = self._rule_based_routing(question)
        
        # 如果规则路由失败，使用 LLM
        if result is None:
            return self._llm_based_routing(question)
        
        # 如果规则路由置信度低，也尝试LLM验证
        if result['confidence'] == 'low':
            llm_result = self._llm_based_routing(question)
            # 如果LLM置信度也低，优先使用规则结果
            if llm_result['confidence'] == 'low':
                return result
            return llm_result
        
        return result
    
    def format_routing_info(self, routing_result: Dict) -> str:
        """格式化路由信息用于调试显示"""
        agent_names = {
            'fundamental': '基本面分析',
            'technical': '技术面分析',
            'sentiment': '市场情绪',
            'comparison': '股票对比'
        }
        
        confidence_emoji = {
            'high': '🟢',
            'medium': '🟡',
            'low': '🔴'
        }
        
        info = "🎯 **路由结果**\n"
        info += f"  • 分析类型: {agent_names.get(routing_result['agent_type'], '未知')}\n"
        info += f"  • 股票代码: {', '.join(routing_result.get('tickers', [])) or '未识别'}\n"
        info += f"  • 置信度: {confidence_emoji.get(routing_result['confidence'], '⚪')} {routing_result['confidence']}\n"
        info += f"  • 路由方法: {routing_result['method']}\n"
        
        return info
