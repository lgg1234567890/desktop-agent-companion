# -*- coding: utf-8 -*-
"""
用户长期记忆模块：
- 记录用户的基本信息、性格、偏好、重要事件
- 从对话中自动提取用户信息
- 在对话中注入用户记忆
- 生成主动跟进问题
"""
import os
import json
import datetime


class UserMemory:
    """用户长期记忆：持久化存储用户画像和重要事件"""

    def __init__(self, memory_file=None):
        if memory_file is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            memory_file = os.path.join(base_dir, "data", "user_memory.json")
        self.memory_file = memory_file
        os.makedirs(os.path.dirname(memory_file), exist_ok=True)
        self.data = {
            "basic_info": {},      # 基本信息：姓名、年龄、职业、城市等
            "personality": [],     # 性格特点
            "preferences": {},     # 喜好：食物、电影、音乐等
            "important_events": [],  # 重要事件列表
            "ongoing": [],         # 正在进行/需要跟进的事情
            "emotional_notes": [],  # 情绪记录
            "conversation_summary": "",  # 对话总结
            "last_updated": "",
        }
        self.load()

    def load(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                self.data.update(loaded)
            except Exception as e:
                print(f"[UserMemory] 加载失败: {e}")

    def save(self):
        self.data["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[UserMemory] 保存失败: {e}")

    def add_basic_info(self, key, value):
        self.data["basic_info"][key] = value
        self.save()

    def add_personality(self, trait):
        if trait not in self.data["personality"]:
            self.data["personality"].append(trait)
            self.save()

    def add_preference(self, category, value):
        if category not in self.data["preferences"]:
            self.data["preferences"][category] = []
        if value not in self.data["preferences"][category]:
            self.data["preferences"][category].append(value)
            self.save()

    def add_event(self, event, date=None, importance="normal"):
        if date is None:
            date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.data["important_events"].append({
            "event": event,
            "date": date,
            "importance": importance,
        })
        self.save()

    def add_ongoing(self, thing, follow_up_hint=""):
        self.data["ongoing"].append({
            "thing": thing,
            "follow_up_hint": follow_up_hint,
            "started": datetime.datetime.now().strftime("%Y-%m-%d"),
            "status": "ongoing",
        })
        self.save()

    def complete_ongoing(self, thing_keyword):
        for item in self.data["ongoing"]:
            if thing_keyword in item["thing"]:
                item["status"] = "completed"
                item["completed"] = datetime.datetime.now().strftime("%Y-%m-%d")
                self.save()
                return True
        return False

    def add_emotional_note(self, note):
        self.data["emotional_notes"].append({
            "note": note,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        # 只保留最近20条
        self.data["emotional_notes"] = self.data["emotional_notes"][-20:]
        self.save()

    def set_conversation_summary(self, summary):
        self.data["conversation_summary"] = summary
        self.save()

    def get_context(self, max_events=5, max_ongoing=3):
        """
        生成可注入对话的用户记忆上下文字符串
        """
        parts = []

        # 基本信息
        if self.data["basic_info"]:
            info_str = "，".join(f"{k}：{v}" for k, v in self.data["basic_info"].items())
            parts.append(f"【用户基本信息】{info_str}")

        # 性格
        if self.data["personality"]:
            parts.append(f"【用户性格】{'、'.join(self.data['personality'][-5:])}")

        # 喜好
        if self.data["preferences"]:
            pref_strs = []
            for cat, vals in self.data["preferences"].items():
                if vals:
                    pref_strs.append(f"{cat}喜欢{'、'.join(vals[-3:])}")
            if pref_strs:
                parts.append(f"【用户喜好】{'；'.join(pref_strs)}")

        # 重要事件（最近的）
        if self.data["important_events"]:
            events = self.data["important_events"][-max_events:]
            event_strs = [f"{e['date']} {e['event']}" for e in events]
            parts.append(f"【用户重要经历】{'；'.join(event_strs)}")

        # 正在进行的事
        ongoing_items = [o for o in self.data["ongoing"] if o["status"] == "ongoing"][-max_ongoing:]
        if ongoing_items:
            ongoing_strs = [f"{o['thing']}（{o.get('follow_up_hint', '可跟进')}）" for o in ongoing_items]
            parts.append(f"【用户正在进行/需跟进】{'；'.join(ongoing_strs)}")

        # 对话总结
        if self.data["conversation_summary"]:
            parts.append(f"【之前聊过】{self.data['conversation_summary']}")

        return "\n".join(parts) if parts else ""

    def get_follow_up_suggestions(self):
        """
        生成主动跟进的话题建议（返回列表）
        """
        suggestions = []
        for item in self.data["ongoing"]:
            if item["status"] == "ongoing":
                hint = item.get("follow_up_hint", "")
                thing = item["thing"]
                if hint:
                    suggestions.append(f"问问用户关于「{thing}」的进展：{hint}")
                else:
                    suggestions.append(f"问问用户「{thing}」最近怎么样了")
        # 基于重要事件生成
        for event in self.data["important_events"][-3:]:
            if "计划" in event["event"] or "打算" in event["event"]:
                suggestions.append(f"问问用户之前提到的「{event['event']}」执行得怎么样了")
        return suggestions

    def has_memory(self):
        """是否有任何记忆"""
        return bool(
            self.data["basic_info"]
            or self.data["personality"]
            or self.data["preferences"]
            or self.data["important_events"]
            or self.data["ongoing"]
        )

    def get_stats(self):
        """返回记忆统计"""
        return {
            "basic_info": len(self.data["basic_info"]),
            "personality": len(self.data["personality"]),
            "preferences": sum(len(v) for v in self.data["preferences"].values()),
            "important_events": len(self.data["important_events"]),
            "ongoing": len([o for o in self.data["ongoing"] if o["status"] == "ongoing"]),
        }


# 全局单例
_user_memory = None


def get_user_memory():
    global _user_memory
    if _user_memory is None:
        _user_memory = UserMemory()
    return _user_memory
