# -*- coding: utf-8 -*-
"""
记忆Agent：负责RAG检索和用户长期记忆的读写
职责：
- 检索角色背景知识（RAG向量库）
- 读取/写入用户记忆（基本信息、事件、性格、偏好）
- 生成记忆上下文注入到对话中
"""
import os
import sys
from typing import Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS

from .base_agent import BaseAgent, AgentMessage, AgentResult


class MemoryAgent(BaseAgent):
    """记忆Agent：管理RAG知识库和用户长期记忆"""

    def __init__(self, knowledge_base=None, user_memory=None):
        super().__init__(
            name="memory_agent",
            description="负责RAG知识检索和用户长期记忆管理，包括角色背景知识检索、用户信息读写、记忆上下文生成"
        )
        self.kb = knowledge_base
        self.user_memory = user_memory
        self.kb_dir = os.path.join(BASE_DIR, "data", "knowledge")

    def set_knowledge_base(self, kb):
        """设置RAG知识库"""
        self.kb = kb

    def set_user_memory(self, user_memory):
        """设置用户记忆"""
        self.user_memory = user_memory

    def run(self, message: AgentMessage) -> AgentResult:
        """
        处理记忆相关请求
        支持的action:
        - retrieve_knowledge: 检索角色背景知识
        - get_user_context: 获取用户记忆上下文
        - save_memory: 保存用户记忆
        - get_memory_stats: 获取记忆统计
        """
        action = message.action
        payload = message.payload

        try:
            if action == "retrieve_knowledge":
                return self._retrieve_knowledge(payload.get("query", ""), payload.get("top_k", 3))
            elif action == "get_user_context":
                return self._get_user_context()
            elif action == "save_memory":
                return self._save_memory(payload)
            elif action == "get_memory_stats":
                return self._get_memory_stats()
            else:
                return AgentResult(False, error=f"未知的记忆操作: {action}")
        except Exception as e:
            return AgentResult(False, error=f"MemoryAgent执行出错: {e}")

    def _retrieve_knowledge(self, query: str, top_k: int = 3) -> AgentResult:
        """RAG检索角色背景知识"""
        if not self.kb:
            return AgentResult(True, content="", data={"context": ""})

        try:
            if self.kb.vector_store.count() == 0:
                self.kb.load_and_index(self.kb_dir)

            context = self.kb.build_context(query, top_k=top_k, min_score=0.25)
            return AgentResult(
                success=True,
                content=context,
                data={"context": context, "has_result": bool(context)}
            )
        except Exception as e:
            print(f"[MemoryAgent] RAG检索失败: {e}")
            return AgentResult(True, content="", data={"context": "", "error": str(e)})

    def _get_user_context(self) -> AgentResult:
        """获取用户记忆上下文文本"""
        if not self.user_memory:
            return AgentResult(True, content="", data={"context": ""})

        context = self.user_memory.get_context()
        return AgentResult(
            success=True,
            content=context,
            data={"context": context, "has_memory": bool(context)}
        )

    def _save_memory(self, payload: Dict[str, Any]) -> AgentResult:
        """保存用户记忆"""
        if not self.user_memory:
            return AgentResult(False, error="用户记忆未初始化")

        category = payload.get("category", "")
        content = payload.get("content", "")

        try:
            if category == "event":
                self.user_memory.add_event(content)
            elif category == "ongoing":
                self.user_memory.add_ongoing(content)
            elif category == "personality":
                self.user_memory.add_personality(content)
            elif category == "info":
                if ":" in content:
                    k, v = content.split(":", 1)
                    self.user_memory.add_basic_info(k.strip(), v.strip())
            elif category == "preference":
                if ":" in content:
                    cat, val = content.split(":", 1)
                    self.user_memory.add_preference(cat.strip(), val.strip())
            else:
                return AgentResult(False, error=f"未知的记忆类别: {category}")

            return AgentResult(True, content=f"记忆已保存: {category}")
        except Exception as e:
            return AgentResult(False, error=f"保存记忆失败: {e}")

    def _get_memory_stats(self) -> AgentResult:
        """获取记忆统计"""
        if not self.user_memory:
            return AgentResult(True, data={"stats": {}})

        stats = self.user_memory.get_stats()
        return AgentResult(True, data={"stats": stats})

    def build_full_context(self, query: str) -> str:
        """
        构建完整的记忆上下文（RAG + 用户记忆）
        供PlannerAgent注入到System Prompt中
        """
        parts = []

        # RAG背景知识
        rag_result = self._retrieve_knowledge(query)
        if rag_result.content:
            parts.append("【相关背景知识】\n" + rag_result.content)

        # 用户记忆
        user_result = self._get_user_context()
        if user_result.content:
            parts.append("【关于用户的记忆】\n" + user_result.content +
                         "\n（请在对话中自然地参考这些信息，让用户感受到你记得他/她）")

        return "\n\n".join(parts)
