#!/usr/bin/env python3
"""検算 c401（a 内部の整合）：警察庁「犯罪統計資料」CSV（令和2〜7年、e-Stat）の全表について
 A 内訳の和＝計（同じ区分 c0 の中で、c1 が「うち」を含まない行の和＝「計」の行）
 B 総数＝ブロック（計の行と、内訳を持たない単独行）の和（表の先頭が「総数」「刑法犯総数」「合計」の行のとき）
 C 「うち」の行 ≦ 親の行
 D 増減＝当年−前年、増減率＝(当年−前年)/前年×100（小数1位）、検挙率＝検挙件数/認知件数×100（小数1位）、増減ポイント＝当年率−前年率
出力: results/keisatsu/c401_estat_internal.tsv（食い違いの明細）と c401_summary.tsv（件数）。"""
import sys, glob, re, math
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT / 'lib'))
import npa_csv
OUT = ROOT / 'results/keisatsu'; OUT.mkdir(parents=True, exist_ok=True)
det, cnt = [], Counter()

def r1(x):  # 四捨五入（小数1位）
    return math.floor(x * 10 + 0.5 + 1e-9) / 10
def t1(x):  # 切り捨て
    return math.floor(x * 10 + 1e-9) / 10

def rec(f, t, kind, key, exp, obs, ok, note=''):
    cnt[(f, kind, 'ok' if ok else 'ng')] += 1
    if not ok: det.append([f, t, kind, key, f'{exp:.6g}' if exp is not None else '', f'{obs:.6g}' if obs is not None else '', note])

PAT = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / 'data/raw/keisatsu/estat/R0*_kakutei_*.csv')
TAG = sys.argv[2] if len(sys.argv) > 2 else ''
for path in sorted(glob.glob(PAT)):
    f = Path(path).name[:3]
    for T in npa_csv.read(path):
        tname = f"{T['no']}{'' if not T.get('part') else '-'+str(T['part']+1)} {T['title'][:30]}"
        cols, rows = T['cols'], T['rows']
        # 列の役割
        groups = {}
        for j, (c, p) in enumerate(cols):
            y = npa_csv.year_of(p)
            g = groups.setdefault(c, {})
            if y: g.setdefault('years', []).append((y, j))
            elif '増減率' in p: g['rate'] = j
            elif 'ポイント' in p: g['pt'] = j
            elif '増減' in p: g['diff'] = j
        count_cols = [j for c, g in groups.items() if '率' not in c for (y, j) in g.get('years', [])]
        # D 算術
        for c, g in groups.items():
            ys = sorted(g.get('years', []), reverse=True)
            if len(ys) < 2: continue
            (yc, jc), (yp, jp) = ys[0], ys[1]
            for c0, c1, v in rows:
                cur, prev = v[jc], v[jp]
                if cur is None or prev is None: continue
                key = f'{c0}/{c1}/{c}'
                if 'diff' in g and v[g['diff']] is not None:
                    rec(f, tname, 'D増減', key, cur - prev, v[g['diff']], abs(cur - prev - v[g['diff']]) < 1e-6)
                if 'pt' in g and v[g['pt']] is not None and cur != 0 and prev != 0:   # 率が0（認知0件で率が定義されない場合を含む）の行は除く
                    rec(f, tname, 'Dポイント', key, r1(cur - prev), v[g['pt']], abs(round(cur - prev, 1) - v[g['pt']]) < 0.051)
                if 'rate' in g and v[g['rate']] is not None and prev > 0:
                    e = (cur - prev) / prev * 100; o = v[g['rate']]
                    ok = abs(r1(e) - o) < 1e-6 or abs(-r1(-e) - o) < 1e-6
                    note = '' if ok else ('切り捨てなら一致' if abs(t1(e) - o) < 1e-6 else '')
                    rec(f, tname, 'D増減率', key, e, o, ok, note)
        # 検挙率の再計算
        if '検挙率' in groups and '認知件数' in groups and '検挙件数' in groups:
            for (y, jr) in groups['検挙率'].get('years', []):
                jn = dict(groups['認知件数']['years']).get(y); jk = dict(groups['検挙件数']['years']).get(y)
                if jn is None or jk is None: continue
                for c0, c1, v in rows:
                    if v[jr] is None or not v[jn]: continue
                    e = v[jk] / v[jn] * 100
                    ok = abs(r1(e) - v[jr]) < 1e-6
                    rec(f, tname, 'D検挙率', f'{c0}/{c1}/{y}', e, v[jr], ok, '' if ok else ('切り捨てなら一致' if abs(t1(e) - v[jr]) < 1e-6 else ''))
        # A・B・C 階層
        isu = lambda s: 'うち' in s
        bygrp = {}
        for i, (c0, c1, v) in enumerate(rows):
            if c0: bygrp.setdefault(c0, []).append(i)
        blocks = []
        for c0, ix in bygrp.items():
            if isu(c0): continue   # 「うち)男」などの部分集合の区分はブロックに数えない
            tot = [i for i in ix if rows[i][1] == '計']
            kids = [i for i in ix if rows[i][1] not in ('計', '') and not isu(rows[i][1])]
            if tot:
                blocks.append(tot[0])
                if kids:
                    for j in count_cols:
                        s = sum(rows[i][2][j] or 0 for i in kids); o = rows[tot[0]][2][j]
                        if o is None: continue
                        rec(f, tname, 'A内訳＝計', f'{c0}/{cols[j][0]}/{cols[j][1]}', s, o, abs(s - o) < 1e-6)
            elif len(ix) == 1 and rows[ix[0]][1] == '':
                blocks.append(ix[0])
        top = [i for i, (c0, c1, v) in enumerate(rows[:2]) if c0 in ('総数', '刑法犯総数', '合計') and c1 in ('', '計')]
        if top and len(blocks) > 2:
            ti = top[0]; bl = [i for i in blocks if i != ti]
            for j in count_cols:
                s = sum(rows[i][2][j] or 0 for i in bl); o = rows[ti][2][j]
                if o is None: continue
                rec(f, tname, 'B総数＝ブロックの和', f'{cols[j][0]}/{cols[j][1]}', s, o, abs(s - o) < 1e-6, f'{len(bl)}ブロック')
        # C うち ≦ 親
        for i, (c0, c1, v) in enumerate(rows):
            if not isu(c1): continue
            pref = re.split(r'\s*うち', c1)[0].strip()
            par = next((k for k in range(i - 1, -1, -1) if rows[k][0] == c0 and (rows[k][1] == pref or (not pref and rows[k][1] == '計'))), None)
            if par is None: continue
            for j in count_cols:
                if v[j] is None or rows[par][2][j] is None: continue
                rec(f, tname, 'Cうち≦親', f'{c0}/{c1}/{cols[j][1]}', rows[par][2][j], v[j], v[j] <= rows[par][2][j] + 1e-9)

with open(OUT / f'c401_estat_internal{TAG}.tsv', 'w') as w:
    w.write('file\ttable\tkind\tkey\texpected\tobserved\tnote\n')
    for d in det: w.write('\t'.join(map(str, d)) + '\n')
with open(OUT / f'c401_summary{TAG}.tsv', 'w') as w:
    w.write('file\tkind\tok\tng\n')
    for (f, k) in sorted({(a, b) for a, b, _ in cnt}):
        w.write(f"{f}\t{k}\t{cnt[(f, k, 'ok')]}\t{cnt[(f, k, 'ng')]}\n")
print('ok', sum(v for (a, b, c), v in cnt.items() if c == 'ok'), 'ng', len(det))

# 照合の要約（lib/tally.py）：A〜D の比較した値。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('keisatsu', 'c401', note='犯罪統計資料 CSV：内訳の和と計、うち≦親、増減・率の再計算', script=__file__)
for (a, b, c), v in cnt.items(): (_t.ok if c == 'ok' else _t.ng)(v)
if not TAG: print('tally', _t.save())  # TAG 付き（陰性対照など）は数えない
