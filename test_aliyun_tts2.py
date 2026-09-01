# -*- coding: utf-8 -*-
import requests, json

api_key = 'sk-ws-H.EXHIPRH.Cxyl.MEUCIQChYoGgVlmuyEkDS07OLx--5Ynlcnyu71kw3_uQm2A1UgIgCcLnFHaYsyvIhT9njvmg0fP_gUQTH23SvMf8oL0fc_4'

# 测试阿里云原生TTS API
url = 'https://dashscope.aliyuncs.com/api/v1/services/audio/tts'
headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json',
    'X-DashScope-Async': 'enable'
}
data = {
    'model': 'cosyvoice-v1',
    'input': {'text': '你好，测试语音'},
    'parameters': {
        'voice': 'longxiaochun',
        'format': 'mp3',
        'sample_rate': 22050
    }
}
try:
    resp = requests.post(url, headers=headers, json=data, timeout=30)
    print('状态码:', resp.status_code)
    print('响应:', resp.text[:500])
except Exception as e:
    print('请求失败:', e)
