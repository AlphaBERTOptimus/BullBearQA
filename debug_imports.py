"""
诊断导入问题
"""
import sys
import traceback

print("="*50)
print("开始诊断导入问题")
print("="*50)

# 测试1: 导入 base_agent
try:
    from agents.base_agent import BaseAgent
    print("✅ base_agent 导入成功")
except Exception as e:
    print(f"❌ base_agent 导入失败: {e}")
    traceback.print_exc()

# 测试2: 导入 fundamental_agent
try:
    from agents.fundamental_agent import FundamentalAgent
    print("✅ fundamental_agent 导入成功")
except Exception as e:
    print(f"❌ fundamental_agent 导入失败: {e}")
    traceback.print_exc()

# 测试3: 导入 technical_agent
try:
    from agents.technical_agent import TechnicalAgent
    print("✅ technical_agent 导入成功")
except Exception as e:
    print(f"❌ technical_agent 导入失败: {e}")
    traceback.print_exc()

# 测试4: 导入 sentiment_agent
try:
    from agents.sentiment_agent import SentimentAgent
    print("✅ sentiment_agent 导入成功")
except Exception as e:
    print(f"❌ sentiment_agent 导入失败: {e}")
    traceback.print_exc()

# 测试5: 导入 comparison_agent
try:
    from agents.comparison_agent import ComparisonAgent
    print("✅ comparison_agent 导入成功")
except Exception as e:
    print(f"❌ comparison_agent 导入失败: {e}")
    traceback.print_exc()

print("="*50)
print("诊断完成")
print("="*50)
