# -*- coding: utf-8 -*-
"""
Agent 核心模块：多Agent协作架构
内部使用 PlannerAgent + MemoryAgent + ToolAgent 三Agent协作
对外接口保持不变，供 pet_agent.py 和 character_settings.py 调用

多Agent架构：
用户消息 → PlannerAgent(主控) → MemoryAgent(RAG+用户记忆) → LLM决策 → ToolAgent(工具执行) → 生成回复
"""
import os
import sys
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS

from config import LLM_API_KEY, LLM_API_URL, LLM_MODEL
from memory.knowledge_base import KnowledgeBase
from memory.user_memory import get_user_memory
from memory.memory_extractor import MemoryExtractor
from tools.registry import get_registry
from llm.character_builder import CharacterBuilder
from llm_client import LLMClient
from agents import PlannerAgent, MemoryAgent, ToolAgent, AgentMessage


class PetAgentCore:
    """
    桌宠 Agent 核心：多Agent协作架构
    对外接口与单Agent版本完全兼容，内部已升级为三Agent协作
    """

    def __init__(self):
        self.api_key = LLM_API_KEY
        self.api_url = LLM_API_URL
        self.model = LLM_MODEL

        # LLM 客户端（共享给PlannerAgent）
        self.llm = LLMClient()

        # RAG 知识库（角色背景知识）
        self.kb = None
        self.kb_dir = os.path.join(BASE_DIR, "data", "knowledge")
        self.persist_dir = os.path.join(BASE_DIR, "data", "vector_db")
        self._init_knowledge_base()

        # Function Calling 工具注册
        self.tool_registry = get_registry()
        self._setup_reminder_callback()

        # 角色画像生成器
        self.character_builder = CharacterBuilder(
            api_key=self.api_key, api_url=self.api_url, model=self.model
        )

        # 用户长期记忆
        self.user_memory = get_user_memory()
        self.memory_extractor = MemoryExtractor(self.llm)

        # ========== 多Agent协作系统 ==========
        # 记忆Agent：负责RAG检索和用户记忆
        self.memory_agent = MemoryAgent(
            knowledge_base=self.kb,
            user_memory=self.user_memory
        )

        # 工具Agent：负责工具执行
        self.tool_agent = ToolAgent(tool_registry=self.tool_registry)

        # 主控规划Agent：协调记忆Agent和工具Agent
        self.planner_agent = PlannerAgent(
            llm_client=self.llm,
            memory_agent=self.memory_agent,
            tool_agent=self.tool_agent,
            memory_extractor=self.memory_extractor
        )

        # 启动所有Agent
        self.memory_agent.start()
        self.tool_agent.start()
        self.planner_agent.start()

        # 当前角色
        self.current_character = "张起灵"

        print("[AgentCore] 多Agent协作系统已初始化 (Planner + Memory + Tool)")

    def _init_knowledge_base(self):
        """初始化 RAG 知识库"""
        try:
            self.kb = KnowledgeBase(
                api_key=self.api_key,
                api_url=self.api_url,
                persist_dir=self.persist_dir,
                collection_name="character_knowledge",
            )
            if self.kb.vector_store.count() == 0:
                print("[AgentCore] 知识库为空，将在首次对话时构建")
            else:
                print(f"[AgentCore] 知识库已加载，共 {self.kb.vector_store.count()} 条记录")
        except Exception as e:
            print(f"[AgentCore] 知识库初始化失败: {e}")
            self.kb = None

    def _setup_reminder_callback(self):
        """设置提醒工具的回调"""
        from tools.time_tools import SetReminderTool
        SetReminderTool.reminder_callback = self._default_reminder_handler

    def _default_reminder_handler(self, delay_ms, message):
        print(f"[AgentCore] 提醒已设置: {delay_ms}ms 后 - {message}")

    def set_reminder_callback(self, callback):
        """主程序调用此方法设置真实的提醒回调"""
        from tools.time_tools import SetReminderTool
        SetReminderTool.reminder_callback = callback

    def chat(self, user_message, use_rag=True, use_tools=True, extract_memory=True):
        """
        统一对话入口：多Agent协作处理
        返回 (回复文本, 是否成功, 调用的工具列表, RAG上下文)
        接口与单Agent版本完全兼容
        """
        # 通过PlannerAgent协调多Agent
        msg = AgentMessage(
            sender="user",
            receiver="planner_agent",
            action="chat",
            payload={
                "user_message": user_message,
                "use_rag": use_rag,
                "use_tools": use_tools,
                "extract_memory": extract_memory
            }
        )

        result = self.planner_agent.run(msg)

        if result.success:
            reply = result.content
            tools_used = result.data.get("tools_used", [])
            rag_context = result.data.get("memory_context", "")
            return reply, True, tools_used, rag_context
        else:
            return result.error or "（处理失败）", False, [], ""

    def generate_character(self, name, source):
        """生成角色画像 + System Prompt"""
        return self.character_builder.generate_and_save(name, source)

    def load_character(self, name):
        """加载已保存的角色画像"""
        return self.character_builder.load_profile(name)

    def list_saved_characters(self):
        """列出已保存的角色"""
        profile_dir = os.path.join(BASE_DIR, "data", "character_profiles")
        if not os.path.exists(profile_dir):
            return []
        return [f.replace(".json", "") for f in os.listdir(profile_dir) if f.endswith(".json")]

    def clear_history(self):
        """清空对话历史（不清空长期记忆）"""
        self.planner_agent.clear_history()

    def set_system_prompt(self, prompt):
        """设置角色 System Prompt"""
        self.llm.system_prompt = prompt

    def get_user_memory_stats(self):
        """获取用户记忆统计"""
        return self.user_memory.get_stats()

    def get_user_memory_context(self):
        """获取用户记忆上下文文本"""
        return self.user_memory.get_context()

    def generate_follow_up_question(self):
        """
        生成一个主动跟进的问题（基于用户记忆）。
        用于桌宠主动开启对话。返回空字符串表示没有可跟进的话题。
        """
        return self.memory_extractor.generate_follow_up_question(
            character_prompt=self.llm.system_prompt
        )

    def add_user_memory_manual(self, category, content):
        """手动添加用户记忆（用于用户主动分享时立即保存）"""
        msg = AgentMessage(
            sender="user",
            receiver="memory_agent",
            action="save_memory",
            payload={"category": category, "content": content}
        )
        self.memory_agent.run(msg)

    def get_multi_agent_status(self):
        """获取多Agent协作系统状态（用于调试和展示）"""
        return self.planner_agent.get_agent_status()

    def get_agent_stats(self):
        """获取多Agent协作统计"""
        return self.planner_agent.get_stats()


# 全局单例
_agent_core = None


def get_agent_core():
    global _agent_core
    if _agent_core is None:
        _agent_core = PetAgentCore()
    return _agent_core
