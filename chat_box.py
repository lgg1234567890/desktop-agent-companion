# -*- coding: utf-8 -*-
"""聊天输入框窗口：桌宠旁边弹出的小输入框"""
from PyQt5.QtWidgets import QWidget, QLineEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class ChatInputBox(QWidget):
    """桌宠旁的聊天输入框"""
    message_sent = pyqtSignal(str)  # 发送消息信号

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedHeight(42)

        # 背景容器
        self.container = QWidget(self)
        self.container.setStyleSheet("""
            QWidget {
                background-color: rgba(40, 40, 50, 240);
                border: 1px solid #ff9eb5;
                border-radius: 8px;
            }
        """)

        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("跟小哥说点什么...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: rgba(60, 60, 75, 200);
                color: #ffe0ea;
                border: 1px solid #ff9eb5;
                border-radius: 6px;
                padding: 4px 8px;
                font-family: "Microsoft YaHei";
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #ffc0cb;
            }
        """)
        self.input_field.setFont(QFont("Microsoft YaHei", 10))
        self.input_field.returnPressed.connect(self._on_send)
        layout.addWidget(self.input_field, 1)

        self.send_btn = QPushButton("发送")
        self.send_btn.setFixedWidth(56)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9eb5;
                color: #402030;
                border: none;
                border-radius: 6px;
                padding: 4px 8px;
                font-family: "Microsoft YaHei";
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffb6c1;
            }
            QPushButton:pressed {
                background-color: #ff85a2;
            }
        """)
        self.send_btn.clicked.connect(self._on_send)
        layout.addWidget(self.send_btn)

        self.container.setGeometry(0, 0, 260, 42)
        self.resize(260, 42)
        self.hide()

    def show_near(self, x, y, width=260):
        """在桌宠旁边显示输入框"""
        self.resize(width, 42)
        self.container.setGeometry(0, 0, width, 42)
        self.move(x, y)
        self.show()
        self.raise_()
        self.input_field.setFocus()
        self.input_field.clear()

    def _on_send(self):
        text = self.input_field.text().strip()
        if text:
            self.message_sent.emit(text)
            self.input_field.clear()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)
