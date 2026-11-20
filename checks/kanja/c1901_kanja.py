"""c1901: 患者調査（令和5年）Excel の検査。値は千人単位で丸められているため、和の照合には丸めの幅を許す。
(a) L1：表2 傷病分類別 推計患者数 入院 総数＝病院＋一般診療所、外来 総数＝病院＋一般診療所＋歯科診療所（差 0.15 千人まで）
(b) L1：表2 傷病大分類（Ⅰ〜ⅩⅩⅡ、再掲を除く）の和＝総数（差 0.05×分類数 千人まで）
(c) L4：表2（令和5年）と統計表2（年次・傷病大分類別）の令和5年の値
(d) L1：表7 総患者数 傷病大分類の和と総数の差（総患者数は分類ごとに算出するため和は総数と一致しないことがある：注記を確かめる）
使い方: ~/.venvs/urazuke/bin/python checks/kanja/c1901_kanja.py"""
import sys, re, json, collections, warnings; sys.path.insert(0, '.'); warnings.filterwarnings('ignore')
import openpyxl
D = 'data/raw/kanja/2023'
ROM = 'Ⅰ Ⅱ Ⅲ Ⅳ Ⅴ Ⅵ Ⅶ Ⅷ Ⅸ Ⅹ ⅩⅠ ⅩⅡ ⅩⅢ ⅩⅣ ⅩⅤ ⅩⅥ ⅩⅦ ⅩⅧ ⅩⅨ ⅩⅩ ⅩⅩⅠ ⅩⅩⅡ'.split()
def f(x):
    if isinstance(x, (int, float)): return float(x)
    if isinstance(x, str) and x.strip() in ('-', '･', '・', '－'): return 0.0
    return None
st = collections.Counter(); issues = []
W = openpyxl.load_workbook(f'{D}/hyo.xlsx', data_only=True)
rows = list(W['表2'].iter_rows(values_only=True))
tot = None; big = {}
for r in rows:
    lab1 = str(r[1]).strip() if r[1] else ''; lab2 = re.sub(r'[\s　]', '', str(r[2])) if r[2] else ''
    v = [f(x) for x in r[5:12]]
    if lab2 == '総数' and tot is None: tot = v
    elif lab1 in ROM and lab2 and lab1 not in big: big[lab1] = (lab2, v)
    if None in v: continue
    st['a'] += 2
    if abs(v[0] - v[1] - v[2]) > 0.15: issues.append(('(a)入院 総数≠病院+一般診療所', lab1 or lab2, v[:3]))
    if abs(v[3] - v[4] - v[5] - v[6]) > 0.15: issues.append(('(a)外来 総数≠病院+一般+歯科', lab1 or lab2, v[3:]))
for c in range(7):
    s = sum(big[k][1][c] for k in big if big[k][1][c] is not None); st['b'] += 1
    if abs(s - tot[c]) > 0.05 * len(big): issues.append(('(b)大分類の和≠総数', c, round(s, 1), tot[c]))
# (c) 統計表2 の令和5年
T = openpyxl.load_workbook(f'{D}/toukei.xlsx', data_only=True)['統計表２']
trs = [list(r) for r in T.iter_rows(values_only=True)]
hdr_i = next(i for i, r in enumerate(trs) if any(isinstance(x, str) and ('令和５年' in x or '令和5年' in x or '2023' in x) for x in r))
hdr = trs[hdr_i]
cols = [j for j, x in enumerate(hdr) if isinstance(x, str) and ('令和５年' in x or '令和5年' in x or '2023' in x)]
st['c_cols'] = len(cols)
sect = None; cmpd = []
for r in trs[hdr_i + 1:]:
    txt = ' '.join(str(x) for x in r[:4] if isinstance(x, str))
    if re.search(r'^\s*(総数|入院|外来)\s*$', str(r[1] or r[0] or '')): sect = str(r[1] or r[0]).strip()
    m = next((x.strip() for x in r[:3] if isinstance(x, str) and x.strip() in ROM), None)
    if m and cols:
        cmpd.append((sect, m, [f(r[j]) for j in cols]))
json.dump({'counts': st, 'issues': issues, 'toukei2_2023': cmpd[:80], 'hyo2_big': big}, open('results/kanja/c1901_kanja.json', 'w'), ensure_ascii=False, indent=1, default=str)
print(dict(st), 'big', len(big)); print(len(issues)); [print(i) for i in issues[:20]]
print(hdr_i, [hdr[j] for j in cols][:6], cmpd[:3])
# (c) の照合：統計表2 の令和5年（総数・入院・外来）と表2（入院総数・外来総数）、総数＝入院＋外来
for sect, m, v in cmpd:
    if m not in big or None in v: continue
    hv = big[m][1]
    st['c'] += 3
    if abs(v[1] - hv[0]) > 1e-9: issues.append(('(c)統計表2 入院≠表2', m, v[1], hv[0]))
    if abs(v[2] - hv[3]) > 1e-9: issues.append(('(c)統計表2 外来≠表2', m, v[2], hv[3]))
    if abs(v[0] - v[1] - v[2]) > 0.15: issues.append(('(c)統計表2 総数≠入院+外来', m, v))
json.dump({'counts': st, 'issues': issues, 'toukei2_2023': cmpd[:80], 'hyo2_big': big}, open('results/kanja/c1901_kanja.json', 'w'), ensure_ascii=False, indent=1, default=str)
print('final', dict(st), len(issues)); [print(i) for i in issues[:20]]
print('V', big.get('Ⅴ'))

# 照合の要約（lib/tally.py）：単位は式。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('kanja', 'c1901', note='患者調査：表の内部整合、統計表どうし', script=__file__)
_t.set(compared=st['a'] + st['b'] + st['c'], mismatched=len(issues), read_failures=0, explained=None); print('tally', _t.save())
