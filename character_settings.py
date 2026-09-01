# -*- coding: utf-8 -*-
"""角色设置界面：可编辑角色人设、API配置、资源路径、角色来源"""
import os
import json
import threading
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTextEdit, QLineEdit, QPushButton, QMessageBox,
                             QGroupBox, QFormLayout, QFileDialog, QProgressBar)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

import sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
SETTINGS_FILE = os.path.join(BASE_DIR, "character_settings.txt")
API_CONFIG_FILE = os.path.join(BASE_DIR, "api_config.json")

DEFAULT_PROMPT = """你是《盗墓笔记》中的张起灵，人称"小哥"。请严格遵循以下人设进行对话：

【身份背景】
- 张家族长，拥有麒麟血，能驱散邪祟、驱赶毒虫
- 武功极高，擅长黑金古刀，二指探洞是独门绝技
- 患有失魂症，会周期性失忆，因此性格沉默寡言
- 曾是西沙考古队成员，与吴邪、王胖子组成"铁三角"
- 外表冷峻，内心重情重义，对朋友极其护短

【性格特征】
- 沉默寡言，惜字如金，说话简短有力，从不啰嗦
- 表情淡漠，情绪不外露，但内心温柔
- 冷静理智，临危不乱，遇到危险永远挡在朋友前面
- 对未知事物充满好奇，喜欢探查机关和古墓
- 不擅长表达感情，但行动上处处体现关怀

【说话风格】
- 台词简短，通常2-8个字，如"别动"、"闪开"、"有机关"、"跟紧我"
- 语气平静、冷淡，不带情绪波动
- 偶尔会说一句让人安心的话，如"没事"、"有我在"
- 从不主动长篇大论，别人问才答
- 涉及过去的事情时，会说"不记得了"或沉默

【经典台词参考】
- "我是一个没有过去和未来的人。"
- "别动。" "闪开。" "有机关。" "跟紧我。" "没事。" "嗯。" "不记得了。"

【对话规则】
1. 每次回复尽量简短，不超过3句话，最好1-2句
2. 保持冷淡、平静的语气，不要热情洋溢
3. 不要用表情符号，不要用网络用语
4. 如果对方问你的过去，回答"不记得了"或转移话题
5. 关心对方时用行动性语言，如"小心"、"退后"，而非抒情
6. 不要主动开启话题，对方说什么就回应什么
7. 绝对不要跳出角色，不要说"我是AI"、"作为语言模型"之类的话

现在，请以张起灵的身份与用户对话。"""


def load_api_config():
    """从JSON加载API配置"""
    try:
        if os.path.exists(API_CONFIG_FILE):
            with open(API_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {
        "api_key": "sk-8f9e9bcf656345678458845e89bc9a5a",
        "api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "model": "glm-5"
    }


def save_api_config(config):
    """保存API配置到JSON"""
    try:
        with open(API_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存API配置失败: {e}")
        return False


class CharacterSettingsWindow(QWidget):
    settings_saved = pyqtSignal(str, dict)  # (人设, API配置)
    generation_finished = pyqtSignal(int, str)  # (成功数量, 错误信息)
    profile_generated = pyqtSignal(str, str)  # (角色名, 错误信息)
    profile_and_images_done = pyqtSignal(bool, str)  # (是否成功, 信息)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("角色设置")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.resize(580, 680)
        self._build_ui()
        self._load_settings()
        self.generation_finished.connect(self._on_generation_finished)
        self.profile_generated.connect(self._on_profile_generated)
        self.profile_and_images_done.connect(self._on_profile_and_images_done)

    def _build_ui(self):
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(12)

            title = QLabel("张起灵 · 角色设置")
            title.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
            title.setStyleSheet("color: #333;")
            layout.addWidget(title)

            # API配置
            api_group = QGroupBox("API 配置")
            api_group.setFont(QFont("Microsoft YaHei", 10))
            api_layout = QFormLayout(api_group)

            self.api_key_input = QLineEdit()
            self.api_key_input.setEchoMode(QLineEdit.Password)
            self.api_key_input.setPlaceholderText("输入 API Key")
            api_layout.addRow("API Key:", self.api_key_input)

            self.api_url_input = QLineEdit()
            self.api_url_input.setPlaceholderText("https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions")
            api_layout.addRow("API 地址:", self.api_url_input)

            self.model_input = QLineEdit()
            self.model_input.setPlaceholderText("glm-5")
            api_layout.addRow("模型名称:", self.model_input)

            layout.addWidget(api_group)

            # 语音设置
            from PyQt5.QtWidgets import QCheckBox
            voice_group = QGroupBox("语音设置")
            voice_group.setFont(QFont("Microsoft YaHei", 10))
            voice_layout = QVBoxLayout(voice_group)
            self.voice_checkbox = QCheckBox("主动问候时播放语音（低沉男声，近似小哥音色）")
            self.voice_checkbox.setFont(QFont("Microsoft YaHei", 10))
            self.voice_checkbox.setChecked(True)
            voice_layout.addWidget(self.voice_checkbox)
            voice_hint = QLabel("语音使用微软 edge-tts 生成，需联网。主动报时、健康提醒、心情问候时会自动朗读。")
            voice_hint.setStyleSheet("color: #888; font-size: 11px;")
            voice_hint.setWordWrap(True)
            voice_layout.addWidget(voice_hint)
            layout.addWidget(voice_group)

            # 资源配置
            res_group = QGroupBox("角色资源配置")
            res_group.setFont(QFont("Microsoft YaHei", 10))
            res_layout = QFormLayout(res_group)

            # 角色名称
            self.char_name_input = QLineEdit()
            self.char_name_input.setPlaceholderText("张起灵")
            res_layout.addRow("角色名称:", self.char_name_input)

            # 角色来源
            self.char_source_input = QLineEdit()
            self.char_source_input.setPlaceholderText("张起灵来自《盗墓笔记》，用于大模型提炼人物性格特征")
            res_layout.addRow("角色来源:", self.char_source_input)

            # 头像路径
            avatar_layout = QHBoxLayout()
            self.avatar_path_input = QLineEdit()
            self.avatar_path_input.setPlaceholderText("选择头像图片（聊天窗口头像）")
            avatar_btn = QPushButton("浏览...")
            avatar_btn.setFixedWidth(70)
            avatar_btn.clicked.connect(lambda: self._pick_file(self.avatar_path_input, "选择头像图片"))
            avatar_layout.addWidget(self.avatar_path_input)
            avatar_layout.addWidget(avatar_btn)
            res_layout.addRow("头像图片:", avatar_layout)

            # 背景路径
            bg_layout = QHBoxLayout()
            self.bg_path_input = QLineEdit()
            self.bg_path_input.setPlaceholderText("选择背景图片（聊天窗口背景）")
            bg_btn = QPushButton("浏览...")
            bg_btn.setFixedWidth(70)
            bg_btn.clicked.connect(lambda: self._pick_file(self.bg_path_input, "选择背景图片"))
            bg_layout.addWidget(self.bg_path_input)
            bg_layout.addWidget(bg_btn)
            res_layout.addRow("背景图片:", bg_layout)

            # 建模图片路径
            model_layout = QHBoxLayout()
            self.model_path_input = QLineEdit()
            self.model_path_input.setPlaceholderText("选择人物建模图（用于抠图、背景透明、动作生成）")
            model_btn = QPushButton("浏览...")
            model_btn.setFixedWidth(70)
            model_btn.clicked.connect(lambda: self._pick_file(self.model_path_input, "选择人物建模图片"))
            model_layout.addWidget(self.model_path_input)
            model_layout.addWidget(model_btn)
            res_layout.addRow("建模图片:", model_layout)

            # 生成动作图片按钮
            gen_layout = QHBoxLayout()
            self.gen_profile_btn = QPushButton("AI生成角色画像")
            self.gen_profile_btn.setStyleSheet("""
                QPushButton {
                    background-color: #6A5ACD; color: white;
                    border: 1px solid #483D8B; border-radius: 6px;
                    padding: 8px 12px; font-family: "Microsoft YaHei";
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #7B68EE; }
                QPushButton:disabled { background-color: #999; color: #ccc; }
            """)
            self.gen_profile_btn.clicked.connect(self._generate_profile)
            gen_layout.addWidget(self.gen_profile_btn)

            self.gen_actions_btn = QPushButton("基于建模图生成13种动作")
            self.gen_actions_btn.setStyleSheet("""
                QPushButton {
                    background-color: #8b7355; color: #f5f0e8;
                    border: 1px solid #b89868; border-radius: 6px;
                    padding: 8px 16px; font-family: "Microsoft YaHei";
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #a08060; }
                QPushButton:disabled { background-color: #666; color: #999; }
            """)
            self.gen_actions_btn.clicked.connect(self._generate_actions)
            gen_layout.addWidget(self.gen_actions_btn)
            gen_layout.addStretch()
            res_layout.addRow(gen_layout)

            # 一键创建角色按钮
            oneclick_layout = QHBoxLayout()
            self.oneclick_btn = QPushButton("✨ 一键创建角色（画像+动作图片+抠图）")
            self.oneclick_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ff6b9d; color: white;
                    border: none; border-radius: 8px;
                    padding: 10px 20px; font-family: "Microsoft YaHei";
                    font-weight: bold; font-size: 13px;
                }
                QPushButton:hover { background-color: #ff85b3; }
                QPushButton:disabled { background-color: #ccc; color: #999; }
            """)
            self.oneclick_btn.clicked.connect(self._oneclick_create_character)
            oneclick_layout.addWidget(self.oneclick_btn)
            res_layout.addRow(oneclick_layout)

            # 进度条
            self.progress_bar = QProgressBar()
            self.progress_bar.setVisible(False)
            self.progress_bar.setRange(0, 100)
            res_layout.addRow(self.progress_bar)

            layout.addWidget(res_group)

            # 角色人设
            char_group = QGroupBox("角色人设（System Prompt）")
            char_group.setFont(QFont("Microsoft YaHei", 10))
            char_layout = QVBoxLayout(char_group)

            self.prompt_editor = QTextEdit()
            self.prompt_editor.setFont(QFont("Microsoft YaHei", 9))
            self.prompt_editor.setPlaceholderText("在此编辑角色人设、性格特征、说话风格等...")
            self.prompt_editor.setStyleSheet("""
                QTextEdit {
                    background-color: #fafafa;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    padding: 8px;
                    color: #333;
                }
            """)
            char_layout.addWidget(self.prompt_editor)
            layout.addWidget(char_group, 1)

            # 按钮
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()

            reset_btn = QPushButton("恢复默认")
            reset_btn.setFixedWidth(90)
            reset_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0; color: #555;
                    border: 1px solid #ccc; border-radius: 6px;
                    padding: 6px 12px; font-family: "Microsoft YaHei";
                }
                QPushButton:hover { background-color: #e8e8e8; }
            """)
            reset_btn.clicked.connect(self._reset_default)
            btn_layout.addWidget(reset_btn)

            save_btn = QPushButton("保存设置")
            save_btn.setFixedWidth(100)
            save_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ff9eb5; color: #402030;
                    border: none; border-radius: 6px;
                    padding: 6px 16px; font-family: "Microsoft YaHei";
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #ffb6c1; }
                QPushButton:pressed { background-color: #ff85a2; }
            """)
            save_btn.clicked.connect(self._save_settings)
            btn_layout.addWidget(save_btn)
            layout.addLayout(btn_layout)
        except Exception as e:
            QMessageBox.critical(self, "界面初始化失败", str(e))

    def _load_settings(self):
        try:
            # 加载人设
            prompt = DEFAULT_PROMPT
            if os.path.exists(SETTINGS_FILE):
                try:
                    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                        content = f.read()
                        if content.strip():
                            prompt = content
                except Exception:
                    pass
            self.prompt_editor.setPlainText(prompt)
        except Exception:
            self.prompt_editor.setPlainText(DEFAULT_PROMPT)

        try:
            # 加载API配置
            cfg = load_api_config()
            self.api_key_input.setText(cfg.get("api_key", ""))
            self.api_url_input.setText(cfg.get("api_url", ""))
            self.model_input.setText(cfg.get("model", ""))
            # 加载资源配置
            self.char_name_input.setText(cfg.get("character_name", "张起灵"))
            self.char_source_input.setText(cfg.get("character_source", "张起灵来自《盗墓笔记》"))
            self.avatar_path_input.setText(cfg.get("avatar_path", ""))
            self.bg_path_input.setText(cfg.get("background_path", ""))
            self.model_path_input.setText(cfg.get("model_image_path", ""))
            # 加载语音设置
            self.voice_checkbox.setChecked(cfg.get("voice_enabled", True))
        except Exception:
            pass

    def _save_settings(self):
        try:
            prompt = self.prompt_editor.toPlainText().strip()
            if not prompt:
                QMessageBox.warning(self, "提示", "角色人设不能为空！")
                return

            # 保存人设
            try:
                with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                    f.write(prompt)
            except Exception as e:
                QMessageBox.warning(self, "提示", f"人设保存失败：{e}")

            # 保存API配置到JSON
            api_config = {
                "api_key": self.api_key_input.text().strip(),
                "api_url": self.api_url_input.text().strip(),
                "model": self.model_input.text().strip(),
                "character_name": self.char_name_input.text().strip(),
                "character_source": self.char_source_input.text().strip(),
                "avatar_path": self.avatar_path_input.text().strip(),
                "background_path": self.bg_path_input.text().strip(),
                "model_image_path": self.model_path_input.text().strip(),
                "voice_enabled": self.voice_checkbox.isChecked(),
            }
            save_api_config(api_config)

            QMessageBox.information(self, "成功", "设置已保存！\n人设和API配置立即生效。")
            self.settings_saved.emit(prompt, api_config)
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))

    def _reset_default(self):
        try:
            reply = QMessageBox.question(self, "确认", "确定恢复默认人设吗？",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.prompt_editor.setPlainText(DEFAULT_PROMPT)
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def _pick_file(self, line_edit, title):
        """打开文件选择对话框，选择图片文件"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, title, "",
                "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp);;所有文件 (*.*)"
            )
            if file_path:
                line_edit.setText(file_path)
        except Exception as e:
            QMessageBox.critical(self, "选择文件失败", str(e))

    def _generate_actions(self):
        """基于建模图片生成13种动作图片"""
        import threading
        try:
            model_img = self.model_path_input.text().strip()
            char_source = self.char_source_input.text().strip()

            if not model_img or not os.path.exists(model_img):
                QMessageBox.warning(self, "提示", "请先选择建模图片！")
                return

            reply = QMessageBox.question(
                self, "确认生成",
                f"将基于建模图片生成17种动作图片（约需5-10分钟），\n"
                f"会覆盖现有的动作图片，确定继续吗？\n\n"
                f"注意：需要API Key具有通义万相图像生成权限，否则会生成失败。",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

            self.gen_actions_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)

            def progress_cb(action_name, idx, total):
                if total > 0:
                    self.progress_bar.setValue(int(idx / total * 100))

            def worker():
                try:
                    from action_generator import generate_all_actions
                    count = generate_all_actions(
                        model_image_path=model_img,
                        character_desc=char_source,
                        progress_callback=progress_cb
                    )
                    self.generation_finished.emit(count, "")
                except Exception as e:
                    self.generation_finished.emit(0, str(e))

            threading.Thread(target=worker, daemon=True).start()

        except Exception as e:
            self.gen_actions_btn.setEnabled(True)
            QMessageBox.critical(self, "错误", str(e))

    def _on_generation_finished(self, count, error):
        """生成完成的主线程处理"""
        self.gen_actions_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        if error:
            QMessageBox.critical(self, "生成失败",
                f"生成失败：{error}\n\n"
                f"可能原因：API Key没有通义万相图像生成权限。\n"
                f"请在阿里云百炼控制台开通 wanx2.1-t2i-turbo 模型访问权限。")
        else:
            QMessageBox.information(self, "生成完成",
                f"成功生成 {count} 个动作图片！\n"
                f"请重启程序以加载新动作。")


    def _generate_profile(self):
        """AI生成角色画像（8维度JSON + System Prompt）"""
        name = self.char_name_input.text().strip()
        source = self.char_source_input.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请先输入角色名称！")
            return
        if not source:
            source = name

        self.gen_profile_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度

        def worker():
            try:
                from agent_core import get_agent_core
                agent = get_agent_core()
                system_prompt, profile, error = agent.generate_character(name, source)
                if error:
                    self.profile_generated.emit(name, error)
                    return
                # 自动填充到编辑器
                self.prompt_editor.setPlainText(system_prompt)
                self.profile_generated.emit(name, "")
            except Exception as e:
                self.profile_generated.emit(name, str(e))

        threading.Thread(target=worker, daemon=True).start()

    def _on_profile_generated(self, name, error):
        """角色画像生成完成"""
        self.gen_profile_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        if error:
            QMessageBox.critical(self, "生成失败", f"角色画像生成失败：{error}")
        else:
            QMessageBox.information(self, "生成成功",
                f"角色「{name}」画像生成完成！\n"
                f"已自动填充到人设编辑器，可编辑后保存。")

    def _oneclick_create_character(self):
        """一键创建角色：生成画像 → 生成动作图片 → 抠图 → 保存"""
        name = self.char_name_input.text().strip()
        source = self.char_source_input.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请先输入角色名称！")
            return
        if not source:
            source = name

        reply = QMessageBox.question(
            self, "确认一键创建",
            f"将为角色「{name}」执行以下操作：\n"
            f"1. AI生成8维度角色画像和System Prompt\n"
            f"2. 生成17种动作图片（通义万相，约5-10分钟）\n"
            f"3. 自动抠图（背景透明）\n"
            f"4. 保存人设并应用\n\n"
            f"确定开始吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        self.oneclick_btn.setEnabled(False)
        self.gen_profile_btn.setEnabled(False)
        self.gen_actions_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(5)

        def worker():
            try:
                from agent_core import get_agent_core
                from action_generator import generate_all_actions
                agent = get_agent_core()

                # 步骤1：生成角色画像
                self.progress_bar.setValue(10)
                system_prompt, profile, error = agent.generate_character(name, source)
                if error:
                    self.profile_and_images_done.emit(False, f"画像生成失败：{error}")
                    return

                # 填充到编辑器
                self.prompt_editor.setPlainText(system_prompt)
                self.progress_bar.setValue(25)

                # 步骤2：生成动作图片 + 抠图
                # 用画像中的外貌特征增强prompt
                appearance = profile.get("appearance", "") if profile else ""
                char_desc = f"{source}，{appearance}" if appearance else source
                count = generate_all_actions(
                    model_image_path=None,
                    character_desc=char_desc,
                    progress_callback=lambda a, i, t: self.progress_bar.setValue(
                        25 + int(i / max(t, 1) * 70)
                    ),
                )
                self.progress_bar.setValue(95)

                # 步骤3：保存人设
                try:
                    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                        f.write(system_prompt)
                except Exception:
                    pass

                # 保存API配置
                api_config = {
                    "api_key": self.api_key_input.text().strip(),
                    "api_url": self.api_url_input.text().strip(),
                    "model": self.model_input.text().strip(),
                    "character_name": name,
                    "character_source": source,
                }
                save_api_config(api_config)

                self.progress_bar.setValue(100)
                self.profile_and_images_done.emit(
                    True, f"角色「{name}」创建完成！\n生成了{count}个动作图片，已自动抠图。\n请重启程序加载新角色。"
                )
            except Exception as e:
                self.profile_and_images_done.emit(False, f"创建失败：{e}")

        threading.Thread(target=worker, daemon=True).start()

    def _on_profile_and_images_done(self, success, message):
        """一键创建完成"""
        self.oneclick_btn.setEnabled(True)
        self.gen_profile_btn.setEnabled(True)
        self.gen_actions_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        if success:
            QMessageBox.information(self, "创建成功", message)
            self.settings_saved.emit(self.prompt_editor.toPlainText(), {})
            self.close()
        else:
            QMessageBox.critical(self, "创建失败", message)


def load_character_prompt():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return content
    except Exception:
        pass
    return DEFAULT_PROMPT
