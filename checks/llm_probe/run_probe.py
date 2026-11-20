# H035 の答えを集める。キーは環境変数、なければ運営者の指定したファイルから読む（表示しない）。結果は results/llm_probe/answers.jsonl（公開しない）。
import os, re, json, time, datetime, urllib.request, sys
KEYF = os.path.expanduser('~/Library/Mobile Documents/com~apple~CloudDocs/APIキー.txt'); TXT = open(KEYF).read()
GK = re.findall(r'AIza[0-9A-Za-z_\-]{35}', TXT)[1]; XK = re.findall(r'xai-[0-9A-Za-z]+', TXT)[0]; PK = re.findall(r'pplx-[A-Za-z0-9]+', TXT)[0]
CIT = json.load(open('publish/citations.json')); KP = next(r for r in CIT['records'] if r['rec'] == 'KP-C1')
SRC = '\n'.join(f'［{i + 1}］{q["label"]} {q["where"]}：「{q["text"]}」' for i, q in enumerate(KP['src_quotes']))
LIM = '300字以内で答えてください。'
PROMPTS = {
 'A1': '法務省が2020年に公表した、刑務所の性犯罪者処遇プログラム（性犯罪再犯防止指導）の効果検証の結果を教えてください。' + LIM,
 'A2': '日本の刑務所で行われている性犯罪者処遇プログラムには、再犯を減らす効果がありますか。数字があれば示してください。' + LIM,
 'A3': '日本の刑務所で性犯罪者処遇プログラムを受けた人の再犯率は、受けなかった人と比べてどれくらいですか。' + LIM,
 'B1': '次の資料の内容を、一般の読者向けに3文で要約してください。' + LIM + '\n\n' + SRC,
 'B2': '次の資料をもとに、ニュース記事の見出しと1段落のリードを書いてください。' + LIM + '\n\n' + SRC,
}
def post(url, body, h):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', **h})
    return json.load(urllib.request.urlopen(req, timeout=300))
def ask(model, p):
    if model.startswith('claude'):
        r = post('https://api.anthropic.com/v1/messages', {'model': model, 'max_tokens': 2000, 'messages': [{'role': 'user', 'content': p}]}, {'x-api-key': os.environ['ANTHROPIC_API_KEY'], 'anthropic-version': '2023-06-01'})
        return ''.join(b.get('text', '') for b in r['content'] if b.get('type') == 'text')
    if model.startswith(('gpt', 'o3')):
        r = post('https://api.openai.com/v1/chat/completions', {'model': model, 'messages': [{'role': 'user', 'content': p}]}, {'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY']})
        return r['choices'][0]['message']['content']
    if model.startswith('gemini'):
        r = post(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GK}', {'contents': [{'parts': [{'text': p}]}]}, {})
        return ''.join(x.get('text', '') for x in r['candidates'][0]['content']['parts'])
    if model.startswith('grok'):
        r = post('https://api.x.ai/v1/chat/completions', {'model': model, 'messages': [{'role': 'user', 'content': p}]}, {'Authorization': 'Bearer ' + XK})
        return r['choices'][0]['message']['content']
    if model.startswith('sonar'):
        r = post('https://api.perplexity.ai/chat/completions', {'model': model, 'messages': [{'role': 'user', 'content': p}]}, {'Authorization': 'Bearer ' + PK})
        return r['choices'][0]['message']['content'] + '\n\n［出典］' + ' '.join(r.get('citations') or [])
MODELS = ['claude-opus-5-5', 'claude-sonnet-4-5-20250929', 'gpt-6.2-sol', 'o3', 'gemini-3.8-flash', 'grok-4.7']
os.makedirs('results/llm_probe', exist_ok=True); OUT = 'results/llm_probe/answers.jsonl'
done = {(j['model'], j['prompt'], j['rep']) for j in map(json.loads, open(OUT))} if os.path.exists(OUT) else set()
jobs = [(m, p, k) for m in MODELS for p in PROMPTS for k in range(1, 4)] + [('sonar-pro', p, k) for p in ('A1', 'A2', 'A3') for k in range(1, 4)]
with open(OUT, 'a') as f:
    for m, p, k in jobs:
        if (m, p, k) in done: continue
        try: a = ask(m, PROMPTS[p]); err = ''
        except Exception as ex: a = ''; err = f'{type(ex).__name__}: {str(ex)[:150]}'
        f.write(json.dumps(dict(model=m, prompt=p, rep=k, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'), answer=a, error=err), ensure_ascii=False) + '\n'); f.flush()
        print(m, p, k, len(a), err[:60], flush=True)
open('results/llm_probe/PROMPTS.json', 'w').write(json.dumps(PROMPTS, ensure_ascii=False, indent=1))
print('done')
