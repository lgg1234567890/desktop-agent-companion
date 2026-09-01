# -*- coding: utf-8 -*-
"""测试API连接"""
import requests

api_key = "sk-8f9e9bcf656345678458845e89bc9a5a"
redirect_url = "https://link.wtturl.cn/?target=https%3A%2F%2Fdashscope.aliyuncs.com%2Fcompatible-mode%2Fv1&scene=im&aid=582478&lang=zh"
direct_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}
payload = {
    "model": "glm-5",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 50,
}

print("=== 测试1: 直接URL (dashscope.aliyuncs.com) ===")
try:
    r = requests.post(direct_url, headers=headers, json=payload, timeout=20, allow_redirects=True)
    print(f"状态码: {r.status_code}")
    if r.status_code == 200:
        print(f"回复: {r.json()['choices'][0]['message']['content'][:80]}")
    else:
        print(f"响应: {r.text[:200]}")
except Exception as e:
    print(f"异常: {e}")

print("\n=== 测试2: 重定向URL + /chat/completions ===")
try:
    test_url = redirect_url + "/chat/completions" if not redirect_url.endswith("/chat/completions") else redirect_url
    r = requests.post(test_url, headers=headers, json=payload, timeout=20, allow_redirects=True)
    print(f"状态码: {r.status_code}")
    print(f"最终URL: {r.url}")
    if r.status_code == 200:
        print(f"回复: {r.json()['choices'][0]['message']['content'][:80]}")
    else:
        print(f"响应: {r.text[:200]}")
except Exception as e:
    print(f"异常: {e}")

print("\n=== 测试3: 重定向URL (不带后缀) ===")
try:
    r = requests.post(redirect_url, headers=headers, json=payload, timeout=20, allow_redirects=True)
    print(f"状态码: {r.status_code}")
    print(f"最终URL: {r.url}")
    if r.status_code == 200:
        print(f"回复: {r.text[:200]}")
    else:
        print(f"响应: {r.text[:200]}")
except Exception as e:
    print(f"异常: {e}")
