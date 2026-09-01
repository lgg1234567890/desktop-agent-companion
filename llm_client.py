# -*- coding: utf-8 -*-
"""大模型对话客户端，含上下文记忆、RAG注入、Function Calling"""
import json
import requests
from config import LLM_TIMEOUT, MAX_HISTORY, LLM_API_KEY, LLM_MODEL, LLM_API_URL
from character import SYSTEM_PROMPT

try:
    from character_settings import load_api_config
except ImportError:
    # 无 PyQt5 环境下的 fallback
    def load_api_config():
        return {"api_key": LLM_API_KEY, "api_url": LLM_API_URL, "model": LLM_MODEL}


class LLMClient:
    def __init__(self):
        self.system_prompt = SYSTEM_PROMPT
        self.history = []
        self._load_config()

    def _load_config(self):
        """从JSON配置文件加载API配置"""
        cfg = load_api_config()
        self.api_key = cfg.get("api_key", "").strip()
        self.model = cfg.get("model", "glm-5").strip() or "glm-5"
        self.api_url = cfg.get("api_url", "").strip()

    def reload_config(self):
        """重新加载配置（角色设置保存后调用）"""
        self._load_config()

    def _build_messages(self, extra_system=None):
        """构建 messages 列表，支持额外的 system 上下文（如RAG检索结果、用户记忆等）"""
        system_content = self.system_prompt
        if extra_system:
            system_content = system_content + "\n\n" + extra_system
        messages = [{"role": "system", "content": system_content}] + self.history
        return messages

    def _raw_chat(self, messages, temperature=0.7, max_tokens=300):
        """
        底层对话接口：直接传入 messages，不修改历史。
        供记忆提取、主动提问等辅助功能使用。
        返回回复文本或None。
        """
        self._load_config()
        if not self.api_key or not self.api_url:
            return None
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=LLM_TIMEOUT)
            if resp.status_code != 200:
                return None
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception:
            return None

    def chat(self, user_message, rag_context=None):
        """
        发送消息并获取回复，返回 (回复文本, 是否成功)
        rag_context: 可选，RAG检索到的上下文文本，会注入到 system prompt 中
        """
        self._load_config()

        if not self.api_key:
            return "（未配置API Key，请在角色设置中配置）", False
        if not self.api_url:
            return "（未配置API地址，请在角色设置中配置）", False

        self.history.append({"role": "user", "content": user_message})
        if len(self.history) > MAX_HISTORY * 2:
            self.history = self.history[-MAX_HISTORY * 2:]

        messages = self._build_messages(extra_system=rag_context)

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 300,
            }
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=LLM_TIMEOUT)
            if resp.status_code == 401:
                return "（API Key无效或已过期，请在角色设置中更换）", False
            if resp.status_code == 404:
                return f"（模型{self.model}不存在或API地址错误，请检查）", False
            if resp.status_code != 200:
                return f"（API错误 {resp.status_code}：{resp.text[:80]}）", False
            data = resp.json()
            reply = data["choices"][0]["message"]["content"].strip()
            self.history.append({"role": "assistant", "content": reply})
            return reply, True
        except requests.exceptions.Timeout:
            if self.history and self.history[-1]["role"] == "user":
                self.history.pop()
            return "（请求超时，请检查网络）", False
        except requests.exceptions.ConnectionError:
            if self.history and self.history[-1]["role"] == "user":
                self.history.pop()
            return "（网络连接失败，请检查网络）", False
        except Exception as e:
            if self.history and self.history[-1]["role"] == "user":
                self.history.pop()
            err_msg = str(e)[:60]
            return f"（调用失败：{err_msg}）", False

    def chat_with_tools(self, user_message, tool_registry, rag_context=None, max_tool_calls=5):
        """
        支持 Function Calling 的对话，自动处理多轮工具调用。
        返回 (最终回复文本, 是否成功, 调用的工具列表)
        """
        self._load_config()

        if not self.api_key or not self.api_url:
            return "（API未配置）", False, []

        self.history.append({"role": "user", "content": user_message})
        if len(self.history) > MAX_HISTORY * 2:
            self.history = self.history[-MAX_HISTORY * 2:]

        tools = tool_registry.get_function_schemas()
        called_tools = []
        messages = self._build_messages(extra_system=rag_context)

        for _ in range(max_tool_calls):
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": "auto",
                    "temperature": 0.7,
                    "max_tokens": 500,
                }
                resp = requests.post(self.api_url, headers=headers, json=payload, timeout=LLM_TIMEOUT)
                if resp.status_code != 200:
                    return f"（API错误 {resp.status_code}）", False, called_tools

                data = resp.json()
                message = data["choices"][0]["message"]
                tool_calls = message.get("tool_calls")

                if not tool_calls:
                    # 没有工具调用，直接返回文本回复
                    reply = (message.get("content") or "").strip()
                    self.history.append({"role": "assistant", "content": reply})
                    return reply, True, called_tools

                # 有工具调用，先把 assistant 的 tool_calls 消息加入历史
                messages.append({
                    "role": "assistant",
                    "content": message.get("content") or "",
                    "tool_calls": tool_calls,
                })
                self.history.append({
                    "role": "assistant",
                    "content": message.get("content") or "",
                    "tool_calls": tool_calls,
                })

                # 执行每个工具调用
                for tc in tool_calls:
                    func = tc.get("function", {})
                    tool_name = func.get("name", "")
                    tool_args = func.get("arguments", "{}")
                    tool_id = tc.get("id", "")

                    result, success = tool_registry.execute_tool(tool_name, tool_args)
                    called_tools.append({"name": tool_name, "args": tool_args, "result": result, "success": success})

                    # 把工具结果加入消息
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": result,
                    })
                    self.history.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": result,
                    })

                # 继续循环，让模型基于工具结果生成最终回复

            except Exception as e:
                if self.history and self.history[-1]["role"] == "user":
                    self.history.pop()
                return f"（调用失败：{str(e)[:60]}）", False, called_tools

        # 超过最大工具调用次数，返回最后一条assistant消息
        last_reply = ""
        for msg in reversed(self.history):
            if msg["role"] == "assistant" and msg.get("content"):
                last_reply = msg["content"]
                break
        return last_reply or "（工具调用次数超限）", True, called_tools

    def clear_history(self):
        self.history = []
