# -*- coding: utf-8 -*-
"""
主动行为模块：桌宠隔一段时间主动发起会话
支持：报时、健康提醒（喝水/久坐/休息）、心情问候、工作关心、记忆跟进
"""
import random
import datetime
import time


class ProactiveBehavior:
    """主动行为生成器"""

    def __init__(self, agent_core=None):
        self.agent = agent_core
        self.last_trigger_time = 0
        self.min_interval = 45  # 最短间隔45秒
        self.max_interval = 90  # 最长间隔90秒（约1分钟）
        self.next_interval = self._random_interval()
        self.behavior_history = []  # 记录最近行为，避免重复

    def _random_interval(self):
        return random.randint(self.min_interval, self.max_interval)

    def should_trigger(self):
        """是否应该触发主动行为"""
        now = time.time()
        # 首次触发（程序启动后30秒）
        if self.last_trigger_time == 0:
            return now > 30  # 启动30秒后第一次
        return (now - self.last_trigger_time) >= self.next_interval

    def is_night_time(self):
        """夜间不主动打扰（23:00 - 8:00）"""
        hour = datetime.datetime.now().hour
        return hour >= 23 or hour < 8

    def generate(self, chat_window_visible=False):
        """
        生成一条主动消息。返回 (消息文本, 行为类型) 或 (None, None)
        """
        if chat_window_visible:
            return None, None  # 聊天窗口打开时不打扰
        if self.is_night_time():
            return None, None  # 夜间不打扰

        now = datetime.datetime.now()
        candidates = []

        # 1. 报时（整点或半点概率更高）
        if now.minute == 0 or now.minute == 30 or random.random() < 0.15:
            candidates.append(("time_report", self._gen_time_report(now)))

        # 2. 健康提醒（工作时段更高概率）
        if 9 <= now.hour <= 18:
            health_type = random.choice(["water", "idle", "rest", "eye"])
            candidates.append(("health", self._gen_health_reminder(health_type, now)))

        # 3. 心情问候（下午/傍晚概率高）
        if 14 <= now.hour <= 20 or random.random() < 0.2:
            candidates.append(("mood", self._gen_mood_check(now)))

        # 4. 工作关心（工作时段）
        if 9 <= now.hour <= 18:
            candidates.append(("work", self._gen_work_check(now)))

        # 5. 记忆跟进（如果有用户记忆）
        if self.agent and self.agent.user_memory.has_memory():
            memory_msg = self._gen_memory_followup()
            if memory_msg:
                candidates.append(("memory", memory_msg))

        if not candidates:
            # 保底：简单问候
            candidates.append(("mood", self._gen_mood_check(now)))

        # 随机选择一个，避免连续重复
        random.shuffle(candidates)
        for btype, msg in candidates:
            if msg and btype not in self.behavior_history[-3:]:
                self.behavior_history.append(btype)
                if len(self.behavior_history) > 10:
                    self.behavior_history = self.behavior_history[-10:]
                self.last_trigger_time = time.time()
                self.next_interval = self._random_interval()
                return msg, btype

        # 如果都重复了，随便选一个
        btype, msg = candidates[0]
        self.last_trigger_time = time.time()
        self.next_interval = self._random_interval()
        return msg, btype

    def _gen_time_report(self, now):
        """报时"""
        hour = now.hour
        minute = now.minute
        if minute == 0:
            time_str = f"{hour}点了"
        elif minute == 30:
            time_str = f"{hour}点半了"
        else:
            time_str = f"快{hour + 1}点了" if minute > 40 else f"{hour}点{minute}分"

        templates = [
            f"{time_str}。",
            f"{time_str}，时间过得真快。",
            f"{time_str}，注意休息。",
        ]
        # 早晨/中午/傍晚特殊问候
        if hour == 8 and minute < 30:
            templates = ["早。", "早上好。", "新的一天。"]
        elif hour == 12:
            templates = ["中午了，该吃饭了。", "饭点到了。"]
        elif hour == 18:
            templates = ["下班了。", "该吃饭了。", "今天辛苦了。"]
        elif 22 <= hour <= 23:
            templates = ["不早了，早点休息。", "该睡了。"]

        return random.choice(templates)

    def _gen_health_reminder(self, htype, now):
        """健康提醒"""
        if htype == "water":
            templates = [
                "喝水了吗？",
                "该喝水了。",
                "多喝水。",
                "杯子空了吗？",
            ]
        elif htype == "idle":
            templates = [
                "坐太久了，起来活动一下。",
                "别一直坐着，走走。",
                "起来动动。",
                "久坐伤身。",
            ]
        elif htype == "rest":
            templates = [
                "休息一下吧。",
                "累了就歇会儿。",
                "别太累。",
                "休息五分钟。",
            ]
        elif htype == "eye":
            templates = [
                "眼睛累了吗？看看远处。",
                "保护视力，远眺一下。",
                "别一直盯着屏幕。",
            ]
        else:
            templates = ["注意身体。"]
        return random.choice(templates)

    def _gen_mood_check(self, now):
        """心情问候"""
        hour = now.hour
        if hour < 12:
            templates = [
                "今天心情怎么样？",
                "早上好，今天有什么计划？",
                "昨晚睡得好吗？",
            ]
        elif 12 <= hour < 14:
            templates = [
                "中午了，吃了吗？",
                "午休了吗？",
            ]
        elif 14 <= hour < 18:
            templates = [
                "下午困不困？",
                "今天顺利吗？",
                "累不累？",
                "在忙什么？",
            ]
        else:
            templates = [
                "今天怎么样？",
                "过得还好吗？",
                "有什么开心的事吗？",
                "累了一天了，放松一下。",
            ]
        return random.choice(templates)

    def _gen_work_check(self, now):
        """工作关心"""
        templates = [
            "工作忙吗？",
            "今天任务多吗？",
            "进展顺利吗？",
            "遇到难题了吗？",
            "别太拼，注意身体。",
            "需要帮忙吗？",
        ]
        return random.choice(templates)

    def _gen_memory_followup(self):
        """基于用户记忆的跟进"""
        if not self.agent:
            return None
        try:
            question = self.agent.generate_follow_up_question()
            return question if question else None
        except Exception:
            return None

    def get_next_trigger_seconds(self):
        """距离下次触发还有多少秒"""
        if self.last_trigger_time == 0:
            return 30  # 首次30秒
        elapsed = time.time() - self.last_trigger_time
        return max(0, self.next_interval - elapsed)
