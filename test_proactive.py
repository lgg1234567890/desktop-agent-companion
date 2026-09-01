# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'D:\my algo\pet')
from proactive import ProactiveBehavior

# 测试主动行为生成（不依赖agent_core）
pb = ProactiveBehavior(agent_core=None)
print("=== 主动行为测试（生成10条）===")
for i in range(10):
    pb.last_trigger_time = 0  # 重置，让每次都能触发
    pb.next_interval = 0
    msg, btype = pb.generate(chat_window_visible=False)
    print(f"[{btype}] {msg}")

print("\n=== Function Calling 测试 ===")
from agent_core import get_agent_core
a = get_agent_core()
a.clear_history()
reply, ok, tools, ctx = a.chat("现在几点了？农历多少？", use_rag=False, use_tools=True)
print(f"回复: {reply}")
print(f"调用工具: {[t['name'] for t in tools]}")
print(f"成功: {ok}")
