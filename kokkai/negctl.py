"""反証の陰性対照（2026-11-21）：Claude が「食い違いなし」とした答弁に、わざと「限定が落ちる」の主張を付けて GPT に渡す。
GPT がこれを支持する割合が、反証の甘さの目安になる。refute.py と同じ形で渡す。python3 kokkai/negctl.py <日付>"""
import json, os, sys, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import refute
D = refute.D
C = [json.loads(l) for l in open(os.path.join(D, 'classified.jsonl'), encoding='utf-8')]
C = [c for c in C if c['claude'].get('type') == '食い違いなし' and c['claude'].get('speech_quote_ok') and c['claude'].get('source_quote_ok')]
for c in C:
    c['claude'] = {**c['claude'], 'type': '限定が落ちる', 'explanation': '答弁は資料にある限定を落とし、資料より強い言い方をしている。'}
with cf.ThreadPoolExecutor(4) as ex, open(os.path.join(D, 'negctl.jsonl'), 'w', encoding='utf-8') as w:
    R = list(ex.map(refute.run, C))
    for r in R: w.write(json.dumps(r, ensure_ascii=False) + '\n')
print('陰性対照', len(R), '支持（誤って）', sum(r['gpt']['result'] == '別系統で支持' for r in R))
