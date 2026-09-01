import requests
key = 'sk-8f9e9bcf656345678458845e89bc9a5a'
for model in ['glm-5', 'glm-4-plus', 'glm-4-air', 'glm-4-flash']:
    try:
        r = requests.post('https://open.bigmodel.cn/api/paas/v4/chat/completions',
            headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
            json={'model': model, 'messages': [{'role':'user','content':'你好'}], 'max_tokens': 50},
            timeout=15)
        print(f'{model}: status={r.status_code}')
        if r.status_code == 200:
            data = r.json()
            print(f'  回复: {data["choices"][0]["message"]["content"][:80]}')
        else:
            print(f'  错误: {r.text[:200]}')
    except Exception as e:
        print(f'{model}: 异常 {e}')
