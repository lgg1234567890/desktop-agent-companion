# -*- coding: utf-8 -*-
import dashscope
from dashscope.audio.tts import SpeechSynthesizer
import inspect

dashscope.api_key = 'sk-ws-H.EXHIPRH.Cxyl.MEUCIQChYoGgVlmuyEkDS07OLx--5Ynlcnyu71kw3_uQm2A1UgIgCcLnFHaYsyvIhT9njvmg0fP_gUQTH23SvMf8oL0fc_4'

# 看看SpeechSynthesizer.call的源码
print(inspect.getsource(SpeechSynthesizer.call))
