"""c2301: 毎月勤労統計調査（全国、確報）の検査。2025年分・2024年分。
(a) L1：第1表 現金給与総額＝きまって支給する給与＋特別に支払われた給与、きまって支給＝所定内＋所定外（各産業・就業形態）
(b) L5：時系列第1表 賃金指数から前年比を再計算し、公表の前年比と比べる（差 0.15 ポイントまで許す）。2024年は概況の注6（ベンチマーク更新の参考値で算出）により指数から計算した値と一致しないことが説明されている
(c) L3：時系列第1表 2025年版と2024年版の重なる年の指数
使い方: ~/.venvs/urazuke/bin/python checks/maikin/c2301_maikin.py"""
import sys, re, json, collections, openpyxl
D = 'data/raw/maikin'
st = collections.Counter(); issues = []; notes = []
def f(x): return float(x) if isinstance(x, (int, float)) else None
for y in ('2025', '2024'):
    ws = openpyxl.load_workbook(f'{D}/{y}/{y[2:]}cc01r.xlsx', data_only=True).worksheets[0]
    for r in ws.iter_rows(values_only=True):
        v = [f(x) for x in r[2:12]]   # 2列目は空
        if r[0] and v[0] is not None and v[2] is not None and v[8] is not None:
            st['a'] += 1
            if abs(v[0] - v[2] - v[8]) > 1: issues.append((y, '(a)総額≠きまって+特別', str(r[0]).strip(), v[0], v[2], v[8]))
            if v[4] is not None and v[6] is not None:
                st['a'] += 1
                if abs(v[2] - v[4] - v[6]) > 1: issues.append((y, '(a)きまって≠所定内+所定外', str(r[0]).strip(), v[2], v[4], v[6]))
def series(p):
    ws = openpyxl.load_workbook(p, data_only=True).worksheets[0]; out = []; sect = -1
    for r in ws.iter_rows(values_only=True):
        lab = str(r[0]).strip() if r[0] else ''
        m = re.fullmatch(r'(\d{4})年', lab.replace('　', '')) or re.fullmatch(r'(平成|令和)(\d+|元)年', lab.replace('　', ''))
        if not m: continue
        yr = int(m[1]) if m.lastindex == 1 else {'平成': 1988, '令和': 2018}[m[1]] + (1 if m[2] == '元' else int(m[2]))
        if not out or yr <= out[-1][0][1]: sect += 1
        out.append(((sect, yr), [x for x in r[1:] if isinstance(x, (int, float)) or (isinstance(x, str) and x.strip() in ('－', '-'))]))
    return dict(out)
S25 = series(f'{D}/2025/25ct01r.xlsx'); S24 = series(f'{D}/2024/24ct01r.xlsx')
# (b) 2025年版：列の並び 指数・前年比・実質前年比 ×（調査産業計・製造業・卸小売・医療福祉）… 先頭の組（調査産業計）だけを使う
for (sect, yr), v in S25.items():
    prev = S25.get((sect, yr - 1))
    if not prev or not isinstance(v[0], float) and not isinstance(v[0], int): continue
    calc = round((v[0] / prev[0] - 1) * 100, 1); pub = v[1]
    if not isinstance(pub, (int, float)): continue
    st['b'] += 1
    if abs(calc - pub) > 0.15:
        (notes if yr == 2024 else issues).append(('(b)指数から計算した前年比≠公表の前年比', sect, yr, prev[0], v[0], calc, pub))
# (c) 版間：区分の順（現金給与総額・きまって・所定内）と年で照合。2024年版は列の並びが違う（指数・前年比 の組が続く）ため先頭の指数だけ比べる
for k in set(S25) & set(S24):
    st['c'] += 1
    if abs(S25[k][0] - S24[k][0]) > 1e-9: issues.append(('(c)指数の版間の差', k, S24[k][0], S25[k][0]))
json.dump({'counts': st, 'issues': issues, 'explained': notes}, open('results/maikin/c2301_maikin.json', 'w'), ensure_ascii=False, indent=1, default=str)
print(dict(st)); print('issues', len(issues)); [print(i) for i in issues[:20]]; print('explained(2024)', len(notes)); [print(n) for n in notes[:6]]

# 照合の要約（lib/tally.py）：単位は式。2024年の前年比3組の違いは概況の注6（ベンチマーク更新の参考値）で説明あり。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('maikin', 'c2301', note='毎月勤労統計：指数・前年比の再計算、表どうし', script=__file__)
_t.set(compared=sum(st.values()), mismatched=len(issues) + len(notes), read_failures=0, explained=len(notes)); print('tally', _t.save())
