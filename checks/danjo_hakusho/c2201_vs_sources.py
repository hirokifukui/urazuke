"""c2201: 男女共同参画白書 令和8年版（第1〜11章 PDF）の数値と、引用元の統計（警察庁）の突き合わせ（L4）。
(1) 5-7図 ストーカー事案の相談等件数 令和7年 22,881・令和6年 19,567 ＝ 警察庁「ストーカー事案、配偶者からの暴力事案等…」令和7年 CSV の被害者 男性＋女性
(2) 5-10図 不同意性交等 4,177（前年比 +241）・不同意わいせつ 7,193（+201）＝ 警察庁「犯罪統計」令和7年・令和6年の認知件数
使い方: ~/.venvs/urazuke/bin/python checks/danjo_hakusho/c2201_vs_sources.py"""
import re, csv, io, json, subprocess, collections
st = collections.Counter(); res = []
W = open('data/raw/danjo_hakusho/r08/06.txt', encoding='utf-8').read()
def num(s): return int(s.replace(',', '').replace(' ', ''))
def wp(pat):
    m = re.search(pat, W, re.S); return m.groups() if m else None
# (1)
rows = list(csv.reader(io.StringIO(open('data/raw/stalker/npa/01_R7_ST.csv', 'rb').read().decode('cp932'))))
hdr = next(r for r in rows if '令和７年' in r); ci = {h: i for i, h in enumerate(hdr)}
sex = {}
for r in rows:
    if len(r) > 2 and r[1] in ('男性', '女性') and r[1] not in sex: sex[r[1]] = r   # 最初の区分（被害者の性別）
for y, pat in [('令和７年', r'令和７（2025）年のストーカー事案の相談等件数は２万\s*([\d,]+)\s*件'), ('令和６年', r'ストーカー事案の相談等件数の推移.*?22,881.*?(\d{2},(?!000)\d{3})')]:
    g = wp(pat); v = (20000 + num(g[0])) if y == '令和７年' else (num(g[0]) if g else None)
    src = num(sex['男性'][ci[y]]) + num(sex['女性'][ci[y]])
    st['n'] += 1; res.append(('ストーカー相談等件数', y, v, src, v == src))
# (2)
def nenpo(p, code):
    t = subprocess.run(['pdftotext', '-layout', p, '-'], capture_output=True, text=True).stdout
    m = re.search(code + r'[^\n]*?\s([\d,]+)\s+[\d,]+\s+\d+\s+[\d,]+\s+[\d,]+\s*$', t, re.M); return num(m[1])
for name, code, pat in [('不同意性交等', r'A-d', r'不同意性交等の認知件数は、令和７（2025）年は\s*([\d,]+)\s*件で、前年に比べ\s*([\d,]+)\s*件'), ('不同意わいせつ', r'E-b-1', r'不同意わいせつの認知件数は、令和７（2025）年は\s*([\d,]+)\s*件で、前年に比べ\s*([\d,]+)\s*件')]:
    g = wp(pat); v7, dv = num(g[0]), num(g[1])
    s7 = nenpo('data/raw/keisatsu/nenpo/R07_ALL.pdf', code); s6 = nenpo('data/raw/keisatsu/nenpo/R06_ALL.pdf', code)
    st['n'] += 2; res.append((name, '令和7年', v7, s7, v7 == s7)); res.append((name, '前年比', dv, s7 - s6, dv == s7 - s6))
json.dump({'counts': st, 'results': res}, open('results/danjo_hakusho/c2201_vs_sources.json', 'w'), ensure_ascii=False, indent=1)
print(dict(st)); [print(r) for r in res]

# 照合の要約（lib/tally.py）：単位は式。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('danjo_hakusho', 'c2201', note='男女共同参画白書の数値と元の統計', script=__file__)
_t.set(compared=len(res), mismatched=sum(1 for r in res if r[4] is not True), read_failures=0, explained=None); print('tally', _t.save())
