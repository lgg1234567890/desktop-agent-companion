# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'D:\my algo\pet')
from agent_core import get_agent_core

a = get_agent_core()
a.user_memory.add_ongoing("正在准备AI Agent岗位面试", "可以问问准备得怎么样了")

# 直接测试记忆提取器
suggestions = a.user_memory.get_follow_up_suggestions()
print("跟进建议:", suggestions)

context = a.user_memory.get_context()
print("用户上下文:", context[:200])

# 测试_raw_chat
prompt = "请用一句话问用户最近面试准备得怎么样了"
messages = [{"role": "user", "content": prompt}]
resp = a.llm._raw_chat(messages, temperature=0.8, max_tokens=100)
print("_raw_chat回复:", resp)

# 测试generate_follow_up_question
q = a.memory_extractor.generate_follow_up_question(character_prompt=a.llm.system_prompt)
print("主动提问:", repr(q))
