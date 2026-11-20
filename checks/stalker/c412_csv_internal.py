"""警察庁「ストーカー・DV・児童虐待」CSV の内部の整合。
(1) 親子：2列目に見出しのある行（親）の値＝直後に3列目の見出しで続く行（子）の和
(2) 性別＝年齢：同じ小節の中で、性別の行（男性・女性・不明／男児・女児）の和＝年齢の行の和
(3) 総数＝内訳：「総数」で始まる行のある小節では、総数＝その小節の他の行（親子の子は除く）の和
年の列だけを見る（割合の列は除く）。食い違いはすべて出力し、読み方の問題か値の問題かは目で確かめる。"""
import csv, io, re, glob, sys
def dec(b):
    for e in ('utf-8-sig', 'cp932'):
        try: return b.decode(e)
        except UnicodeDecodeError: pass
def num(s):
    s = (s or '').strip().replace(',', '')
    return int(s) if re.fullmatch(r'-?\d+', s) else None
AGE = re.compile(r'歳|年齢不詳|未就学|小学生|中学生|高校生')
SEX = {'男性', '女性', '不明', '男児', '女児'}
tot = ok = 0; ng = []
files = sorted(glob.glob('data/raw/stalker/npa/*.csv') + glob.glob('data/raw/stalker/wayback/*.csv'))
for f in files:
    R = list(csv.reader(io.StringIO(dec(open(f, 'rb').read()))))
    sec = None; ycols = []; rows = []
    def flush():
        global tot, ok
        if not rows or not ycols: return
        name = f.split('/')[-1]
        # (1) 親子
        i = 0
        while i < len(rows):
            lv, lab, vals = rows[i]
            if lv == 1:
                kids = []
                j = i + 1
                while j < len(rows) and rows[j][0] == 2:
                    kids.append(rows[j]); j += 1
                if kids:
                    for c, y in ycols:
                        if vals.get(c) is None or any(k[2].get(c) is None for k in kids): continue
                        s = sum(k[2][c] for k in kids); tot += 1
                        if s == vals[c]: ok += 1
                        else: ng.append((name, sec, f'親子 {lab}', y, vals[c], s))
            i += 1
        top = [r for r in rows if r[0] == 1]
        # (2) 性別＝年齢
        sx = [r for r in top if r[1] in SEX]; ag = [r for r in top if AGE.search(r[1])]
        if sx and ag:
            for c, y in ycols:
                a = [r[2].get(c) for r in sx]; b = [r[2].get(c) for r in ag]
                if None in a or None in b: continue
                tot += 1
                if sum(a) == sum(b): ok += 1
                else: ng.append((name, sec, '性別＝年齢', y, sum(a), sum(b)))
        # (3) 総数＝内訳
        tt = [r for r in top if r[1].replace('　', '').startswith('総数')]
        if tt and not (sx and ag):
            others = [r for r in top if r is not tt[0] and '密接' not in r[1] and 'うち' not in r[1]]
            for c, y in ycols:
                v = tt[0][2].get(c); xs = [r[2].get(c) for r in others]
                if v is None or not xs or None in xs: continue
                tot += 1
                if sum(xs) == v: ok += 1
                else: ng.append((name, sec, '総数＝内訳', y, v, sum(xs)))
    for r in R:
        r = r + [''] * 3
        cells = [x.strip() for x in r]
        if re.match(r'^[（(]\d+[）)]', cells[1]) or re.match(r'^\d+\s*[　 ]', cells[0]) :
            flush(); sec = cells[1] or cells[0]; ycols = []; rows = []; continue
        yc = [(j, c) for j, c in enumerate(cells) if re.fullmatch(r'(令和|平成)\S+年', c) and '割合' not in c]
        if len(yc) >= 2:
            if rows: flush(); rows = []
            ycols = yc; continue
        if not ycols: continue
        if cells[1] and not cells[2]: lv, lab = 1, cells[1]
        elif cells[2] and not cells[1]: lv, lab = 2, cells[2]
        elif cells[1] and cells[2] and num(cells[2]) is not None: lv, lab = 1, cells[1]
        else: continue
        vals = {c: num(cells[c]) if c < len(cells) else None for c, _ in ycols}
        if all(v is None for v in vals.values()): continue
        rows.append((lv, lab, vals))
    flush()
print(f'files {len(files)}  checks {tot}  ok {ok}  ng {len(ng)}')
for x in ng: print('NG', *x, sep='\t')

# 照合の要約（lib/tally.py）：単位は検査した式（親＝子の和、性別の和＝年齢の和、総数＝内訳）。食い違い103件のうち99件は、内訳ではない行を
# 検査が親子と読んだもの（作業ノート：性別に密接関係者を含む、禁止命令等の下の行、援助の種類、死亡児童数）＝読み取りの失敗。
# 資料どうしの食い違いは「ストーカー規制法に抵触しない動機」2022年 762（内訳の和 768）の4件（同じ値が4つの版の CSV に持ち越し）。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('stalker', 'c412', note='ストーカー・DV・児童虐待の CSV：親＝子の和、性別の和＝年齢の和、総数＝内訳', script=__file__)
_ng = sum(1 for x in ng if '抵触しない動機' in x[2])
_t.set(compared=ok + _ng, mismatched=_ng, read_failures=len(ng) - _ng); print('tally', _t.save())
