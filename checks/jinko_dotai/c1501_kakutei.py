"""c1501: 人口動態統計（確定数）統計表 Excel の検査。令和7年（2025）・令和6年（2024）。
(a) L1：第4表 都道府県（47）の和＝全国（各列）、総数＝男＋女（出生・死亡・乳児死亡）
(b) L1：第8表 死因簡単分類 総数＝男＋女（令和7年）
(c) L3：第2表（年次推移）令和7年の表と令和6年の表で、重なる年の値が同じか
(d) L3：第8表 令和7年の表の「令和6年」の列＝令和6年の表の令和6年の値（死因ごと）
(e) 他の資料：第8表の自殺（コード20200）の死亡数と、自殺対策白書（令和8年版）参考資料2-1 の人口動態統計の自殺者数
使い方: ~/.venvs/urazuke/bin/python checks/jinko_dotai/c1501_kakutei.py"""
import sys, re, json, collections, warnings; sys.path.insert(0, '.'); warnings.filterwarnings('ignore')
import openpyxl
D = 'data/raw/jinko_dotai'
W25 = openpyxl.load_workbook(f'{D}/kakutei25/06_hyoR07.xlsx', data_only=True)
W24 = openpyxl.load_workbook(f'{D}/kakutei24/16_hyoR06.xlsx', data_only=True)
PREF = '北海道 青森 岩手 宮城 秋田 山形 福島 茨城 栃木 群馬 埼玉 千葉 東京 神奈川 新潟 富山 石川 福井 山梨 長野 岐阜 静岡 愛知 三重 滋賀 京都 大阪 兵庫 奈良 和歌山 鳥取 島根 岡山 広島 山口 徳島 香川 愛媛 高知 福岡 佐賀 長崎 熊本 大分 宮崎 鹿児島 沖縄'.split()
def n(v):
    if isinstance(v, (int, float)): return float(v)
    if isinstance(v, str) and v.strip() in ('-', '－'): return 0.0
    return None
def nm(v): return re.sub(r'[\s　\d)）]', '', str(v)) if v is not None else ''
st = collections.Counter(); issues = []
for tag, W in [('r07', W25), ('r06', W24)]:
    ws = W['第４表']; rows = {}
    for r in ws.iter_rows(values_only=True):
        k = nm(r[1])
        if k in PREF + ['全国'] and k not in rows: rows[k] = [n(x) for x in r[2:16]]
    if len(rows) != 48: issues.append((tag, '第4表 行数', len(rows))); continue
    for c in range(14):
        vs = [rows[p][c] for p in PREF]
        if rows['全国'][c] is None or None in vs: continue
        st['a_sum'] += 1
        if abs(sum(vs) - rows['全国'][c]) > 0.5: issues.append((tag, '第4表 都道府県の和≠全国', c, sum(vs), rows['全国'][c]))
    for k, v in rows.items():
        for t, a, b in [(0, 1, 2), (3, 4, 5), (6, 7, 8)]:
            if None not in (v[t], v[a], v[b]):
                st['a_mf'] += 1
                if abs(v[t] - v[a] - v[b]) > 0.5: issues.append((tag, '第4表 総数≠男+女', k, t, v[t], v[a], v[b]))
# (b)(d)(e) 第8表
def t8(W, sheets):
    out = {}
    for sh in sheets:
        for r in W[sh].iter_rows(values_only=True):
            code = str(r[1]).strip() if r[1] is not None else ''
            if re.fullmatch(r'\d{5}', code) or (r[2] and '総' in str(r[2]) and code in ('', 'None')):
                key = code if code else '総数'
                if key not in out: out[key] = [n(x) for x in r[3:7]]
    return out
s25 = [s for s in W25.sheetnames if s.startswith('第８表')]; s24 = [s for s in W24.sheetnames if s.startswith('第９表')]
T25 = t8(W25, s25); T24 = t8(W24, s24)
for k, v in T25.items():
    if None not in v[:3]:
        st['b'] += 1
        if abs(v[0] - v[1] - v[2]) > 0.5: issues.append(('r07', '第8表 総数≠男+女', k, v[:3]))
    if k in T24 and v[3] is not None and T24[k][0] is not None:
        st['d'] += 1
        if abs(v[3] - T24[k][0]) > 0.5: issues.append(('第8表 令和6年の列≠令和6年の表', k, v[3], T24[k][0]))
# (c) 第2表 年次推移
def t2(W):
    out = {}
    for sh in [s for s in W.sheetnames if s.startswith('第２表')]:
        ws = W[sh]
        for r in ws.iter_rows(values_only=True):
            y = r[1]
            if isinstance(y, (int, float)) and 1899 <= y <= 2030:
                vals = [n(x) for x in r[3:20]]
                key = (int(y), sh[-1] in '①③' and 'A' or 'B')
                out.setdefault(key, vals)
    return out
A = t2(W25); B = t2(W24)
for k in set(A) & set(B):
    for i, (x, y) in enumerate(zip(A[k], B[k])):
        if x is None or y is None: continue
        st['c'] += 1
        if abs(x - y) > 0.5: issues.append(('第2表 版間', k, i, y, x))
# (e) 自殺：白書の人口動態統計の列
wb = openpyxl.load_workbook('data/raw/jisatsu_hakusho/r2026/sanko2_001760475.xlsx', data_only=True)
hak = {}
for r in wb['参考資料2-1表'].iter_rows(values_only=True):
    m = re.match(r'令和\s*(\d+|元)', str(r[0])) if r[0] else None
    if m: hak[2018 + (1 if m[1] == '元' else int(m[1]))] = r[8]
cmp_e = {'2025': (T25.get('20200', [None])[0], hak.get(2025)), '2024': (T24.get('20200', [None])[0], hak.get(2024))}
st['e'] = len(cmp_e)
for y, (a, b) in cmp_e.items():
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) > 0.5: issues.append(('自殺 人口動態確定数≠白書2-1の人口動態', y, a, b))
json.dump({'counts': st, 'issues': issues, 'jisatsu_compare': cmp_e}, open('results/jinko_dotai/c1501_kakutei.json', 'w'), ensure_ascii=False, indent=1, default=str)
print(dict(st)); print('jisatsu', cmp_e); print(len(issues)); [print(i) for i in issues[:30]]

# 照合の要約（lib/tally.py）：単位は式。第4表の都道府県の和＜全国は、第5表の注（全国には住所が外国・不詳を含む）で説明あり。(e) 自殺統計との並置は定義が違うため数えない。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('jinko_dotai', 'c1501', note='人口動態統計 確定数：男女の和、都道府県の和、死因の和、自殺統計との並置', script=__file__)
_t.set(compared=sum(v for k, v in st.items() if k != "e"), mismatched=len(issues), read_failures=0, explained=sum(1 for i in issues if '都道府県の和' in str(i[1]))); print('tally', _t.save())
