# -*- coding: utf-8 -*-
"""自动化测试聊天功能"""
import sys
import os
sys.path.insert(0, r"D:\my algo\pet")
os.chdir(r"D:\my algo\pet")

# 清空旧日志
if os.path.exists("pet_debug.log"):
    os.remove("pet_debug.log")

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from pet_agent import PetWindow

app = QApplication(sys.argv)
pet = PetWindow()

# 2秒后模拟发送聊天消息
def test_chat():
    print("模拟发送聊天消息: 你好")
    pet._on_chat_message("你好")

# 8秒后检查日志并退出
def check_and_exit():
    print("\n=== 调试日志 ===")
    if os.path.exists("pet_debug.log"):
        with open("pet_debug.log", "r", encoding="utf-8") as f:
            print(f.read())
    else:
        print("日志文件不存在!")
    app.quit()

QTimer.singleShot(2000, test_chat)
QTimer.singleShot(10000, check_and_exit)

sys.exit(app.exec_())
