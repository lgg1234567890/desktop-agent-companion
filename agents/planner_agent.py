# -*- coding: utf-8 -*-
"""
主控规划Agent（Planner Agent）：多Agent协作的核心调度者
职责：
- 接收用户消息，理解意图
- 调用MemoryAgent获取RAG背景和用户记忆
- 通过Function Calling决定是否调用ToolAgent执行工具
- 基于工具结果生成最终的角色化回复
- 管理对话历史和多Agent协作流程

架构：
用户消息 → PlannerAgent → MemoryAgent(获取上下文) → LLM决策 → ToolAgent(执行工具) → LLM生成回复 → 返回
"""
import os
import sys
import json
import threading
from typing import Dict, Any, List, Tuple, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS

from .base_agent import BaseAgent, AgentMessage, AgentResult
from .memory_agent import MemoryAgent
from .tool_agent import ToolAgent

try:
    from llm_client import LLMClient
except ImportError:
    LLMClient = None

try:
    from memory.memory_extractor import MemoryExtractor
except ImportError:
    MemoryExtractor = None


# 工具使用说明：注入到System Prompt
TOOL_USAGE_HINT = """【工具使用规则】
你可以使用以下工具来帮助回答问题：
- get_current_time：查询当前时间
- set_reminder：设置定时提醒
- check_idle_time：检测用户久坐时间
- take_screenshot：截取屏幕
- open_application：打开应用程序

当用户询问时间、日期、需要提醒、久坐提醒等问题时，必须主动调用对应工具，不要凭感觉回答或说"不知道"。调用工具是你能力的一部分，不算跳出角色。"""


class PlannerAgent(BaseAgent):
    """主控规划Agent：协调MemoryAgent和ToolAgent完成多Agent协作对话"""

    def __init__(self, llm_client=None, memory_agent=None, tool_agent=None,
                 memory_extractor=None):
        super().__init__(
            name="planner_agent",
            description="主控规划Agent，负责理解用户意图，协调记忆Agent和工具Agent完成多Agent协作对话"
        )
        self.llm = llm_client
        self.memory_agent = memory_agent or MemoryAgent()
        self.tool_agent = tool_agent or ToolAgent()
        self.memory_extractor = memory_extractor

        # 对话历史
        self.history = []
        self.max_history = 20  # 保留最近10轮

        # 协作统计
        self.stats = {
            "total_calls": 0,
            "memory_calls": 0,
            "tool_calls": 0,
            "direct_replies": 0
        }

    def set_llm(self, llm_client):
        """设置LLM客户端"""
        self.llm = llm_client

    def set_memory_agent(self, agent: MemoryAgent):
        """设置记忆Agent"""
        self.memory_agent = agent

    def set_tool_agent(self, agent: ToolAgent):
        """设置工具Agent"""
        self.tool_agent = agent

    def run(self, message: AgentMessage) -> AgentResult:
        """
        处理用户消息，协调多Agent完成对话
        payload需要包含: user_message
        """
        user_message = message.payload.get("user_message", "")
        use_rag = message.payload.get("use_rag", True)
        use_tools = message.payload.get("use_tools", True)
        extract_memory = message.payload.get("extract_memory", True)

        if not user_message:
            return AgentResult(False, error="用户消息为空")

        self.stats["total_calls"] += 1

        try:
            # ========== 第1步：调用MemoryAgent获取上下文 ==========
            memory_context = ""
            if use_rag:
                mem_msg = AgentMessage(
                    sender=self.name,
                    receiver="memory_agent",
                    action="retrieve_knowledge",
                    payload={"query": user_message, "top_k": 3}
                )
                mem_result = self.memory_agent.run(mem_msg)
                self.stats["memory_calls"] += 1
                if mem_result.success and mem_result.content:
                    memory_context = mem_result.content

            # 获取用户记忆上下文
            user_ctx_msg = AgentMessage(
                sender=self.name,
                receiver="memory_agent",
                action="get_user_context",
                payload={}
            )
            user_ctx_result = self.memory_agent.run(user_ctx_msg)
            user_context = user_ctx_result.content if user_ctx_result.success else ""

            # 构建完整System上下文
            full_context = self._build_system_context(memory_context, user_context)

            # ========== 第2步：调用LLM决策（Function Calling） ==========
            if use_tools and self.tool_agent:
                reply, ok, tools_used = self._chat_with_tools(user_message, full_context)
            else:
                reply, ok = self._chat_direct(user_message, full_context)
                tools_used = []

            if tools_used:
                self.stats["tool_calls"] += 1
            else:
                self.stats["direct_replies"] += 1

            # ========== 第3步：异步提取用户记忆 ==========
            if extract_memory and ok and self.memory_extractor:
                if self.memory_extractor.should_extract():
                    threading.Thread(
                        target=self.memory_extractor.extract,
                        args=(user_message, reply),
                        daemon=True
                    ).start()

            # 返回结果
            return AgentResult(
                success=ok,
                content=reply,
                data={
                    "reply": reply,
                    "tools_used": tools_used,
                    "memory_context": memory_context,
                    "user_context": user_context,
                    "stats": self.stats.copy()
                }
            )

        except Exception as e:
            print(f"[PlannerAgent] 处理失败: {e}")
            return AgentResult(False, error=f"PlannerAgent处理失败: {e}")

    def _build_system_context(self, rag_context: str = "", user_context: str = "") -> str:
        """构建完整的System上下文"""
        parts = [TOOL_USAGE_HINT]

        if user_context:
            parts.append("【关于用户的记忆】\n" + user_context +
                         "\n（请在对话中自然地参考这些信息，让用户感受到你记得他/她）")

        if rag_context:
            parts.append("【相关背景知识】\n" + rag_context)

        return "\n\n".join(parts)

    def _chat_direct(self, user_message: str, context: str) -> Tuple[str, bool]:
        """直接对话（不使用工具）"""
        if not self.llm:
            return "（LLM未初始化）", False

        # 保存原始system_prompt，临时添加上下文
        original_system = self.llm.system_prompt
        try:
            self.llm.system_prompt = original_system + "\n\n" + context if context else original_system
            reply, ok = self.llm.chat(user_message)
            return reply, ok
        finally:
            self.llm.system_prompt = original_system

    def _chat_with_tools(self, user_message: str, context: str,
                         max_tool_calls: int = 5) -> Tuple[str, bool, List[Dict]]:
        """
        支持Function Calling的对话，协调ToolAgent执行工具
        返回 (最终回复, 是否成功, 调用的工具列表)
        """
        if not self.llm:
            return "（LLM未初始化）", False, []

        # 获取工具schema
        tool_schemas = self.tool_agent.get_function_schemas()
        if not tool_schemas:
            return self._chat_direct(user_message, context) + ([],)

        # 构建消息
        original_system = self.llm.system_prompt
        enhanced_system = original_system + "\n\n" + context if context else original_system

        messages = [{"role": "system", "content": enhanced_system}]
        messages.extend(self.history[-self.max_history:])
        messages.append({"role": "user", "content": user_message})

        called_tools = []

        for _ in range(max_tool_calls):
            try:
                # 调用LLM
                response = self.llm._raw_chat_with_tools(messages, tool_schemas)
                if response is None:
                    return "（API调用失败）", False, called_tools

                message = response.get("message", {})
                tool_calls = message.get("tool_calls")

                if not tool_calls:
                    # 没有工具调用，直接返回
                    reply = (message.get("content") or "").strip()
                    self._update_history(user_message, reply)
                    return reply, True, called_tools

                # 有工具调用，加入消息历史
                messages.append({
                    "role": "assistant",
                    "content": message.get("content") or "",
                    "tool_calls": tool_calls
                })

                # 调用ToolAgent执行每个工具
                for tc in tool_calls:
                    func = tc.get("function", {})
                    tool_name = func.get("name", "")
                    tool_args = func.get("arguments", "{}")
                    tool_id = tc.get("id", "")

                    # 通过ToolAgent执行
                    tool_msg = AgentMessage(
                        sender=self.name,
                        receiver="tool_agent",
                        action="execute",
                        payload={"tool_name": tool_name, "arguments": tool_args}
                    )
                    tool_result = self.tool_agent.run(tool_msg)
                    result_str = tool_result.content

                    called_tools.append({
                        "name": tool_name,
                        "args": tool_args,
                        "result": result_str,
                        "success": tool_result.success
                    })

                    # 工具结果加入消息
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": result_str
                    })

                # 继续循环，让LLM基于工具结果生成最终回复

            except Exception as e:
                print(f"[PlannerAgent] 工具调用循环出错: {e}")
                return f"（调用失败：{str(e)[:60]}）", False, called_tools

        # 超过最大工具调用次数
        last_reply = ""
        for msg in reversed(messages):
            if msg["role"] == "assistant" and msg.get("content"):
                last_reply = msg["content"]
                break
        self._update_history(user_message, last_reply or "（工具调用次数超限）")
        return last_reply or "（工具调用次数超限）", True, called_tools

    def _update_history(self, user_msg: str, reply: str):
        """更新对话历史"""
        self.history.append({"role": "user", "content": user_msg})
        self.history.append({"role": "assistant", "content": reply})
        if len(self.history) > self.max_history * 2:
            self.history = self.history[-self.max_history * 2:]

    def clear_history(self):
        """清空对话历史"""
        self.history = []
        if self.llm:
            self.llm.clear_history()

    def get_stats(self) -> Dict:
        """获取多Agent协作统计"""
        return self.stats.copy()

    def get_agent_status(self) -> Dict:
        """获取所有Agent的状态"""
        return {
            "planner": {"running": self.is_running, "stats": self.stats},
            "memory_agent": {"running": self.memory_agent.is_running},
            "tool_agent": {"running": self.tool_agent.is_running,
                           "tools": self.tool_agent.tool_registry.list_tools() if self.tool_agent.tool_registry else []}
        }
