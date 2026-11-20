#!/usr/bin/env python3
"""検算 c702（b 版の比較）：児童虐待相談対応件数の「速報値」資料（厚労省・こども家庭庁）↔ 確定値（福祉行政報告例、e-Stat）
 1 当年度の速報値 ↔ 当年度の確定値（全国・都道府県・指定都市・児童相談所設置市別）
 2 速報値資料に載る前年度の値 ↔ 前年度の確定値（資料に載る過去の値が確定値どおりか）
 3 速報値資料の内部：増減＝当年度−前年度
速報値資料の都道府県表は「番号 名称 前年度 当年度 増減 増減率」が2段組みで並ぶ。
自治体の訂正予定（c700、報告表第49）と重なる行には印を付ける。
出力: results/gyakutai/c702_sokuhou_vs_kakutei.tsv（全行）、c702_summary.tsv"""
import sys, glob, re, subprocess, csv
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT / 'lib'))
import fukushi_csv as F
OUT = ROOT / 'results/gyakutai'
DOCS = {2015: 'H27_sokuhou_shingikai_003_1.pdf', 2018: 'H30_sokuhou_000552878.pdf', 2020: 'R2_sokuhou_000824359.pdf',
        2022: 'R4_sokuhou_cfa_20230401_19.pdf', 2024: 'R6_sokuhou_cfa_20260130.pdf'}
def kakutei(fy):
    fs = glob.glob(str(ROOT / f'data/raw/gyakutai/estat/FY{fy}_ken_shubetsu_*.csv'))
    if not fs: return {}
    T = F.read(fs[0]); ti = T['cols'].index('総数')
    return {re.sub(r'[\s　]', '', c1 or c0).replace('（別掲）', ''): v[ti] for c0, c1, v in T['rows']}
teisei = defaultdict(set)
tp = OUT / 'c700_teisei_yotei.tsv'
if tp.exists():
    for r in csv.DictReader(open(tp), delimiter='\t'):
        if r['report_table'] == '第49': teisei[int(r['fiscal_year'])].add(r['authority'])
PAT = re.compile(r'(?:(\d+)\s+)?(全\s*国|[^\s\d▲※]+?(?:県|都|道|府|市|区))\s+(?:※[\d,]+\s+)?([\d,]+)\s+([\d,]+)\s+(▲\s*[\d,]+|-?[\d,]+)')
rows, cnt = [], Counter()
for fy, fn in DOCS.items():
    p = ROOT / 'data/raw/gyakutai/sokuhou' / fn
    if not p.exists(): cnt[('資料なし', fy)] += 1; continue
    txt = subprocess.run(['pdftotext', '-layout', str(p), '-'], capture_output=True, text=True).stdout
    K, Kp = kakutei(fy), kakutei(fy - 1)
    got = 0
    for line in txt.splitlines():
        for m in PAT.finditer(line):
            name = re.sub(r'\s', '', m[2]); prev, cur = float(m[3].replace(',', '')), float(m[4].replace(',', ''))
            d = m[5].replace(' ', '').replace(',', ''); d = -float(d[1:]) if d.startswith('▲') else float(d)
            got += 1
            kk = K.get(name); kp = Kp.get(name)
            flag = '訂正予定(第49)' if (name in teisei[fy] or name in teisei[fy - 1]) else ''
            rows.append([fy, name, prev, kp, cur, kk, d, (kk - cur) if kk is not None else '', (kp - prev) if kp is not None else '', flag])
            cnt[('3増減', fy, abs(cur - prev - d) < 1e-9)] += 1
            if kk is not None: cnt[('1速報↔確定', fy, abs(kk - cur) < 1e-9)] += 1
            if kp is not None: cnt[('2前年度の値↔確定', fy, abs(kp - prev) < 1e-9)] += 1
    cnt[('読めた行', fy)] = got
with open(OUT / 'c702_sokuhou_vs_kakutei.tsv', 'w') as w:
    w.write('fy\tauthority\tprev_in_sokuhou\tprev_kakutei\tsokuhou\tkakutei\tdiff_stated\tkakutei_minus_sokuhou\tprevkakutei_minus_prevstated\tflag\n')
    for r in rows: w.write('\t'.join('' if x is None else (f'{x:g}' if isinstance(x, float) else str(x)) for x in r) + '\n')
with open(OUT / 'c702_summary.tsv', 'w') as w:
    for k, n in sorted(cnt.items(), key=str): w.write('\t'.join(map(str, k)) + f'\t{n}\n')
for k, n in sorted(cnt.items(), key=str): print(k, n)
print('全国:'); [print(r) for r in rows if r[1] == '全国']

# 照合の要約（lib/tally.py）：1 速報値↔確定値、2 速報値資料の前年度の値↔確定値、3 増減の欄の算術。
# 速報値と確定値の違いは食い違いに数える（令和4年度の大きな減少は理由が資料にないため、説明ありにはしない）。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('gyakutai', 'c702', note='児童虐待相談対応件数：速報値と確定値（自治体別）、前年度の値、増減の算術', script=__file__)
for k, n in cnt.items():
    if k[0][0] in '123': (_t.ok if k[2] else _t.ng)(n)
print('tally', _t.save())
