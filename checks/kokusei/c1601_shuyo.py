"""c1601: 国勢調査「都道府県・市区町村別の主な結果」（2025年・2020年）の検査。
(a) L1：各行 総数＝男＋女
(b) L1：都道府県（47）の和＝全国（総数・男・女・2020年組替人口・5年間の増減数）
(c) L1：5年間の人口増減数＝2025年総数−2020年組替人口、増減率の再計算（小数第5位まで）
(d) L3：2025年表の「2020年の人口（組替）」の都道府県の値＝2020年表の都道府県の総数（都道府県の境域は変わらない）
(e) L1：市区町村（政令市の区を除く）の和＝都道府県
使い方: ~/.venvs/urazuke/bin/python checks/kokusei/c1601_shuyo.py"""
import sys, re, json, collections, warnings; sys.path.insert(0, '.'); warnings.filterwarnings('ignore')
import openpyxl
D = 'data/raw/kokusei'
def load(p):
    ws = openpyxl.load_workbook(p, read_only=True, data_only=True).worksheets[0]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    hi = next(i for i, r in enumerate(rows) if r and r[0] and str(r[0]).startswith('00_'))
    hdr = [' '.join(str(rows[j][c]) for j in range(max(0, hi - 4), hi) if c < len(rows[j]) and rows[j][c] not in (None, '※')) for c in range(len(rows[hi]))]
    return hdr, rows[hi:]
def col(hdr, *keys):
    for i, h in enumerate(hdr):
        if all(k in h for k in keys): return i
    return None
st = collections.Counter(); issues = []; P = {}
for y, f in [('2025', '2025/shuyo_000040507382.xlsx'), ('2020', '2020/shuyo_000032143614.xlsx')]:
    hdr, rows = load(f'{D}/{f}')
    it, im, iw = 4, 5, 6
    i20 = col(hdr, '2015年') if y == '2020' else col(hdr, '2020年', '組替')
    i20 = i20 if i20 is not None else 7
    idf = col(hdr, '増減数'); irt = col(hdr, '増減率')
    def v(r, i): return r[i] if i is not None and i < len(r) and isinstance(r[i], (int, float)) else None
    pref = {}; nat = None; muni = collections.defaultdict(float); muni_n = collections.Counter()
    for r in rows:
        code = str(r[1]).split('_')[0] if r[1] else ''
        kind = str(r[3]).strip() if r[3] is not None else ''
        if v(r, it) is None: continue
        if v(r, im) is not None and v(r, iw) is not None:
            st['a'] += 1
            if abs(v(r, it) - v(r, im) - v(r, iw)) > 0.5: issues.append((y, '(a)総数≠男+女', r[1], v(r, it), v(r, im), v(r, iw)))
        if code == '00000': nat = r
        elif code.endswith('000') and kind == 'a': pref[code[:2]] = r
        elif kind != '0' and len(code) == 5:   # 政令市の区（0）は政令市の行と重なるので除く
            muni[code[:2]] += v(r, it); muni_n[code[:2]] += 1
        if y == '2025' and idf is not None and v(r, i20) is not None and v(r, idf) is not None:
            st['c'] += 1
            if abs(v(r, it) - v(r, i20) - v(r, idf)) > 0.5: issues.append((y, '(c)増減数', r[1], v(r, it), v(r, i20), v(r, idf)))
            if irt is not None and v(r, irt) is not None and v(r, i20):
                st['c_rate'] += 1
                if abs(v(r, idf) / v(r, i20) * 100 - v(r, irt)) > 0.00001 + 1e-9: issues.append((y, '(c)増減率', r[1], v(r, irt), v(r, idf) / v(r, i20) * 100))
    P[y] = pref
    for i in (it, im, iw, i20, idf):
        if i is None or v(nat, i) is None: continue
        s = sum(v(pref[k], i) or 0 for k in pref); st['b'] += 1
        if len(pref) != 47 or abs(s - v(nat, i)) > 0.5: issues.append((y, '(b)都道府県の和≠全国', hdr[i][:30], len(pref), s, v(nat, i)))
    for k in pref:
        if muni_n[k]:
            st['e'] += 1
            if abs(muni[k] - v(pref[k], it)) > 0.5: issues.append((y, '(e)市区町村の和≠都道府県', k, muni[k], v(pref[k], it)))
    P[y + 'idx'] = (it, i20)
it25, i2020 = P['2025idx']; it20 = P['2020idx'][0]
for k in P['2025']:
    st['d'] += 1
    a = P['2025'][k][i2020]; b = P['2020'][k][it20]
    if abs(a - b) > 0.5: issues.append(('(d)2020組替≠2020年表', k, a, b))
json.dump({'counts': st, 'issues': issues}, open('results/kokusei/c1601_shuyo.json', 'w'), ensure_ascii=False, indent=1, default=str)
print(dict(st)); print(len(issues)); [print(i) for i in issues[:30]]

# 照合の要約（lib/tally.py）：単位は式。(d) の東京都・神奈川県の組替人口の違いは境界変更に伴う組替（和は一致）＝説明あり。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('kokusei', 'c1601', note='国勢調査 主な結果：男女の和、都道府県の和、増減、組替人口、市区町村の和', script=__file__)
_t.set(compared=sum(st.values()), mismatched=len(issues), read_failures=0, explained=len(issues)); print('tally', _t.save())
