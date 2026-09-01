# -*- coding: utf-8 -*-
"""
Embedding 客户端：调用阿里云百炼 text-embedding-v3 API
"""
import requests


class EmbeddingClient:
    def __init__(self, api_key, api_url=None, model="qwen3.7-text-embedding"):
        self.api_key = api_key
        self.model = model
        if api_url:
            # 从 chat completions URL 推导 embedding URL
            base = api_url.replace("/chat/completions", "")
            self.api_url = f"{base}/embeddings"
        else:
            self.api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"

    def embed(self, text):
        """单文本 embedding，返回 list[float]"""
        result = self.embed_batch([text])
        return result[0] if result else None

    def embed_batch(self, texts):
        """批量 embedding，返回 list[list[float]]"""
        if not texts:
            return []
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": texts,
        }
        try:
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            if resp.status_code != 200:
                print(f"[Embedding] API错误 {resp.status_code}: {resp.text[:200]}")
                return []
            data = resp.json()
            return [item["embedding"] for item in data["data"]]
        except Exception as e:
            print(f"[Embedding] 调用失败: {e}")
            return []
