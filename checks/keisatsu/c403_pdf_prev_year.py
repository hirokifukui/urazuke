#!/usr/bin/env python3
"""検算 c403（b 版の比較、PDF を含む）：犯罪統計資料の第1表（罪種別）と第3表（都道府県別）を、
平成27〜令和元年は PDF（pdftotext -layout）、令和2年以降は CSV から読み、
N年の資料の「前年」の値と、N−1年の資料の「当年」の値を突き合わせる。
あわせて、PDF と CSV の両方がある年（令和2〜5・7年）は、同じ年の PDF と CSV の値を突き合わせる（形式間の整合）。
行の対応：罪名・地域名の空白を除き、「管区」「方面」「計」を落とし、文字の並びをそろえた（並べ替えた）文字列で対応させる
（PDF では「刑法犯総数」が「刑法犯数総」の順に出るため）。
列：第1表 認知件数・検挙件数・検挙人員（当年・前年）、第3表 認知件数・検挙件数・検挙人員（当年・前年）。
出力: results/keisatsu/c403_pdf_prev_year.tsv（食い違い）、c403_summary.tsv。"""
import sys, glob, re, subprocess
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT / 'lib'))
import npa_csv
RAW = ROOT / 'data/raw/keisatsu/estat'; OUT = ROOT / 'results/keisatsu'
ED = {'H27': 2015, 'H28': 2016, 'H29': 2017, 'H30': 2018, 'R01': 2019, 'R02': 2020, 'R03': 2021, 'R04': 2022, 'R05': 2023, 'R06': 2024, 'R07': 2025}

def norm(s):
    s = re.sub(r'\s', '', s)
    s = s.replace('管区', '').replace('方面', '').replace('うち）', 'うち)').replace('うち)', '')
    if s.endswith('計') and len(s) > 1: s = s[:-1]
    return ''.join(sorted(s))

BLOCKS = ['その他の刑法犯', '凶悪犯', '粗暴犯', '窃盗犯', '知能犯', '風俗犯', '北海道', '東北', '関東', '中部', '近畿', '中国', '四国', '九州']
NUM = re.compile(r'^-?[\d,]+(\.\d+)?$|^-$')
def tok2v(t): return 0.0 if t == '-' else float(t.replace(',', ''))

def pdf_tables(path):
    n = int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', path], capture_output=True, text=True).stdout)[1])
    res = {}
    for p in range(1, min(n, 25) + 1):
        txt = subprocess.run(['pdftotext', '-layout', '-f', str(p), '-l', str(p), path, '-'], capture_output=True, text=True).stdout
        head = re.sub(r'\s', '', txt[:300])
        m = re.match(r'第([１３13])表', head)
        if not m or m[1] not in '１３13': continue
        tno = 1 if m[1] in '１1' else 3
        if tno in res: continue
        rows = {}
        for line in txt.splitlines():
            parts = re.split(r'\s{2,}', line.strip())
            # 先頭から数値でない部分をラベルに、残りを数値に
            toks = line.split()
            k = 0
            while k < len(toks) and not NUM.match(toks[k]): k += 1
            lab, nums = ''.join(toks[:k]), toks[k:]
            if not lab or len(nums) < 9 or not all(NUM.match(x) for x in nums): continue
            v = [tok2v(x) for x in nums]
            if tno == 1:   # 認知 cur,prev,増減,率 / 検挙 cur,prev,増減,率 / 検挙率 cur,prev,pt / 人員 cur,prev,...
                d = {'認知件数': (v[0], v[1]), '検挙件数': (v[4], v[5]), '検挙人員': (v[11], v[12])} if len(v) >= 13 else None
            else:          # 認知 cur,prev,増減,率 / 検挙 cur,prev,増減,率 / 人員 cur,prev,増減,率 / 検挙率
                d = {'認知件数': (v[0], v[1]), '検挙件数': (v[4], v[5]), '検挙人員': (v[8], v[9])} if len(v) >= 10 else None
            # 令和2年以降の PDF は行頭に区分名（凶悪犯・東北など）が付く。区分名の後ろに名前が続く行は前置を外す
            for blk in BLOCKS:
                if lab.startswith(blk) and len(lab) > len(blk) and not lab[len(blk):].startswith('計'):
                    lab = lab[len(blk):]; break
            if d: rows.setdefault(norm(lab), d)
        res[tno] = rows
    return res

def csv_tables(path):
    res = {1: {}, 3: {}}
    for T in npa_csv.read(path):
        tno = {'第１表': 1, '第３表': 3}.get(T['no'])
        if tno is None or T['part'] != 0: continue
        idx = {}
        for j, (c, p) in enumerate(T['cols']):
            y = npa_csv.year_of(p)
            if y and c in ('認知件数', '検挙件数', '検挙人員'): idx.setdefault(c, []).append((y, j))
        for c0, c1, v in T['rows']:
            name = c0 if c1 in ('計', '') else re.split(r'うち[）)]', c1)[-1]
            d = {}
            for c, lst in idx.items():
                lst = sorted(lst, reverse=True)
                d[c] = (v[lst[0][1]], v[lst[1][1]])
            res[tno].setdefault(norm(name), d)
    return res

src = {}
for ed in ED:
    pdfs = sorted(RAW.glob(f'{ed}_kakutei_*.pdf')); csvs = sorted(RAW.glob(f'{ed}_kakutei_*.csv'))
    if pdfs: src[(ed, 'pdf')] = pdf_tables(str(pdfs[0]))
    if csvs: src[(ed, 'csv')] = csv_tables(str(csvs[0]))
det, cnt = [], Counter()
def cmp(kind, la, A, lb, B, ia, ib):
    for tno in (1, 3):
        for key, db in B.get(tno, {}).items():
            da = A.get(tno, {}).get(key)
            if da is None: cnt[(kind, la, lb, '対応なし')] += 1; continue
            for c in ('認知件数', '検挙件数', '検挙人員'):
                a, b = da[c][ia], db[c][ib]
                if a is None or b is None: continue
                if abs(a - b) < 1e-9: cnt[(kind, la, lb, '一致')] += 1
                else:
                    cnt[(kind, la, lb, '食い違い')] += 1
                    det.append([kind, la, lb, f'第{tno}表', ''.join(sorted(key)), c, a, b])
eds = list(ED)
# 版の比較（N−1 の当年 ↔ N の前年）。CSV があれば CSV を、なければ PDF を使う
def pick(ed): return src.get((ed, 'csv')) or src.get((ed, 'pdf'))
for a, b in zip(eds, eds[1:]):
    if pick(a) and pick(b): cmp('b版の比較', a, pick(a), b, pick(b), 0, 1)
# 形式間（同じ年の PDF ↔ CSV、当年・前年とも）
for ed in eds:
    if (ed, 'pdf') in src and (ed, 'csv') in src:
        cmp('a形式間', ed + 'pdf', src[(ed, 'pdf')], ed + 'csv', src[(ed, 'csv')], 0, 0)
        cmp('a形式間(前年列)', ed + 'pdf', src[(ed, 'pdf')], ed + 'csv', src[(ed, 'csv')], 1, 1)
with open(OUT / 'c403_pdf_prev_year.tsv', 'w') as w:
    w.write('kind\tA\tB\ttable\trow(並べ替え後の文字)\tcol\tA_value\tB_value\n')
    for d in det: w.write('\t'.join(map(str, d)) + '\n')
with open(OUT / 'c403_summary.tsv', 'w') as w:
    w.write('kind\tA\tB\tstatus\tn\n')
    for k, n in sorted(cnt.items()): w.write('\t'.join(k) + f'\t{n}\n')
for k, n in sorted(cnt.items()): print(k, n)
print('食い違い', len(det), ' 読めた表:', {k: {t: len(v) for t, v in s.items()} for k, s in src.items()})
# 対応が取れなかった行の一覧（形式間、令和2年）を残す
import os
if os.environ.get('C403_DEBUG'):
    a, b = src[('R02', 'pdf')], src[('R02', 'csv')]
    for t in (1, 3):
        print(t, 'PDFのみ', [''.join(k) for k in a[t] if k not in b[t]][:20])
        print(t, 'CSVのみ', [''.join(k) for k in b[t] if k not in a[t]][:20])

# 照合の要約（lib/tally.py）：対応の取れた同じ表・同じ年の値。対応なしは読み取りの失敗。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('keisatsu', 'c403', note='犯罪統計資料 PDF と CSV：版の比較と形式間', script=__file__)
for k, n in cnt.items(): {'一致': _t.ok, '食い違い': _t.ng}.get(k[-1], _t.fail)(n)
print('tally', _t.save())
