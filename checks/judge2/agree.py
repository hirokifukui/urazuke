# H037：GPT と Gemini の判定の一致を測る。results/judge2/agreement.json と AGREEMENT.md を書く。
import os, re, json, collections
ROUNDS = ['R029_gpt_types', 'R030_gpt_types', 'R031_gpt_types', 'R035_h036_KP-C1', 'R037_h036_YK-C1', 'R039_h036_JH-A1', 'R040_h036_ST-I2',
          'R042_h036_630-D1', 'R043_h036_SO-P1', 'R044_h036_GY-Q1', 'R045_h036_NK-K1']
TYPES = ['T0', 'T1', 'T2', 'T3', 'T4', '判定不能']
def parse(path):
    rows = {}
    for ln in open(path).read().splitlines():
        c = [x.strip() for x in ln.strip().strip('|').split('|')]
        if len(c) >= 2 and re.fullmatch(r'\**([CD]\d{2,3})\**', c[0]):
            rows[re.sub(r'\*', '', c[0])] = c
    return rows
def tset(s): return frozenset(re.findall(r'T\d|判定不能', s))
def kappa(a, b):
    n = len(a); po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n; pe = pa * pb + (1 - pa) * (1 - pb)
    return None if pe == 1 else round((po - pe) / (1 - pe), 2)
OUT = {}; L = ['# H037 二つの判定者の一致（GPT / Codex と Gemini gemini-4-argon）', '', '| 回 | 組 | Gemini の作例 | 型の集合が一致 | ' + ' | '.join(f'κ {t}' for t in TYPES[:5]) + ' |', '|' + ' --- |' * 9]
for rn in ROUNDS:
    d = f'replications/{rn}'
    if not os.path.exists(f'{d}/REPORT_gemini.md'): L.append(f'| {rn} | Gemini の報告なし |'); continue
    key = json.load(open(f'{d}/KEY.json')); g1 = parse(f'{d}/REPORT.md'); g2 = parse(f'{d}/REPORT_gemini.md')
    by = {}
    for cid, q in key.items():
        if cid in g1 and cid in g2: by[q] = (tset(g1[cid][1]), tset(g2[cid][1]), g1[cid][1], g2[cid][1])
    ctrl_ok = by.get('CTRL-T0', (0, frozenset()))[1] == frozenset({'T0'}) and 'T1' in by.get('CTRL-T1', (0, frozenset()))[1]
    items = {q: v for q, v in by.items() if not q.startswith('CTRL')}
    agree = sum(v[0] == v[1] for v in items.values())
    ks = [kappa([t in v[0] for v in items.values()], [t in v[1] for v in items.values()]) for t in TYPES[:5]]
    OUT[rn] = dict(ctrl_ok=ctrl_ok, n=len(items), n_key=len([k for k in key.values() if not k.startswith('CTRL')]), agree=agree, kappa=dict(zip(TYPES[:5], ks)),
                   items={q: dict(gpt=sorted(v[0]), gemini=sorted(v[1]), gpt_raw=v[2], gemini_raw=v[3]) for q, v in items.items()})
    L.append(f'| {rn} | {len(items)}/{OUT[rn]["n_key"]} | {"正答" if ctrl_ok else "正答でない"} | {agree}（{round(100 * agree / max(1, len(items)))}％） | ' + ' | '.join('—' if k is None else str(k) for k in ks) + ' |')
os.makedirs('results/judge2', exist_ok=True)
json.dump(OUT, open('results/judge2/agreement.json', 'w'), ensure_ascii=False, indent=1)
open('results/judge2/AGREEMENT.md', 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
