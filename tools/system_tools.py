# -*- coding: utf-8 -*-
"""
系统工具：空闲检测、截图、打开应用
"""
import os
import datetime
from .base import BaseTool


class CheckIdleTimeTool(BaseTool):
    """检测用户空闲时长（Windows 平台）"""

    @property
    def name(self):
        return "check_idle_time"

    @property
    def description(self):
        return "检测用户已经多久没有操作电脑（鼠标/键盘），用于久坐提醒、健康关怀场景。返回空闲分钟数。"

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def execute(self, **kwargs):
        try:
            import ctypes
            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
            ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
            idle_ms = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
            idle_min = idle_ms / 1000 / 60
            if idle_min >= 60:
                return f"用户已空闲 {idle_min:.0f} 分钟（超过1小时，建议提醒休息）"
            elif idle_min >= 30:
                return f"用户已空闲 {idle_min:.0f} 分钟（久坐状态，可提醒活动）"
            else:
                return f"用户已空闲 {idle_min:.1f} 分钟（正常使用中）"
        except Exception as e:
            return f"空闲检测失败：{e}"


class TakeScreenshotTool(BaseTool):
    """截取屏幕（仅返回描述，不保存文件）"""

    @property
    def name(self):
        return "take_screenshot"

    @property
    def description(self):
        return "截取当前屏幕画面，用于了解用户正在做什么、屏幕上有什么内容。返回截图的基本信息。"

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def execute(self, **kwargs):
        try:
            from PIL import ImageGrab
            screenshot = ImageGrab.grab()
            width, height = screenshot.size
            # 保存到临时目录供后续分析
            save_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data", "latest_screenshot.png"
            )
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            screenshot.save(save_path)
            return f"已截取屏幕，分辨率 {width}x{height}，保存至 {save_path}"
        except ImportError:
            return "截图失败：未安装 Pillow 库"
        except Exception as e:
            return f"截图失败：{e}"


class OpenApplicationTool(BaseTool):
    """打开指定应用程序"""

    # 常用应用路径映射
    APP_MAP = {
        "浏览器": "chrome.exe",
        "chrome": "chrome.exe",
        "记事本": "notepad.exe",
        "计算器": "calc.exe",
        "画图": "mspaint.exe",
        "资源管理器": "explorer.exe",
        "命令行": "cmd.exe",
    }

    @property
    def name(self):
        return "open_application"

    @property
    def description(self):
        return "打开指定的应用程序，如浏览器、记事本、计算器等。当用户要求打开某个软件时使用。"

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "应用名称，如'浏览器''记事本''计算器'",
                },
            },
            "required": ["app_name"],
        }

    def execute(self, app_name="", **kwargs):
        if not app_name:
            return "请指定要打开的应用名称"
        exe = self.APP_MAP.get(app_name, app_name)
        try:
            os.startfile(exe)
            return f"正在打开：{app_name}"
        except Exception as e:
            return f"打开应用失败：{app_name}（{e}）"
