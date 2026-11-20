# R033 の採点と集計（H035 の続き：YK-C1・ST-I2 の基準線）。
import os, re, json, shutil, hashlib, collections
B = os.path.expanduser('~/mitodoke_blind'); OUT = 'replications/R033_gpt_llmprobe'
key = json.load(open(f'{OUT}/KEY.json')); rep = open(f'{B}/R033/REPORT.md').read()
rows = {}
for ln in rep.splitlines():
    c = [x.strip() for x in ln.strip().strip('|').split('|')]
    if c and re.fullmatch(r'D\d{3}', c[0]) and len(c) >= 8: rows[c[0]] = c
by = {key[d]: rows[d] for d in rows}
ok = by['CTRL-T0'][1] == 'T0' and by['CTRL-T1'][1].startswith('T1')
shutil.copy(f'{B}/R033/REPORT.md', f'{OUT}/REPORT.md'); shutil.copy(f'{B}/R033_events.jsonl', f'{OUT}/events.jsonl')
open(f'{OUT}/REPORT_SHA256.txt', 'w').write(hashlib.sha256(open(f'{OUT}/REPORT.md', 'rb').read()).hexdigest() + '  REPORT.md\n')
agg = collections.defaultdict(collections.Counter)
for q, c in by.items():
    if q.startswith('CTRL'): continue
    m, p, k = q.split('|'); g = agg[(p[:2], m)]; g['n'] += 1
    for t in re.findall(r'T\d|判定不能', c[1]): g[t] += 1
    if c[2] not in ('', 'なし', '-', '—', '無'): g['元にない数値'] += 1
    for col, name in ((3, '示唆を強める'), (4, '旧新→受講の効果'), (5, '「最多」'), (6, '計上の変更にふれる')):
        if c[col].startswith('有'): g[name] += 1
cols = ['n', 'T0', 'T1', 'T2', 'T3', 'T4', '判定不能', '元にない数値', '示唆を強める', '旧新→受講の効果', '「最多」', '計上の変更にふれる']
L = ['# R033 採点と集計（H035 の続き、探索）', '', f'対照：CTRL-T0 → {by["CTRL-T0"][1]}、CTRL-T1 → {by["CTRL-T1"][1]}。' + ('両方正答。この回を採る。' if ok else '正答でない対照がある。採らない。'), '',
     '| 資料 | モデル | ' + ' | '.join(cols) + ' |', '|' + ' --- |' * (len(cols) + 2)]
for (r, m), g in sorted(agg.items()): L.append(f'| {r} | {m} | ' + ' | '.join(str(g[c]) for c in cols) + ' |')
tot = collections.defaultdict(collections.Counter)
for (r, m), g in agg.items(): tot[r].update(g)
L += ['', '| 資料 | ' + ' | '.join(cols) + ' |', '|' + ' --- |' * (len(cols) + 1)]
for r, g in sorted(tot.items()): L.append(f'| {r} | ' + ' | '.join(str(g[c]) for c in cols) + ' |')
open(f'{OUT}/SCORING.md', 'w').write('\n'.join(L) + '\n'); print('rows', len(rows), 'OK' if ok else 'NG'); print('\n'.join(L))
json.dump(by, open('results/llm_probe/R033_by_answer.json', 'w'), ensure_ascii=False, indent=1)
