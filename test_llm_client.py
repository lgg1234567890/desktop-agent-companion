# -*- coding: utf-8 -*-
"""测试LLMClient"""
import sys
import os
sys.path.insert(0, r"D:\my algo\pet")
os.chdir(r"D:\my algo\pet")

from llm_client import LLMClient

llm = LLMClient()
print(f"API URL: {llm.api_url}")
print(f"Model: {llm.model}")
print(f"API Key: {llm.api_key[:10]}...")
print()

print("正在调用LLM...")
reply, ok = llm.chat("你好")
print(f"成功: {ok}")
print(f"回复: {reply}")
