"""反証の成績表（2026-11-19、点検の改訂案2）。replications/R0xx_gpt_refute/SCORING.md を読み、回ごとの数を数える。
出力：results/refute/scoreboard.json（サイトの方法のページが読む）。
数え方：SCORING.md の表の行で「判定」の列が 支持／反証／判定不能 のものを本題として数える（対照の行は表に入れていない）。
回を採ったかどうかは、SCORING.md の「対照」の文に「採らない」「無効」があるかで決める。"""
import os, re, json, glob, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ID = re.compile(r'\b(?:[A-Z]{2,3}|630)-[A-Z]{1,2}\d{1,2}\b')
rows = []
EV = []
# R003〜R006 は記録の ID を付ける前の回で、表の形が違う。SCORING.md を読んで数えた値（R003 の P02 は1回目の判定不能で数える）。
EARLY = {'R003': (0, 5, 0, 4, 3), 'R004': (0, 3, 0, 1, 8), 'R005': (0, 1, 0, 0, 2), 'R006': (0, 1, 0, 0, 2)}
for d in sorted(glob.glob(os.path.join(ROOT, 'replications/R*_gpt_refute'))):
    r = os.path.basename(d).split('_')[0]; sc = os.path.join(d, 'SCORING.md')
    if not os.path.exists(sc): continue
    if r in EARLY:
        _, a, b, cc, k = EARLY[r]; rows.append(dict(round=r, n=a + b + cc, 支持=a, 反証=b, 判定不能=cc, controls=k, adopted=True, records=[])); continue
    t = open(sc, encoding='utf-8').read()
    c = {'支持': 0, '反証': 0, '判定不能': 0}; recs = []
    dm = re.search(r'(20\d\d-\d\d-\d\d)', t); date = dm.group(1) if dm else ''
    if not date:  # 実行の日付が書かれていない回は、SCORING.md を最初に記録した日
        date = subprocess.run(['git', 'log', '--diff-filter=A', '--format=%ad', '--date=short', '--', sc], cwd=ROOT, capture_output=True, text=True).stdout.strip().split('\n')[-1]
    for line in t.splitlines():
        if not line.startswith('|') or '---' in line: continue
        cells = [x.strip() for x in line.strip('|').split('|')]
        v = next((x for x in cells[:4] if x in c), None)
        # 記録の ID は問・記録の欄の中から探す（「JH-A1 その1（…）」「（G2→SD-A2）」の形も拾う）。
        # 問が「Q1〜Q3」のように範囲なら、その数だけ本題として数える（2026-11-19、点検で成績表と経過の食い違いを指摘されて直した）
        ids = ID.findall(' '.join(cells[:2]))
        qm = next((re.fullmatch(r'Q(\d+)(?:\s*[〜~～-]\s*Q?(\d+))?', x) for x in cells[:2] if re.fullmatch(r'Q\d+(?:\s*[〜~～-]\s*Q?\d+)?', x)), None)
        qs = [f'Q{i}' for i in range(int(qm.group(1)), int(qm.group(2) or qm.group(1)) + 1)] if qm else ['']
        if v and (ids or qm):
            for q in qs:
                c[v] += 1; recs.append(ids[0] if ids else ''); EV.append(dict(id=ids[0] if ids else '', round=r, q=q, verdict=v, date=date, plain=os.path.exists(os.path.join(d, 'PLAIN.json'))))
    ctl = ' '.join(l for l in t.splitlines() if '対照' in l)
    nctl = len(re.findall(r'Q\d+（(?:偽|真)', ctl))
    adopted = not re.search(r'採らない|無効', ctl)
    rows.append(dict(round=r, n=sum(c.values()), **c, controls=nctl, adopted=adopted, records=recs, date=date))
    if not adopted: EV[:] = [e for e in EV if e['round'] != r]
# R003〜R006 の本題は記録の ID を付ける前の番号で採点した。対応は各記録の「再現」の欄と SCORING.md による（2026-11-19、点検で経過のない「支持」を指摘されて足した）
EARLY_EV = [('HK-A6', 'R003', 'P04', '支持'), ('HK-A7', 'R003', 'P02', '判定不能'), ('HK-A7', 'R003', 'P02+', '支持'), ('HK-B1', 'R003', 'P09', '支持'),
            ('HK-A4', 'R003', 'P06', '判定不能'), ('SO-P1', 'R003', 'P05', '判定不能'),
            ('630-A1', 'R004', 'H002', '支持'), ('MK-I1', 'R004', 'H003', '支持'), ('ST-I1', 'R004', 'H004', '支持'),
            ('ST-B1', 'R004', 'H005', '判定不能'), ('ST-B1', 'R005', 'Q2', '支持'), ('SH-B1', 'R006', 'Q3', '支持')]
_ED = {'R003': '2026-11-16', 'R004': '2026-11-16', 'R005': '2026-11-16', 'R006': '2026-11-16'}
EV[:0] = [dict(id=i, round=r, q=q, verdict=v, date=_ED[r]) for i, r, q, v in EARLY_EV]
tot = {k: sum(x[k] for x in rows if x['adopted']) for k in ('n', '支持', '反証', '判定不能')}
tot['rounds'] = len(rows); tot['rounds_adopted'] = sum(x['adopted'] for x in rows)
os.makedirs(os.path.join(ROOT, 'results/refute'), exist_ok=True)
json.dump(dict(rounds=rows, total=tot, events=EV), open(os.path.join(ROOT, 'results/refute/scoreboard.json'), 'w'), ensure_ascii=False, indent=1)
print(tot)
for x in rows: print(x['round'], x['n'], x['支持'], x['反証'], x['判定不能'], x['controls'], x['adopted'])
