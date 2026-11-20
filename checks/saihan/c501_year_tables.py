#!/usr/bin/env python3
"""検算 c501（b 版の比較）：再犯防止推進白書（平成30年版〜令和7年版）の全体版 PDF にある「年 次」で始まる表
（成果指標の推移など。行が年、列が数値）を版ごとに読み、同じ表・同じ年の行の数値の並びを突き合わせる。
表の鍵：「年 次」の見出し行の文字（空白を除く）。年の行：「平成 27 年」「28」「令和元年」「２」など（前の年から1ずつ）。
正誤表（2025-12-26 公表）の訂正箇所が、版の間の食い違いとして出るかも見る（陽性対照）。
出力: results/saihan/c501_year_tables.tsv（2版以上に出る表×年の、版ごとの数値の並び）、c501_summary.tsv"""
import re, unicodedata
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; TXT = ROOT / 'data/derived/saihan'; OUT = ROOT / 'results/saihan'; OUT.mkdir(parents=True, exist_ok=True)
EDS = ['H30', 'R01', 'R02', 'R03', 'R04', 'R05', 'R06', 'R07']
vals = defaultdict(dict); cnt = Counter()
for ed in EDS:
    p = TXT / f'{ed}.txt'
    if not p.exists(): cnt[('なし', ed)] += 1; continue
    head, last, n = None, None, 0
    for line in p.read_text().splitlines():
        s = unicodedata.normalize('NFKC', line).strip()
        if re.match(r'^年\s*次', s):
            head = re.sub(r'\s', '', s)[:60]; last = None; continue
        if not head: continue
        m = re.match(r'^(?:(平成|令和)\s*)?(\d+|元)\s*(?:年度?)?\s+(.*)$', s)
        if not m:
            if s and not re.match(r'^[\d,.\s()（）%]+$', s): head = None if len(s) > 40 else head
            continue
        era, y = m[1], (1 if m[2] == '元' else int(m[2]))
        if era == '平成' or (era is None and last and last[0] == 'H' and y == last[1] + 1): yy = ('H', y)
        elif era == '令和' or (era is None and last and last[0] in 'HR' and (y == 1 or y == last[1] + 1)): yy = ('R', y)
        else: continue
        if era is None and last and not (y == last[1] + 1 or (y == 1 and last[0] == 'H')): continue
        last = yy
        year = (1988 + yy[1]) if yy[0] == 'H' else (2018 + yy[1])
        nums = re.findall(r'(?<![\d.])\d[\d,]*(?:\.\d+)?', m[3])
        if not nums: continue
        vals[(head, year)][ed] = ' '.join(nums[:8]); n += 1
    cnt[('読めた行', ed)] = n
rows = []
for (h, y), d in sorted(vals.items()):
    if len(d) < 2: continue
    ok = len(set(d.values())) == 1
    cnt[('比較', '一致' if ok else '食い違い')] += 1
    rows.append([h, y, ' | '.join(f'{e}: {v}' for e, v in d.items()), '一致' if ok else '食い違い'])
with open(OUT / 'c501_year_tables.tsv', 'w') as w:
    w.write('table_header\tyear\tvalues_by_edition\tstatus\n')
    for r in rows: w.write('\t'.join(map(str, r)) + '\n')
with open(OUT / 'c501_summary.tsv', 'w') as w:
    for k, v in sorted(cnt.items(), key=str): w.write('\t'.join(map(str, k)) + f'\t{v}\n')
for k, v in sorted(cnt.items(), key=str): print(k, v)

# 照合の要約（lib/tally.py）：単位は2版以上に出る（表・年）の行。食い違いの行は次の順に分ける。
#  1) 見出しが「年次」だけの表：別の表の混同＝読み取りの失敗
#  2) 版ごとの数値の並びから、頁番号らしい末尾の1語を除き（他の版の並びと一致するとき）、数値の読めない並び（すべて2桁以下）を除いて、
#     残りが一致すれば読み取りの失敗、違えば資料どうしの食い違い。作業ノートで説明を確かめた行（正誤表・元の統計の正誤情報）は説明あり。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_EXPL = {('年次保護観察終了者(総数)職業不詳の者無職である者', 2019), ('年次刑務所出所者総数帰住先がない者', 2022)}
_t = Tally('saihan', 'c501', note='再犯防止推進白書 平成30〜令和7年版：「年次」の表の同じ年の行の、版どうしの比較', script=__file__)
for (h, y), d in sorted(vals.items()):
    if len(d) < 2: continue
    if len(set(d.values())) == 1: _t.ok(); continue
    if h == '年次': _t.fail(); continue
    L = {e: v.split() for e, v in d.items()}
    C = {}
    for e, l in L.items():
        others = [m for f, m in L.items() if f != e]
        c = l[:-1] if (l not in others and l[:-1] in others) else l
        if all(len(t.replace(',', '').split('.')[0]) <= 2 for t in c): continue
        C[e] = ' '.join(c)
    if len(set(C.values())) <= 1: _t.fail()
    else: _t.ng(explained=(h, y) in _EXPL)
print('tally', _t.save())
