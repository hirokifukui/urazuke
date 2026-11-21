"""Claude・GPT を API で呼ぶ（キーは環境変数か運営者の鍵のファイルから。表示しない）。"""
import json, os, re, time, urllib.request
KEYF = os.path.expanduser('~/Library/Mobile Documents/com~apple~CloudDocs/APIキー.txt')
def _k(env, pat, excl=None):
    v = os.environ.get(env)
    if v: return v
    xs = [x for x in re.findall(pat, open(KEYF, encoding='utf-8').read()) if not (excl and x.startswith(excl))]
    return xs[0]
def _post(url, h, body):
    for i in range(4):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(url, data=json.dumps(body).encode(), headers=h), timeout=300))
        except Exception as ex:
            if i == 3: raise
            time.sleep(10 * (i + 1))
def claude(prompt, model='claude-opus-5-5', max_tokens=2000):
    d = _post('https://api.anthropic.com/v1/messages', {'x-api-key': _k('URAZUKE_ANTHROPIC_API_KEY', r'sk-ant-[A-Za-z0-9_-]{20,}'), 'anthropic-version': '2023-06-01', 'content-type': 'application/json'},
              {'model': model, 'max_tokens': max_tokens, 'messages': [{'role': 'user', 'content': prompt}]})
    return ''.join(c.get('text', '') for c in d['content'])
def gpt(prompt, model='gpt-5.5'):
    d = _post('https://api.openai.com/v1/chat/completions', {'Authorization': 'Bearer ' + _k('OPENAI_API_KEY', r'sk-(?:proj-)?[A-Za-z0-9_-]{40,}', 'sk-ant'), 'Content-Type': 'application/json'},
              {'model': model, 'messages': [{'role': 'user', 'content': prompt}]})
    return d['choices'][0]['message']['content']
def js(t):
    m = re.search(r'\{.*\}', t, re.S)
    return json.loads(m.group(0)) if m else None
