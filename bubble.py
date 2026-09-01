# -*- coding: utf-8 -*-
"""对话气泡：不透明背景，自动换行，显示在角色旁不遮脸"""
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush, QPen, QPolygon, QFontMetrics
from PyQt5.QtCore import Qt, QRect, QTimer, QPoint


class BubbleWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self._text = ""
        self._wrapped_lines = []
        self.hide()

    def _wrap_text(self, text, max_width, fm):
        """根据最大宽度自动换行，支持中英文混合"""
        if not text:
            return [""]
        lines = []
        for paragraph in text.split('\n'):
            if not paragraph:
                lines.append("")
                continue
            current_line = ""
            current_width = 0
            for char in paragraph:
                char_width = fm.horizontalAdvance(char)
                if current_width + char_width > max_width and current_line:
                    lines.append(current_line)
                    current_line = char
                    current_width = char_width
                else:
                    current_line += char
                    current_width += char_width
            if current_line:
                lines.append(current_line)
        return lines if lines else [""]

    def show_text(self, text, x, y, duration=3000):
        """
        在角色旁显示气泡，自动换行
        x, y: 气泡左上角目标位置（已计算好，不遮脸）
        """
        self._text = text
        # 使用与绘制时相同的字体计算尺寸
        font = QFont("Microsoft YaHei", 11, QFont.Bold)
        fm = QFontMetrics(font)
        # 最大宽度420px，左右各留20px边距
        max_text_width = 380
        self._wrapped_lines = self._wrap_text(text, max_text_width, fm)
        # 计算气泡宽度：取最长行的宽度 + 边距
        max_line_width = max(fm.horizontalAdvance(line) for line in self._wrapped_lines)
        w = max(120, min(450, max_line_width + 44))
        # 计算气泡高度：行数 * 行高 + 边距
        line_height = fm.height() + 4
        h = max(48, line_height * len(self._wrapped_lines) + 28)
        self.resize(w, h)
        self.move(x, y)
        self.show()
        self.raise_()
        self.update()
        QTimer.singleShot(duration, self.hide)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        # 不透明粉色气泡
        bubble_rect = QRect(6, 4, w - 12, h - 16)
        bg_color = QColor(255, 240, 245)  # 不透明浅粉
        border_color = QColor(255, 150, 170)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, 2))
        painter.drawRoundedRect(bubble_rect, 12, 12)
        # 小尾巴
        tail_x = w // 2
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        tail = QPolygon([
            QPoint(tail_x - 7, h - 16),
            QPoint(tail_x + 7, h - 16),
            QPoint(tail_x, h - 1),
        ])
        painter.drawPolygon(tail)
        # 描边尾巴
        painter.setPen(QPen(border_color, 2))
        painter.drawLine(tail_x - 7, h - 16, tail_x, h - 1)
        painter.drawLine(tail_x + 7, h - 16, tail_x, h - 1)
        # 文字 - 逐行绘制，居中对齐
        painter.setPen(QColor(60, 30, 45))
        font = QFont("Microsoft YaHei", 11, QFont.Bold)
        painter.setFont(font)
        fm = QFontMetrics(font)
        line_height = fm.height() + 4
        total_text_height = line_height * len(self._wrapped_lines)
        start_y = (h - total_text_height) // 2 + 2
        for i, line in enumerate(self._wrapped_lines):
            line_width = fm.horizontalAdvance(line)
            text_x = (w - line_width) // 2
            text_y = start_y + i * line_height + fm.ascent()
            painter.drawText(text_x, text_y, line)
