# -*- coding: utf-8 -*-
"""
工具基类：所有 Agent 工具继承此类
"""
from abc import ABC, abstractmethod


class BaseTool(ABC):
    """工具基类，定义统一接口"""

    @property
    @abstractmethod
    def name(self):
        """工具名称，英文小写+下划线，如 get_current_time"""
        pass

    @property
    @abstractmethod
    def description(self):
        """工具描述，告诉 LLM 什么时候用这个工具"""
        pass

    @property
    @abstractmethod
    def parameters(self):
        """
        JSON Schema 格式的参数定义，例如：
        {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名"}
            },
            "required": ["city"]
        }
        """
        pass

    @abstractmethod
    def execute(self, **kwargs):
        """执行工具，返回结果字符串"""
        pass

    def to_function_schema(self):
        """转换为 OpenAI Function Calling 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
