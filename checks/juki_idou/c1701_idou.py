"""c1701: 住民基本台帳人口移動報告 2025年 の検査。
(a) L1：表1 各都道府県・国籍区分で 転入超過数＝転入−転出、総数＝男＋女
(b) L1：都道府県の転入の和＝転出の和＝全国の都道府県間移動者数、転入超過の和＝0
(c) L1：表2（移動前の住所地別 都道府県間移動者数）の行の和＝表1の転入者数、移動前の住所地ごとの和＝表1の転出者数
(d) L4：付表（社会増減数、2025hyo2.xlsx）の国内の転入・転出＝表1、社会増加数＝A−B+C−D+E−F の計算
使い方: ~/.venvs/urazuke/bin/python checks/juki_idou/c1701_idou.py"""
import sys, re, json, collections, warnings; sys.path.insert(0, '.'); warnings.filterwarnings('ignore')
import openpyxl
D = 'data/raw/juki_idou/2025'
PREF = '北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 群馬県 埼玉県 千葉県 東京都 神奈川県 新潟県 富山県 石川県 福井県 山梨県 長野県 岐阜県 静岡県 愛知県 三重県 滋賀県 京都府 大阪府 兵庫県 奈良県 和歌山県 鳥取県 島根県 岡山県 広島県 山口県 徳島県 香川県 愛媛県 高知県 福岡県 佐賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県'.split()
st = collections.Counter(); issues = []
ws = openpyxl.load_workbook(f'{D}/t1_000040407038.xlsx', read_only=True, data_only=True).worksheets[0]
T1 = collections.defaultdict(dict)
for r in ws.iter_rows(values_only=True):
    if r and r[0] and str(r[0]).isdigit() and r[5]:
        vals = [x if isinstance(x, (int, float)) else None for x in r[6:18]]
        T1[r[1]][r[5]] = vals
for nat, d in T1.items():
    for k, v in d.items():
        if None in v: continue
        for a in range(4):
            st['a_mf'] += 1
            if v[3 * a] != v[3 * a + 1] + v[3 * a + 2]: issues.append((nat, k, '(a)総数≠男+女', a, v[3 * a:3 * a + 3]))
        for s in range(3):
            st['a_net'] += 1
            if v[9 + s] != v[3 + s] - v[6 + s]: issues.append((nat, k, '(a)転入超過≠転入−転出', s, v[3 + s], v[6 + s], v[9 + s]))
    ps = [k for k in d if k in PREF]
    if len(ps) == 47:
        for s in range(3):
            si = sum(d[k][3 + s] for k in ps); so = sum(d[k][6 + s] for k in ps); sn = sum(d[k][9 + s] for k in ps)
            st['b'] += 3
            if si != so or sn != 0: issues.append((nat, '(b)転入の和・転出の和・転入超過の和', s, si, so, sn))
            if '全国' in d and d['全国'][3 + s] is not None and d['全国'][3 + s] != si: issues.append((nat, '(b)全国の転入≠都道府県の和', s, d['全国'][3 + s], si))
# (c) 表2：行＝移動前の住所地（転出元）、列＝移動後の都道府県（総数・男・女の3列ずつ）
wb2 = openpyxl.load_workbook(f'{D}/t2_000040407039.xlsx', read_only=True, data_only=True); ws2 = wb2.worksheets[0]
rows = [list(r) for r in ws2.iter_rows(values_only=True)]
hp, hs = rows[4], rows[5]
dcols = {str(hp[j]).strip(): j for j in range(len(hp)) if str(hp[j]).strip() in PREF + ['全国'] and str(hs[j]).strip() == '総数'}
M = collections.defaultdict(dict)
for r in rows[7:]:
    if not r or not r[1] or not str(r[1]).isdigit(): continue
    nat, org = r[2], str(r[6]).strip()
    M[nat][org] = {d: (r[j] if isinstance(r[j], (int, float)) else 0) for d, j in dcols.items()}
for nat, d in M.items():
    if nat not in T1: continue
    for org in PREF:
        if org in d and org in T1[nat]:
            st['c_row'] += 1
            if d[org]['全国'] != T1[nat][org][6]: issues.append((nat, org, '(c)表2の全国列（転出）≠表1の転出', d[org]['全国'], T1[nat][org][6]))
            s = sum(v for k, v in d[org].items() if k in PREF)
            st['c_rowsum'] += 1
            if s != d[org]['全国']: issues.append((nat, org, '(c)表2の行の都道府県の和≠全国列', s, d[org]['全国']))
    for dest in PREF:
        s = sum(d[o][dest] for o in PREF if o in d)
        st['c_col'] += 1
        if dest in T1[nat] and s != T1[nat][dest][3]: issues.append((nat, dest, '(c)表2の列の和≠表1の転入', s, T1[nat][dest][3]))
        if '総数' in d and d['総数'][dest] != s: issues.append((nat, dest, '(c)表2の総数行≠列の和', d['総数'][dest], s))
# (d) 付表
ws3 = openpyxl.load_workbook(f'{D}/2025hyo2.xlsx', data_only=True).worksheets[0]
for r in ws3.iter_rows(values_only=True):
    k = str(r[1]).strip() if r[1] else ''
    if k in PREF + ['全国'] and all(isinstance(x, (int, float)) for x in r[2:9]):
        A, B, Cc, Dd, E, F, G = r[2:9]; st['d'] += 1
        if A - B + Cc - Dd + E - F != G: issues.append((k, '(d)社会増加数の計算', A, B, Cc, Dd, E, F, G))
        t = T1.get('移動者', {}).get(k)
        if t and k != '全国' and (A != t[3] or B != t[6]): issues.append((k, '(d)付表の国内転入・転出≠表1', A, B, t[3], t[6]))
json.dump({'counts': st, 'issues': issues}, open('results/juki_idou/c1701_idou.json', 'w'), ensure_ascii=False, indent=1, default=str)
print(dict(st), 'nat', list(T1), 'M', {k: len(v) for k, v in M.items()}); print(len(issues)); [print(i) for i in issues[:30]]

# 照合の要約（lib/tally.py）：単位は式。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('juki_idou', 'c1701', note='住民基本台帳人口移動報告：男女の和、転入超過、行列の和', script=__file__)
_t.set(compared=sum(st.values()), mismatched=len(issues), read_failures=0, explained=None); print('tally', _t.save())
