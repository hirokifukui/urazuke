"""c1401: 衛生行政報告例 第1章 精神保健福祉（CSV）の検査。2023〜2025年度。
(a) L1：都道府県（47）の和＝全国（各表・各列）
(b) L1：第2表-1 措置患者の流れ 本年度末＝前年度末＋新規−解除（全国・各都道府県）
(c) L3：年度の連続 第2表-1 の「前年度末患者数」（当年度表）＝前年度の表の「本年度末患者数」（全国・各都道府県）
(d) L1：第5表 精神障害者保健福祉手帳 年度末＝前年度末＋新規＋転入−転出−返還（等級の変更は増減が相殺）
使い方: ~/.venvs/urazuke/bin/python checks/eisei/c1401_seishin_tables.py"""
import sys, glob, csv, io, json, collections, re; sys.path.insert(0, '.')
from lib.pref_blocks import PREF
D = 'data/raw/eisei'; Y = {'r05': 2023, 'r06': 2024, 'r07': 2025}
def load(p):
    b = open(p, 'rb').read()
    for enc in ('cp932', 'utf-8-sig'):
        try: t = b.decode(enc); break
        except UnicodeDecodeError: pass
    rows = list(csv.reader(io.StringIO(t)))
    hdr = [r for r in rows[:12] if r and r[0] == '' and len(r) > 2]
    data = {}
    two = any(len(r) > 1 and r[1] == '全国' for r in rows)   # 第4表・第5表は1列目が区分、2列目が都道府県
    sect0 = None
    for r in rows:
        if two and len(r) > 1 and (r[1] in PREF or r[1] == '全国'):
            if sect0 is None: sect0 = r[0]
            if r[0] != sect0: break              # 最初の区分（総数）だけ
            r = r[1:]
        if r and (r[0] in PREF or r[0] == '全国'):
            if r[0] in data: break   # 指定都市（再掲）の前で止める（同名の重複に備える）
            data[r[0]] = [None if x.strip() in ('', '…', 'x', 'X') else (0 if x.strip() in ('-', '－') else float(x.replace(',', ''))) if re.fullmatch(r'[-－]|[\d,]+(\.\d+)?', x.strip()) else None for x in r[1:]]
    return hdr, data
st = collections.Counter(); issues = []; T = {}
for y in Y:
    for p in sorted(glob.glob(f'{D}/{y}/t*.csv')):
        tid = re.match(r't([\d-]+)_', p.split('/')[-1])[1]
        hdr, d = load(p); T[(y, tid)] = (hdr, d)
        if '全国' not in d or sum(1 for k in d if k in PREF) != 47: issues.append((y, tid, 'shape', len(d))); continue
        for c in range(len(d['全国'])):
            nat = d['全国'][c]
            vs = [d[k][c] if c < len(d[k]) else None for k in PREF]
            if nat is None or any(v is None for v in vs): st['a_skip'] += 1; continue
            hdrc = ' '.join(h[c + 1] for h in hdr if c + 1 < len(h))
            if re.search(r'率|割合|％|%|平均', hdrc): continue
            st['a'] += 1
            if abs(sum(vs) - nat) > 0.5: issues.append((y, tid, '(a)都道府県の和≠全国', c + 1, hdrc[:40], sum(vs), nat))
    hdr, d = T[(y, '2-1')]
    for k, v in d.items():
        st['b'] += 1
        if None not in v[:4] and abs(v[0] + v[1] - v[2] - v[3]) > 0.5: issues.append((y, '2-1', '(b)前年度末+新規−解除≠本年度末', k, v[:4]))
    hdr, d = T[(y, '5')]
    for k, v in d.items():
        st['d'] += 1
        if None not in v[:9] and abs(v[0] + v[1] + v[2] - v[3] - v[4] + v[5] - v[6] - v[7]) > 0.5: issues.append((y, '5', '(d)前年度末+新規+転入−転出−返還≠年度末', k, v[:9]))
for a, b in [('r05', 'r06'), ('r06', 'r07')]:
    da = T[(a, '2-1')][1]; db = T[(b, '2-1')][1]
    for k in db:
        if k in da and da[k][3] is not None and db[k][0] is not None:
            st['c'] += 1
            if abs(da[k][3] - db[k][0]) > 0.5: issues.append(('(c)年度末→翌年度の前年度末', a, b, k, da[k][3], db[k][0]))
# (c') 指定都市（再掲）の年度の連続（R008 の指摘で追加：都道府県の件数に指定都市を混ぜないため、別に数える）
def cities(p):
    b = open(p, 'rb').read().decode('cp932'); rows = list(csv.reader(io.StringIO(b))); out = {}; on = False
    for r in rows:
        if r and r[0].startswith('指定都市'): on = True; continue
        if on and r and r[0].strip() and len(r) > 4:
            try: out[r[0].strip()] = [float(x) if x.strip() not in ('-', '－') else 0.0 for x in r[1:5]]
            except ValueError: pass
    return out
import glob as _g
C = {y: cities(_g.glob(f'{D}/{y}/t2-1_*.csv')[0]) for y in Y}
for a, b in [('r05', 'r06'), ('r06', 'r07')]:
    for k in C[b]:
        if k in C[a]:
            st['c_city'] += 1
            if abs(C[a][k][3] - C[b][k][0]) > 0.5: issues.append(('(c)指定都市 年度末→翌年度の前年度末', a, b, k, C[a][k][3], C[b][k][0]))
n_pref = sum(1 for i in issues if i[0].startswith('(c)年度末') and i[3] != '全国'); n_nat = sum(1 for i in issues if i[0].startswith('(c)年度末') and i[3] == '全国'); n_city = sum(1 for i in issues if i[0].startswith('(c)指定都市'))
st['c_diff_pref'] = n_pref; st['c_diff_national'] = n_nat; st['c_diff_city'] = n_city
json.dump({'counts': st, 'issues': issues}, open('results/eisei/c1401_seishin.json', 'w'), ensure_ascii=False, indent=1)
print(dict(st)); print(len(issues)); [print(i) for i in issues[:40]]

# 照合の要約（lib/tally.py）：(a)(b)(c)(d) の式。(c) の年度末と翌年度の前年度末の違い（ES-I1）は資料どうしの食い違い（説明なし）。表の形が読めないものは読み取りの失敗。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('eisei', 'c1401', note='衛生行政報告例（精神保健福祉）：都道府県の和、措置患者・手帳の年度の連続', script=__file__)
_f = sum(1 for i in issues if len(i) > 2 and i[2] == 'shape')
_t.set(compared=st['a'] + st['b'] + st['c'] + st['d'] + st['c_city'], mismatched=len(issues) - _f, read_failures=_f); print('tally', _t.save())
