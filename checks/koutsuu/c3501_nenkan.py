"""c3501 警察庁「令和7年における交通事故の発生状況について」（令和8年2月26日）と令和6年版の 1-2（死者・重傷者の年齢層別推移）。
図の数値ラベルを出現順に読む（軸の目盛り＝500の倍数は除く）：最初の11個が全体、次の11個が65歳以上。
(a) 65歳以上の構成率 = 65歳以上/全体（小数1位、±0.051%）
(b) 版間：令和6年版と令和7年版で、重なる年（H27〜R6、令和6年版は H26〜R6）の値が同じか
(c) 本文の「令和7年中の死者数は2,547人で、前年比116人、4.4％減」などの前年比
使い方: c3501_nenkan.py [root]   出力: results/koutsuu/c3501.tsv"""
import sys, os, re, subprocess, unicodedata
root = sys.argv[1] if len(sys.argv) > 1 else '.'
D = os.path.join(root, 'data/raw/koutsuu/nenkan')
out = []; n = 0

def chk(ed, where, what, a, b, tol=0):
    global n
    n += 1
    if abs(a - b) > tol + 1e-9: out.append((ed, where, what, a, round(b, 3)))

def series(txt, start, stop):
    i = txt.index(start); j = txt.index(stop, i)
    seg = txt[i:j]
    vals = [int(x.replace(',', '')) for x in re.findall(r'(?<![\d,])(\d{1,2},\d{3})(?![\d,])', seg)]
    vals = [v for v in vals if v % 500 != 0]
    rates = [float(x) for x in re.findall(r'(\d+\.\d)%', txt[j:j + 400])][:11]
    return vals, rates

R = {}
for ed, fn, years in (('R07', 'R07nenkan.pdf', list(range(2015, 2026))), ('R06', 'R06nenkan.pdf', list(range(2014, 2025)))):
    txt = unicodedata.normalize('NFKC', subprocess.run(['pdftotext', '-layout', f'{D}/{fn}', '-'], capture_output=True, text=True).stdout)
    # 重傷者の図は数値ラベルが年の順に並ばない（令和4年のラベルが下の行にある）ため、読まない
    for kind, start in (('死者', '死者数の推移'),):
        if start not in txt: continue  # 令和6年版の1-2には重傷者の図がない
        vals, rates = series(txt, start, '65歳以上の構成率')
        if len(vals) < 22:
            out.append((ed, kind, '数値ラベルが22個読めない', len(vals), '')); continue
        allv, old = vals[:11], vals[11:22]
        R[(ed, kind)] = dict(zip(years, zip(allv, old)))
        for y, a, o, r in zip(years, allv, old, rates):
            chk(ed, f'{kind} {y}', '65歳以上の構成率', r, o / a * 100, 0.051)
    m = re.search(r'令和7年中の死者数は([\d,]+)人で、前年比(\d+)人、([\d.]+)%減', txt) if ed == 'R07' else None
    if m and ('R07', '死者') in R:
        cur, d, pct = int(m[1].replace(',', '')), int(m[2]), float(m[3])
        prev = R[('R07', '死者')][2024][0]
        chk(ed, '本文', '死者数の前年比（人）', d, prev - cur)
        chk(ed, '本文', '死者数の前年比（%）', pct, (prev - cur) / prev * 100, 0.051)
for kind in ('死者',):
    a, b = R.get(('R06', kind), {}), R.get(('R07', kind), {})
    for y in sorted(set(a) & set(b)):
        n += 1
        if a[y] != b[y]: out.append(('版間', f'{kind} {y}', '令和6年版≠令和7年版', a[y], b[y]))
os.makedirs(os.path.join(root, 'results/koutsuu'), exist_ok=True)
with open(os.path.join(root, 'results/koutsuu/c3501.tsv'), 'w') as fo:
    fo.write('版\t場所\t式\t表の値\t計算値\n')
    for o in out: fo.write('\t'.join(map(str, o)) + '\n')
print('式の数', n, '不一致', len(out))
for k, v in R.items(): print(k, list(v.items())[:2], '...', list(v.items())[-1])
for o in out: print(*o)

# 照合の要約（lib/tally.py）：単位は式。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('koutsuu', 'c3501', note='交通事故の発生状況：構成率、版間、本文の前年比', script=__file__)
_t.set(compared=n, mismatched=len(out), read_failures=0, explained=None); print('tally', _t.save())
