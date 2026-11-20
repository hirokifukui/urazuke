#!/usr/bin/env python3
"""検算 c601：文科省「公立学校教職員の人事行政状況調査」懲戒処分等（教育職員）平成27〜令和6年度
 資料：各年度の「2-1（2-1-1）懲戒処分等の状況一覧」（都道府県・指定都市×処分の種類、当該年度）と、
       令和3年度版以降の「2-1-2 懲戒処分等の推移（過去5年間）」、および性犯罪・性暴力等（旧 わいせつ行為等）・体罰・交通の推移表。
 (a) 状況一覧：免職＋停職＋減給＋戒告＝合計（懲戒処分）、合計＋訓告等＝総計（各行）、67自治体の和＝合計の行（各列）
     推移表：67自治体の和＝合計の行（各年度）
 (b) 同じ自治体・同じ年度の値を、状況一覧（当該年度版、現在掲載のファイル）と各版の推移表とで突き合わせる
 PDF は pdftotext -layout。括弧内の数（当事者の数）は除く。
出力: results/monka/c601_internal.tsv（(a) の食い違い）、c601_versions.tsv（(b) 全件の値の並び）、c601_summary.tsv"""
import sys, re, subprocess, csv
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'data/raw/monka'; OUT = ROOT / 'results/monka'; OUT.mkdir(parents=True, exist_ok=True)
EDY = {'H27': 2015, 'H28': 2016, 'H29': 2017, 'H30': 2018, 'R01': 2019, 'R02': 2020, 'R03': 2021, 'R04': 2022, 'R05': 2023, 'R06': 2024}
titles = {}
for l in open(ROOT / 'sources/generic/list_monka_titles_all.tsv'):
    e, u, t = (l.rstrip('\n').split('\t') + [''])[:3]
    titles.setdefault((e, u), '')
    titles[(e, u)] += t
def files(ed, pat):
    return [RAW / ed / u.rsplit('/', 1)[1] for (e, u), t in titles.items() if e == ed and re.search(pat, t)]
def text(p): return subprocess.run(['pdftotext', '-layout', str(p), '-'], capture_output=True, text=True).stdout
ROW = re.compile(r'^\s*(\d{1,2})\s+([^\s\d(（]+)\s+(.*)$')
def nums(s):
    s = re.sub(r'[（(]\s*[\d,]*\s*[)）]', ' ', s)           # 当事者の数（括弧内）を除く
    s = re.sub(r'\d+\.\d+%', ' ', s)                         # 割合を除く
    return [float(x.replace(',', '')) for x in re.findall(r'(?<![\d.])[\d,]+(?![\d.%])', s)]
def total_row(line):
    return re.match(r'^\s*合\s*計\s+(.*)$', line)

det, cnt = [], Counter()
vals = defaultdict(dict)        # (種類, 自治体, 年度) -> {出典: 値}
# 状況一覧（現行の掲載ファイル）と、Wayback に残る差し替え前の版
WB = {'000026693': 'R03'}   # 文科省の資料番号 → 版
JOBS = []
for ed, fy in EDY.items():
    fs = files(ed, r'^2[－-]1([－-]1)?\s*懲戒処分等の状況一覧')
    JOBS.append((ed, fy, fs[0] if fs else None, f'{ed}状況一覧'))
for p in sorted((RAW / 'wayback').glob('*_02_01_01.pdf')):
    ed = next(v for k, v in WB.items() if k in p.name)
    JOBS.append((ed + 'wb', EDY[ed], p, f'{ed}状況一覧(差替前 {p.name[:8]})'))
for ed, fy, fpath, srcname in JOBS:
    if not fpath or not fpath.exists(): cnt[('状況一覧なし', ed)] += 1; continue
    rows, tot = {}, None
    for line in text(fpath).splitlines():
        m = ROW.match(line)
        if m:
            v = nums(m[3])
            if len(v) >= 7: rows.setdefault(m[2], v[:7])
        t = total_row(line)
        if t and tot is None:
            v = nums(t[1])
            if len(v) >= 7: tot = v[:7]
    cnt[('状況一覧の行数', ed)] = len(rows)
    for n, v in list(rows.items()) + ([('合計', tot)] if tot else []):
        ok1 = abs(sum(v[:4]) - v[4]) < 1e-9; ok2 = abs(v[4] + v[5] - v[6]) < 1e-9
        cnt[('a種類の和＝合計', ok1)] += 1; cnt[('a合計＋訓告等＝総計', ok2)] += 1
        if not ok1: det.append([ed, '状況一覧', n, '免職＋停職＋減給＋戒告＝合計', sum(v[:4]), v[4]])
        if not ok2: det.append([ed, '状況一覧', n, '合計＋訓告等＝総計', v[4] + v[5], v[6]])
        vals[('懲戒処分等（総計）', n, fy)][srcname] = v[6]
    if tot:
        for j, lab in enumerate(['免職', '停職', '減給', '戒告', '合計', '訓告等', '総計']):
            s = sum(v[j] for v in rows.values()); ok = abs(s - tot[j]) < 1e-9
            cnt[('a自治体の和＝合計の行', ok)] += 1
            if not ok: det.append([ed, '状況一覧', lab, f'{len(rows)}自治体の和＝合計', s, tot[j]])
# 推移表
KINDS = {'懲戒処分等（総計）': r'^2[－-]1[－-]2\s*懲戒処分等の推移', '性犯罪・性暴力等': r'(性犯罪・性暴力等|わいせつ行為等)に係る懲戒処分等の推移',
         '体罰': r'体罰に係る懲戒処分等の推移', '交通違反・交通事故': r'交通違反・交通事故に係る懲戒処分等の推移'}
def fy_of(h):
    m = re.match(r'(H|R|平成|令和)\s*([０-９\d]+|元)', h)
    if not m: return None
    n = 1 if m[2] == '元' else int(m[2].translate(str.maketrans('０１２３４５６７８９', '0123456789')))
    return 1988 + n if m[1] in ('H', '平成') else 2018 + n
TJOBS = [(ed, kind, f, f'{ed}推移') for ed in EDY for kind, pat in KINDS.items() for f in files(ed, pat)]
for p in sorted((RAW / 'wayback').glob('*_02_01_02.pdf')):
    ed = next(v for k, v in WB.items() if k in p.name)
    TJOBS.append((ed, '懲戒処分等（総計）', p, f'{ed}推移(差替前 {p.name[:8]})'))
for ed, kind, f, srcname in TJOBS:
        if True:
            if not f.exists(): continue
            tx = text(f); hdr = None; rows = {}; tot = None
            for line in tx.splitlines():
                ys = [fy_of(h) for h in re.findall(r'(?:H|R|平成|令和)\s*(?:[０-９\d]+|元)(?=\s*年度)', line)]
                if len(ys) >= 3 and hdr is None: hdr = ys; continue
                m = ROW.match(line)
                if m and hdr:
                    v = nums(m[3])
                    if len(v) >= len(hdr): rows.setdefault(m[2], v[:len(hdr)])
                t = total_row(line)
                if t and hdr and tot is None:
                    v = nums(t[1])
                    if len(v) >= len(hdr): tot = v[:len(hdr)]
            if not hdr: cnt[('推移表の見出しが読めない', ed, kind)] += 1; continue
            for n, v in list(rows.items()) + ([('合計', tot)] if tot else []):
                for y, x in zip(hdr, v): vals[(kind, n, y)][srcname] = x
            if tot:
                for k, y in enumerate(hdr):
                    s = sum(v[k] for v in rows.values()); ok = abs(s - tot[k]) < 1e-9
                    cnt[('a推移表 自治体の和＝合計', ok)] += 1
                    if not ok: det.append([ed, f'推移 {kind}', y, f'{len(rows)}自治体の和＝合計', s, tot[k]])
# (b)
ver = []
for (kind, n, y), d in sorted(vals.items(), key=lambda kv: (kv[0][0], kv[0][2], kv[0][1])):
    if len(d) < 2: continue
    s = set(d.values()); ok = len(s) == 1
    cnt[('b版の比較', kind, ok)] += 1
    ver.append([kind, y, n, ' '.join(f'{k}={v:g}' for k, v in sorted(d.items())), '一致' if ok else '食い違い'])
with open(OUT / 'c601_internal.tsv', 'w') as w:
    w.write('edition\ttable\trow\tcheck\tsum\tstated\n')
    for d in det: w.write('\t'.join(map(str, d)) + '\n')
with open(OUT / 'c601_versions.tsv', 'w') as w:
    w.write('kind\tfiscal_year\tauthority\tvalues_by_source\tstatus\n')
    for v in ver: w.write('\t'.join(map(str, v)) + '\n')
with open(OUT / 'c601_summary.tsv', 'w') as w:
    for k, n in sorted(cnt.items(), key=str): w.write('\t'.join(map(str, k)) + f'\t{n}\n')
for k, n in sorted(cnt.items(), key=str): print(k, n)

# 照合の要約（lib/tally.py）：a（内部の整合）と b（版の比較）。見出しが読めない推移表は読み取りの失敗。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('monka', 'c601', note='公立学校教職員の人事行政状況調査：内訳の和と合計、版の比較', script=__file__)
for k, n in cnt.items():
    if k[0].startswith(('a', 'b')):
        if k[-1] is True: _t.ok(n)
        else: _t.ng(n, explained=(k[0] == 'b版の比較' and k[1] == '懲戒処分等（総計）'))  # 令和3年度版の差し替え（令和6年12月の告知つき）の前後の値（作業ノート）
    elif k[0] == '推移表の見出しが読めない': _t.fail(n)
print('tally', _t.save())
