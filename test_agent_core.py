# -*- coding: utf-8 -*-
"""快速测试 agent_core 初始化"""
import sys
sys.path.insert(0, r"D:\my algo\pet")

try:
    from agent_core import get_agent_core
    a = get_agent_core()
    print("✅ AgentCore 初始化成功")
    print(f"   工具列表: {a.tool_registry.list_tools()}")
    if a.kb:
        print(f"   知识库记录数: {a.kb.vector_store.count()}")
    else:
        print("   知识库: 未初始化")
    print(f"   已保存角色: {a.list_saved_characters()}")

    # 测试一次对话（含RAG + Function Calling）
    print("\n测试对话（含RAG+Function Calling）...")
    reply, ok, tools, ctx = a.chat("现在几点了？", use_rag=True, use_tools=True)
    print(f"   回复: {reply}")
    print(f"   成功: {ok}")
    print(f"   调用工具: {[t['name'] for t in tools]}")
    print(f"   RAG上下文: {'有' if ctx else '无'} ({len(ctx)}字符)")

    print("\n✅ 全部测试通过！")
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
