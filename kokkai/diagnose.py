"""確かめの段で型が合わなかった候補の原因を調べる（2026-11-21、運営者の決定：割れたら材料の不足→定義の穴→文が二通りに読める、の順に AI の外の原因を特定する）。
confirm.py と同じ課題文を GPT と Gemini に各3回渡し、型・説明に加えて「根拠」（拠った型の定義の文）と「足りない情報」を答えさせる。
出力：diagnose.jsonl。python3 kokkai/diagnose.py <日付>"""
import json, os, sys, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import refute, llm, classify_prompt, series_check
D = refute.D
F = [json.loads(l) for l in open(os.path.join(D, 'confirmed.jsonl'), encoding='utf-8')]
bad = {(x['speechID'], x['type']) for x in F if x['results'][0] != '別系統で支持'}
R = [json.loads(l) for f in ('refuted.jsonl', 'refuted2.jsonl', 'refuted3.jsonl', 'refuted_shuisho.jsonl') if os.path.exists(os.path.join(D, f)) for l in open(os.path.join(D, f), encoding='utf-8')]
C = [r for r in R if (r['speechID'], r['claude']['type']) in bad]
EXTRA = '\n\n追加の出力：JSON に "根拠"（型を決めるときに拠った型の定義の文や決まりを、上の文からそのまま写す）と "足りない情報"（判定に足りなかった情報があれば具体的に。なければ空）を加える。'
def run(job):
    r, name, n = job
    P = (series_check.prompt(r, r['source']) if r.get('source') else classify_prompt.prompt(r)) + EXTRA
    try: j = llm.js((llm.gpt if name == 'gpt' else llm.gemini)(P)) or {}
    except Exception as ex: j = {'type': 'エラー', 'explanation': type(ex).__name__}
    return dict(speechID=r['speechID'], url=r['url'], claude=r['claude']['type'], judge=name, n=n, type=j.get('type'), explanation=j.get('explanation'), basis=j.get('根拠'), missing=j.get('足りない情報'), speech_quote=j.get('speech_quote'), source_quote=j.get('source_quote'))
jobs = [(r, nm, n) for r in C for nm in ('gpt', 'gemini') for n in range(3)]
with cf.ThreadPoolExecutor(6) as ex, open(os.path.join(D, 'diagnose.jsonl'), 'w', encoding='utf-8') as w:
    for x in ex.map(run, jobs):
        w.write(json.dumps(x, ensure_ascii=False) + '\n'); print(x['speechID'], x['judge'], x['type'], flush=True)
print('候補', len(C))
