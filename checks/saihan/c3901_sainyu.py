"""c3901 再犯指標の総点検（H011）その1：犯罪白書の「出所受刑者の出所事由別再入率の推移」（5-3-9図 ①2年以内・②5年以内）を、
出典の矯正統計年報 第64表（再入受刑者の前刑出所年及び出所事由別 再入状況、2020〜2025年の年報）から計算し直す。
(a) 白書の表の中：A=B+D、F=G+I、比率=人員/人員（%）
(b) 白書と矯正統計：出所年ごと・出所事由ごとの出所人員と k年以内再入者人員（k=2,5）。k年以内＝出所年を1年目として k年目の年末まで（白書の注4）。
    満期釈放等＝満期釈放＋一部執行猶予の実刑期終了、仮釈放＝仮釈放（一部猶予なし）＋仮釈放（一部猶予あり）。その他（出所事由）は除く（白書の注3）。
(c) 矯正統計の版間：同じ出所年・事由・再入年の人数が、年報の版の間で同じか。
(d) 白書の版間：令和5・6・7年版で、同じ出所年の同じ値が同じか。
使い方: c3901_sainyu.py [root]   出力: results/saihan/c3901.tsv"""
import sys, os, re, glob, unicodedata
from collections import defaultdict
root = sys.argv[1] if len(sys.argv) > 1 else '.'
sys.path.insert(0, os.path.join(root, 'lib'))
from seigo import raw_rows
import openpyxl
out = []; n = 0
JIYU = {'満期釈放': 'man', '仮釈放(一部猶予なし)': 'kari0', '実刑期終了(一部猶予)': 'jikkei', '仮釈放(一部猶予あり)': 'kari1', 'その他': 'other'}

def nf(s): return re.sub(r'\s+', '', unicodedata.normalize('NFKC', str(s)))
def chk(src, where, what, a, b, tol=0):
    global n
    n += 1
    if a is None or b is None or abs(a - b) > tol + 1e-9: out.append((src, where, what, a, b))

def year_of(era, num):
    num = 1 if str(num) in ('元',) else int(float(num))
    return (1988 if era == '平成' else 2018) + num

# ---- 矯正統計 第64表
K = {}   # (yearbook, 出所年, jiyu) -> (出所人員, {再入年: 人数})
for p in sorted(glob.glob(os.path.join(root, 'data/raw/kyosei/20*/*-00-64.xlsx'))):
    yb = int(p.split('/')[-2])
    raw = raw_rows(p)
    hdr = None
    for r in raw:
        cells = [x for x in r if x is not None]
        txt = [nf(x) for x in cells]
        if '計' in txt and any(t.endswith('年') and ('平成' in t or '令和' in t) for t in txt) and hdr is None:
            # 再入年の見出し行：「計」「平成30年」「令和元年」「2」…
            i = txt.index('計'); ys = []; era = None
            for t in txt[i + 1:]:
                m = re.match(r'(平成|令和)(元|\d+)年', t)
                if m: era = m[1]; ys.append(year_of(era, m[2]))
                elif re.fullmatch(r'\d+', t) and era: ys.append(year_of(era, t))
                elif t.startswith('再入率'): break
            hdr = ys
            continue
        if hdr is None: continue
        # データ行：… 年号 年 事由 計/男/女 出所人員 計 再入年… 再入率
        era = next((t for t in txt if t in ('平成', '令和')), None)
        jy = next((JIYU[t] for t in txt if t in JIYU), None)
        if not era or not jy or '計' not in txt: continue
        k = txt.index(era)
        y = year_of(era, txt[k + 1])
        sx = txt[txt.index(next(t for t in txt if t in JIYU)) + 1]
        if sx != '計': continue
        nums = [x for x in cells if isinstance(x, (int, float)) or re.fullmatch(r'-?\d+(\.\d+)?', nf(x))]
        nums = [float(nf(x)) for x in nums if not hasattr(x, 'year')]
        # 先頭の数は年号の数字のことがあるので、出所人員以降を取る：出所人員, 計, 再入年×len(hdr), 再入率
        tail = nums[-(len(hdr) + 3):]
        out_n, tot = tail[0], tail[1]; per = dict(zip(hdr, tail[2:2 + len(hdr)]))
        chk(f'矯正統計{yb}', f'{y}出所 {jy}', '再入 計=再入年の和', tot, sum(per.values()))
        K[(yb, y, jy)] = (out_n, per)

# (c) 矯正統計の版間
by = defaultdict(dict)
for (yb, y, jy), (o, per) in K.items(): by[(y, jy)][yb] = (o, per)
for (y, jy), d in by.items():
    ybs = sorted(d)
    for a, b in zip(ybs, ybs[1:]):
        chk(f'矯正統計{a}→{b}', f'{y}出所 {jy}', '出所人員', d[a][0], d[b][0])
        for ry in d[a][1]:
            if ry in d[b][1]: chk(f'矯正統計{a}→{b}', f'{y}出所 {jy} 再入{ry}', '再入人数', d[a][1][ry], d[b][1][ry])

def kyosei_k(y, k):
    """出所年 y の k年以内（y..y+k-1）を、その年をすべて含む最新の年報で数える。"""
    need = list(range(y, y + k))
    for yb in sorted({yb for (yb, yy, _) in K if yy == y}, reverse=True):
        rec = {jy: K.get((yb, y, jy)) for jy in ('man', 'jikkei', 'kari0', 'kari1')}
        if all(v is not None and all(t in v[1] for t in need) for v in rec.values() if v is not None) and rec['man'] and rec['kari0']:
            g = lambda jy: (rec[jy][0], sum(rec[jy][1][t] for t in need)) if rec[jy] else (0, 0)
            return yb, {jy: g(jy) for jy in rec}
    return None, None

# ---- 犯罪白書 5-3-9図
W = {}
eds = {'令和5年版': '70_20261116T073025Z', '令和6年版': '71_20261116T090659Z', '令和7年版': '72'}
for ed, d in eds.items():
    p = os.path.join(root, f'data/raw/hanzai_hakusho/{d}/zuhyo/5-3-9.xlsx')
    if not os.path.exists(p): out.append((ed, '', '5-3-9図がない', '', '')); continue
    wb = openpyxl.load_workbook(p, data_only=True)
    pick = {}
    for ws in wb.worksheets:
        if '閲覧用' in ws.title: continue
        if '①' in ws.title: pick[2] = ws
        elif '②' in ws.title: pick[5] = ws
    for k, ws in sorted(pick.items()):
        for r in ws.iter_rows(values_only=True):
            c = [x for x in r if x is not None]
            if len(c) < 10: continue
            m = re.fullmatch(r'(\d{4})年', nf(c[1])) if len(c) > 1 else None
            if not m: continue
            y = int(m[1])
            v = [None if (isinstance(x, str) and '…' in x) else float(x) for x in c[2:]]
            # A B C D E F F% G G% H H% I I% J J%
            W[(ed, k, y)] = v
            A, B, C, D, E, F, Fp, G, Gp, H, Hp, I, Ip = v[:13]
            chk(f'犯罪白書{ed}', f'{k}年以内 {y}', 'A=B+D', A, B + D)
            if len(v) >= 15: chk(f'犯罪白書{ed}', f'{k}年以内 {y}', 'F=G+I', F, G + v[11])
            chk(f'犯罪白書{ed}', f'{k}年以内 {y}', '比率F/A', Fp, F / A * 100, 1e-6)
            chk(f'犯罪白書{ed}', f'{k}年以内 {y}', '比率G/B', Gp, G / B * 100, 1e-6)
            yb, kk = kyosei_k(y, k)
            if not kk: continue
            src = f'犯罪白書{ed}×矯正統計{yb}'
            chk(src, f'{k}年以内 {y}', '満期釈放等の出所人員 B', B, kk['man'][0] + kk['jikkei'][0])
            chk(src, f'{k}年以内 {y}', '仮釈放の出所人員 D', D, kk['kari0'][0] + kk['kari1'][0])
            chk(src, f'{k}年以内 {y}', '満期釈放等の再入 G', G, kk['man'][1] + kk['jikkei'][1])
            chk(src, f'{k}年以内 {y}', '仮釈放の再入 I', I, kk['kari0'][1] + kk['kari1'][1])
            if C is not None: chk(src, f'{k}年以内 {y}', '実刑期終了の出所人員 C', C, kk['jikkei'][0])
            if H is not None: chk(src, f'{k}年以内 {y}', '実刑期終了の再入 H', H, kk['jikkei'][1])
# (d) 白書の版間
keys = defaultdict(dict)
for (ed, k, y), v in W.items(): keys[(k, y)][ed] = v
for (k, y), d in sorted(keys.items()):
    e = list(d)
    for a, b in zip(e, e[1:]):
        n += 1
        va = [round(x, 6) if x is not None else None for x in d[a]]; vb = [round(x, 6) if x is not None else None for x in d[b]]
        if va[:len(vb)] != vb[:len(va)]: out.append((f'犯罪白書{a}→{b}', f'{k}年以内 {y}', '同じ出所年の値が版で違う', d[a][:9], d[b][:9]))
os.makedirs(os.path.join(root, 'results/saihan'), exist_ok=True)
with open(os.path.join(root, 'results/saihan/c3901.tsv'), 'w') as fo:
    fo.write('資料\t場所\t式\t値1\t値2\n')
    for o in out: fo.write('\t'.join(map(str, o)) + '\n')
print('矯正統計の行', len(K), '白書の行', len(W), '式の数', n, '不一致', len(out))
for o in out[:40]: print(*o)

# 照合の要約（lib/tally.py）：単位は式（白書の内部整合・矯正統計との照合・版間）。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('saihan', 'c3901', note='犯罪白書 5-3-9図の再入率と矯正統計 第64表、白書の版間', script=__file__)
_t.set(compared=n, mismatched=len(out)); print('tally', _t.save())
