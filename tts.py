# -*- coding: utf-8 -*-
"""
TTS 语音模块：优先阿里云 CosyVoice（低沉男声），失败降级 edge-tts
"""
import os
import sys
import asyncio
import tempfile
import threading
import datetime

# 日志文件（固定路径，方便查找）
LOG_FILE = r"D:\my algo\pet\tts_debug.log"

def _log(msg):
    """写入日志文件"""
    try:
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except Exception as e:
        # 日志写入失败时，尝试写到temp
        try:
            import tempfile
            with open(os.path.join(tempfile.gettempdir(), "xiaoge_tts_fallback.log"), "a", encoding="utf-8") as f:
                f.write(f"{msg}\n")
        except Exception:
            pass

# 临时音频目录
TEMP_DIR = os.path.join(tempfile.gettempdir(), "xiaoge_tts")
os.makedirs(TEMP_DIR, exist_ok=True)

# CosyVoice 配置：沉稳磁性男声 + 自然语速
COSYVOICE_MODEL = "cosyvoice-v1"
COSYVOICE_VOICE = "longmiao"  # 龙渺：沉稳磁性男声，更接近小哥的冷静低沉
COSYVOICE_RATE = 0.95  # 语速稍慢，自然不机械
COSYVOICE_PITCH = 1.0  # 不调整音调，保持自然
COSYVOICE_VOLUME = 80  # 音量

# edge-tts 配置（降级用）
EDGE_VOICE = "zh-CN-YunjianNeural"  # 云健：低沉男声
EDGE_RATE = "-15%"
EDGE_PITCH = "-5Hz"


class TTSPlayer:
    """TTS 生成 + 播放"""

    def __init__(self):
        self.enabled = True
        self._temp_files = []
        self._cosyvoice_available = None  # None=未检测, True=可用, False=不可用
        self._player = None
        self._audio_output = None
        self._play_handler = None
        self._init_player()

    def _init_player(self):
        """在主线程初始化播放器（必须在主线程调用），兼容新旧版PyQt5 API"""
        try:
            from PyQt5.QtMultimedia import QMediaPlayer
            from PyQt5.QtCore import QObject, pyqtSignal

            class PlayHandler(QObject):
                play_signal = pyqtSignal(str)

                def __init__(self):
                    super().__init__()
                    self.player = QMediaPlayer()
                    self._use_new_api = False
                    # 尝试新版API（setAudioOutput）
                    try:
                        from PyQt5.QtMultimedia import QAudioOutput
                        self.audio_output = QAudioOutput()
                        self.player.setAudioOutput(self.audio_output)
                        self.audio_output.setVolume(0.8)
                        self._use_new_api = True
                        _log("使用新版API: setAudioOutput")
                    except (AttributeError, ImportError):
                        # 旧版API：直接setVolume
                        self.player.setVolume(80)
                        _log("使用旧版API: setVolume")
                    self.play_signal.connect(self._do_play)
                    # 监听播放状态
                    try:
                        self.player.mediaStatusChanged.connect(self._on_status)
                    except Exception:
                        pass

                def _on_status(self, status):
                    from PyQt5.QtMultimedia import QMediaPlayer
                    _log(f"播放状态变化: {status}")
                    if status == QMediaPlayer.MediaStatus.EndOfMedia:
                        _log("播放完成")
                    elif status == QMediaPlayer.MediaStatus.InvalidMedia:
                        _log("无效媒体")
                    elif status == QMediaPlayer.MediaStatus.BufferedMedia:
                        _log("媒体已缓冲")

                def _do_play(self, path):
                    from PyQt5.QtCore import QUrl
                    _log(f"主线程播放: {path}")
                    # 先停止当前播放，避免叠加
                    try:
                        self.player.stop()
                    except Exception:
                        pass
                    if self._use_new_api:
                        self.player.setSource(QUrl.fromLocalFile(path))
                    else:
                        from PyQt5.QtMultimedia import QMediaContent
                        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
                    self.player.play()
                    _log("play()已调用")

            self._play_handler = PlayHandler()
            _log("播放器初始化成功")
        except Exception as e:
            _log(f"播放器初始化失败: {e}")
            import traceback
            _log(traceback.format_exc())

    def set_enabled(self, enabled):
        self.enabled = enabled

    def speak(self, text, on_finished=None):
        """文本转语音并播放（异步，不阻塞UI）"""
        _log(f"speak被调用: enabled={self.enabled}, text='{text[:30]}'")
        if not self.enabled or not text or not text.strip():
            _log(f"speak跳过: enabled={self.enabled}, text_empty={not text}")
            if on_finished:
                on_finished()
            return

        def worker():
            try:
                _log(f"开始生成音频: '{text[:30]}'")
                audio_path = self._generate(text)
                if audio_path:
                    _log(f"音频生成成功: {audio_path}")
                    self._play(audio_path, on_finished)
                else:
                    _log("音频生成失败，无路径")
                    if on_finished:
                        on_finished()
            except Exception as e:
                _log(f"播放异常: {e}")
                import traceback
                _log(traceback.format_exc())
                if on_finished:
                    on_finished()

        threading.Thread(target=worker, daemon=True).start()

    def _generate(self, text):
        """生成音频，优先 CosyVoice，失败降级 edge-tts"""
        clean_text = self._clean_text(text)
        if not clean_text:
            _log("清理后文本为空")
            return None

        # 缓存检查
        cache_file = self._get_cache_path(clean_text)
        if os.path.exists(cache_file) and os.path.getsize(cache_file) > 0:
            _log(f"使用缓存: {cache_file}")
            return cache_file

        # 优先 CosyVoice
        if self._cosyvoice_available is not False:
            try:
                _log("尝试CosyVoice...")
                path = self._generate_cosyvoice(clean_text, cache_file)
                if path:
                    self._cosyvoice_available = True
                    _log("CosyVoice成功")
                    return path
            except Exception as e:
                _log(f"CosyVoice失败: {e}")
                import traceback
                _log(traceback.format_exc())
                self._cosyvoice_available = False

        # 降级 edge-tts
        try:
            _log("尝试edge-tts...")
            path = self._generate_edge(clean_text, cache_file)
            if path:
                _log("edge-tts成功")
                return path
        except Exception as e:
            _log(f"edge-tts失败: {e}")
            import traceback
            _log(traceback.format_exc())

        _log("所有TTS后端都失败了")
        return None

    def _generate_cosyvoice(self, text, cache_file):
        """用阿里云 CosyVoice 生成音频"""
        import dashscope
        from dashscope.audio.tts import SpeechSynthesizer
        from config import LLM_API_KEY

        dashscope.api_key = LLM_API_KEY
        result = SpeechSynthesizer.call(
            model=COSYVOICE_MODEL,
            text=text,
            voice=COSYVOICE_VOICE,
            format="mp3",
            sample_rate=22050,
            rate=COSYVOICE_RATE,
            pitch=COSYVOICE_PITCH,
            volume=COSYVOICE_VOLUME,
        )
        audio = result.get_audio_data()
        if audio and len(audio) > 0:
            with open(cache_file, "wb") as f:
                f.write(audio)
            self._record_cache(cache_file)
            return cache_file
        return None

    def _generate_edge(self, text, cache_file):
        """用 edge-tts 生成音频（降级方案）"""
        import edge_tts

        async def _gen():
            communicate = edge_tts.Communicate(
                text=text,
                voice=EDGE_VOICE,
                rate=EDGE_RATE,
                pitch=EDGE_PITCH,
            )
            await communicate.save(cache_file)

        asyncio.run(_gen())
        if os.path.exists(cache_file) and os.path.getsize(cache_file) > 0:
            self._record_cache(cache_file)
            return cache_file
        return None

    def _clean_text(self, text):
        """清理文本，去掉表情符号，处理可能导致TTS截断的标点"""
        clean = text.strip()
        # 去掉表情符号
        for ch in ["⏰", "💧", "❤️", "✨", "🎵", "💪", "😊", "😴"]:
            clean = clean.replace(ch, "")
        # 省略号替换为句号，避免TTS提前结束
        clean = clean.replace("……", "。").replace("...", "。")
        # 去掉首尾标点
        clean = clean.strip("，。！？、；：")
        # 如果文本太短，加个语气词让TTS更自然
        if len(clean) <= 2:
            clean = clean + "。"
        # 去掉过长的文本（TTS限制）
        if len(clean) > 300:
            clean = clean[:300]
        return clean

    def _get_cache_path(self, text):
        """获取缓存文件路径（包含音色和参数，换参数后自动失效）"""
        cache_key = f"{COSYVOICE_VOICE}_{COSYVOICE_RATE}_{COSYVOICE_PITCH}_{text}"
        filename = f"tts_{abs(hash(cache_key))}_{len(text)}.mp3"
        return os.path.join(TEMP_DIR, filename)

    def _record_cache(self, path):
        """记录缓存文件，清理旧缓存"""
        self._temp_files.append(path)
        if len(self._temp_files) > 20:
            old = self._temp_files.pop(0)
            try:
                if os.path.exists(old):
                    os.remove(old)
            except Exception:
                pass

    def _play(self, audio_path, on_finished=None):
        """用 PyQt5 播放音频（通过信号在主线程播放）"""
        try:
            _log(f"准备播放: {audio_path}")
            if self._play_handler:
                self._play_handler.play_signal.emit(audio_path)
                if on_finished:
                    # 简单延迟回调（不精确，但够用）
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(3000, on_finished)
            else:
                _log("播放器未初始化，尝试直接播放")
                from PyQt5.QtMultimedia import QMediaPlayer
                from PyQt5.QtCore import QUrl
                player = QMediaPlayer()
                # 兼容新旧API
                try:
                    from PyQt5.QtMultimedia import QAudioOutput
                    audio = QAudioOutput()
                    player.setAudioOutput(audio)
                    audio.setVolume(0.8)
                    player.setSource(QUrl.fromLocalFile(audio_path))
                except (AttributeError, ImportError):
                    player.setVolume(80)
                    from PyQt5.QtMultimedia import QMediaContent
                    player.setMedia(QMediaContent(QUrl.fromLocalFile(audio_path)))
                player.play()
                _log("fallback play()已调用")
                if on_finished:
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(3000, on_finished)
        except Exception as e:
            _log(f"播放异常: {e}")
            import traceback
            _log(traceback.format_exc())
            if on_finished:
                on_finished()

    def cleanup(self):
        """清理临时文件"""
        for f in self._temp_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass
        self._temp_files = []


# 全局单例
_tts_player = None


def get_tts_player():
    global _tts_player
    if _tts_player is None:
        _tts_player = TTSPlayer()
    return _tts_player
