# -*- coding: utf-8 -*-
"""
对话记忆提取器：从用户消息中自动提取用户信息，保存到长期记忆
"""
import json
from memory.user_memory import get_user_memory


EXTRACT_PROMPT = """你是一个用户画像分析专家。请从以下用户消息中提取关于用户的信息，输出严格的JSON格式。

用户消息：{user_message}
助手回复：{assistant_reply}

请提取以下信息（没有的字段留空数组或空对象）：
{{
  "basic_info": {{}},        // 基本信息，如{{"姓名": "张三", "年龄": "30", "职业": "工程师", "城市": "深圳"}}
  "personality": [],         // 性格特点，如["坚韧", "理性", "有点焦虑"]
  "preferences": {{}},       // 喜好，如{{"食物": ["火锅", "日料"], "电影": ["科幻"]}}
  "important_events": [],    // 重要事件，如["最近换了工作", "计划下个月去泰国旅游"]
  "ongoing": [],             // 正在进行/需跟进的事，如["正在准备面试", "在学Python"]
  "emotional": []            // 情绪状态，如["最近压力大", "今天心情不错"]
}}

只输出JSON，不要输出其他文字。"""


class MemoryExtractor:
    """从对话中提取用户记忆"""

    def __init__(self, llm_client):
        self.llm = llm_client
        self.user_memory = get_user_memory()
        self.conversation_count = 0
        self.extract_interval = 3  # 每3轮对话提取一次

    def should_extract(self):
        """是否应该提取记忆（每N轮一次，或用户消息较长时）"""
        self.conversation_count += 1
        return self.conversation_count % self.extract_interval == 0

    def extract(self, user_message, assistant_reply):
        """
        从对话中提取用户信息并保存。
        异步调用，不阻塞主流程。
        """
        try:
            prompt = EXTRACT_PROMPT.format(
                user_message=user_message[:500],
                assistant_reply=assistant_reply[:300]
            )
            messages = [{"role": "user", "content": prompt}]
            resp = self.llm._raw_chat(messages, temperature=0.3, max_tokens=500)
            if not resp:
                return

            # 清理JSON
            content = resp.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)
            self._apply_extraction(data)
        except Exception as e:
            print(f"[MemoryExtractor] 提取失败: {e}")

    def _apply_extraction(self, data):
        """将提取的信息应用到用户记忆"""
        # 基本信息
        for k, v in data.get("basic_info", {}).items():
            if v:
                self.user_memory.add_basic_info(k, v)

        # 性格
        for trait in data.get("personality", []):
            if trait:
                self.user_memory.add_personality(trait)

        # 喜好
        for cat, vals in data.get("preferences", {}).items():
            for v in vals:
                if v:
                    self.user_memory.add_preference(cat, v)

        # 重要事件
        for event in data.get("important_events", []):
            if event:
                self.user_memory.add_event(event)

        # 正在进行
        for thing in data.get("ongoing", []):
            if thing:
                self.user_memory.add_ongoing(thing)

        # 情绪
        for emo in data.get("emotional", []):
            if emo:
                self.user_memory.add_emotional_note(emo)

    def generate_follow_up_question(self, character_prompt=""):
        """
        生成一个主动跟进的问题（基于用户记忆）。
        character_prompt: 角色人设，用于调整语气
        """
        suggestions = self.user_memory.get_follow_up_suggestions()
        if not suggestions:
            return ""

        # 用LLM生成自然的跟进问题
        context = self.user_memory.get_context()
        prompt = f"""你正在扮演一个桌面角色，虽然平时话不多，但会默默关心朋友。现在用户空闲了一会儿，你想主动问一句关于他/她之前事情的进展。

用户信息：
{context}

可以跟进的方向：
{chr(10).join('- ' + s for s in suggestions[:3])}

要求：
1. 用简短、自然的语气提问，像朋友随口一问
2. 结合用户之前提到的具体事情
3. 不超过15个字
4. 只输出问题本身，不要引号，不要解释
5. 这是角色关心朋友的表现，是符合人设的

请输出跟进问题："""

        try:
            messages = [{"role": "user", "content": prompt}]
            resp = self.llm._raw_chat(messages, temperature=0.8, max_tokens=80)
            if resp:
                # 清理可能的引号和前缀
                resp = resp.strip().strip('"').strip("'").strip("「」")
                # 取第一行
                resp = resp.split("\n")[0].strip()
                return resp
        except Exception as e:
            print(f"[MemoryExtractor] 主动提问生成失败: {e}")

        # fallback：用模板生成
        if suggestions:
            return f"你之前说的{suggestions[0].split('「')[1].split('」')[0] if '「' in suggestions[0] else '那件事'}，怎么样了？"
        return ""
