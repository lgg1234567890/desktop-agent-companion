# -*- coding: utf-8 -*-
"""窗口管理器：枚举桌面窗口，检测边缘与碰撞"""
import win32gui
from PyQt5.QtCore import QRect


class WindowManager:
    def __init__(self):
        self.windows = []

    def refresh(self):
        self.windows = []
        def callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return True
            title = win32gui.GetWindowText(hwnd)
            if not title:
                return True
            if title in ["Program Manager", "Windows 输入体验", "Settings",
                         "Microsoft Store", "Windows 资源管理器", ""]:
                return True
            rect = win32gui.GetWindowRect(hwnd)
            if rect[2] - rect[0] < 80 or rect[3] - rect[1] < 80:
                return True
            if rect[0] <= -32000:
                return True
            self.windows.append((hwnd, title, rect))
            return True
        try:
            win32gui.EnumWindows(callback, None)
        except Exception:
            pass

    def is_window_alive(self, hwnd):
        try:
            if not win32gui.IsWindow(hwnd) or not win32gui.IsWindowVisible(hwnd):
                return False
            rect = win32gui.GetWindowRect(hwnd)
            return rect[0] > -32000
        except Exception:
            return False

    def get_window_rect(self, hwnd):
        try:
            return win32gui.GetWindowRect(hwnd)
        except Exception:
            return None

    def find_edge_at(self, x, y, threshold=55):
        """检测点附近最近的窗口边缘"""
        best = None
        best_dist = threshold
        for hwnd, title, rect in self.windows:
            l, t, r, b = rect
            if l - threshold < x < r + threshold:
                d = abs(y - t)
                if d < best_dist:
                    best = (hwnd, 'top', rect)
                    best_dist = d
                d = abs(y - b)
                if d < best_dist:
                    best = (hwnd, 'bottom', rect)
                    best_dist = d
            if t - threshold < y < b + threshold:
                d = abs(x - l)
                if d < best_dist:
                    best = (hwnd, 'left', rect)
                    best_dist = d
                d = abs(x - r)
                if d < best_dist:
                    best = (hwnd, 'right', rect)
                    best_dist = d
        return best

    def check_collision(self, x, y, w, h):
        """检测桌宠矩形是否与窗口内部碰撞"""
        pet_rect = QRect(x, y, w, h)
        for hwnd, title, rect in self.windows:
            l, t, r, b = rect
            win_rect = QRect(l + 10, t + 10, r - l - 20, b - t - 20)
            if pet_rect.intersects(win_rect):
                return True
        return False
