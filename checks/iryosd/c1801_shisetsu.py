"""c1801: 医療施設（動態）調査 統計表 Excel の検査。令和7年（2025、2026-11-10 再計算後）・令和6年（2024）。
(a) L1：統計表10 都道府県（47）の和＝全国（病床数の各列）、病院の病床＝精神＋感染症＋結核＋療養＋一般
(b) L5：統計表10 人口10万対病床数を、国勢調査2025年 人口等基本集計の都道府県人口で再計算（小数第1位で一致するか）。統計表9（施設数）も同じ
(c) L3：統計表1（年次推移）令和7年版と令和6年版の重なる年
使い方: ~/.venvs/urazuke/bin/python checks/iryosd/c1801_shisetsu.py"""
import sys, re, json, collections, warnings, decimal; sys.path.insert(0, '.'); warnings.filterwarnings('ignore')
import openpyxl
D = 'data/raw/iryosd'
PREF = '北海道 青森 岩手 宮城 秋田 山形 福島 茨城 栃木 群馬 埼玉 千葉 東京 神奈川 新潟 富山 石川 福井 山梨 長野 岐阜 静岡 愛知 三重 滋賀 京都 大阪 兵庫 奈良 和歌山 鳥取 島根 岡山 広島 山口 徳島 香川 愛媛 高知 福岡 佐賀 長崎 熊本 大分 宮崎 鹿児島 沖縄'.split()
def nm(x): return re.sub(r'[\s　]', '', str(x)) if x is not None else ''
def rnd(x, d=1): return float(decimal.Decimal(str(x)).quantize(decimal.Decimal('0.1') if d == 1 else decimal.Decimal('1'), rounding=decimal.ROUND_HALF_UP))
st = collections.Counter(); issues = []
# 国勢調査 2025 都道府県人口
ws = openpyxl.load_workbook('data/raw/kokusei/2025/shuyo_000040507382.xlsx', read_only=True, data_only=True).worksheets[0]
POP = {}
for r in ws.iter_rows(values_only=True):
    if r[1] and re.fullmatch(r'\d\d000_.*', str(r[1])) and str(r[3]).strip() == 'a':
        name = str(r[1]).split('_')[1]; name = name if name == '北海道' else re.sub(r'[都府県]$', '', name)
        POP[name] = r[4]
    if r[1] and str(r[1]).startswith('00000'): POP['全国'] = r[4]
def table(W, sh, ncount, nrate):
    out = {}
    for r in W[sh].iter_rows(values_only=True):
        k = nm(r[2])
        if k in PREF + ['全国'] and k not in out:
            z = lambda x: 0 if isinstance(x, str) and x.strip() in ('-', '－') else x
            out[k] = ([z(x) for x in r[4:4 + ncount]], [z(x) for x in r[4 + ncount:4 + ncount + nrate]])
    return out
W25 = openpyxl.load_workbook(f'{D}/2025/07sisetutoukei07.xlsx', data_only=True)
W24 = openpyxl.load_workbook(f'{D}/2024/07sisetutoukei06.xlsx', data_only=True)
for tag, W in [('r07', W25), ('r06', W24)]:
    T = table(W, '統計表10', 7, 7)
    if len(T) != 48: issues.append((tag, '統計表10 行数', len(T))); continue
    for c in range(7):
        s = sum(T[p][0][c] for p in PREF); st['a_sum'] += 1
        if s != T['全国'][0][c]: issues.append((tag, '(a)都道府県の和≠全国', c, s, T['全国'][0][c]))
    for k, (cnt, rate) in T.items():
        st['a_bed'] += 1
        if cnt[0] != sum(cnt[1:6]): issues.append((tag, '(a)病院の病床≠種類の和', k, cnt[0], sum(cnt[1:6])))
        if tag == 'r07' and k in POP:
            for c in range(7):
                if isinstance(cnt[c], (int, float)) and isinstance(rate[c], (int, float)):
                    st['b10'] += 1
                    calc = rnd(cnt[c] / POP[k] * 1e5)
                    if abs(calc - rate[c]) > 0.051: issues.append((tag, '(b)統計表10 人口10万対の再計算', k, c, cnt[c], POP[k], rate[c], calc))
    if tag == 'r07':
        T9 = {}
        for r in W['統計表９'].iter_rows(values_only=True):
            k = nm(r[2])
            if k in PREF + ['全国'] and k not in T9: T9[k] = list(r[4:16])
        ncol = sum(1 for x in T9.get('全国', []) if isinstance(x, (int, float)))
        half = ncol // 2
        for k, v in T9.items():
            vv = [x for x in v if isinstance(x, (int, float))]
            if k not in POP or len(vv) != ncol: continue
            for c in range(half):
                st['b9'] += 1
                calc = rnd(vv[c] / POP[k] * 1e5)
                if abs(calc - vv[half + c]) > 0.051: issues.append((tag, '(b)統計表9 人口10万対の再計算', k, c, vv[c], POP[k], vv[half + c], calc))
# (c) 統計表1 年次推移
def t1(W):
    out = {}
    for r in W['統計表１'].iter_rows(values_only=True):
        lab = ''.join(nm(x) for x in r[:4] if x is not None)
        m = re.search(r'(\d{4})', lab)
        vals = [x for x in r[4:] if isinstance(x, (int, float))]
        if m and len(vals) >= 5: out.setdefault(int(m[1]), vals)
    return out
A, B = t1(W25), t1(W24)
for y in set(A) & set(B):
    for i, (x, z) in enumerate(zip(A[y], B[y])):
        st['c'] += 1
        if abs(x - z) > 1e-9: issues.append(('(c)統計表1 版間', y, i, z, x))
json.dump({'counts': st, 'issues': issues}, open('results/iryosd/c1801_shisetsu.json', 'w'), ensure_ascii=False, indent=1, default=str)
print(dict(st), 'pop', len(POP)); print(len(issues)); [print(i) for i in issues[:30]]

# 照合の要約（lib/tally.py）：単位は式。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('iryosd', 'c1801', note='医療施設調査：施設数・病床数の和、表どうし', script=__file__)
_t.set(compared=sum(st.values()), mismatched=len(issues), read_failures=0, explained=None); print('tally', _t.save())
