# H036 の採点と、サイト用のデータ（publish/llm_answers.json）。使い方：python3 score_h036.py <回の日付> <記録=R0xx> ...
import os, sys, re, json, shutil, hashlib, random, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h036_spec as S
RUN = sys.argv[1]; PAIRS = [a.split('=') for a in sys.argv[2:]]
B = os.path.expanduser('~/mitodoke_blind')
ANS = {}
for j in map(json.loads, open(f'results/llm_probe/h036/{RUN}/answers.jsonl')):
    if j['answer']: ANS.setdefault((j['model'], j['key'], j['rep']), j)
PUB = 'publish/llm_answers.json'
pub = json.load(open(PUB)) if os.path.exists(PUB) else {'runs': {}}
TY = {'T0': '同じ', 'T1': '値が違う', 'T2': '量が置き換わる', 'T3': '言い方が強まる', 'T4': '限定が落ちる', '判定不能': '判定が分かれた'}
COND = lambda m, p: ('検索あり' if m == S.SEARCH_MODEL else '検索なし') if p.startswith('A') else '原文を渡す'
AG = json.load(open('results/judge2/agreement.json')) if os.path.exists('results/judge2/agreement.json') else {}
run = pub['runs'].setdefault(RUN, {'models': S.MODELS + [S.SEARCH_MODEL], 'reps': S.REPS, 'records': {}})
for rec, rn in PAIRS:
    out = f'replications/{rn}_h036_{rec}'; key = json.load(open(f'{out}/KEY.json')); rep = open(f'{B}/{rn}/REPORT.md').read()
    rows = {}
    for ln in rep.splitlines():
        c = [x.strip() for x in ln.strip().strip('|').split('|')]
        if c and re.fullmatch(r'D\d{3}', c[0]) and len(c) >= 5: rows[c[0]] = c
    by = {key[d]: rows[d] for d in rows if d in key}
    ok = by.get('CTRL-T0', ['', ''])[1] == 'T0' and by.get('CTRL-T1', ['', ''])[1].startswith('T1') and len(by) == len(key)
    shutil.copy(f'{B}/{rn}/REPORT.md', f'{out}/REPORT.md'); shutil.copy(f'{B}/{rn}_events.jsonl', f'{out}/events.jsonl')
    open(f'{out}/REPORT_SHA256.txt', 'w').write(hashlib.sha256(open(f'{out}/REPORT.md', 'rb').read()).hexdigest() + '  REPORT.md\n')
    open(f'{out}/SCORING.md', 'w').write(f'# {rn} 採点（{rec}）\n\n対照：CTRL-T0 → {by.get("CTRL-T0", ["", "なし"])[1]}、CTRL-T1 → {by.get("CTRL-T1", ["", "なし"])[1]}。行 {len(by)}／{len(key)}。' + ('採る。' if ok else '採らない。') + '\n')
    print(rec, rn, 'OK' if ok else 'NG', len(by), len(key))
    if not ok: continue
    agg = collections.defaultdict(collections.Counter); items = collections.defaultdict(list)
    for q, c in by.items():
        if q.startswith('CTRL'): continue
        m, p, r = q.split('|'); cond = COND(m, p); g = agg[(cond, m)]; g['n'] += 1
        ts = re.findall(r'T\d|判定不能', c[1])
        ag = AG.get(f'{rn}_h036_{rec}', {})
        if ag.get('ctrl_ok') and q in ag['items']:   # H037：二つの判定者がともに付けた型だけを数える。集合が違えば「判定が分かれた」
            g1, g2 = set(ag['items'][q]['gpt']), set(ag['items'][q]['gemini'])
            if g1 != g2 or g1 == {'判定不能'}: g['判定が分かれた'] += 1
            ts = sorted((g1 & g2) - {'判定不能'})
            for t in ts: g[TY[t]] += 1
        else:
            for t in ts: g[TY[t]] += 1
        if c[2] not in ('', 'なし', '-', '—', '無'): g['元にない数値'] += 1
        a = ANS[(m, f'{rec}|{p}', int(r))]['answer'].split('\n\n［出典］')[0]
        items[cond].append(dict(model=m, prompt=p, rep=int(r), types=[TY[t] for t in ts], why=c[-1], excerpt=re.sub(r'[#*\s]+', ' ', a).strip()[:90]))
    rnd = random.Random(int(hashlib.sha256((RUN + rec).encode()).hexdigest()[:8], 16))
    ex = {cond: rnd.choice(sorted(v, key=lambda x: (x['model'], x['prompt'], x['rep']))) for cond, v in items.items()}
    ag = AG.get(f'{rn}_h036_{rec}', {})
    run['records'][rec] = dict(round=rn, judge2=('gemini-4-argon' if ag.get('ctrl_ok') else None), agree=(round(100 * ag['agree'] / ag['n']) if ag.get('ctrl_ok') else None), table=[dict(cond=c, model=m, **{k: g[k] for k in ['n'] + list(TY.values()) + ['元にない数値']}) for (c, m), g in sorted(agg.items())], examples=ex)
json.dump(pub, open(PUB, 'w'), ensure_ascii=False, indent=1)
