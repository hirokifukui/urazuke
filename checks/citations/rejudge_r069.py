"""R069（2026-11-21）：R067・R068 は不採用。引用の文に見出しや鍵の言い回しだけを渡し、元の回（R029〜R066）で渡していた本文の該当文や注を渡していなかったため（例：本文に但し書きがある記事を見出しだけで T4 にした）。
R069 は、各引用を最後に判定した回のプロンプトから、その組（元の資料の文・引用の文）をそのまま取り出し、型の定義だけを R067 の定義（重要性の条件つき）に替える。
各判定者に3回ずつ（順序は回ごとに乱す）。対照に正答した回だけを使い、各判定者で2回以上正答した場合に採る。型は、採った全ての回で共通するものだけを残す。"""
import json, os, random, re, sys, csv, datetime, hashlib, ast
sys.path.insert(0, 'kokkai'); import llm
OUT = 'replications/R069_rejudge3'; os.makedirs(OUT, exist_ok=True)
DIR = {'R029': 'R029_gpt_types', 'R030': 'R030_gpt_types', 'R031': 'R031_gpt_types', 'R046': 'R046_gpt_hakusho', 'R047': 'R047_gpt_hakusho', 'R066': 'R066_gpt_types'}
def blocks(d):
    P = open(f'replications/{d}/PROMPT.md').read(); K = json.load(open(f'replications/{d}/KEY.json'))
    b = re.split(r'(?m)^### (C\d+)\n', P.split('## 組\n', 1)[1])[1:]
    return {K[b[i]]: b[i + 1].strip() + '\n\n' for i in range(0, len(b), 2)}
B = {r: blocks(d) for r, d in DIR.items()}
# 各回の組の名前と引用ID
M = {}
for line in open('checks/citations/add_r030_r031.py'):
    m = re.match(r"\s*\('(Q-[^']+)', '(P-[^']+)'", line)
    if m: M[m.group(1)] = m.group(2)
M.update({f'Q-KP-C1-{n:03d}': 'W-KP' for n in range(7, 13)}); M.update({f'Q-SO-P1-{n:03d}': 'W-SO' for n in range(3, 8)})
M.update({'Q-YK-C1-004': 'W-YK', 'Q-ST-D1-001': 'P2-ST-02', 'Q-SK-C1-001': 'P2-SK-01', 'Q-SH-C1-001': 'P2-SH-01', 'Q-GY-Q1-007': 'P2-GY-02', 'Q-JH-A1-005': 'P2-JH-01'})
T = list(csv.DictReader(open('results/citations/citations.tsv'), delimiter='\t'))
items, cmap = {}, {}
for t in T:
    rnd = t['型の判定'][:4]; k = M.get(t['引用ID'], t['引用ID'])
    blk = B[rnd].get(k); assert blk, (t['引用ID'], rnd, k)
    u = f'{rnd}:{k}'; items[u] = blk; cmap.setdefault(u, []).append(t['引用ID'])
items['CTRL-T1'] = B['R029']['CTRL-T1'] if 'CTRL-T1' in B['R029'] else B['R030']['CTRL-T1']; items['CTRL-T0'] = B['R029']['CTRL-T0']
head = open('replications/R067_rejudge/PROMPT.md').read().split('## 組\n', 1)[0]
CTRL = {'CTRL-T1': {'T1'}, 'CTRL-T0': {'T0'}}
runs = {'gpt': [], 'gemini': []}
for n in range(3):
    ids = list(items); random.Random(690 + n).shuffle(ids)
    key = {f'C{i + 1:02d}': x for i, x in enumerate(ids)}
    P = head + '## 組\n' + ''.join(f'### {k}\n{items[x]}' for k, x in key.items())
    open(f'{OUT}/PROMPT_{n}.md', 'w').write(P); json.dump(key, open(f'{OUT}/KEY_{n}.json', 'w'), ensure_ascii=False, indent=1)
    for name, fn in (('gpt', llm.gpt), ('gemini', llm.gemini)):
        t = fn(P); open(f'{OUT}/REPORT_{name}_{n}.txt', 'w').write(t)
        j = llm.js(t) or {}; r = {key[k]: v.get('型', []) for k, v in j.items() if k in key}
        ok = all(set(r.get(c, [])) == e for c, e in CTRL.items())
        runs[name].append(dict(ok=ok, res=r)); print(name, n, '対照', ok, flush=True)
use = {k: [x['res'] for x in v if x['ok']] for k, v in runs.items()}
out = dict(round='R069', date=datetime.date.today().isoformat(), adopted=all(len(v) >= 2 for v in use.values()), control={k: [x['ok'] for x in v] for k, v in runs.items()}, items={})
for u, cids in cmap.items():
    per = [set(x for x in r.get(u, []) if x.startswith('T')) for v in use.values() for r in v]
    com = sorted(set.intersection(*per)) if per else []
    for c in cids:
        out['items'][c] = dict(pair=u, gpt=[r.get(u, []) for r in use['gpt']], gemini=[r.get(u, []) for r in use['gemini']], common=com, unanimous=len(set(map(frozenset, per))) == 1)
json.dump(out, open('results/citations/R069.json', 'w'), ensure_ascii=False, indent=1)
print('採用', out['adopted'], '組', len(cmap), '引用', len(out['items']), '全回一致', sum(v['unanimous'] for v in out['items'].values()))
