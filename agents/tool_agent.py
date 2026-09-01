# -*- coding: utf-8 -*-
"""
工具Agent：负责执行具体的工具调用
职责：
- 管理工具注册表
- 执行工具调用（时间查询、提醒、截屏、应用启动等）
- 导出工具schema供PlannerAgent使用
"""
import json
from typing import Dict, Any, List

from .base_agent import BaseAgent, AgentMessage, AgentResult


class ToolAgent(BaseAgent):
    """工具Agent：统一管理和执行所有工具调用"""

    def __init__(self, tool_registry=None):
        super().__init__(
            name="tool_agent",
            description="负责执行各种工具调用，包括时间查询、定时提醒、久坐检测、截屏、应用启动等系统工具"
        )
        self.tool_registry = tool_registry
        self._call_history = []

    def set_tool_registry(self, registry):
        """设置工具注册表"""
        self.tool_registry = registry

    def run(self, message: AgentMessage) -> AgentResult:
        """
        处理工具执行请求
        支持的action:
        - execute: 执行指定工具
        - list_tools: 列出所有可用工具
        - get_schemas: 获取工具的Function Calling schema
        - get_history: 获取工具调用历史
        """
        action = message.action
        payload = message.payload

        try:
            if action == "execute":
                return self._execute_tool(
                    payload.get("tool_name", ""),
                    payload.get("arguments", {})
                )
            elif action == "list_tools":
                return self._list_tools()
            elif action == "get_schemas":
                return self._get_schemas()
            elif action == "get_history":
                return AgentResult(True, data={"history": self._call_history[-10:]})
            else:
                return AgentResult(False, error=f"未知的工具操作: {action}")
        except Exception as e:
            return AgentResult(False, error=f"ToolAgent执行出错: {e}")

    def _execute_tool(self, tool_name: str, arguments: Any) -> AgentResult:
        """执行指定工具"""
        if not self.tool_registry:
            return AgentResult(False, error="工具注册表未初始化")

        # 解析参数
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}
        if not isinstance(arguments, dict):
            arguments = {}

        # 执行工具
        result, success = self.tool_registry.execute_tool(tool_name, arguments)

        # 记录调用历史
        self._call_history.append({
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result,
            "success": success
        })
        if len(self._call_history) > 100:
            self._call_history = self._call_history[-100:]

        return AgentResult(
            success=success,
            content=result,
            data={"tool_name": tool_name, "result": result, "success": success}
        )

    def _list_tools(self) -> AgentResult:
        """列出所有可用工具"""
        if not self.tool_registry:
            return AgentResult(True, data={"tools": []})

        tools = self.tool_registry.list_tools()
        return AgentResult(
            success=True,
            content=f"可用工具: {', '.join(tools)}",
            data={"tools": tools}
        )

    def _get_schemas(self) -> AgentResult:
        """获取工具的Function Calling schema列表"""
        if not self.tool_registry:
            return AgentResult(True, data={"schemas": []})

        schemas = self.tool_registry.get_function_schemas()
        return AgentResult(
            success=True,
            data={"schemas": schemas, "count": len(schemas)}
        )

    def get_function_schemas(self) -> List[Dict]:
        """快捷方法：获取工具schema列表（供LLM Function Calling使用）"""
        if not self.tool_registry:
            return []
        return self.tool_registry.get_function_schemas()

    def execute_tool(self, tool_name: str, arguments: Any) -> tuple:
        """快捷方法：执行工具，返回(结果, 是否成功)"""
        result = self._execute_tool(tool_name, arguments)
        return result.content, result.success
