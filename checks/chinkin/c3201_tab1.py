"""c3201 賃金構造基本統計調査 概況（令和7年・令和6年）第1表「性別賃金、対前年増減率及び男女間賃金格差の推移」。
(a) 男女間賃金格差 = 女/男×100（小数1位、±0.11）
(b) 対前年増減率 = 当年/前年−1（表の賃金は千円・小数1位で丸めてあるため ±0.15。令和2年は注2の※令和元年（新方式）を前年とする）
(c) 格差の対前年差 = 当年の格差 − 前年の格差（±0.11）
(d) 版間：令和6年版と令和7年版の同じ年の行が同じか
(e) 形式間：概況 PDF の第1表の行に、Excel の値が並んでいるか
使い方: c3201_tab1.py [root]   出力: results/chinkin/c3201.tsv"""
import sys, os, re, subprocess, unicodedata, openpyxl
root = sys.argv[1] if len(sys.argv) > 1 else '.'
D = os.path.join(root, 'data/raw/chinkin')
out = []; n = 0

def chk(ed, where, what, a, b, tol):
    global n
    n += 1
    if abs(a - b) > tol + 1e-9: out.append((ed, where, what, a, round(b, 2)))

def tab1(ed):
    ws = openpyxl.load_workbook(f'{D}/{ed}/zuhyo.xlsx', data_only=True)['第１表']
    rows = {}
    for r in ws.iter_rows(values_only=True):
        cells = [x for x in r if x is not None and str(x).strip() != '']
        yr = next((int(x) for x in cells if isinstance(x, (int, float)) and 1990 < x < 2100 and float(x).is_integer()), None)
        if not yr: continue
        lab = ''.join(str(x) for x in cells[:3])
        key = f'{yr}新方式' if '※' in lab else str(yr)
        i = cells.index(next(x for x in cells if isinstance(x, (int, float)) and x == yr))
        vals = cells[i + 1:]
        vals = [v for v in vals if not (isinstance(v, str) and v.strip() in ('年', '年2)'))]
        rows[key] = [None if (isinstance(v, str) and '…' in v) else round(float(v), 6) for v in vals[:8]]
    return rows

T = {}
for ed in ('2024', '2025'):
    t = tab1(ed); T[ed] = t
    keys = list(t.keys())
    for k in keys:
        a, ra, m, rm, f, rf, gap, dgap = t[k]
        chk(ed, k, '格差=女/男×100', gap, f / m * 100, 0.11)
    for k in keys:
        if not k.isdigit(): continue
        y = int(k)
        prev = t.get('2019新方式') if y == 2020 else t.get(str(y - 1))
        if not prev: continue
        cur = t[k]
        for j, nm in ((0, '男女計'), (2, '男'), (4, '女')):
            if cur[j + 1] is not None: chk(ed, k, f'{nm} 対前年増減率', cur[j + 1], (cur[j] / prev[j] - 1) * 100, 0.15)
        if cur[7] is not None: chk(ed, k, '格差の対前年差', cur[7], cur[6] - prev[6], 0.11)
    # (e) PDF
    txt = unicodedata.normalize('NFKC', subprocess.run(['pdftotext', '-layout', f'{D}/{ed}/gaikyo.pdf', '-'], capture_output=True, text=True).stdout)
    for k, v in t.items():
        if not k.isdigit() or int(k) < 2015: continue
        line = next((l for l in txt.split('\n') if re.search(rf'\(?{k}\)?', l) and '…' not in l and re.search(r'\d{3}\.\d', l)), None)
        n_ok = 0
        if line:
            toks = re.findall(r'-?△?▲?\d+\.\d|-?\d+', line.replace('△', '-').replace('▲', '-'))
            for x in v:
                if x is None: continue
                n_ok += any(abs(float(tk) - x) < 1e-6 for tk in toks if re.fullmatch(r'-?\d+(\.\d)?', tk))
        n += 1
        if not line or n_ok < 6: out.append((ed, k, 'PDFの第1表の行にExcelの値がそろわない', n_ok, (line or '')[:80]))
for k in T['2024']:
    if k in T['2025']:
        n += 1
        if T['2024'][k] != T['2025'][k]: out.append(('版間', k, '令和6年版≠令和7年版', T['2024'][k], T['2025'][k]))
os.makedirs(os.path.join(root, 'results/chinkin'), exist_ok=True)
with open(os.path.join(root, 'results/chinkin/c3201.tsv'), 'w') as f:
    f.write('版\t年\t式\t表の値\t計算値\n')
    for o in out: f.write('\t'.join(map(str, o)) + '\n')
print('式の数', n, '不一致', len(out), {e: len(T[e]) for e in T})
for o in out: print(*o)

# 照合の要約（lib/tally.py）：単位は式。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('chinkin', 'c3201', note='賃金構造基本統計調査 第1表：格差・増減率の再計算、版間、形式間', script=__file__)
_t.set(compared=n, mismatched=len(out), read_failures=0, explained=None); print('tally', _t.save())
