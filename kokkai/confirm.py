"""確かめの段（2026-11-21 改め）。サイトに載せる候補（Claude が3回とも同じ型、GPT と Gemini が反証でそろって支持、引かれ方のページがある記録）を、
GPT と Gemini に「型を一から付けさせる」。Claude の主張は見せず、Claude に渡したのと同じ課題文（同じ型の一覧・同じ資料）を渡す。
二つとも Claude と同じ型（サイトに出す型として同じもの。範囲のずれ は 限定が落ちる と同じに数える）を付けたものだけを export.py が載せる。
前の版（主張の順序を変えて反証を2回やり直す）は、候補の全てで3回とも支持になり、ふるいとして効かなかった。主張を見せると、判定者はそれに引かれる。
出力：confirmed.jsonl（results に 'blind' の型）。python3 kokkai/confirm.py <日付>"""
import json, os, sys, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import refute, llm, classify_prompt, series_check
D = refute.D
CIT = {r['rec'] for r in json.load(open(os.path.join(refute.ROOT, 'publish/citations.json'), encoding='utf-8'))['records']}
TY = {'言い方が強まる', '限定が落ちる', '範囲のずれ', '数字の不一致', '食い違いなし'}
G = {'範囲のずれ': '限定が落ちる'}; g = lambda t: G.get(t, t)
R = [json.loads(l) for f in ('refuted.jsonl', 'refuted2.jsonl', 'refuted3.jsonl', 'refuted_shuisho.jsonl', 'refuted_q.jsonl')
     if os.path.exists(os.path.join(D, f)) for l in open(os.path.join(D, f), encoding='utf-8')]
def cand(r):
    j = r['claude']; runs = j.get('runs') or []
    return r['gpt']['result'] == '別系統で支持' and j.get('type') in TY and len(runs) >= 3 and runs.count(j.get('type')) * 2 > len(runs) and set(j.get('record_ids') or []) & CIT
C = [r for r in R if cand(r)]
NB = int(os.environ.get('KOKKAI_NBLIND', '5'))
def blind(r):   # 2026-11-21：各判定者に5回渡し、過半の型をその判定者の型とする（1回だけだと外れ1回で落ちる。引かれ方の R072 と同じ考え方）
    P = series_check.prompt(r, r['source']) if r.get('source') else classify_prompt.prompt(r)
    out, raw = {}, {}
    for name, fn in (('gpt', llm.gpt), ('gemini', llm.gemini)):
        ts = []
        for _ in range(NB):
            try: ts.append(g((llm.js(fn(P)) or {}).get('type', '')))
            except Exception: ts.append('エラー')
        raw[name] = ts
        top = max(set(ts), key=ts.count)
        out[name] = top if ts.count(top) * 2 > len(ts) else '過半なし'
    ok = all(t == g(r['claude']['type']) for t in out.values())
    return {'speechID': r['speechID'], 'url': r['url'], 'type': r['claude']['type'], 'blind': out, 'runs': raw, 'results': ['別系統で支持' if ok else '型が合わない']}
with cf.ThreadPoolExecutor(4) as ex, open(os.path.join(D, 'confirmed.jsonl'), 'w', encoding='utf-8') as w:
    for x in ex.map(blind, C):
        w.write(json.dumps(x, ensure_ascii=False) + '\n'); print(x['url'][-30:], x['type'], x['blind'], x['results'][0], flush=True)
print('候補', len(C))
