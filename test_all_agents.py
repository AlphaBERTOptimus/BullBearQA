"""测试所有代理"""
from agents import (
    TechnicalAgent,
    FundamentalAgent,
    SentimentAgent,
    ComparisonAgent
)


def test_all_agents():
    """测试所有代理功能"""
    
    print("=" * 60)
    print("测试所有 Agent 模块")
    print("=" * 60)
    
    # 1. 技术分析
    print("\n1️⃣  技术分析代理")
    print("-" * 60)
    tech_agent = TechnicalAgent()
    tech_result = tech_agent.analyze("AAPL")
    print(f"状态: {tech_result.get('status')}")
    print(f"摘要: {tech_result.get('summary')}")
    
    # 2. 基本面分析
    print("\n2️⃣  基本面分析代理")
    print("-" * 60)
    fund_agent = FundamentalAgent()
    fund_result = fund_agent.analyze("AAPL")
    print(f"状态: {fund_result.get('status')}")
    print(f"公司: {fund_result.get('company_name')}")
    print(f"摘要: {fund_result.get('summary')}")
    
    # 3. 情绪分析
    print("\n3️⃣  情绪分析代理")
    print("-" * 60)
    sent_agent = SentimentAgent()
    sent_result = sent_agent.analyze("AAPL")
    print(f"状态: {sent_result.get('status')}")
    print(f"摘要: {sent_result.get('summary')}")
    
    # 4. 对比分析
    print("\n4️⃣  对比分析代理")
    print("-" * 60)
    comp_agent = ComparisonAgent()
    comp_result = comp_agent.analyze(["AAPL", "MSFT", "GOOGL"])
    print(f"状态: {comp_result.get('status')}")
    print(f"摘要: {comp_result.get('summary')}")
    if 'comparison_table' in comp_result:
        print("\n对比表格:")
        print(comp_result['comparison_table'])
    
    print("\n" + "=" * 60)
    print("✅ 所有代理测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_all_agents()
