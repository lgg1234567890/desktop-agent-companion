# -*- coding: utf-8 -*-
"""
时间与提醒工具
"""
import datetime
from .base import BaseTool
from .lunar import solar_to_lunar


class GetCurrentTimeTool(BaseTool):
    """获取当前日期时间（含阳历、农历、星期）"""

    @property
    def name(self):
        return "get_current_time"

    @property
    def description(self):
        return "获取当前的日期和时间，包括阳历日期、农历日期、星期几、生肖年。当用户问时间、日期、星期、农历、生肖、或需要基于当前时间做决策时使用。"

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def execute(self, **kwargs):
        now = datetime.datetime.now()
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        lunar = solar_to_lunar(now.date())
        return (
            f"当前时间：{now.strftime('%Y年%m月%d日 %H:%M')}，{weekdays[now.weekday()]}\n"
            f"阳历：{now.strftime('%Y年%m月%d日')}\n"
            f"农历：{lunar['full']}"
        )


class SetReminderTool(BaseTool):
    """设置定时提醒（通过回调触发）"""

    # 类变量：存储提醒回调，由主程序设置
    reminder_callback = None
    active_reminders = []

    @property
    def name(self):
        return "set_reminder"

    @property
    def description(self):
        return "设置一个定时提醒，在指定分钟数后触发。用于喝水提醒、休息提醒、待办提醒等健康关怀场景。"

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "minutes": {
                    "type": "number",
                    "description": "多少分钟后触发提醒，例如 30 表示30分钟后",
                },
                "message": {
                    "type": "string",
                    "description": "提醒时显示的消息内容，例如'该喝水了''起来活动一下'",
                },
            },
            "required": ["minutes", "message"],
        }

    def execute(self, minutes=30, message="该休息了", **kwargs):
        try:
            minutes = float(minutes)
        except (ValueError, TypeError):
            return "提醒设置失败：分钟数必须是数字"

        if minutes <= 0 or minutes > 1440:
            return "提醒设置失败：分钟数应在1到1440之间"

        reminder_info = f"{minutes:.0f}分钟后提醒：{message}"
        if SetReminderTool.reminder_callback:
            SetReminderTool.reminder_callback(minutes * 60 * 1000, message)
            SetReminderTool.active_reminders.append(reminder_info)
            return f"已设置提醒：{minutes:.0f}分钟后——{message}"
        else:
            # 无回调时仅记录
            SetReminderTool.active_reminders.append(reminder_info)
            return f"已记录提醒：{minutes:.0f}分钟后——{message}（提醒功能待启用）"
