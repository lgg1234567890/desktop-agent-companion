# -*- coding: utf-8 -*-
"""服务端API测试脚本"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_1_health():
    """测试1: 服务健康检查"""
    print("=" * 60)
    print("测试1: 服务健康检查")
    print("=" * 60)
    try:
        r = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"状态码: {r.status_code}")
        data = r.json()
        print(f"服务: {data.get('service')}")
        print(f"版本: {data.get('version')}")
        print(f"架构: {data.get('architecture')}")
        print(f"状态: {data.get('status')}")
        return True
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_2_agent_status():
    """测试2: 多Agent状态"""
    print("\n" + "=" * 60)
    print("测试2: 多Agent协作状态")
    print("=" * 60)
    try:
        r = requests.get(f"{BASE_URL}/api/agents/status", timeout=10)
        print(f"状态码: {r.status_code}")
        data = r.json()
        print(f"Planner Agent 运行: {data['planner']['running']}")
        print(f"Memory Agent 运行: {data['memory_agent']['running']}")
        print(f"Tool Agent 运行: {data['tool_agent']['running']}")
        print(f"可用工具: {data['tool_agent']['tools']}")
        return True
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_3_tools():
    """测试3: 工具列表"""
    print("\n" + "=" * 60)
    print("测试3: 可用工具列表")
    print("=" * 60)
    try:
        r = requests.get(f"{BASE_URL}/api/tools", timeout=5)
        data = r.json()
        print(f"工具数量: {len(data['tools'])}")
        for tool in data['tools']:
            print(f"  - {tool}")
        return True
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_4_chat_simple():
    """测试4: 简单对话"""
    print("\n" + "=" * 60)
    print("测试4: 简单对话（不调用工具）")
    print("=" * 60)
    try:
        payload = {
            "message": "你好，你是谁？",
            "use_rag": True,
            "use_tools": True,
            "extract_memory": False
        }
        print(f"用户: {payload['message']}")
        r = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=30)
        data = r.json()
        print(f"状态码: {r.status_code}")
        print(f"成功: {data['success']}")
        print(f"回复: {data['reply']}")
        print(f"调用工具: {data.get('tools_used', [])}")
        return data['success']
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_5_chat_with_tool():
    """测试5: 调用工具的对话（时间查询）"""
    print("\n" + "=" * 60)
    print("测试5: Function Calling（查询时间）")
    print("=" * 60)
    try:
        payload = {
            "message": "现在几点了？",
            "use_rag": True,
            "use_tools": True,
            "extract_memory": False
        }
        print(f"用户: {payload['message']}")
        r = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=30)
        data = r.json()
        print(f"状态码: {r.status_code}")
        print(f"成功: {data['success']}")
        print(f"回复: {data['reply']}")
        tools = data.get('tools_used', [])
        if tools:
            print(f"✅ 调用了工具:")
            for t in tools:
                print(f"  - {t['name']}: {t.get('result', '')[:50]}")
        else:
            print("⚠️  未调用工具（可能模型直接回答了）")
        return data['success']
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_6_memory():
    """测试6: 用户记忆"""
    print("\n" + "=" * 60)
    print("测试6: 用户记忆")
    print("=" * 60)
    try:
        r = requests.get(f"{BASE_URL}/api/memory", timeout=5)
        data = r.json()
        print(f"记忆上下文: {data.get('context', '')[:100]}")
        print(f"记忆统计: {data.get('stats', {})}")
        return True
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_7_stats():
    """测试7: 多Agent协作统计"""
    print("\n" + "=" * 60)
    print("测试7: 多Agent协作统计")
    print("=" * 60)
    try:
        r = requests.get(f"{BASE_URL}/api/status", timeout=5)
        data = r.json()
        stats = data.get('stats', {})
        print(f"总调用次数: {stats.get('total_calls', 0)}")
        print(f"记忆检索次数: {stats.get('memory_calls', 0)}")
        print(f"工具调用次数: {stats.get('tool_calls', 0)}")
        print(f"直接回复次数: {stats.get('direct_replies', 0)}")
        return True
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

if __name__ == "__main__":
    print("\n🚀 桌面AI陪伴Agent - 服务端API测试\n")
    
    results = []
    results.append(("健康检查", test_1_health()))
    results.append(("Agent状态", test_2_agent_status()))
    results.append(("工具列表", test_3_tools()))
    results.append(("简单对话", test_4_chat_simple()))
    results.append(("Function Calling", test_5_chat_with_tool()))
    results.append(("用户记忆", test_6_memory()))
    results.append(("协作统计", test_7_stats()))
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    for name, r in results:
        status = "✅ 通过" if r else "❌ 失败"
        print(f"  {name}: {status}")
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！多Agent协作服务端运行正常！")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查日志")
