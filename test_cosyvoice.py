# -*- coding: utf-8 -*-
import dashscope
from dashscope.audio.tts import SpeechSynthesizer

dashscope.api_key = 'sk-ws-H.EXHIPRH.Cxyl.MEUCIQChYoGgVlmuyEkDS07OLx--5Ynlcnyu71kw3_uQm2A1UgIgCcLnFHaYsyvIhT9njvmg0fP_gUQTH23SvMf8oL0fc_4'

try:
    result = SpeechSynthesizer.call(
        model='cosyvoice-v1',
        text='你好，我是张起灵。该喝水了。',
        voice='longxiaochun',
        format='mp3',
        sample_rate=22050
    )
    print('状态:', result.get_status())
    if result.get_audio_data() is not None:
        audio = result.get_audio_data()
        print('音频大小:', len(audio), 'bytes')
        with open(r'D:\my algo\pet\test_cosyvoice.mp3', 'wb') as f:
            f.write(audio)
        print('CosyVoice TTS成功！已保存test_cosyvoice.mp3')
    else:
        print('错误:', result.get_message())
except Exception as e:
    print('调用失败:', e)
    import traceback
    traceback.print_exc()
