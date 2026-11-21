"""R068（2026-11-21）：R067 は GPT が対照（214,843 と 214,483 の取り違え）を見落とし、規則どおり不採用。
国会の判定と同じく、各判定者に同じプロンプト（R067 と同一、順序だけ回ごとに乱す）を3回ずつ渡す。
対照に正答した回だけを使い、各判定者で2回以上正答した場合に採る。型は、採った全ての回で共通するものだけを残す。"""
import json, os, random, sys, hashlib, datetime, re
sys.path.insert(0, 'kokkai'); import llm
SRC = 'replications/R067_rejudge'; OUT = 'replications/R068_rejudge3'; os.makedirs(OUT, exist_ok=True)
P0 = open(f'{SRC}/PROMPT.md').read(); key0 = json.load(open(f'{SRC}/KEY.json'))
head, body = P0.split('## 組\n', 1)
blocks = re.split(r'(?m)^### (C\d+)\n', body)[1:]
items = {key0[blocks[i]]: blocks[i + 1] for i in range(0, len(blocks), 2)}
CTRL = {'CTRL-T1': {'T1'}, 'CTRL-T0': {'T0'}}
runs = {'gpt': [], 'gemini': []}
for n in range(3):
    ids = list(items); random.Random(680 + n).shuffle(ids)
    key = {f'C{i + 1:02d}': x for i, x in enumerate(ids)}
    P = head + '## 組\n' + ''.join(f'### {k}\n{items[x]}' for k, x in key.items())
    open(f'{OUT}/PROMPT_{n}.md', 'w').write(P); json.dump(key, open(f'{OUT}/KEY_{n}.json', 'w'), ensure_ascii=False, indent=1)
    for name, fn in (('gpt', llm.gpt), ('gemini', llm.gemini)):
        t = fn(P); open(f'{OUT}/REPORT_{name}_{n}.txt', 'w').write(t)
        j = llm.js(t) or {}; r = {key[k]: v.get('型', []) for k, v in j.items() if k in key}
        ok = all(set(r.get(c, [])) == e for c, e in CTRL.items())
        runs[name].append(dict(n=n, ok=ok, res=r)); print(name, n, '対照', ok, flush=True)
use = {k: [x['res'] for x in v if x['ok']] for k, v in runs.items()}
adopt = all(len(v) >= 2 for v in use.values())
out = dict(round='R068', date=datetime.date.today().isoformat(), adopted=adopt, control={k: [x['ok'] for x in v] for k, v in runs.items()}, items={})
for i in items:
    if i in CTRL: continue
    per = [set(t for t in r.get(i, []) if t.startswith('T')) for v in use.values() for r in v]
    com = sorted(set.intersection(*per)) if per else []
    out['items'][i] = dict(gpt=[r.get(i, []) for r in use['gpt']], gemini=[r.get(i, []) for r in use['gemini']], common=com, unanimous=len(set(map(frozenset, per))) == 1)
json.dump(out, open('results/citations/R068.json', 'w'), ensure_ascii=False, indent=1)
print('採用', adopt, '件数', len(out['items']), '共通の型あり', sum(1 for v in out['items'].values() if v['common']), '全回一致', sum(1 for v in out['items'].values() if v['unanimous']))
