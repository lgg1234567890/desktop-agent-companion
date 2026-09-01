# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'D:\my algo\pet')
from llm_client import LLMClient
from tools.registry import get_registry
from character import SYSTEM_PROMPT

llm = LLMClient()
llm.clear_history()
llm.system_prompt = SYSTEM_PROMPT

registry = get_registry()
print('Tools:', [t['function']['name'] for t in registry.get_function_schemas()])

reply, ok, tools = llm.chat_with_tools('几点了？', registry)
print('回复:', reply)
print('调用工具:', [t['name'] for t in tools])
print('成功:', ok)
