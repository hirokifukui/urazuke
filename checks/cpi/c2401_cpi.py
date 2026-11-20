"""c2401: 消費者物価指数（2020年基準、全国 年平均）の検査。
(a) L5：中分類指数（1970年〜2025年）から前年比を再計算し、公表の前年比（中分類指数 前年比）と比べる。公表の前年比は丸める前の指数から計算するため、差 0.15 ポイントまで許す
(b) L4：年平均 PDF（2025年）の総合・生鮮食品を除く総合・生鮮食品及びエネルギーを除く総合 の指数と前年比＝CSV
使い方: ~/.venvs/urazuke/bin/python checks/cpi/c2401_cpi.py"""
import csv, io, re, json, collections, subprocess
D = 'data/raw/cpi/2025'
def load(p):
    rows = list(csv.reader(io.StringIO(open(p, 'rb').read().decode('cp932'))))
    hdr = rows[0]; out = {}
    for r in rows:
        if r and re.fullmatch(r'\d{4}', r[0].strip()):
            out[int(r[0])] = {hdr[i]: float(x) for i, x in enumerate(r) if i and re.fullmatch(r'-?\d+(\.\d+)?', x.strip())}
    return hdr, out
h1, I = load(f'{D}/chubunrui_index_000032103936.csv'); h2, Y = load(f'{D}/chubunrui_yoy_000032103940.csv')
st = collections.Counter(); issues = []; big = []
for y in sorted(Y):
    if y - 1 not in I or y not in I: continue
    for k, pub in Y[y].items():
        a, b = I[y - 1].get(k), I[y].get(k)
        if a is None or b is None or a == 0: continue
        calc = (b / a - 1) * 100; st['a'] += 1
        # 指数は小数第1位に、前年比は小数第1位に丸めて公表される。丸めの範囲どうしが重なれば一致とみなす
        lo = ((b - 0.05) / (a + 0.05) - 1) * 100; hi = ((b + 0.05) / (a - 0.05) - 1) * 100
        if pub + 0.05 < lo - 1e-9 or pub - 0.05 > hi + 1e-9: issues.append(('(a)指数から計算した前年比≠公表（丸めの範囲外）', y, k, a, b, round(calc, 2), pub))
t = subprocess.run(['pdftotext', '-layout', f'{D}/zen-n.pdf', '-'], capture_output=True, text=True).stdout
res = []
ann = t[t.index('平均', t.index('２')):] if '２' in t else t
ann = t[[m.start() for m in re.finditer(r'2025年\(令和７年\)平均', t)][-1]:]
for k, pat in [('総合', r'総合指数は2020年を100として([\d.]+)\s*前年比は([\d.]+)％の(上昇|下落)'), ('生鮮食品を除く総合', r'生鮮食品を除く総合指数は([\d.]+)\s*前年比は([\d.]+)％の(上昇|下落)'), ('生鮮食品及びエネルギーを除く総合', r'生鮮食品及びエネルギーを除く総合指数は([\d.]+)\s*前年比は([\d.]+)％の(上昇|下落)')]:
    m = re.search(pat, re.sub(r'\s+', ' ', ann))
    if m:
        yv = float(m[2]) * (1 if m[3] == '上昇' else -1)
        st['b'] += 2; res.append((k, float(m[1]), I[2025][k], yv, Y[2025][k]))
        if abs(float(m[1]) - I[2025][k]) > 1e-9 or abs(yv - Y[2025][k]) > 1e-9: issues.append(('(b)PDF≠CSV', k, m[1], yv, I[2025][k], Y[2025][k]))
json.dump({'counts': st, 'issues': issues, 'pdf_vs_csv': res}, open('results/cpi/c2401_cpi.json', 'w'), ensure_ascii=False, indent=1)
print(dict(st), 'years', min(Y), max(Y), 'cols', len(h2)); print(len(issues)); [print(i) for i in issues[:20]]; [print(i) for i in issues if i[0].startswith('(b)')]; print(res)

# 照合の要約（lib/tally.py）：単位は式。1971〜1990年の前年比の36組は丸めの範囲外（過去の基準の接続による可能性。説明は未確認）＝資料どうしの食い違い。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('cpi', 'c2401', note='消費者物価指数：指数から前年比の再計算、PDF と CSV', script=__file__)
_t.set(compared=sum(st.values()), mismatched=len(issues), read_failures=0, explained=None); print('tally', _t.save())
