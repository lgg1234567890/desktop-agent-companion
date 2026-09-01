# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'D:\my algo\pet')
from tts import TTSPlayer

tts = TTSPlayer()
print("正在生成语音：该喝水了")
path = tts._generate("该喝水了")
if path:
    import os
    print(f"音频生成成功: {path}")
    print(f"文件大小: {os.path.getsize(path)} bytes")
else:
    print("音频生成失败")
