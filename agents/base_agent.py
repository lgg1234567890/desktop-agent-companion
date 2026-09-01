# -*- coding: utf-8 -*-
"""
多Agent协作系统基类
每个Agent有独立的职责、System Prompt和执行逻辑
Agent间通过结构化消息通信
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class AgentMessage:
    """Agent间通信的结构化消息"""
    def __init__(self, sender: str, receiver: str, action: str, payload: Dict[str, Any] = None):
        self.sender = sender
        self.receiver = receiver
        self.action = action  # query / retrieve / execute / respond
        self.payload = payload or {}

    def to_dict(self):
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "action": self.action,
            "payload": self.payload
        }

    def __repr__(self):
        return f"AgentMessage({self.sender}->{self.receiver}: {self.action})"


class AgentResult:
    """Agent执行结果"""
    def __init__(self, success: bool, content: str = "", data: Dict[str, Any] = None, error: str = ""):
        self.success = success
        self.content = content
        self.data = data or {}
        self.error = error

    def to_dict(self):
        return {
            "success": self.success,
            "content": self.content,
            "data": self.data,
            "error": self.error
        }


class BaseAgent(ABC):
    """所有Agent的基类"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self._is_running = False

    @abstractmethod
    def run(self, message: AgentMessage) -> AgentResult:
        """执行Agent的核心逻辑，返回结果"""
        pass

    @property
    def is_running(self):
        return self._is_running

    def start(self):
        self._is_running = True
        print(f"[Agent] {self.name} 已启动")

    def stop(self):
        self._is_running = False
        print(f"[Agent] {self.name} 已停止")

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"
