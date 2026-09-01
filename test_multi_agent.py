# -*- coding: utf-8 -*-
"""
多Agent协作系统测试脚本
验证 PlannerAgent + MemoryAgent + ToolAgent 三Agent协作
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents import PlannerAgent, MemoryAgent, ToolAgent, AgentMessage
from llm_client import LLMClient
from memory.knowledge_base import KnowledgeBase
from memory.user_memory import get_user_memory
from tools.registry import get_registry


def test_multi_agent():
    print("=" * 60)
    print("多Agent协作系统测试")
    print("=" * 60)

    # 1. 初始化各Agent
    print("\n[1/4] 初始化Agent...")
    llm = LLMClient()
    kb = KnowledgeBase(
        api_key=llm.api_key,
        api_url=llm.api_url,
        persist_dir="data/vector_db",
        collection_name="character_knowledge"
    )
    user_memory = get_user_memory()
    tool_registry = get_registry()

    memory_agent = MemoryAgent(knowledge_base=kb, user_memory=user_memory)
    tool_agent = ToolAgent(tool_registry=tool_registry)
    planner = PlannerAgent(
        llm_client=llm,
        memory_agent=memory_agent,
        tool_agent=tool_agent
    )

    memory_agent.start()
    tool_agent.start()
    planner.start()

    print(f"  - MemoryAgent: {memory_agent.name}")
    print(f"  - ToolAgent: {tool_agent.name}")
    print(f"  - PlannerAgent: {planner.name}")

    # 2. 测试MemoryAgent
    print("\n[2/4] 测试MemoryAgent...")
    mem_msg = AgentMessage(
        sender="test", receiver="memory_agent",
        action="get_user_context", payload={}
    )
    mem_result = memory_agent.run(mem_msg)
    print(f"  用户记忆上下文: {'有' if mem_result.content else '无'} ({len(mem_result.content)}字)")

    # 3. 测试ToolAgent
    print("\n[3/4] 测试ToolAgent...")
    tool_msg = AgentMessage(
        sender="test", receiver="tool_agent",
        action="list_tools", payload={}
    )
    tool_result = tool_agent.run(tool_msg)
    print(f"  可用工具: {tool_result.data.get('tools', [])}")

    # 测试时间查询工具
    time_msg = AgentMessage(
        sender="test", receiver="tool_agent",
        action="execute",
        payload={"tool_name": "get_current_time", "arguments": {}}
    )
    time_result = tool_agent.run(time_msg)
    print(f"  时间查询结果: {time_result.content}")

    # 4. 测试PlannerAgent（完整对话）
    print("\n[4/4] 测试PlannerAgent完整对话...")
    test_messages = [
        "你好",
        "现在几点了？",
    ]

    for msg_text in test_messages:
        print(f"\n  用户: {msg_text}")
        chat_msg = AgentMessage(
            sender="user", receiver="planner_agent",
            action="chat",
            payload={"user_message": msg_text, "use_rag": True, "use_tools": True}
        )
        result = planner.run(chat_msg)
        print(f"  Agent: {result.content}")
        if result.data.get("tools_used"):
            print(f"  调用工具: {[t['name'] for t in result.data['tools_used']]}")

    # 5. 显示统计
    print("\n" + "=" * 60)
    print("多Agent协作统计")
    print("=" * 60)
    stats = planner.get_stats()
    print(f"  总调用次数: {stats['total_calls']}")
    print(f"  记忆检索次数: {stats['memory_calls']}")
    print(f"  工具调用次数: {stats['tool_calls']}")
    print(f"  直接回复次数: {stats['direct_replies']}")

    print("\n✅ 多Agent协作系统测试完成！")


if __name__ == "__main__":
    test_multi_agent()
