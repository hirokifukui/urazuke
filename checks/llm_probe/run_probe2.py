# H035 の続き：YK-C1・ST-I2 の基準線（原文を渡す）。キーは環境変数、なければ運営者の指定したファイルから読む（表示しない）。結果は results/llm_probe/answers.jsonl（公開しない）。
import os, re, json, time, datetime, urllib.request, sys
KEYF = os.path.expanduser('~/Library/Mobile Documents/com~apple~CloudDocs/APIキー.txt'); TXT = open(KEYF).read()
GK = re.findall(r'AIza[0-9A-Za-z_\-]{35}', TXT)[1]; XK = re.findall(r'xai-[0-9A-Za-z]+', TXT)[0]; PK = re.findall(r'pplx-[A-Za-z0-9]+', TXT)[0]
SRCS = {
 'YK': """法務省矯正局・保護局「刑事施設及び保護観察所における薬物事犯者に対するプログラムの効果検証結果（概要）」（令和４年10月）より
○ 再犯追跡調査 ⇒刑事施設及び保護観察所におけるプログラムの処遇効果が示唆された
【刑事施設】薬物依存離脱指導対象者742名について、出所後2年間の再犯状況を追跡調査し、旧実施体制における再犯率と比較した。再犯率：旧実施体制 26.6%、新実施体制 20.9%（5.7ポイント差）。
※ 旧実施体制＝平成25年に出所した標準プログラム改訂前の薬物依存離脱指導対象者593名　※ 新実施体制＝平成30年11月から令和元年5月までに出所した標準プログラム改訂後の薬物依存離脱指導対象者742名
【保護観察所】平成30年に薬物事犯により保護観察を開始した成人の保護観察対象者4,661名のうち、受講の有無以外の要因が結果に影響を与えないよう、受講群と非受講群の属性や特性等が等質となるように抽出した2,812名について、保護観察開始から令和３年末まで最長４年間の再犯状況を追跡調査し、コアプログラム受講の有無で再犯率を比較した。再犯率：非受講群 34.6%、受講群 30.3%（4.3ポイント差）。""",
 'ST': """警察庁「令和７年におけるストーカー事案、配偶者からの暴力事案等、児童虐待事案等への対応状況について」より
４ ストーカー事案の検挙状況　ストーカー規制法違反の検挙は、令和７年は1,546件（前年比＋205件、＋15.3％）、ストーカー事案に関連する刑法犯・他の特別法犯の検挙は、令和７年は2,171件（前年比＋428件、＋24.6％）と法施行後でそれぞれ最多となった。
表　ストーカー規制法違反の検挙件数：令和３年 937、令和４年 1,028、令和５年 1,081、令和６年 1,341、令和７年 1,546
注）ストーカー規制法に基づく行政措置、ストーカー事案の検挙状況及び警察本部長等の援助については、令和５年までは基準年中に受理した相談のうち同年中に実施した行政措置、検挙及び援助（以下「行政措置等」という。）した件数を計上していたところ、令和６年からは、基準年中に受理した相談の有無に関わらず、基準年中に実施した行政措置等の件数は全て計上することに変更した。""",
}
LIM = '300字以内で答えてください。'
PROMPTS = {}
for r, src in SRCS.items():
    PROMPTS[r + '-B1'] = '次の資料の内容を、一般の読者向けに3文で要約してください。' + LIM + '\n\n' + src
    PROMPTS[r + '-B2'] = '次の資料をもとに、ニュース記事の見出しと1段落のリードを書いてください。' + LIM + '\n\n' + src
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
os.makedirs('results/llm_probe', exist_ok=True); OUT = 'results/llm_probe/answers2.jsonl'
done = {(j['model'], j['prompt'], j['rep']) for j in map(json.loads, open(OUT))} if os.path.exists(OUT) else set()
jobs = [(m, p, k) for m in MODELS for p in PROMPTS for k in range(1, 4)]
with open(OUT, 'a') as f:
    for m, p, k in jobs:
        if (m, p, k) in done: continue
        try: a = ask(m, PROMPTS[p]); err = ''
        except Exception as ex: a = ''; err = f'{type(ex).__name__}: {str(ex)[:150]}'
        f.write(json.dumps(dict(model=m, prompt=p, rep=k, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'), answer=a, error=err), ensure_ascii=False) + '\n'); f.flush()
        print(m, p, k, len(a), err[:60], flush=True)
open('results/llm_probe/PROMPTS2.json', 'w').write(json.dumps(PROMPTS, ensure_ascii=False, indent=1))
print('done')
