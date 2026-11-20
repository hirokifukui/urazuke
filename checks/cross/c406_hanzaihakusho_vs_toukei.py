#!/usr/bin/env python3
"""検算 c406（c 統計をまたぐ）：犯罪白書 資料1-1（刑法犯 認知件数・検挙件数・検挙人員の推移）令和2〜7年版 ↔
警察庁 犯罪統計資料 第1表「刑法犯総数」（2015〜2025年。令和2年以降は CSV、それ以前は PDF）。
c005（令和7年版・2年分）を、6版×10年に広げたもの。範囲（交通業過を含むか）は、白書の注と犯罪統計資料の「刑法犯総数」の定義が同じ
（いずれも交通業過を除く）ことを前提にし、食い違いが出たら注を確かめる。
出力: results/cross/c406_hanzaihakusho_vs_toukei.tsv（全件）"""
import sys, re
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT / 'lib'))
import xlsx
from tables import sheet_rows, year
src = (ROOT / 'checks/keisatsu/c403_pdf_prev_year.py').read_text().split('src = {}')[0].replace("ROOT = Path(__file__).resolve().parents[2]", f"ROOT = Path({str(ROOT)!r})")
ns = {}; exec(src, ns)
RAW = ROOT / 'data/raw/keisatsu/estat'; OUT = ROOT / 'results/cross'; OUT.mkdir(parents=True, exist_ok=True)
ED = {'H27': 2015, 'H28': 2016, 'H29': 2017, 'H30': 2018, 'R01': 2019, 'R02': 2020, 'R03': 2021, 'R04': 2022, 'R05': 2023, 'R06': 2024, 'R07': 2025}
pol = {}
for ed, y in ED.items():
    csvs = sorted(RAW.glob(f'{ed}_kakutei_*.csv')); pdfs = sorted(RAW.glob(f'{ed}_kakutei_*.pdf'))
    t1 = (ns['csv_tables'](str(csvs[0])) if csvs else ns['pdf_tables'](str(pdfs[0])))[1]
    pol[y] = t1[ns['norm']('刑法犯総数')]
LAB = {65: '平成30年版', 66: '令和元年版', 67: '令和2年版', 68: '令和3年版', 69: '令和4年版', 70: '令和5年版', 71: '令和6年版', 72: '令和7年版'}
rows, cnt = [], Counter()
for e in range(67, 73):
    p = ROOT / f'data/raw/hanzai_hakusho/{e}/shiryo/shiryo1-1.xlsx'
    if not p.exists(): cnt[('欠測', e)] += 1; continue
    S = {}
    for cells in xlsx.read_sheets(p).values():
        t, _ = sheet_rows(cells, key_cols=(3,))
        S.update({year(k): v for k, v in t.items() if year(k)})
    for y in range(2015, 2026):
        if y not in S or y not in pol: continue
        for q in ('認知件数', '検挙件数', '検挙人員'):
            h = S[y].get(f'{q}_刑法犯'); n = pol[y][q][0]
            if h is None: cnt[('白書に列なし', e)] += 1; continue
            st = '一致' if abs(h - n) < 1e-9 else '食い違い'
            cnt[(st,)] += 1
            rows.append([LAB[e], y, q, h, n, st])
with open(OUT / 'c406_hanzaihakusho_vs_toukei.tsv', 'w') as w:
    w.write('hakusho_edition\tyear\titem\thakusho_shiryo1-1\tnpa_table1_keihouhan_sousu\tstatus\n')
    for r in rows: w.write('\t'.join(map(str, r)) + '\n')
print(dict(cnt))
for r in rows:
    if r[-1] != '一致': print(*r, sep='\t')

# 照合の要約（lib/tally.py）：一致・食い違いを照合の数に、欠測（値が読めない・対応なし）を読み取りの失敗に数える。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('hanzai_hakusho', 'c406', note='犯罪白書 資料1-1（令和2〜7年版）と犯罪統計資料 第1表', script=__file__)
for _r in rows:
    _st = _r[-1]
    if _st == '一致': _t.ok()
    elif _st == '食い違い': _t.ng(explained=bool(False))
    else: _t.fail()
print('tally', _t.save())
# 白書に列がない組は読み取りの失敗（対応なし）
_t.fail(sum(n for k, n in cnt.items() if k[0] == '白書に列なし')); print('tally', _t.save())
