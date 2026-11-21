"""反証の陰性対照（2026-11-21 改め）。
前の版は「Claude が食い違いなしとした答弁」を土台にしたが、2026-11-21s の回で、その土台に Claude の誤り（実際に限定が落ちている答弁）が含まれていた
（3件。GPT と Gemini がそろって資料の「全ての犯罪」の限定を指摘）。それでは反証の甘さではなく Claude の誤りを数えてしまう。
改めた土台：三つの判定者がそろって食い違いなしとしたもの（Claude が3回とも食い違いなし、かつ GPT と Gemini の反証で「食い違わない」が支持）。
これに、わざと「限定が落ちる」の主張を付けて、refute.py と同じ形で GPT と Gemini に渡す。二つともが支持した割合が、反証の甘さの目安になる。
python3 kokkai/negctl.py <日付>"""
import json, os, sys, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import refute
D = refute.D
R = [json.loads(l) for f in ('refuted.jsonl', 'refuted2.jsonl', 'refuted3.jsonl', 'refuted_shuisho.jsonl', 'refuted_q.jsonl')
     if os.path.exists(os.path.join(D, f)) for l in open(os.path.join(D, f), encoding='utf-8')]
def base(r):
    j = r['claude']; runs = j.get('runs') or []
    return j.get('type') == '食い違いなし' and len(runs) >= 3 and len(set(runs)) == 1 and r['gpt']['result'] == '別系統で支持' \
        and j.get('speech_quote_ok') and j.get('source_quote_ok')
C = []
for r in filter(base, R):
    c = {k: v for k, v in r.items() if k not in ('gpt', 'gemini')}
    c['claude'] = {**r['claude'], 'type': '限定が落ちる', 'explanation': '答弁は資料にある限定を落とし、資料より強い言い方をしている。'}
    C.append(c)
with cf.ThreadPoolExecutor(4) as ex, open(os.path.join(D, 'negctl.jsonl'), 'w', encoding='utf-8') as w:
    out = list(ex.map(refute.run, C))
    for r in out: w.write(json.dumps(r, ensure_ascii=False) + '\n')
print('陰性対照', len(out), '二つとも支持（誤って）', sum(r['gpt']['result'] == '別系統で支持' for r in out))
