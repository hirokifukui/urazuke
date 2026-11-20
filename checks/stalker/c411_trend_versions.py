#!/usr/bin/env python3
"""検算 c411（b 版の比較）：警察庁「ストーカー事案、配偶者からの暴力事案等…への対応状況について」各年の資料（PDF）には、
項目ごとに過去5年（古い資料は10年）の推移表がある。同じ項目・同じ年の値を、資料の版（公表年）ごとに突き合わせる。
読み取り：pdftotext -layout。年の見出し行（「平成27年 …」「令和元年 …」が3つ以上並ぶ行）を見つけ、続く行の「ラベル 数値…」を年に割り当てる。
項目の鍵：直前の小見出し（「（1）被害者の性別」など。番号を除く）＋ ラベル。小見出しの言い回しが版で変わると対応しない（対応なしとして数える）。
出力: results/stalker/c411_trend_versions.tsv（2つ以上の版に出る項目×年の値の並び）、c411_summary.tsv"""
import re, subprocess, sys
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; RAW = ROOT / 'data/raw/stalker'; OUT = ROOT / 'results/stalker'; OUT.mkdir(parents=True, exist_ok=True)
DOCS = [('H26', 'wayback/20150524041509_seianki26STDV.pdf'), ('H27', 'wayback/20160528040909_seianki27STDV.pdf'),
        ('H29', 'wayback/20190331135409_H29STDV_taioujoukyou.pdf'), ('H30', 'wayback/20190712171731_H30taioujoukyou.pdf'),
        ('R01', 'wayback/20200927010635_R1_STDVkouhoushiryou.pdf'), ('R02', 'npa/R2_STDVRPkouhyousiryou.pdf'),
        ('R03', 'npa/R3_STDVRPkouhousiryou.pdf'), ('R04', 'wayback/20230417003728_R4_STDVRPCAkouhousiryou.pdf'),
        ('R05原版', 'wayback/20240513060832_R5_STDVRPCAkouhousiryou.pdf'), ('R05修正版', 'npa/R5_STDVRPCAkouhousiryou_syuusei.pdf'),
        ('R06', 'npa/R6_STDVRP_CA_kouhoushiryou.pdf'), ('R07', 'npa/R7_STDVRPCA_kouhou.pdf')]
def year(tok):
    m = re.match(r'(平成|令和)(\d+|元)年', tok)
    if not m: return None
    n = 1 if m[2] == '元' else int(m[2]); return (1988 + n) if m[1] == '平成' else (2018 + n)
NUM = re.compile(r'^-?[\d,]+(\.\d+)?$')
vals = defaultdict(dict); cnt = Counter()
for ed, rel in DOCS:
    p = RAW / rel
    if not p.exists(): cnt[('資料なし', ed)] += 1; continue
    txt = subprocess.run(['pdftotext', '-layout', str(p), '-'], capture_output=True, text=True).stdout
    txt = txt.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
    head, years, nrow, last_text, sec = '', None, 0, '', ''
    for line in txt.splitlines():
        s = line.strip()
        if not s: continue
        for k, v in (('ストーカー', 'ST'), ('配偶者', 'DV'), ('私事性的', 'RP'), ('リベンジ', 'RP'), ('児童虐待', 'CA')):
            if re.match(r'^[第\d０-９IⅠ-Ⅹ一二三四五六七八九十\s.．、（(]*' + k, s): sec = v
        toks = re.findall(r'(?:平成|令和)\s*(?:\d+|元)\s*年', s)
        ys = [year(t.replace(' ', '')) for t in toks]
        if len(ys) >= 3:
            seen = []                      # 「令和5年の割合」のように同じ年が二度出る列は割合なので、その位置で打ち切る
            for y in ys:
                if y in seen: break
                seen.append(y)
            years = seen; head = sec + ':' + last_text; continue
        if not re.search(r'\d{2,}', s.replace('令和', '').replace('平成', '')):
            last_text = re.sub(r'[\s（）()0-9０-９]', '', s)[:30]; years = None if len(s) > 6 else years
            continue
        if not years: continue
        parts = s.split()
        k = 0
        while k < len(parts) and not NUM.match(parts[k]): k += 1
        lab = ''.join(parts[:k]); nums = [x for x in parts[k:] if NUM.match(x)]
        if not lab or len(nums) < len(years): continue
        for y, x in zip(years, nums[:len(years)]):
            vals[(head, re.sub(r'[※注\d]', '', lab), y)][ed] = float(x.replace(',', ''))
        nrow += 1
    cnt[('読めた行', ed)] = nrow
rows = []
for (h, lab, y), d in sorted(vals.items()):
    if len(d) < 2: continue
    ok = len(set(d.values())) == 1
    cnt[('比較', '一致' if ok else '食い違い')] += 1
    rows.append([h, lab, y, ' '.join(f'{e}={v:g}' for e, v in d.items()), '一致' if ok else '食い違い'])
with open(OUT / 'c411_trend_versions.tsv', 'w') as w:
    w.write('heading\tlabel\tyear\tvalues_by_edition\tstatus\n')
    for r in rows: w.write('\t'.join(map(str, r)) + '\n')
with open(OUT / 'c411_summary.tsv', 'w') as w:
    for k, n in sorted(cnt.items(), key=str): w.write('\t'.join(map(str, k)) + f'\t{n}\n')
for k, n in sorted(cnt.items(), key=str): print(k, n)

# 照合の要約（lib/tally.py）：単位は2版以上に出る（項目・年）。値の並びに小数（割合）と整数（件数）が混じる行は、割合と件数の列の読み違い＝読み取りの失敗。
# 説明のある食い違い：令和5年 DV の被害者の性別（修正版の告知つきの差し替え）、令和4年 ストーカーの防犯指導（注4の訂正）。児童虐待事件の殺人の既遂・未遂（ST-B1）は説明なし。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_EXPL = {('DV:被害者の性別', 2023), ('ST:その他の対応', 2022)}
_t = Tally('stalker', 'c411', note='ストーカー・DV・児童虐待の対応状況：推移表の同じ項目・同じ年の値の、資料の版どうしの比較', script=__file__)
for (h, lab, y), d in sorted(vals.items()):
    if len(d) < 2: continue
    v = list(d.values())
    if len(set(v)) == 1: _t.ok(); continue
    if any(x != int(x) for x in v) and any(x == int(x) for x in v): _t.fail(); continue
    _t.ng(explained=(h, y) in _EXPL)
print('tally', _t.save())
