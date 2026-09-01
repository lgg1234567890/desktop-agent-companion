# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'D:\my algo\pet')
from tts import TTSPlayer

tts = TTSPlayer()
print("正在生成语音（优先CosyVoice）...")
path = tts._generate("你好，我是张起灵。该喝水了。")
if path:
    import os
    print(f"音频生成成功: {path}")
    print(f"文件大小: {os.path.getsize(path)} bytes")
    print(f"CosyVoice可用: {tts._cosyvoice_available}")
else:
    print("音频生成失败")
