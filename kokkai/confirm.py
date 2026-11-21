"""反証のやり直し（2026-11-21）。サイトに載せる候補（Claude が3回とも同じ型、GPT と Gemini がそろって支持、引かれ方のページがある記録）だけを、
主張の順序を変えてさらに2回反証にかける。3回とも「別系統で支持」のものだけを export.py が載せる。
（同じ答弁で、回によって二つの判定者がそろって逆の主張を支持したことがあったため。）出力：confirmed.jsonl。python3 kokkai/confirm.py <日付>"""
import json, os, sys, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import refute
D = refute.D
CIT = {r['rec'] for r in json.load(open(os.path.join(refute.ROOT, 'publish/citations.json'), encoding='utf-8'))['records']}
TY = {'言い方が強まる', '限定が落ちる', '範囲のずれ', '数字の不一致', '食い違いなし'}
R = [json.loads(l) for f in ('refuted.jsonl', 'refuted2.jsonl', 'refuted3.jsonl', 'refuted_shuisho.jsonl', 'refuted_q.jsonl')
     if os.path.exists(os.path.join(D, f)) for l in open(os.path.join(D, f), encoding='utf-8')]
def cand(r):
    j = r['claude']; runs = j.get('runs') or []
    return r['gpt']['result'] == '別系統で支持' and j.get('type') in TY and len(runs) >= 3 and len(set(runs)) == 1 and set(j.get('record_ids') or []) & CIT
C = [r for r in R if cand(r)]
def again(r):
    c = {k: v for k, v in r.items() if k not in ('gpt', 'gemini')}
    res = [refute.run(c, k)['gpt']['result'] for k in (1, 2)]
    return {'speechID': r['speechID'], 'url': r['url'], 'type': r['claude']['type'], 'results': [r['gpt']['result']] + res}
with cf.ThreadPoolExecutor(4) as ex, open(os.path.join(D, 'confirmed.jsonl'), 'w', encoding='utf-8') as w:
    for x in ex.map(again, C):
        w.write(json.dumps(x, ensure_ascii=False) + '\n'); print(x['url'][-30:], x['type'], x['results'], flush=True)
