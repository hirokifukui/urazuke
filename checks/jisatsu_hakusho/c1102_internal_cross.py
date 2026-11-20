"""c1102: 自殺対策白書の内部整合（L1）・形式間（L4）・他の資料との突き合わせ。
(a) 参考資料2：2-1 総数＝男＋女（自殺統計・人口動態統計）、2-14 合計＝男＋女、2-15 合計＝小＋中＋高
(b) 2-13 都道府県の和＝2-1 の自殺統計の総数（各年）
(c) 2-13 の直近3年＝「地域における自殺の基礎資料」B6（発見日・発見地）の各都道府県
(d) 本文 図表1-25（PDF、令和7・8年版）の自殺者数・前年差＝2-13／B6、自殺死亡率＝「自殺の状況」図表4-4 の率と比べる
使い方: ~/.venvs/urazuke/bin/python checks/jisatsu_hakusho/c1102_internal_cross.py"""
import sys, re, glob, json, collections; sys.path.insert(0, '.')
import openpyxl
from lib.xls import read_sheets
D = 'data/raw/jisatsu_hakusho'; K = 'data/raw/jisatsu/kiso'; J = 'data/raw/jisatsu/joukyou'
ED = {'r2026': f'{D}/r2026/sanko2_001760475.xlsx', 'r2025': f'{D}/r2025/sanko2_001593171.xlsx', 'r2024': f'{D}/r2024/sanko2_001332662.xlsx'}
st = collections.Counter(); issues = []; notes = []
def g(ws): return [list(r) for r in ws.iter_rows(values_only=True)]
def isn(v): return isinstance(v, (int, float))
PREFS = '北海道 青森 岩手 宮城 秋田 山形 福島 茨城 栃木 群馬 埼玉 千葉 東京 神奈川 新潟 富山 石川 福井 山梨 長野 岐阜 静岡 愛知 三重 滋賀 京都 大阪 兵庫 奈良 和歌山 鳥取 島根 岡山 広島 山口 徳島 香川 愛媛 高知 福岡 佐賀 長崎 熊本 大分 宮崎 鹿児島 沖縄'.split()
def era(lab):
    lab = str(lab).replace('元', '1')
    m = re.match(r'(昭和|平成|令和)\s*(\d+)', lab)
    if not m: return None
    return {'昭和': 1925, '平成': 1988, '令和': 2018}[m[1]] + int(m[2])
S13 = {}
for ed, p in ED.items():
    wb = openpyxl.load_workbook(p, data_only=True); sh = {re.sub(r'\s', '', w.title.replace('２', '2')): g(w) for w in wb.worksheets}
    t1 = {}
    for r in sh['参考資料2-1表']:
        y = era(r[0]) if r[0] else None
        if y and isn(r[2]):
            t1[y] = r[2]
            for a, b, c in [(2, 3, 4), (8, 9, 10)]:
                if isn(r[a]) and isn(r[b]) and isn(r[c]):
                    st['a_2-1'] += 1
                    if abs(r[a] - r[b] - r[c]) > 0.5: issues.append((ed, '2-1 総数≠男+女', y, r[a], r[b], r[c]))
    started = False
    for r in sh['参考資料2-14表']:
        if r[0] and era(r[0]) and all(isn(x) for x in r[1:4]): started = True
        elif started: break
        if r[0] and era(r[0]) and all(isn(x) for x in r[1:4]):
            st['a_2-14'] += 1
            if abs(r[1] - r[2] - r[3]) > 0.5: issues.append((ed, '2-14 合計≠男+女', r[0], r[1:4]))
    for r in sh['参考資料2-15表']:
        if r[0] and era(r[0]) and all(isn(x) for x in r[1:5]):
            st['a_2-15'] += 1
            if abs(r[1] - r[2] - r[3] - r[4]) > 0.5: issues.append((ed, '2-15 合計≠小+中+高', r[0], r[1:5]))
    rows = sh['参考資料2-13表']; hdr = None; s13 = {}
    for r in rows:
        if r[1] == '北海道': hdr = [str(x).strip() if x else '' for x in r]; continue
        if hdr and r[0] and era(r[0]) and isn(r[1]):
            y = era(r[0]); vals = {hdr[i]: r[i] for i in range(1, len(r)) if i < len(hdr) and hdr[i] in PREFS and isn(r[i])}
            if len(vals) == 47 and y not in s13 and all(float(v).is_integer() for v in vals.values()):
                s13[y] = vals; st['b'] += 1
                tot = sum(vals.values())
                if y in t1 and abs(tot - t1[y]) > 0.5: issues.append((ed, '2-13 都道府県の和≠2-1 総数', y, tot, t1[y]))
    S13[ed] = s13
    last_rate = max(era(r[0]) for r in rows if r[0] and era(r[0]))
    if max(s13) != last_rate: issues.append((ed, '2-13 (1)自殺者数の最終年≠(2)自殺死亡率の最終年', max(s13), last_rate))
# (c) 基礎資料 B6
KISO = {2023: 'r05_hakkenbi_001236400', 2024: 'r06_hakkenbi_001464823', 2025: 'r07_hakkenbi_001680832'}
B6 = {}
for y, dn in KISO.items():
    S = read_sheets(glob.glob(f'{K}/{dn}/*_B6表*.xls')[0]); s = S[list(S)[0]]; d = {}
    for r in range(9, 80):
        if isinstance(s.get((r, 2)), float):
            nm = re.sub(r'\s', '', str(s.get((r, 3))))
            nm = nm.replace('県', '').replace('府', '') if nm not in ('北海道',) else nm
            nm = '東京' if nm.startswith('東京') else nm
            d[nm] = (s.get((r, 4)), s.get((r, 5)))
    B6[y] = d
for ed, s13 in S13.items():
    for y in KISO:
        if y not in s13: continue
        for p in PREFS:
            st['c'] += 1
            if p not in B6[y]: issues.append((ed, 'B6 に名なし', y, p)); continue
            if abs(s13[y][p] - B6[y][p][0]) > 0.5: issues.append((ed, '2-13≠B6', y, p, s13[y][p], B6[y][p][0]))
# (d) 図表1-25（PDF）
def p125(path):
    out = {}
    for l in open(path, encoding='utf-8', errors='replace'):
        m = re.search(r'(?:^|\s)([\d,]+)\s*[（(]\s*([－＋±+\-]?\s*[\d,]+)\s*[）)]\s*(\S+?[都道府県])\s+([\d.]+)\s*[（(]\s*([－＋±+\-]?\s*[\d.]+)\s*[）)]', l)
        if m:
            nm = m[3]; nm = nm if nm == '北海道' else re.sub(r'[都府県]$', '', nm)
            out[nm] = (float(m[1].replace(',', '')), m[2].replace(' ', ''), float(m[4]), m[5].replace(' ', ''))
    return out
def dnum(s): return float(s.replace('＋', '+').replace('－', '-').replace('±', '').replace(',', ''))
REP = {2025: f'{J}/r07_honbun_001680736.txt', 2024: f'{J}/r06_honbun_001464717.txt'}
def parse44(path):
    t = open(path, encoding='utf-8').read().split('\n'); d = {}
    i = [k for k, l in enumerate(t) if '都道府県別自殺者数及び自殺死亡率' in l and '・・' not in l][-1]
    for l in t[i:i + 80]:
        m = re.match(r'^\s*([^\d\s\-+][^\d\-+]*?)\s+([\d,]+)\s+([\d.]+)\s+([\d,]+)\s+([\d.]+)\s+([-+]\s*[\d,]+|±?0)\s+([-+]\s*[\d.]+|±?0\.0|0\.0)\s*$', l)
        if m:
            nm = re.sub(r'\s', '', m[1]); nm = nm if nm == '北海道' else re.sub(r'[都府県]$', '', nm)
            d[nm] = (float(m[2].replace(',', '')), float(m[3]), float(m[4].replace(',', '')), float(m[5]))
    return d
rates = []
for ed, f, y in [('r2026', '001760196', 2025), ('r2025', '001581169', 2024)]:
    P = p125(f'{D}/{ed}/{f}.txt'); st['d_rows_' + ed] = len(P)
    R44 = parse44(REP[y])
    for p in PREFS:
        if p not in P: issues.append((ed, '1-25 読めず', p)); continue
        if p in S13[ed].get(y, {}) and abs(P[p][0] - S13[ed][y][p]) > 0.5: issues.append((ed, '1-25≠2-13', p))
        c, dc, r, dr = P[p]; st['d'] += 1
        if abs(c - B6[y][p][0]) > 0.5: issues.append((ed, '1-25 数≠B6', p, c, B6[y][p][0]))
        if abs((c - dnum(dc)) - B6[y - 1][p][0]) > 0.5: issues.append((ed, '1-25 前年差≠B6前年', p, c, dc, B6[y - 1][p][0]))
        if p in R44:
            rates.append((ed, p, c, r, R44[p][1], round(B6[y][p][1], 2) if isinstance(B6[y][p][1], float) else '', round(c / r * 1e5), round(c / R44[p][1] * 1e5)))
            if abs(r - R44[p][1]) > 0.05: st['d_rate_diff_' + ed] += 1
            # 前年の率：今年の白書の（前年差）から前年率＝r−dr
            st['d_rate_cmp'] += 1
open('results/jisatsu_hakusho/c1102_rates.tsv', 'w').write('ed\tpref\tcount\thakusho_rate\tjoukyou_rate\tkiso_rate\timplied_pop_hakusho\timplied_pop_joukyou\n' + ''.join('\t'.join(map(str, r)) + '\n' for r in rates))
json.dump({'counts': st, 'issues': issues}, open('results/jisatsu_hakusho/c1102_internal_cross.json', 'w'), ensure_ascii=False, indent=1, default=str)
print(dict(st)); print(len(issues), 'issues', collections.Counter(i[1] for i in issues)); [print(i) for i in issues[:40]]

# 照合の要約（lib/tally.py）：(a)(b)(c)(d) の式と、図表1-25 の率と「自殺の状況」の率。率の違いは割る人口の違い（白書は人口推計と明記）＝説明あり。
# 2-13表（1）の最終年が（2）より1年前で終わる1件は資料どうしの食い違い（説明なし）。読めない行は読み取りの失敗。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('jisatsu_hakusho', 'c1102', note='自殺対策白書：参考資料の内部整合、基礎資料・本文との照合', script=__file__)
_rd = sum(v for k, v in st.items() if k.startswith('d_rate_diff_'))
_f = sum(1 for i in issues if '読めず' in str(i[1]))
_t.set(compared=sum(st[k] for k in ('a_2-1', 'a_2-14', 'a_2-15', 'b', 'c', 'd', 'd_rate_cmp')), mismatched=len(issues) - _f + _rd, read_failures=_f, explained=_rd); print('tally', _t.save())
