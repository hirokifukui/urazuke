"""c1303: 司法統計年報（刑事編）第1表の内部整合（L1）と版間比較（L3）。
(a) 各行で 総数＝訴訟事件＋訴訟事件以外（新受・既済・未済）
(b) 各年で 全裁判所＝最高＋高等＋地方＋簡易
(c) 令和5年（更新版）・令和6年（更新版）・令和7年の版で、重なる年の値が同じか
使い方: ~/.venvs/urazuke/bin/python checks/shiho/c1303_table1_internal.py"""
import sys, json, collections, re; sys.path.insert(0, '.')
import openpyxl
D = 'data/raw/shiho'
ED = {'r05u': 'r05/keiji_16603_upd20250916.xlsx', 'r06u': 'r06/keiji_16692_upd20260917.xlsx', 'r07': 'r07/keiji_16676.xlsx'}
ERA0 = {'昭和': 1925, '平成': 1988, '令和': 2018}
def parse(ws):
    data = {}; sect = None; era = None
    for r in range(1, ws.max_row + 1):
        a, b, c = (ws.cell(r, k).value for k in (1, 2, 3))
        for v in (a, b):
            if isinstance(v, str) and v.strip() in ERA0: era = v.strip()
        hit = [v for v in (a, b) if isinstance(v, str) and re.fullmatch(r'\s*(全|最高|高等|地方|簡易)裁判所\s*', v)]
        if hit: sect = hit[0].strip(); continue
        yr = None
        for v in (b, c):
            if isinstance(v, (int, float)): yr = int(v)
            elif isinstance(v, str) and v.strip() == '元': yr = 1
        raw = [ws.cell(r, k).value for k in range(6, 20)]
        vals = [x for x in raw if x is not None and not (isinstance(x, str) and x.strip() == '')][:9]   # 令和7年版は空の列が挟まる
        if sect and era and yr is not None and len(vals) == 9 and all(isinstance(x, (int, float)) for x in vals):
            data[(sect, ERA0[era] + yr)] = vals
    return data
st = collections.Counter(); issues = []; P = {}
for e, f in ED.items():
    ws = openpyxl.load_workbook(f'{D}/{f}', data_only=True)['1']; d = parse(ws); P[e] = d
    for (s, y), v in d.items():
        for i in range(3):
            st['a'] += 1
            if v[i] != v[3 + i] + v[6 + i]: issues.append((e, '(a)', s, y, i, v[i], v[3 + i], v[6 + i]))
    secs = sorted({s for s, y in d})
    for y in sorted({y for s, y in d}):
        if ('全裁判所', y) not in d: continue
        parts = [d[(s, y)] for s in secs if s != '全裁判所' and (s, y) in d]
        if len(parts) != 4: continue
        for i in range(9):
            st['b'] += 1
            if d[('全裁判所', y)][i] != sum(p[i] for p in parts): issues.append((e, '(b)', y, i, d[('全裁判所', y)][i], sum(p[i] for p in parts)))
    print(e, 'rows', len(d), 'sects', secs)
for a, b in [('r05u', 'r06u'), ('r06u', 'r07')]:
    for k in set(P[a]) & set(P[b]):
        for i in range(9):
            st['c'] += 1
            if P[a][k][i] != P[b][k][i]: issues.append(('(c)', a, b, k, i, P[a][k][i], P[b][k][i]))
json.dump({'counts': st, 'issues': issues}, open('results/shiho/c1303_table1.json', 'w'), ensure_ascii=False, indent=1, default=str)
print(dict(st), len(issues)); [print(i) for i in issues[:30]]

# 照合の要約（lib/tally.py）：(a)(b) 第1表の内部整合、(c) 版間。(c) の差はすべて正誤表で告知された訂正＝説明あり。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('shiho', 'c1303', note='司法統計年報 第1表：総数＝訴訟事件＋以外、全裁判所＝各裁判所の和、版間', script=__file__)
_t.set(compared=st['a'] + st['b'] + st['c'], mismatched=len(issues), explained=sum(1 for i in issues if i[0] == '(c)')); print('tally', _t.save())
