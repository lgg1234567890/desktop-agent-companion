# -*- coding: utf-8 -*-
"""
张起灵桌面 Agent - 主程序（升级版）
- 轮廓窗口（setMask跟随人物形状）
- 单击切换13种动作
- 双击开启聊天
- 角色设置界面
- 气泡面部智能偏移
"""
import sys
import os
import math
import time
import random
import ctypes
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMenu, QAction
from PyQt5.QtGui import QPixmap, QTransform, QRegion, QCursor
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect, pyqtSignal

from config import *
from character import CLICK_BUBBLES, RANDOM_ACTIONS
from llm_client import LLMClient
from chat_window import ChatWindow
from bubble import BubbleWindow
import os
import sys

# 调试日志
def _debug_log(msg):
    try:
        log_path = r"D:\my algo\pet\pet_debug.log"
        with open(log_path, "a", encoding="utf-8") as f:
            import datetime
            f.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}\n")
    except Exception:
        pass
from window_manager import WindowManager
from character_settings import CharacterSettingsWindow, load_character_prompt
from agent_core import get_agent_core
from tts import get_tts_player

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

ACTION_IMAGES = {
    "idle": "idle.png", "walk": "walk.png", "monkey_crawl": "monkey_crawl.png",
    "slash": "slash.png", "qilin_blood": "qilin_blood.png", "two_fingers": "two_fingers.png",
    "jump": "jump.png", "crouch": "crouch.png", "nod": "nod.png",
    "injured": "injured.png", "squeeze": "squeeze.png", "eat_noodle": "eat_noodle.png",
    "kneel": "kneel.png", "kneel_apologize": "kneel_apologize.png",
    "climb": "climb.png", "sit": "sit.png", "fall": "fall.png",
}

# 单击循环切换的13种动作 + 台词
CLICK_ACTION_CYCLE = [
    ("idle",            None),
    ("monkey_crawl",    None),
    ("slash",           "闪开"),
    ("qilin_blood",     "别动"),
    ("two_fingers",     "有机关"),
    ("jump",            "跟上"),
    ("crouch",          "这里有问题"),
    ("nod",             "你来了"),
    ("injured",         "没事"),
    ("squeeze",         "等我"),
    ("eat_noodle",      "嗯"),
    ("kneel",           "爸爸"),
    ("kneel_apologize", "我错了"),
]


class PetWindow(QWidget):
    # 聊天回复信号（子线程→主线程）: 回复文本, 是否成功, 调用的工具列表, RAG上下文
    chat_reply_signal = pyqtSignal(str, bool, list, str)

    def __init__(self):
        super().__init__()
        # 无边框、透明、置顶、工具窗口
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # 尺寸
        self.pet_width = DEFAULT_PET_WIDTH
        self.pet_height = DEFAULT_PET_HEIGHT
        self.resize(self.pet_width, self.pet_height)

        # 加载原始图片
        self.raw_pixmaps = {}
        self._load_raw_images()

        # 浮动相位（必须在_update之前）
        self.float_phase = 0
        self.float_offset = 0

        # 状态: idle / walking / interacting / climbing / sitting / falling / chatting
        self.state = "idle"
        self.current_action = "idle"
        self.facing_right = True
        self.walk_direction = 1

        # 单击动作索引 + 防抖
        self.click_action_idx = 0
        self._last_click_time = 0

        # 步行到目标位置
        self.walk_target = None
        self.walk_target_pos = QPoint()

        # 显示标签
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setGeometry(0, 0, self.pet_width, self.pet_height)
        self._update_pixmap()
        self._update_mask()

        # 主循环
        self.tick_timer = QTimer()
        self.tick_timer.timeout.connect(self._on_tick)
        self.tick_timer.start(TICK_INTERVAL)

        # 自主活动
        self.auto_active = True
        self.idle_timer = QTimer()
        self.idle_timer.setSingleShot(True)
        self.idle_timer.timeout.connect(self._start_walking)
        self.walk_timer = QTimer()
        self.walk_timer.setSingleShot(True)
        self.walk_timer.timeout.connect(self._start_idle)
        self.random_action_timer = QTimer()
        self.random_action_timer.setSingleShot(True)
        self.random_action_timer.timeout.connect(self._do_random_action)

        # 互动恢复计时
        self.interaction_end_timer = QTimer()
        self.interaction_end_timer.setSingleShot(True)
        self.interaction_end_timer.timeout.connect(self._end_interaction)

        # 掉落
        self.fall_velocity = 0
        self.fall_timer = QTimer()
        self.fall_timer.timeout.connect(self._on_fall_tick)

        # 窗口管理
        self.win_mgr = WindowManager()
        self.win_mgr.refresh()
        self.win_refresh_timer = QTimer()
        self.win_refresh_timer.timeout.connect(self.win_mgr.refresh)
        self.win_refresh_timer.start(800)

        # 附着窗口
        self.attached_hwnd = None
        self.attached_edge = None

        # 拖拽
        self.dragging = False
        self.drag_offset = QPoint()
        self.press_pos = QPoint()

        # 单击/双击区分
        self.click_timer = QTimer()
        self.click_timer.setSingleShot(True)
        self.click_timer.timeout.connect(self._on_single_click)
        self._pending_single_click = False

        # LLM + Agent核心（RAG + Function Calling + 角色管理）
        self.agent = get_agent_core()
        self.llm = self.agent.llm
        # 设置提醒回调：触发时显示气泡通知
        self.agent.set_reminder_callback(self._on_reminder_triggered)

        # 主动行为：隔一段时间主动发起会话（报时/健康提醒/问心情/问工作/记忆跟进）
        from proactive import ProactiveBehavior
        self.proactive = ProactiveBehavior(agent_core=self.agent)
        self.proactive_timer = QTimer()
        self.proactive_timer.timeout.connect(self._check_proactive)
        self.proactive_timer.start(60 * 1000)  # 每分钟检查一次

        # TTS 语音播放
        self.tts = get_tts_player()
        _debug_log(f"TTS初始化完成: tts={self.tts is not None}, enabled={self.tts.enabled}")
        try:
            from character_settings import load_api_config
            cfg = load_api_config()
            self.tts.set_enabled(cfg.get("voice_enabled", True))
            _debug_log(f"TTS配置加载: voice_enabled={cfg.get('voice_enabled', True)}")
        except Exception as e:
            _debug_log(f"TTS配置加载失败: {e}")
            self.tts.set_enabled(True)
        # 从文件加载人设
        custom_prompt = load_character_prompt()
        if custom_prompt:
            self.llm.system_prompt = custom_prompt
            self.agent.set_system_prompt(custom_prompt)
        self.chat_window = ChatWindow()
        self.chat_window.message_sent.connect(self._on_chat_message)
        self.chat_reply_signal.connect(self._on_llm_reply)
        _debug_log("程序启动，信号已连接")
        self.bubble = BubbleWindow()

        # 角色设置窗口
        self.settings_window = None

        # 初始位置：右下角
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - self.pet_width - 40,
                  screen.height() - self.pet_height - 20)

        # 启动后保持静止待机，不自动走动
        self.state = "idle"
        self.current_action = "idle"
        self._update_pixmap()
        self._update_mask()
        self.show()

    # ==================== 图片 ====================
    def _load_raw_images(self):
        for action, filename in ACTION_IMAGES.items():
            path = os.path.join(ASSETS_DIR, filename)
            if os.path.exists(path):
                self.raw_pixmaps[action] = QPixmap(path)

    def _get_scaled_pixmap(self):
        """获取当前动作的缩放+翻转后的pixmap"""
        if self.current_action not in self.raw_pixmaps:
            return None
        pix = self.raw_pixmaps[self.current_action]
        scaled = pix.scaled(self.pet_width, self.pet_height,
                            Qt.KeepAspectRatio, Qt.SmoothTransformation)
        if not self.facing_right:
            scaled = scaled.transformed(QTransform().scale(-1, 1))
        return scaled

    def _update_pixmap(self):
        scaled = self._get_scaled_pixmap()
        if scaled:
            self.label.setPixmap(scaled)
        self.label.setGeometry(0, int(self.float_offset), self.pet_width, self.pet_height)

    def _update_mask(self):
        """更新窗口遮罩，使窗口形状跟随人物轮廓"""
        scaled = self._get_scaled_pixmap()
        if scaled and not scaled.isNull():
            mask = scaled.mask()
            if not mask.isNull():
                self.setMask(QRegion(mask))

    def _rescale(self):
        """滚轮缩放后更新"""
        self.resize(self.pet_width, self.pet_height)
        self.label.setGeometry(0, 0, self.pet_width, self.pet_height)
        self._update_pixmap()
        self._update_mask()

    # ==================== 主循环 ====================
    def _on_tick(self):
        # 步行到目标位置（最高优先级）
        if self.walk_target:
            self._do_walk_to_target()
            return

        if self.state in ("interacting", "falling", "chatting"):
            return

        self.float_phase += 0.08
        if self.state == "walking":
            self.float_offset = int(3 * math.sin(self.float_phase * 1.5))
        elif self.state == "idle":
            self.float_offset = int(2 * math.sin(self.float_phase))
        else:
            self.float_offset = 0

        if self.state == "walking":
            self._do_walk()
        elif self.state in ("climbing", "sitting"):
            self._check_attached_window()

        self._update_pixmap()

    # ==================== 自主活动 ====================
    def _start_idle(self):
        if self.state != "walking" or not self.auto_active:
            return
        self.state = "idle"
        self.current_action = "idle"
        self._update_mask()
        # 已禁用自动走动

    def _start_walking(self):
        """已禁用：不自动走动"""
        pass

    def _schedule_idle(self):
        """已禁用"""
        pass

    def _schedule_walk(self):
        """已禁用：不自动走动"""
        pass

    def _schedule_random_action(self):
        """已禁用：不自动随机切换动作"""
        pass

    def _do_random_action(self):
        """已禁用：不自动随机切换动作"""
        pass
        QTimer.singleShot(1500, self._resume_walk)

    def _resume_walk(self):
        if self.state == "walking":
            self.current_action = "walk"
            self._update_mask()
            self._schedule_random_action()

    def _do_walk_to_target(self):
        """保持走路姿态，匀速移动到目标位置"""
        target = self.walk_target_pos
        x, y = self.x(), self.y()
        speed = WALK_SPEED
        dx = target.x() - x
        dy = target.y() - y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < speed:
            # 到达目标
            self.move(target.x(), target.y())
            self.walk_target = False
            self.current_action = "idle"
            self._update_pixmap()
            self._update_mask()
            return

        # 匀速移动
        move_x = int(dx / dist * speed)
        move_y = int(dy / dist * speed)

        # 根据移动方向设置朝向
        if move_x > 0:
            self.facing_right = True
        elif move_x < 0:
            self.facing_right = False

        # 保持走路姿态
        self.current_action = "walk"
        self.float_phase += 0.15
        self.float_offset = int(3 * math.sin(self.float_phase * 1.5))
        self.move(x + move_x, y + move_y)
        self._update_pixmap()
        self._update_mask()

    def _do_walk(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x, y = self.x(), self.y()
        speed = WALK_SPEED if self.current_action == "walk" else CRAWL_SPEED
        new_x = x + self.walk_direction * speed

        if new_x < 0:
            new_x = 0
            self.walk_direction = 1
            self.facing_right = True
            self._update_mask()
        elif new_x > screen.width() - self.pet_width:
            new_x = screen.width() - self.pet_width
            self.walk_direction = -1
            self.facing_right = False
            self._update_mask()

        if self.win_mgr.check_collision(new_x, y, self.pet_width, self.pet_height):
            self.walk_direction *= -1
            self.facing_right = (self.walk_direction > 0)
            self._update_mask()
            new_x = x + self.walk_direction * speed
            if self.win_mgr.check_collision(new_x, y, self.pet_width, self.pet_height):
                y += random.choice([-3, 3])
                y = max(screen.top(), min(screen.bottom() - self.pet_height, y))

        if random.random() < 0.003:
            self.walk_direction *= -1
            self.facing_right = (self.walk_direction > 0)
            self._update_mask()

        self.move(new_x, y)

    # ==================== 鼠标事件 ====================
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_offset = event.globalPos() - self.frameGeometry().topLeft()
            self.press_pos = event.globalPos()
            self.idle_timer.stop()
            self.walk_timer.stop()
            self.random_action_timer.stop()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.dragging:
            self.dragging = False
            moved = (event.globalPos() - self.press_pos).manhattanLength() > 10
            if moved:
                self._try_attach_to_window(event.globalPos())
            else:
                self._pending_single_click = True
                self.click_timer.start(200)
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pending_single_click = False
            self.click_timer.stop()
            self._open_chat()
            event.accept()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.pet_width = min(MAX_PET_WIDTH, self.pet_width + 15)
        else:
            self.pet_width = max(MIN_PET_WIDTH, self.pet_width - 15)
        self.pet_height = int(self.pet_width * 1.44)
        self._rescale()
        event.accept()

    # ==================== 单击切换动作 ====================
    def _on_single_click(self):
        if not self._pending_single_click:
            return
        self._pending_single_click = False
        # 单击随时切换动作，不受状态限制
        self._cycle_action()

    def _cycle_action(self):
        """单击轮流切换13种动作，切换时人物完全静止"""
        action_key, text = CLICK_ACTION_CYCLE[self.click_action_idx % len(CLICK_ACTION_CYCLE)]
        self.click_action_idx += 1
        # 停止所有定时器，确保静止
        self.idle_timer.stop()
        self.walk_timer.stop()
        self.random_action_timer.stop()
        self.interaction_end_timer.stop()
        self.state = "interacting"
        self.current_action = action_key
        self.float_offset = 0
        self._update_pixmap()
        self._update_mask()
        if text:
            self._show_face_bubble(text)
        elif action_key in ("idle", "monkey_crawl"):
            if random.random() < 0.3:
                self._show_face_bubble(random.choice(CLICK_BUBBLES))
        self.interaction_end_timer.start(INTERACTION_DURATION)

    def _end_interaction(self):
        """10秒间隔结束后，保持当前动作不变，不切换到idle"""
        if self.state == "interacting":
            self.state = "idle"
            # 保持 current_action 不变，不切换到 idle 图片
            self.float_offset = 0
            self._update_pixmap()
            self._update_mask()
            # 不启动自主活动，保持当前动作直到下一次单击

    # ==================== 气泡（面部智能偏移） ====================
    def _show_face_bubble(self, text, duration=BUBBLE_DURATION):
        """在面部附近显示气泡，智能偏移不遮脸，自动换行"""
        _debug_log(f"显示气泡: {text[:30]}")
        screen = QApplication.primaryScreen().availableGeometry()
        # 面部大约在人物上方22%处
        face_center_y = self.y() + int(self.pet_height * 0.22)

        # 使用与气泡绘制一致的字体计算尺寸
        from PyQt5.QtGui import QFont, QFontMetrics
        font = QFont("Microsoft YaHei", 11, QFont.Bold)
        fm = QFontMetrics(font)
        max_text_width = 380
        # 简单换行估算
        lines = []
        for paragraph in text.split('\n'):
            if not paragraph:
                lines.append("")
                continue
            cur = ""
            cur_w = 0
            for ch in paragraph:
                ch_w = fm.horizontalAdvance(ch)
                if cur_w + ch_w > max_text_width and cur:
                    lines.append(cur)
                    cur = ch
                    cur_w = ch_w
                else:
                    cur += ch
                    cur_w += ch_w
            if cur:
                lines.append(cur)
        max_line_w = max(fm.horizontalAdvance(ln) for ln in lines) if lines else 0
        bubble_w = max(120, min(450, max_line_w + 44))
        line_h = fm.height() + 4
        bubble_h = max(48, line_h * len(lines) + 28)

        # 根据朝向决定气泡在脸的哪一侧
        if self.facing_right:
            bubble_x = self.x() - bubble_w - 8
        else:
            bubble_x = self.x() + self.pet_width + 8

        # 垂直居中对齐面部
        bubble_y = face_center_y - bubble_h // 2

        # 防止超出屏幕
        bubble_x = max(5, min(screen.width() - bubble_w - 5, bubble_x))
        bubble_y = max(5, min(screen.height() - bubble_h - 5, bubble_y))

        self.bubble.show_text(text, bubble_x, bubble_y, duration)
        # 气泡文字自动朗读（动作切换、主动打招呼、提醒等所有气泡）
        tts = getattr(self, 'tts', None)
        _debug_log(f"_show_face_bubble: text='{text[:30]}', tts_exists={tts is not None}")
        if tts:
            _debug_log(f"tts.enabled={tts.enabled}, cosyvoice_available={tts._cosyvoice_available}")
            tts.speak(text)
        else:
            _debug_log("tts未初始化，跳过朗读")

    # ==================== 拖拽附着窗口 ====================
    def _try_attach_to_window(self, release_pos):
        """改进的边缘检测：检测图片四边到窗口边缘的距离，任意一边靠近就附着"""
        left = self.x()
        right = self.x() + self.pet_width
        top = self.y()
        bottom = self.y() + self.pet_height
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        threshold = 150
        best_edge = None
        best_dist = threshold
        best_hwnd = None
        best_rect = None
        for hwnd, title, rect in self.win_mgr.windows:
            wl, wt, wr, wb = rect
            if wl - 20 < center_x < wr + 20:
                d = abs(top - wt)
                if d < best_dist:
                    best_edge, best_dist, best_hwnd, best_rect = 'top', d, hwnd, rect
                d = abs(bottom - wb)
                if d < best_dist:
                    best_edge, best_dist, best_hwnd, best_rect = 'bottom', d, hwnd, rect
            if wt - 20 < center_y < wb + 20:
                d = abs(left - wl)
                if d < best_dist:
                    best_edge, best_dist, best_hwnd, best_rect = 'left', d, hwnd, rect
                d = abs(right - wr)
                if d < best_dist:
                    best_edge, best_dist, best_hwnd, best_rect = 'right', d, hwnd, rect
        if best_hwnd and best_edge and best_rect:
            self._attach_to_window(best_hwnd, best_edge, best_rect)
        else:
            self.attached_hwnd = None
            self.attached_edge = None
            self.state = "idle"
            self.current_action = "idle"
            self._update_pixmap()
            self._update_mask()
            if self.auto_active:
                self._schedule_walk()

    def _attach_to_window(self, hwnd, edge_type, rect):
        l, t, r, b = rect
        self.attached_hwnd = hwnd
        self.attached_edge = edge_type
        if edge_type == 'top':
            self.state = "sitting"
            self.current_action = "sit"
            new_x = max(l, min(r - self.pet_width, self.x()))
            new_y = t - self.pet_height + 40
            self.move(new_x, new_y)
        elif edge_type in ('left', 'right'):
            self.state = "climbing"
            self.current_action = "climb"
            if edge_type == 'left':
                self.move(l - self.pet_width // 2, max(t, min(b - self.pet_height, self.y())))
                self.facing_right = True
            else:
                self.move(r - self.pet_width // 2, max(t, min(b - self.pet_height, self.y())))
                self.facing_right = False
        else:
            self.attached_hwnd = None
            self.state = "idle"
            self.current_action = "idle"
        self._update_pixmap()
        self._update_mask()

    def _check_attached_window(self):
        if self.attached_hwnd is None:
            return
        if not self.win_mgr.is_window_alive(self.attached_hwnd):
            self._start_falling()
            return
        rect = self.win_mgr.get_window_rect(self.attached_hwnd)
        if not rect:
            self._start_falling()
            return
        l, t, r, b = rect
        if self.attached_edge == 'top':
            target_y = t - self.pet_height + 40
            if abs(self.y() - target_y) > 3:
                self.move(self.x(), target_y)
        elif self.attached_edge == 'left':
            target_x = l - self.pet_width // 2
            if abs(self.x() - target_x) > 3:
                self.move(target_x, self.y())
        elif self.attached_edge == 'right':
            target_x = r - self.pet_width // 2
            if abs(self.x() - target_x) > 3:
                self.move(target_x, self.y())

    def _start_falling(self):
        self.state = "falling"
        self.current_action = "fall"
        self._update_pixmap()
        self._update_mask()
        self.fall_velocity = 0
        self.attached_hwnd = None
        self.fall_timer.start(30)

    def _on_fall_tick(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.fall_velocity += 1.8
        new_y = self.y() + int(self.fall_velocity)
        if new_y >= screen.bottom() - self.pet_height:
            new_y = screen.bottom() - self.pet_height
            self.fall_timer.stop()
            self.fall_velocity = 0
            self.state = "idle"
            self.current_action = "idle"
            self._update_pixmap()
            self._update_mask()
            if self.auto_active:
                self._schedule_walk()
        else:
            self.move(self.x(), new_y)

    # ==================== 聊天 ====================
    def _open_chat(self):
        self.state = "idle"
        self.current_action = "idle"
        self._update_pixmap()
        self._update_mask()
        self.idle_timer.stop()
        self.walk_timer.stop()
        # 聊天窗口显示在角色右侧
        box_x = self.x() + self.pet_width + 10
        box_y = self.y()
        self.chat_window.show_near(box_x, box_y)

    def _on_chat_message(self, text):
        _debug_log(f"收到聊天消息: {text}")
        self.state = "chatting"
        self.current_action = "idle"
        self._update_pixmap()
        self._update_mask()
        # 将用户消息添加到聊天窗口
        self.chat_window.add_user_message(text)
        # 显示正在输入
        self.chat_window.show_typing()
        _debug_log("启动LLM子线程")
        threading.Thread(target=self._llm_chat_worker, args=(text,), daemon=True).start()

    def _llm_chat_worker(self, text):
        _debug_log("子线程开始调用LLM（含RAG+Function Calling）")
        try:
            reply, ok, tools_used, rag_context = self.agent.chat(text, use_rag=True, use_tools=True)
            _debug_log(f"LLM调用完成: ok={ok}, tools={[t['name'] for t in tools_used]}, reply={reply[:50]}")
        except Exception as e:
            _debug_log(f"LLM调用异常: {type(e).__name__}: {str(e)[:100]}")
            reply, ok, tools_used, rag_context = f"（调用异常：{type(e).__name__}）", False, [], ""
        # 通过信号通知主线程（子线程不能直接操作UI）
        self.chat_reply_signal.emit(reply, ok, tools_used, rag_context)

    def _on_llm_reply(self, reply, ok, tools_used=None, rag_context=""):
        _debug_log(f"_on_llm_reply被调用: ok={ok}, tools={len(tools_used or [])}, reply={reply[:50]}")
        # 将回复添加到聊天窗口
        self.chat_window.add_bot_message(reply)
        # 如果调用了工具，在气泡中显示工具调用信息
        if tools_used:
            tool_names = "、".join(t.get("name", "") for t in tools_used)
            _debug_log(f"本次调用工具: {tool_names}")
        # 只有聊天窗口未打开时，才在角色旁边显示粉色气泡
        if not self.chat_window.isVisible():
            self._show_face_bubble(reply, duration=5000)
        else:
            # 聊天窗口打开时，直接朗读回复（气泡不显示但声音要播）
            if hasattr(self, 'tts'):
                self.tts.speak(reply)
        self.state = "idle"
        self.current_action = "idle"
        self._update_pixmap()
        self._update_mask()
        if self.auto_active:
            self._schedule_walk()
        # 用户对话后，推迟主动行为（避免刚聊完又主动说话）
        self.proactive.last_trigger_time = time.time()

    def _check_proactive(self):
        """每分钟检查一次是否应该主动发起会话"""
        if not self.proactive.should_trigger():
            return
        if self.chat_window.isVisible():
            return  # 聊天窗口打开时不打扰
        if self.state != "idle":
            return  # 非空闲状态不打扰

        msg, btype = self.proactive.generate(chat_window_visible=False)
        if msg:
            self._show_face_bubble(msg, duration=8000)
            _debug_log(f"主动行为[{btype}]: {msg}")
            # 主动打招呼内容写入聊天历史，双击打开对话框可见
            try:
                self.chat_window.add_bot_message(msg)
            except Exception:
                pass

    def _on_reminder_triggered(self, delay_ms, message):
        """提醒触发：延迟显示气泡通知"""
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(int(delay_ms), lambda: self._show_face_bubble(f"⏰ {message}", duration=8000))
        _debug_log(f"提醒已设置: {delay_ms}ms 后 - {message}")

    # ==================== 右键菜单 ====================
    def contextMenuEvent(self, event):
        # 记录右键点击位置，用于"步行到此处"
        self._right_click_pos = event.globalPos()

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(40, 40, 50, 240);
                color: #ffd6e0;
                border: 1px solid #ff9eb5;
                border-radius: 8px;
                padding: 6px;
                font-family: "Microsoft YaHei"; font-size: 13px;
            }
            QMenu::item { padding: 6px 24px; border-radius: 4px; }
            QMenu::item:selected { background-color: rgba(255, 158, 181, 200); color: #402030; }
            QMenu::separator { height: 1px; background: #ff9eb5; margin: 4px 8px; }
        """)

        # 角色设置
        settings_act = QAction("角色设置", self)
        settings_act.triggered.connect(self._open_settings)
        menu.addAction(settings_act)

        # 步行到此处
        walk_act = QAction("步行到此处", self)
        walk_act.triggered.connect(self._start_walk_to_click)
        menu.addAction(walk_act)

        # 和小哥聊天
        chat_act = QAction("和小哥聊天", self)
        chat_act.triggered.connect(self._open_chat)
        menu.addAction(chat_act)

        # 自主活动开关
        auto_text = "关闭自主活动" if self.auto_active else "开启自主活动"
        auto_act = QAction(auto_text, self)
        auto_act.triggered.connect(self._toggle_auto_active)
        menu.addAction(auto_act)

        # 清空记忆
        clear_act = QAction("清空对话记忆", self)
        clear_act.triggered.connect(self._clear_memory)
        menu.addAction(clear_act)

        menu.addSeparator()

        # 13种动作
        for label, action_key, text in [
            ("待机站立", "idle", None),
            ("猴子爬行", "monkey_crawl", None),
            ("挥刀斩击", "slash", "闪开"),
            ("麒麟放血", "qilin_blood", "别动"),
            ("二指探洞", "two_fingers", "有机关"),
            ("跳跃飞身", "jump", "跟上"),
            ("蹲下探查", "crouch", "这里有问题"),
            ("点头致意", "nod", "你来了"),
            ("受伤踉跄", "injured", "没事"),
            ("缩骨钻缝", "squeeze", "等我"),
            ("吃泡面", "eat_noodle", "嗯"),
            ("叫爸爸", "kneel", "爸爸"),
            ("我错了", "kneel_apologize", "我错了"),
        ]:
            act = QAction(label, self)
            act.triggered.connect(lambda checked, ak=action_key, t=text:
                                  self._play_menu_action(ak, t))
            menu.addAction(act)

        menu.addSeparator()
        quit_act = QAction("退出", self)
        quit_act.triggered.connect(QApplication.instance().quit)
        menu.addAction(quit_act)
        menu.exec_(event.globalPos())

    def _start_walk_to_click(self):
        """右键菜单选择步行到此处，人物保持走路姿态移动到右键点击位置"""
        if not hasattr(self, '_right_click_pos'):
            return
        self.walk_target = True
        self.walk_target_pos = QPoint(
            self._right_click_pos.x() - self.pet_width // 2,
            self._right_click_pos.y() - self.pet_height // 2
        )
        # 停止其他定时器
        self.idle_timer.stop()
        self.walk_timer.stop()
        self.random_action_timer.stop()
        self.interaction_end_timer.stop()
        self.attached_hwnd = None
        self.attached_edge = None

    def _open_settings(self):
        if self.settings_window is None:
            self.settings_window = CharacterSettingsWindow()
            self.settings_window.settings_saved.connect(self._on_settings_saved)
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def _on_settings_saved(self, new_prompt, api_config):
        self.llm.system_prompt = new_prompt
        self.agent.set_system_prompt(new_prompt)
        self.llm.reload_config()
        self.llm.clear_history()
        self.agent.clear_history()
        # 更新语音开关
        try:
            from character_settings import load_api_config
            cfg = load_api_config()
            self.tts.set_enabled(cfg.get("voice_enabled", True))
        except Exception:
            pass
        # 重新加载聊天窗口资源（头像、背景等）
        try:
            self.chat_window.reload_resources()
        except Exception as e:
            _debug_log(f"重新加载聊天窗口资源失败: {e}")

    def _toggle_auto_active(self):
        self.auto_active = not self.auto_active
        if self.auto_active:
            self.state = "idle"
            self.current_action = "idle"
            self._update_pixmap()
            self._update_mask()
            self._schedule_walk()
        else:
            self.idle_timer.stop()
            self.walk_timer.stop()
            self.random_action_timer.stop()
            self.state = "idle"
            self.current_action = "idle"
            self._update_pixmap()
            self._update_mask()

    def _clear_memory(self):
        self.llm.clear_history()
        self.agent.clear_history()
        self._show_face_bubble("记忆已清空。")

    def _play_menu_action(self, action_key, text):
        self.idle_timer.stop()
        self.walk_timer.stop()
        self.random_action_timer.stop()
        self.interaction_end_timer.stop()
        self.state = "interacting"
        self.current_action = action_key
        self.float_offset = 0
        self._update_pixmap()
        self._update_mask()
        if text:
            self._show_face_bubble(text)
        self.interaction_end_timer.start(INTERACTION_DURATION)


# ==================== 主入口 ====================
def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("xiaoge.agent.pet")
    pet = PetWindow()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
