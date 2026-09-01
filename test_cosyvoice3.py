# -*- coding: utf-8 -*-
import dashscope
from dashscope.audio.tts import SpeechSynthesizer

dashscope.api_key = 'sk-ws-H.EXHIPRH.Cxyl.MEUCIQChYoGgVlmuyEkDS07OLx--5Ynlcnyu71kw3_uQm2A1UgIgCcLnFHaYsyvIhT9njvmg0fP_gUQTH23SvMf8oL0fc_4'

result = SpeechSynthesizer.call(
    model='cosyvoice-v1',
    text='你好，我是张起灵。该喝水了。',
    voice='longxiaochun',
    format='mp3',
    sample_rate=22050
)
print('类型:', type(result))
print('属性:', [a for a in dir(result) if not a.startswith('_')])
audio = result.get_audio_data()
if audio:
    print('音频大小:', len(audio), 'bytes')
    with open(r'D:\my algo\pet\test_cosyvoice.mp3', 'wb') as f:
        f.write(audio)
    print('成功！已保存test_cosyvoice.mp3')
else:
    print('没有音频数据')
    print('response:', result.get_response())
