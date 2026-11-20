# R032 の採点と集計（H035）。
import os, re, json, shutil, hashlib, collections
B = os.path.expanduser('~/mitodoke_blind'); OUT = 'replications/R032_gpt_llmprobe'
key = json.load(open(f'{OUT}/KEY.json')); rep = open(f'{B}/R032/REPORT.md').read()
rows = {}
for ln in rep.splitlines():
    c = [x.strip() for x in ln.strip().strip('|').split('|')]
    if c and re.fullmatch(r'D\d{3}', c[0]) and len(c) >= 8: rows[c[0]] = c
by = {key[d]: rows[d] for d in rows}
ok = by['CTRL-T0'][1] == 'T0' and by['CTRL-T1'][1].startswith('T1')
shutil.copy(f'{B}/R032/REPORT.md', f'{OUT}/REPORT.md'); shutil.copy(f'{B}/R032_events.jsonl', f'{OUT}/events.jsonl')
open(f'{OUT}/REPORT_SHA256.txt', 'w').write(hashlib.sha256(open(f'{OUT}/REPORT.md', 'rb').read()).hexdigest() + '  REPORT.md\n')
print('rows', len(rows), 'of', len(key), 'controls', by['CTRL-T0'][1], '/', by['CTRL-T1'][1], 'OK' if ok else 'NG')
agg = collections.defaultdict(lambda: collections.Counter())
for q, c in by.items():
    if q.startswith('CTRL'): continue
    m, p, k = q.split('|'); cond = 'A（検索なし）' if p[0] == 'A' and m != 'sonar-pro' else ('A（検索あり）' if p[0] == 'A' else 'B（原文を渡す）')
    g = agg[(cond, m)]; g['n'] += 1
    for t in re.findall(r'T\d|判定不能', c[1]): g[t] += 1
    if c[2] not in ('', 'なし', '-', '—', '無'): g['元にない数値'] += 1
    if c[3] not in ('', 'なし', '-', '—', '無'): g['別の調査の数値'] += 1
    if c[4].startswith('有'): g['再犯可能性→再犯率'] += 1
    if c[5].startswith('有'): g['群の比較→低下'] += 1
    if c[6].startswith('有'): g['罪名の限定にふれる'] += 1
cols = ['n', 'T0', 'T1', 'T2', 'T3', 'T4', '判定不能', '元にない数値', '別の調査の数値', '再犯可能性→再犯率', '群の比較→低下', '罪名の限定にふれる']
L = ['# R032 採点と集計（H035、探索）', '', f'対照：CTRL-T0 → {by["CTRL-T0"][1]}、CTRL-T1 → {by["CTRL-T1"][1]}。' + ('両方正答。この回を採る。' if ok else '正答でない対照がある。採らない。'), '',
     '| 条件 | モデル | ' + ' | '.join(cols) + ' |', '|' + ' --- |' * (len(cols) + 2)]
for (cond, m), g in sorted(agg.items()):
    L.append(f'| {cond} | {m} | ' + ' | '.join(str(g[c]) for c in cols) + ' |')
tot = collections.defaultdict(collections.Counter)
for (cond, m), g in agg.items(): tot[cond].update(g)
L += ['', '| 条件 | ' + ' | '.join(cols) + ' |', '|' + ' --- |' * (len(cols) + 1)]
for cond, g in sorted(tot.items()): L.append(f'| {cond} | ' + ' | '.join(str(g[c]) for c in cols) + ' |')
open(f'{OUT}/SCORING.md', 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
json.dump({q: c for q, c in by.items()}, open('results/llm_probe/R032_by_answer.json', 'w'), ensure_ascii=False, indent=1)
