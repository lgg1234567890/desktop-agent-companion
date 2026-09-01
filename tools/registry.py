# -*- coding: utf-8 -*-
"""
工具注册表：管理所有工具，提供 schema 导出和执行调度
"""
from .base import BaseTool
from .time_tools import GetCurrentTimeTool, SetReminderTool
from .system_tools import CheckIdleTimeTool, TakeScreenshotTool, OpenApplicationTool


class ToolRegistry:
    def __init__(self):
        self._tools = {}
        # 注册默认工具
        self.register(GetCurrentTimeTool())
        self.register(SetReminderTool())
        self.register(CheckIdleTimeTool())
        self.register(TakeScreenshotTool())
        self.register(OpenApplicationTool())

    def register(self, tool):
        if not isinstance(tool, BaseTool):
            raise TypeError(f"工具必须继承 BaseTool，得到 {type(tool)}")
        self._tools[tool.name] = tool

    def get(self, name):
        return self._tools.get(name)

    def get_function_schemas(self):
        """导出所有工具的 OpenAI Function Calling schema 列表"""
        return [tool.to_function_schema() for tool in self._tools.values()]

    def execute_tool(self, name, arguments):
        """
        执行指定工具。
        arguments: dict 或 JSON 字符串
        返回 (结果字符串, 是否成功)
        """
        tool = self._tools.get(name)
        if tool is None:
            return f"未知工具：{name}", False

        # 解析参数
        if isinstance(arguments, str):
            import json
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}
        if not isinstance(arguments, dict):
            arguments = {}

        try:
            result = tool.execute(**arguments)
            return str(result), True
        except Exception as e:
            return f"工具 {name} 执行出错：{e}", False

    def list_tools(self):
        return list(self._tools.keys())


# 全局单例
_registry = None


def get_registry():
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
