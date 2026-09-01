# -*- coding: utf-8 -*-
import requests, json

api_key = 'sk-ws-H.EXHIPRH.Cxyl.MEUCIQChYoGgVlmuyEkDS07OLx--5Ynlcnyu71kw3_uQm2A1UgIgCcLnFHaYsyvIhT9njvmg0fP_gUQTH23SvMf8oL0fc_4'

# 测试OpenAI兼容模式的TTS
url = 'https://dashscope.aliyuncs.com/compatible-mode/v1/audio/speech'
headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
data = {'model': 'cosyvoice-v1', 'input': '你好，测试语音', 'voice': 'longxiaochun', 'response_format': 'mp3'}
try:
    resp = requests.post(url, headers=headers, json=data, timeout=30)
    print('状态码:', resp.status_code)
    ct = resp.headers.get('Content-Type', '')
    print('Content-Type:', ct)
    if resp.status_code == 200:
        print('音频大小:', len(resp.content), 'bytes')
        with open(r'D:\my algo\pet\test_aliyun.mp3', 'wb') as f:
            f.write(resp.content)
        print('阿里云TTS成功！已保存test_aliyun.mp3')
    else:
        print('响应:', resp.text[:500])
except Exception as e:
    print('请求失败:', e)
