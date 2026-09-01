# -*- coding: utf-8 -*-
"""青铜墨冰聊天窗口：青铜门背景 + 白金色气泡 + 头像 + 自适应宽度"""
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QScrollArea, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPoint, QRect
from PyQt5.QtGui import (QFont, QFontMetrics, QPixmap, QPainter, QColor,
                          QBrush, QPen, QPainterPath, QLinearGradient)


# ========== 配色（白金主题）==========
# 小哥气泡（米白底 + 金边）
COLOR_BOT_BG = "#f5f0e8"
COLOR_BOT_BORDER = "#b89868"
COLOR_BOT_TEXT = "#2a2018"
# 用户气泡（暗金底 + 金边）
COLOR_USER_BG = "#8b7355"
COLOR_USER_BORDER = "#c8a878"
COLOR_USER_TEXT = "#f5f0e8"
# 输入框（深褐底 + 金边）
COLOR_INPUT_BG = "#1e1812"
COLOR_INPUT_BORDER = "#8b7355"
COLOR_INPUT_TEXT = "#d4c8a8"
# 头像边框（金色）
COLOR_AVATAR_BORDER = "#b89868"
# 状态点（暗金微光）
COLOR_STATUS = "#b89868"
# 文字
COLOR_TITLE_TEXT = "#f5f0e8"
COLOR_SUBTITLE = "#c8b898"
COLOR_CLOSE_BTN = "#c8b898"
# 滚动条（暗金）
COLOR_SCROLLBAR = "#8b7355"
# 分隔线
COLOR_SEP = "#5a4a38"

# 资源路径
XIAOGE_DIR = r"D:\dataset\xiaoge"
BG_FILE = "张起灵，我们来接你回家"
AVATAR_FILE = "这张脸，就是我心里的张起灵"


def find_resource(keyword):
    """模糊匹配资源文件"""
    if os.path.exists(XIAOGE_DIR):
        for f in os.listdir(XIAOGE_DIR):
            if keyword in f:
                return os.path.join(XIAOGE_DIR, f)
    return None


def make_rounded_bg(source_path, width, height, radius=14):
    """将背景图裁剪成圆角矩形（不叠加颜色，保留原图）"""
    result = QPixmap(width, height)
    result.fill(Qt.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)

    # 圆角裁剪路径
    path = QPainterPath()
    path.addRoundedRect(0, 0, width, height, radius, radius)
    painter.setClipPath(path)

    if source_path and os.path.exists(source_path):
        pix = QPixmap(source_path)
        if not pix.isNull():
            # 按高度缩放，居中裁剪（保持比例）
            scaled = pix.scaledToHeight(height, Qt.SmoothTransformation)
            if scaled.width() < width:
                scaled = pix.scaledToWidth(width, Qt.SmoothTransformation)
            x = (width - scaled.width()) // 2
            y = (height - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

    painter.setClipping(False)
    # 金色细边框
    painter.setPen(QPen(QColor(COLOR_AVATAR_BORDER), 1))
    painter.setBrush(Qt.NoBrush)
    painter.drawRoundedRect(0, 0, width - 1, height - 1, radius, radius)
    painter.end()
    return result


def make_avatar(source_path, size=36, face_y_ratio=0.5, face_x_ratio=0.5):
    """圆形头像：金色细边框，脸部居中（可调整裁剪偏移）"""
    result = QPixmap(size, size)
    result.fill(Qt.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)

    # 圆形裁剪
    path = QPainterPath()
    path.addEllipse(2, 2, size - 4, size - 4)
    painter.setClipPath(path)

    if source_path and os.path.exists(source_path):
        pix = QPixmap(source_path)
        if not pix.isNull():
            crop_size = size - 4
            scaled = pix.scaled(crop_size, crop_size,
                                Qt.KeepAspectRatioByExpanding,
                                Qt.SmoothTransformation)
            # 脸部居中：根据脸部在原图中的比例调整裁剪偏移
            face_x_scaled = scaled.width() * face_x_ratio
            face_y_scaled = scaled.height() * face_y_ratio
            x = 2 + crop_size // 2 - face_x_scaled
            y = 2 + crop_size // 2 - face_y_scaled
            # 限制偏移范围，不超出图片边界
            x = max(2 + crop_size - scaled.width(), min(2, x))
            y = max(2 + crop_size - scaled.height(), min(2, y))
            painter.drawPixmap(x, y, scaled)

    painter.setClipping(False)
    # 金色细边框
    painter.setPen(QPen(QColor(COLOR_AVATAR_BORDER), 2))
    painter.setBrush(Qt.NoBrush)
    painter.drawEllipse(2, 2, size - 4, size - 4)
    painter.end()
    return result


class MessageBubble(QWidget):
    """消息气泡：头像 + 自适应宽度气泡 + 尖角"""
    def __init__(self, text, is_user=True, parent=None,
                 bot_avatar=None, user_avatar=None):
        super().__init__(parent)
        self.is_user = is_user

        max_bubble_w = 150  # 气泡最大宽度
        min_bubble_w = 32   # 气泡最小宽度
        avatar_size = 34
        # 小padding：上下2px，左右3px；border 1px
        # extra_w = 3*2(padding) + 1*2(border) = 8
        extra_w = 8
        padding_v = 4  # 上下各2

        # 用字体度量手动换行
        font = QFont("Microsoft YaHei", 11)
        fm = QFontMetrics(font)
        max_text_w = max_bubble_w - extra_w  # 文字最大宽度 = 142

        # 第一步：用最大宽度手动换行
        lines = []
        for paragraph in text.split('\n'):
            if not paragraph:
                lines.append("")
                continue
            cur = ""
            cur_w = 0
            for ch in paragraph:
                ch_w = fm.horizontalAdvance(ch)
                if cur_w + ch_w > max_text_w and cur:
                    lines.append(cur)
                    cur = ch
                    cur_w = ch_w
                else:
                    cur += ch
                    cur_w += ch_w
            if cur:
                lines.append(cur)

        # 用\n连接手动换行后的文本
        wrapped_text = "\n".join(lines)

        # 通用气泡样式（小padding）
        if is_user:
            qss = f"""
                QLabel {{
                    background-color: {COLOR_USER_BG};
                    color: {COLOR_USER_TEXT};
                    border: 1px solid {COLOR_USER_BORDER};
                    border-top-left-radius: 5px;
                    border-top-right-radius: 2px;
                    border-bottom-right-radius: 5px;
                    border-bottom-left-radius: 5px;
                    padding: 2px 3px;
                    font-family: "Microsoft YaHei";
                    font-size: 11px;
                }}
            """
        else:
            qss = f"""
                QLabel {{
                    background-color: {COLOR_BOT_BG};
                    color: {COLOR_BOT_TEXT};
                    border: 1px solid {COLOR_BOT_BORDER};
                    border-top-left-radius: 2px;
                    border-top-right-radius: 5px;
                    border-bottom-right-radius: 5px;
                    border-bottom-left-radius: 5px;
                    padding: 2px 3px;
                    font-family: "Microsoft YaHei";
                    font-size: 11px;
                }}
            """

        # 创建气泡：手动换行 + 关闭自动换行 + adjustSize实测尺寸
        bubble = QLabel(wrapped_text)
        bubble.setWordWrap(False)
        bubble.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)  # 可选中复制
        bubble.setStyleSheet(qss)
        bubble.ensurePolished()
        # adjustSize获取实际渲染的精确尺寸（像微信一样紧贴文字）
        bubble.adjustSize()
        bubble_w = bubble.width()
        bubble_h = bubble.height()
        # 安全限制
        if bubble_w < min_bubble_w:
            bubble_w = min_bubble_w
            bubble.setFixedWidth(bubble_w)
        if bubble_w > max_bubble_w:
            bubble_w = max_bubble_w
            bubble.setFixedWidth(bubble_w)
            bubble.adjustSize()
            bubble_h = bubble.height()
        if bubble_h < 20:
            bubble_h = 20
        bubble.setFixedSize(bubble_w, bubble_h)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(6, 3, 6, 3)
        main_layout.setSpacing(7)

        if is_user:
            # 用户侧：右对齐 [气泡] [头像]
            main_layout.addStretch()
            main_layout.addWidget(bubble)
            self.avatar_label = QLabel()
            self.avatar_label.setFixedSize(avatar_size, avatar_size)
            self.avatar_label.setPixmap(user_avatar if user_avatar else make_avatar(None, avatar_size))
            main_layout.addWidget(self.avatar_label)
        else:
            # 小哥侧：左对齐 [头像] [气泡]
            self.avatar_label = QLabel()
            self.avatar_label.setFixedSize(avatar_size, avatar_size)
            self.avatar_label.setPixmap(bot_avatar if bot_avatar else make_avatar(None, avatar_size))
            main_layout.addWidget(self.avatar_label)
            main_layout.addWidget(bubble)
            main_layout.addStretch()

        self.setMinimumHeight(max(bubble_h + 6, avatar_size + 6))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def update_avatar(self, new_avatar):
        """更新头像"""
        self.avatar_label.setPixmap(new_avatar)


class StatusDot(QWidget):
    """暗金微光状态点"""
    def __init__(self, color=COLOR_STATUS, parent=None):
        super().__init__(parent)
        self.color = color
        self.setFixedSize(8, 8)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        from PyQt5.QtGui import QRadialGradient
        grad = QRadialGradient(4, 4, 4)
        base = QColor(self.color)
        grad.setColorAt(0.3, base)
        base.setAlpha(80)
        grad.setColorAt(0.7, base)
        base.setAlpha(0)
        grad.setColorAt(1.0, base)
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, 8, 8)
        painter.end()


class ChatWindow(QWidget):
    """青铜墨冰聊天窗口"""
    message_sent = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._typing_label = None
        self._drag_pos = None
        self.message_bubbles = []  # 保存所有消息气泡引用
        # 加载配置（优先用自定义路径）
        self._load_config()
        # 加载资源
        self.bg_path = self.config.get("background_path") or find_resource(BG_FILE)
        self.avatar_path = self.config.get("avatar_path") or find_resource(AVATAR_FILE)
        self.bot_avatar = make_avatar(self.avatar_path, 36, face_y_ratio=0.22, face_x_ratio=0.65)
        self.user_avatar = make_avatar(None, 36)
        self._setup_ui()

    def _load_config(self):
        """加载配置文件"""
        import json
        import sys
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "api_config.json")
        self.config = {}
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
        except Exception:
            pass

    def reload_resources(self):
        """重新加载资源（设置保存后调用）"""
        self._load_config()
        new_bg = self.config.get("background_path") or find_resource(BG_FILE)
        new_avatar = self.config.get("avatar_path") or find_resource(AVATAR_FILE)
        if new_bg != self.bg_path or new_avatar != self.avatar_path:
            self.bg_path = new_bg
            self.avatar_path = new_avatar
            self.bot_avatar = make_avatar(self.avatar_path, 36, face_y_ratio=0.22, face_x_ratio=0.65)
            self._update_background()
            # 更新标题栏头像
            for child in self.findChildren(QLabel):
                if child.width() == 38 and child.height() == 38:
                    child.setPixmap(self.bot_avatar)
                    break
            # 更新所有消息气泡中的小哥头像
            for bubble in self.message_bubbles:
                if not bubble.is_user:
                    bubble.update_avatar(self.bot_avatar)

    def _setup_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(310, 430)

        # 主容器（圆角背景图）
        self.container = QFrame(self)
        self.container.setStyleSheet("background: transparent; border: none;")
        self.container.setGeometry(0, 0, 310, 430)

        # 背景图label（圆角裁剪）
        self.bg_label = QLabel(self.container)
        self.bg_label.setGeometry(0, 0, 310, 430)
        self.bg_label.setStyleSheet("background: transparent; border: none;")
        self._update_background()

        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ===== 标题栏 =====
        title_bar = QWidget()
        title_bar.setFixedHeight(56)
        title_bar.setStyleSheet("background: transparent;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(14, 10, 10, 8)
        title_layout.setSpacing(10)

        # 头像
        title_avatar = QLabel()
        title_avatar.setFixedSize(38, 38)
        title_avatar.setPixmap(self.bot_avatar)
        title_layout.addWidget(title_avatar)

        # 昵称列
        title_col = QVBoxLayout()
        title_col.setContentsMargins(0, 0, 0, 0)
        title_col.setSpacing(2)

        name_row = QHBoxLayout()
        name_row.setContentsMargins(0, 0, 0, 0)
        name_row.setSpacing(6)
        name_label = QLabel("张起灵")
        name_label.setFont(QFont("STKaiti", 15, QFont.Bold))
        name_label.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_TITLE_TEXT};
                background: transparent;
            }}
        """)
        name_row.addWidget(name_label)
        status_dot = StatusDot(COLOR_STATUS)
        name_row.addWidget(status_dot)
        name_row.addStretch()
        title_col.addLayout(name_row)

        subtitle = QLabel("青铜门后 · 人间看不见的绝色")
        subtitle.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        subtitle.setStyleSheet(f"""
            QLabel {{
                color: #ffd700;
                background: transparent;
            }}
        """)
        title_col.addWidget(subtitle)

        title_layout.addLayout(title_col, 1)

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(26, 26)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLOR_CLOSE_BTN};
                border: none;
                border-radius: 13px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: rgba(184, 152, 104, 50);
                color: {COLOR_TITLE_TEXT};
            }}
        """)
        self.close_btn.clicked.connect(self.hide)
        title_layout.addWidget(self.close_btn)

        main_layout.addWidget(title_bar)

        # 分隔线
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {COLOR_SEP};")
        main_layout.addWidget(sep)

        # 拖动
        title_bar.mousePressEvent = self._title_press
        title_bar.mouseMoveEvent = self._title_move
        title_bar.mouseReleaseEvent = self._title_release

        # ===== 聊天记录区（透明，露出背景）=====
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                width: 4px;
                background: transparent;
            }}
            QScrollBar::handle:vertical {{
                background: {COLOR_SCROLLBAR};
                border-radius: 2px;
                min-height: 24px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(4, 12, 4, 12)
        self.chat_layout.setSpacing(6)
        self.chat_layout.addStretch()

        self.scroll_area.setWidget(self.chat_container)
        main_layout.addWidget(self.scroll_area, 1)

        # ===== 输入区域（无发送按钮，回车发送）=====
        input_bar = QWidget()
        input_bar.setFixedHeight(48)
        input_bar.setStyleSheet("background: transparent;")
        input_layout = QHBoxLayout(input_bar)
        input_layout.setContentsMargins(12, 8, 12, 12)
        input_layout.setSpacing(0)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("想问小哥什么...（回车发送）")
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLOR_INPUT_BG};
                color: {COLOR_INPUT_TEXT};
                border: 1px solid {COLOR_INPUT_BORDER};
                border-radius: 6px;
                padding: 7px 12px;
                font-family: "Microsoft YaHei";
                font-size: 11px;
            }}
            QLineEdit:focus {{
                border-color: #d4b888;
            }}
        """)
        self.input_field.setFont(QFont("Microsoft YaHei", 10))
        self.input_field.returnPressed.connect(self._on_send)
        input_layout.addWidget(self.input_field)

        main_layout.addWidget(input_bar)

    def _update_background(self):
        """更新圆角背景图"""
        if self.bg_path:
            bg = make_rounded_bg(self.bg_path, 310, 430, radius=14)
            if hasattr(self, 'bg_label'):
                self.bg_label.setPixmap(bg)

    # ===== 窗口拖动 =====
    def _title_press(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def _title_move(self, event):
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def _title_release(self, event):
        self._drag_pos = None

    # ===== 消息操作 =====
    def add_user_message(self, text):
        self._remove_typing()
        bubble = MessageBubble(text, is_user=True,
                               bot_avatar=self.bot_avatar,
                               user_avatar=self.user_avatar)
        self.message_bubbles.append(bubble)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        QTimer.singleShot(10, self._scroll_to_bottom)

    def add_bot_message(self, text):
        self._remove_typing()
        bubble = MessageBubble(text, is_user=False,
                               bot_avatar=self.bot_avatar,
                               user_avatar=self.user_avatar)
        self.message_bubbles.append(bubble)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        QTimer.singleShot(10, self._scroll_to_bottom)

    def show_typing(self):
        self._remove_typing()
        self._typing_label = MessageBubble("...", is_user=False,
                                            bot_avatar=self.bot_avatar,
                                            user_avatar=self.user_avatar)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, self._typing_label)
        QTimer.singleShot(10, self._scroll_to_bottom)

    def _remove_typing(self):
        if self._typing_label:
            self.chat_layout.removeWidget(self._typing_label)
            self._typing_label.deleteLater()
            self._typing_label = None

    def _scroll_to_bottom(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_send(self):
        text = self.input_field.text().strip()
        if text:
            self.message_sent.emit(text)
            self.input_field.clear()
            self.input_field.setFocus()

    def show_near(self, x, y):
        screen = self.screen().availableGeometry() if self.screen() else None
        if screen:
            x = max(screen.left(), min(x, screen.right() - self.width()))
            y = max(screen.top(), min(y, screen.bottom() - self.height()))
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
        self.input_field.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)
