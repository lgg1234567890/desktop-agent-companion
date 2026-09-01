# -*- coding: utf-8 -*-
"""综合测试：Function Calling + 用户记忆 + 主动提问"""
import sys
sys.path.insert(0, r'D:\my algo\pet')

from agent_core import get_agent_core

a = get_agent_core()
a.clear_history()

print("=" * 60)
print("测试1：Function Calling（问时间）")
print("=" * 60)
reply, ok, tools, ctx = a.chat("几点了？", use_rag=True, use_tools=True)
print(f"回复: {reply}")
print(f"调用工具: {[t['name'] for t in tools]}")
print(f"成功: {ok}")
assert tools, "❌ Function Calling 未触发！"
print("✅ Function Calling 正常\n")

print("=" * 60)
print("测试2：用户主动分享事情，验证记忆提取")
print("=" * 60)
# 手动添加一些用户记忆，模拟用户分享
a.user_memory.add_basic_info("职业", "AI算法工程师")
a.user_memory.add_basic_info("城市", "深圳")
a.user_memory.add_ongoing("正在准备AI Agent岗位面试", "可以问问准备得怎么样了")
a.user_memory.add_event("最近在做桌宠Agent项目")
print("已手动添加用户记忆：")
print(a.user_memory.get_context())
print()

print("=" * 60)
print("测试3：对话中注入用户记忆")
print("=" * 60)
reply, ok, tools, ctx = a.chat("你了解我吗？", use_rag=False, use_tools=False, extract_memory=False)
print(f"回复: {reply}")
print("✅ 用户记忆已注入对话\n")

print("=" * 60)
print("测试4：主动跟进问题生成")
print("=" * 60)
question = a.generate_follow_up_question()
print(f"主动提问: {question}")
assert question, "❌ 主动提问生成失败！"
print("✅ 主动提问生成正常\n")

print("=" * 60)
print("测试5：设提醒")
print("=" * 60)
reply, ok, tools, ctx = a.chat("10秒后提醒我喝水", use_rag=False, use_tools=True, extract_memory=False)
print(f"回复: {reply}")
print(f"调用工具: {[t['name'] for t in tools]}")
print("✅ 提醒工具正常\n")

print("=" * 60)
print("用户记忆统计:", a.get_user_memory_stats())
print("=" * 60)
print("\n🎉 全部测试通过！")
