# -*- coding: utf-8 -*-
"""
Agent 核心模块：封装 RAG 检索 + Function Calling + 角色画像 + 用户长期记忆
供 pet_agent.py 和 character_settings.py 调用
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


# 工具使用说明：注入到 System Prompt，确保模型不会因人设太强而拒绝调用工具
TOOL_USAGE_HINT = """【工具使用规则】
你可以使用以下工具来帮助回答问题：
- get_current_time：查询当前时间
- set_reminder：设置定时提醒
- check_idle_time：检测用户久坐时间
- take_screenshot：截取屏幕
- open_application：打开应用程序

当用户询问时间、日期、需要提醒、久坐提醒等问题时，必须主动调用对应工具，不要凭感觉回答或说"不知道"。调用工具是你能力的一部分，不算跳出角色。"""


class PetAgentCore:
    """桌宠 Agent 核心：统一管理 RAG、工具、角色、用户记忆、对话"""

    def __init__(self):
        self.api_key = LLM_API_KEY
        self.api_url = LLM_API_URL
        self.model = LLM_MODEL

        # LLM 客户端
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

        # 当前角色
        self.current_character = "张起灵"

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

    def _build_system_context(self, rag_context=""):
        """
        构建完整的 System 上下文：
        工具使用说明 + 用户记忆 + RAG背景知识
        """
        parts = [TOOL_USAGE_HINT]

        # 用户记忆
        user_ctx = self.user_memory.get_context()
        if user_ctx:
            parts.append("【关于用户的记忆】\n" + user_ctx + "\n（请在对话中自然地参考这些信息，让用户感受到你记得他/她）")

        # RAG 背景知识
        if rag_context:
            parts.append("【相关背景知识】\n" + rag_context)

        return "\n\n".join(parts)

    def chat(self, user_message, use_rag=True, use_tools=True, extract_memory=True):
        """
        统一对话入口：自动 RAG 检索 + Function Calling + 用户记忆注入 + 记忆提取
        返回 (回复文本, 是否成功, 调用的工具列表, RAG上下文)
        """
        # 1. RAG 检索
        rag_context = ""
        if use_rag and self.kb:
            try:
                if self.kb.vector_store.count() == 0:
                    self.kb.load_and_index(self.kb_dir)
                rag_context = self.kb.build_context(user_message, top_k=3, min_score=0.25)
            except Exception as e:
                print(f"[AgentCore] RAG检索失败: {e}")

        # 2. 构建完整 System 上下文
        full_context = self._build_system_context(rag_context)

        # 3. Function Calling 对话
        if use_tools:
            reply, ok, tools_used = self.llm.chat_with_tools(
                user_message, self.tool_registry, rag_context=full_context
            )
        else:
            reply, ok = self.llm.chat(user_message, rag_context=full_context)
            tools_used = []

        # 4. 异步提取用户记忆（不阻塞回复）
        if extract_memory and ok and self.memory_extractor.should_extract():
            threading.Thread(
                target=self.memory_extractor.extract,
                args=(user_message, reply),
                daemon=True
            ).start()

        return reply, ok, tools_used, rag_context

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
        self.llm.clear_history()

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
        if category == "event":
            self.user_memory.add_event(content)
        elif category == "ongoing":
            self.user_memory.add_ongoing(content)
        elif category == "personality":
            self.user_memory.add_personality(content)
        elif category == "info":
            # content 格式 "key:value"
            if ":" in content:
                k, v = content.split(":", 1)
                self.user_memory.add_basic_info(k.strip(), v.strip())


# 全局单例
_agent_core = None


def get_agent_core():
    global _agent_core
    if _agent_core is None:
        _agent_core = PetAgentCore()
    return _agent_core
