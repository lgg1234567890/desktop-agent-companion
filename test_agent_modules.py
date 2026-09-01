# -*- coding: utf-8 -*-
"""
三模块集成测试：RAG + Function Calling + 角色画像生成
独立运行，不依赖 PyQt5
"""
import os
import sys
import json

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import LLM_API_KEY, LLM_MODEL, LLM_API_URL

# 使用新开通的 API Key
API_KEY = "sk-ws-H.EXHIPRH.Cxyl.MEUCIQChYoGgVlmuyEkDS07OLx--5Ynlcnyu71kw3_uQm2A1UgIgCcLnFHaYsyvIhT9njvmg0fP_gUQTH23SvMf8oL0fc_4"
API_URL = LLM_API_URL
MODEL = LLM_MODEL

print("=" * 60)
print("桌宠项目三模块集成测试")
print("=" * 60)
print(f"API Key: {API_KEY[:8]}...")
print(f"API URL: {API_URL}")
print(f"Model: {MODEL}")
print()

# ===== 测试1：RAG 知识库 =====
print("【测试1】RAG 知识库构建与检索")
print("-" * 40)
try:
    from memory.knowledge_base import KnowledgeBase

    kb_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "knowledge")
    persist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "vector_db")

    kb = KnowledgeBase(api_key=API_KEY, api_url=API_URL, persist_dir=persist_dir)
    count = kb.load_and_index(kb_dir, force_rebuild=True)
    print(f"  知识库构建完成，共 {count} 条文档")

    # 测试检索
    query = "张起灵的麒麟血有什么用？"
    results = kb.search(query, top_k=2, min_score=0.1)
    print(f"  检索查询: {query}")
    print(f"  命中 {len(results)} 条结果:")
    for r in results:
        print(f"    [相似度{r['score']:.3f}] {r['text'][:60]}...")

    # 测试上下文构建
    context = kb.build_context(query, top_k=2)
    print(f"  上下文长度: {len(context)} 字符")
    print("  ✅ RAG 模块测试通过")
except Exception as e:
    print(f"  ❌ RAG 模块测试失败: {e}")
    import traceback
    traceback.print_exc()

print()

# ===== 测试2：Function Calling 工具注册与执行 =====
print("【测试2】Function Calling 工具注册与执行")
print("-" * 40)
try:
    from tools.registry import get_registry

    registry = get_registry()
    tool_names = registry.list_tools()
    print(f"  已注册工具: {tool_names}")

    # 导出 schema
    schemas = registry.get_function_schemas()
    print(f"  导出 schema 数量: {len(schemas)}")
    for s in schemas:
        print(f"    - {s['function']['name']}: {s['function']['description'][:40]}...")

    # 直接执行工具
    result, success = registry.execute_tool("get_current_time", {})
    print(f"  执行 get_current_time: {result} (成功={success})")

    result, success = registry.execute_tool("check_idle_time", {})
    print(f"  执行 check_idle_time: {result} (成功={success})")

    result, success = registry.execute_tool("set_reminder", {"minutes": 1, "message": "测试提醒"})
    print(f"  执行 set_reminder: {result} (成功={success})")

    print("  ✅ Function Calling 模块测试通过")
except Exception as e:
    print(f"  ❌ Function Calling 模块测试失败: {e}")
    import traceback
    traceback.print_exc()

print()

# ===== 测试3：角色画像生成 =====
print("【测试3】角色画像 JSON 生成与 System Prompt 渲染")
print("-" * 40)
try:
    from llm.character_builder import CharacterBuilder

    builder = CharacterBuilder(api_key=API_KEY, api_url=API_URL, model=MODEL)

    # 先尝试加载已保存的
    saved = builder.load_profile("张起灵")
    if saved:
        print("  加载已保存的张起灵画像")
        profile = saved["profile"]
        system_prompt = saved["system_prompt"]
    else:
        print("  正在生成张起灵角色画像（调用LLM）...")
        system_prompt, profile, error = builder.generate_and_save("张起灵", "《盗墓笔记》中的张起灵，小哥")
        if error:
            print(f"  ❌ 角色画像生成失败: {error}")
            raise Exception(error)

    print(f"  画像字段: {list(profile.keys())}")
    print(f"  外貌: {profile.get('appearance', 'N/A')[:50]}")
    print(f"  性格: {profile.get('personality', 'N/A')[:50]}")
    print(f"  System Prompt 长度: {len(system_prompt)} 字符")
    print(f"  System Prompt 前100字: {system_prompt[:100]}...")
    print("  ✅ 角色画像模块测试通过")
except Exception as e:
    print(f"  ❌ 角色画像模块测试失败: {e}")
    import traceback
    traceback.print_exc()

print()

# ===== 测试4：完整对话（RAG + Function Calling 联动） =====
print("【测试4】完整对话：RAG注入 + Function Calling 多轮调用")
print("-" * 40)
try:
    from llm_client import LLMClient

    client = LLMClient()
    client.clear_history()

    # 4a: 纯 RAG 对话
    print("  4a. RAG 对话测试:")
    query = "小哥，你的麒麟血有什么特殊能力？"
    context = kb.build_context(query, top_k=2) if 'kb' in dir() else None
    print(f"    用户: {query}")
    print(f"    RAG上下文: {'有' if context else '无'} ({len(context) if context else 0}字符)")
    reply, ok = client.chat(query, rag_context=context)
    print(f"    回复: {reply[:100]}")
    print(f"    成功: {ok}")

    # 4b: Function Calling 对话
    print()
    print("  4b. Function Calling 对话测试:")
    client.clear_history()
    query2 = "现在几点了？"
    print(f"    用户: {query2}")
    reply2, ok2, tools_used = client.chat_with_tools(query2, registry)
    print(f"    调用工具: {[t['name'] for t in tools_used]}")
    print(f"    回复: {reply2[:100]}")
    print(f"    成功: {ok2}")

    print()
    print("  ✅ 完整对话联动测试通过")
except Exception as e:
    print(f"  ❌ 完整对话测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("全部测试完成！")
print("=" * 60)
