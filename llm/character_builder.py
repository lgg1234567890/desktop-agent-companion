# -*- coding: utf-8 -*-
"""
角色画像生成器：
输入角色名+出处 → LLM 输出8维度JSON画像 → 自动渲染System Prompt
"""
import json
import os
import requests


CHARACTER_PROFILE_PROMPT = """你是一个角色设定专家。请根据以下角色信息，生成一个结构化的角色画像JSON。

角色名称：{name}
角色出处：{source}

请严格输出JSON格式，包含以下8个字段：
1. "appearance"：外貌特征描述（50字以内）
2. "personality"：性格特质（50字以内）
3. "speaking_style"：语言逻辑与说话风格（50字以内）
4. "voice_style"：配音/音色风格描述（30字以内）
5. "classic_lines"：经典台词列表（3-5句）
6. "typical_actions"：典型动作或习惯（3-5个）
7. "background"：背景知识与关键经历（100字以内）
8. "task_mode"：任务模式与交互倾向（50字以内，如"被动回应型""主动关怀型"等）

只输出JSON，不要输出任何其他文字、解释或markdown标记。"""


SYSTEM_PROMPT_TEMPLATE = """你是{name}，出自{source}。请严格遵循以下角色画像进行对话：

【外貌特征】
{appearance}

【性格特质】
{personality}

【说话风格】
{speaking_style}

【音色特征】
{voice_style}

【经典台词】
{classic_lines}

【典型动作】
{typical_actions}

【背景知识】
{background}

【交互模式】
{task_mode}

【对话规则】
1. 始终保持角色身份，不要跳出角色，不要说"我是AI"或"作为语言模型"
2. 说话风格符合上述设定，不要与角色设定矛盾
3. 回答简洁自然，符合角色的语言习惯
4. 当用户问题涉及角色背景时，基于上述背景知识回答

现在，请以{name}的身份与用户对话。"""


class CharacterBuilder:
    def __init__(self, api_key, api_url=None, model="glm-5"):
        self.api_key = api_key
        self.model = model
        if api_url:
            self.api_url = api_url
        else:
            self.api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        self.profile_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "character_profiles"
        )
        os.makedirs(self.profile_dir, exist_ok=True)

    def generate_profile(self, name, source):
        """
        生成角色画像JSON。
        返回 (profile_dict, error_msg)
        """
        prompt = CHARACTER_PROFILE_PROMPT.format(name=name, source=source)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 800,
            "response_format": {"type": "json_object"},
        }
        try:
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            if resp.status_code != 200:
                return None, f"API错误 {resp.status_code}: {resp.text[:200]}"
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            # 清理可能的markdown标记
            content = content.replace("```json", "").replace("```", "").strip()
            profile = json.loads(content)
            return profile, None
        except json.JSONDecodeError as e:
            return None, f"JSON解析失败: {e}\n原始内容: {content[:200]}"
        except Exception as e:
            return None, f"生成失败: {e}"

    def render_system_prompt(self, name, source, profile):
        """将角色画像渲染为 System Prompt 文本"""
        classic_lines = profile.get("classic_lines", [])
        if isinstance(classic_lines, list):
            classic_lines_str = "\n".join(f"- {line}" for line in classic_lines)
        else:
            classic_lines_str = str(classic_lines)

        typical_actions = profile.get("typical_actions", [])
        if isinstance(typical_actions, list):
            typical_actions_str = "、".join(typical_actions)
        else:
            typical_actions_str = str(typical_actions)

        return SYSTEM_PROMPT_TEMPLATE.format(
            name=name,
            source=source,
            appearance=profile.get("appearance", "未知"),
            personality=profile.get("personality", "未知"),
            speaking_style=profile.get("speaking_style", "未知"),
            voice_style=profile.get("voice_style", "未知"),
            classic_lines=classic_lines_str,
            typical_actions=typical_actions_str,
            background=profile.get("background", "未知"),
            task_mode=profile.get("task_mode", "被动回应型"),
        )

    def save_profile(self, name, source, profile, system_prompt):
        """保存角色画像到文件"""
        safe_name = "".join(c for c in name if c.isalnum() or c in "_-")
        filepath = os.path.join(self.profile_dir, f"{safe_name}.json")
        data = {
            "name": name,
            "source": source,
            "profile": profile,
            "system_prompt": system_prompt,
        }
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return filepath
        except Exception as e:
            print(f"[CharacterBuilder] 保存失败: {e}")
            return None

    def load_profile(self, name):
        """从文件加载角色画像"""
        safe_name = "".join(c for c in name if c.isalnum() or c in "_-")
        filepath = os.path.join(self.profile_dir, f"{safe_name}.json")
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def generate_and_save(self, name, source):
        """一键生成并保存，返回 (system_prompt, profile, error)"""
        profile, error = self.generate_profile(name, source)
        if error:
            return None, None, error
        system_prompt = self.render_system_prompt(name, source, profile)
        self.save_profile(name, source, profile, system_prompt)
        return system_prompt, profile, None
