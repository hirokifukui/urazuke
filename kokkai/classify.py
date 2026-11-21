"""国会の発言の候補を Claude で分類する（2026-11-21）。答弁が記録の資料をどう引いたかを、決めた型のどれかに当てる。
逐語の引用（答弁から一つ、資料から一つ）を必ず出させ、機械でその文字列が元にあるかを確かめる（無ければ「引用が元にない」で落とす）。
python3 kokkai/classify.py <日付> [件数の上限]"""
import json, os, re, sys, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import llm
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
day = sys.argv[1]; LIM = int(sys.argv[2]) if len(sys.argv) > 2 else 10**9; D = os.path.join(ROOT, 'results/kokkai', day)
from classify_prompt import F, TYPES, prompt
import classify_src
norm = lambda s: re.sub(r'\s+', '', s or '')
NRUN = int(os.environ.get('KOKKAI_NRUN', '5'))   # 同じ候補を何回分類するか（2026-11-22：5回の過半。全一致は境目の候補を1回の外れで落とすため改めた）
def one(c):
    try:
        t = llm.claude(prompt(c)); j = llm.js(t) or {}
    except Exception as ex: j = {'type': 'エラー', 'explanation': type(ex).__name__}
    srcs = norm(' '.join(q['文'] for r in c['records'] for q in F[r].get('原文の引用', [])) + ' '.join(q['text'] for r in c['records'] if r in classify_src.CIT for q in classify_src.CIT[r]['src_quotes']) + ' '.join(t for r in c['records'] for t in classify_src.EXTRA.get(r, [])))  # 2026-11-21：補足の原文も引用の確かめに含める
    j['speech_quote_ok'] = bool(j.get('speech_quote')) and norm(j['speech_quote']) in norm(c['passage'])
    j['source_quote_ok'] = bool(j.get('source_quote')) and norm(j['source_quote']) in srcs
    return j
def run(c):   # 2026-11-22：独立に NRUN 回（既定5）判定し、過半の型を採る（全一致を求めると、境目の候補は1回の外れで落ちる。引かれ方の R072 と同じ考え方）
    runs = [one(c) for _ in range(NRUN)]
    types = [r.get('type') for r in runs]
    top = max(set(types), key=types.count)
    ok = [r for r in runs if r.get('type') == top and r.get('speech_quote_ok') and r.get('source_quote_ok')]
    if types.count(top) * 2 > len(types) and ok: j = dict(ok[0])
    else: j = dict(runs[0]); j['type'] = '判定が分かれた'
    j['runs'] = types
    return {**c, 'claude': j}
IN, OUT = (sys.argv[3], sys.argv[4]) if len(sys.argv) > 4 else ('candidates.jsonl', 'classified.jsonl')
C = [json.loads(l) for l in open(os.path.join(D, IN), encoding='utf-8')][:LIM]
with cf.ThreadPoolExecutor(4) as ex, open(os.path.join(D, OUT), 'w', encoding='utf-8') as w:
    for r in ex.map(run, C):
        w.write(json.dumps(r, ensure_ascii=False) + '\n'); w.flush()
        print(r['date'], r['speaker'], r['claude'].get('type'), r['claude'].get('record_ids'), r['claude'].get('speech_quote_ok'), r['claude'].get('source_quote_ok'), flush=True)
