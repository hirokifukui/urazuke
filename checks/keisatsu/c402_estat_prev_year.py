#!/usr/bin/env python3
"""検算 c402（b 版の比較）：犯罪統計資料 CSV の「前年」列（N年の資料）と、前年の資料（N−1年）の「当年」列を突き合わせる。
対応の鍵：表番号・部分・（第6・9・13表は表題の括弧内）・区分（c0, c1）・列の区分。罪名の変更（強制わいせつ→不同意わいせつ等）で鍵が変わる行は「対応なし」として数える。
使い方: c402_estat_prev_year.py [CSV のグロブ]（既定は data/raw/keisatsu/estat/R0*_kakutei_*.csv）
出力: results/keisatsu/c402_estat_prev_year.tsv（食い違いの明細）、c402_summary.tsv。"""
import sys, glob, re
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT / 'lib'))
import npa_csv
OUT = ROOT / 'results/keisatsu'; OUT.mkdir(parents=True, exist_ok=True)
pat = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / 'data/raw/keisatsu/estat/R0*_kakutei_*.csv')
tag = sys.argv[2] if len(sys.argv) > 2 else ''

def cells(path):
    d = {}
    for T in npa_csv.read(path):
        sub = re.search(r'[（(]([^）)]+)[）)]\s*$', T['title'])
        tk = (T['no'], T['part'], sub[1] if (sub and T['no'] in ('第６表', '第９表', '第１３表')) else '')
        for c0, c1, v in T['rows']:
            for j, (c, p) in enumerate(T['cols']):
                y = npa_csv.year_of(p)
                if y and v[j] is not None:
                    d[(tk, c0, c1, c, y)] = v[j]
    return d

files = sorted(glob.glob(pat))
data = {Path(f).name[:3]: cells(f) for f in files}
keys = sorted(data)
det, cnt = [], Counter()
for a, b in zip(keys, keys[1:]):          # a = N−1年の資料, b = N年の資料
    A, B = data[a], data[b]
    ya = max(k[4] for k in A)              # a の当年
    for k, vb in B.items():
        if k[4] != ya: continue
        va = A.get(k)
        if va is None: cnt[(b, '対応なし')] += 1; continue
        if abs(va - vb) < 1e-9: cnt[(b, '一致')] += 1
        else:
            cnt[(b, '食い違い')] += 1
            det.append([f'{a}→{b}', ya, '|'.join(map(str, k[0])), k[1], k[2], k[3], va, vb, vb - va])
with open(OUT / f'c402_estat_prev_year{tag}.tsv', 'w') as w:
    w.write('pair\tyear\ttable\tc0\tc1\tcol\tvalue_in_prev_edition\tvalue_in_next_edition\tdiff\n')
    for d in det: w.write('\t'.join(map(str, d)) + '\n')
with open(OUT / f'c402_summary{tag}.tsv', 'w') as w:
    w.write('edition\tstatus\tn\n')
    for (f, s), n in sorted(cnt.items()): w.write(f'{f}\t{s}\t{n}\n')
print(dict(cnt)); print('食い違い', len(det))

# 照合の要約（lib/tally.py）：対応の取れた同じ表・同じ年の値。対応なし（罪名の変更などで鍵が変わる行）は読み取りの失敗に数える。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('keisatsu', 'c402', note='犯罪統計資料 CSV：N年版の前年列とN−1年版の当年列', script=__file__)
for (f, s), n in cnt.items():
    if s == '一致': _t.ok(n)
    elif s != '食い違い': _t.fail(n)
# 食い違い：令和3年版で主要法令の区分が増え、第15表の「その他」が縮んだもの（特別法犯計は一致。作業ノート）＝説明あり
for d in det: _t.ng(explained=(d[0] == 'R02→R03' and d[2].startswith('第１５表') and d[3] == 'その他'))
if not tag: print('tally', _t.save())  # tag 付き（陰性対照など）は数えない
