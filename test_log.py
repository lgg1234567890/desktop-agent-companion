# -*- coding: utf-8 -*-
import datetime
import os

log_path = r"D:\my algo\pet\test_write.log"

# 测试1: 基本写入
try:
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("测试1: 基本写入成功\n")
    print("测试1成功")
except Exception as e:
    print(f"测试1失败: {e}")

# 测试2: 带时间戳的f-string
try:
    with open(log_path, "a", encoding="utf-8") as f:
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        f.write(f"[{ts}] 测试2: f-string写入成功\n")
    print("测试2成功")
except Exception as e:
    print(f"测试2失败: {e}")

# 测试3: 中文内容
try:
    with open(log_path, "a", encoding="utf-8") as f:
        f.write("测试3: 中文内容写入成功，闪开别动\n")
    print("测试3成功")
except Exception as e:
    print(f"测试3失败: {e}")

# 读取验证
print("\n=== 文件内容 ===")
with open(log_path, "r", encoding="utf-8") as f:
    print(f.read())

print(f"文件大小: {os.path.getsize(log_path)} bytes")
