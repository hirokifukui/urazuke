"""再犯防止推進白書 指標7「保護観察終了時に無職である者」の表の保護観察終了者（総数）・無職である者を、
保護統計年報 表38「保護観察終了者の終了事由・終了時状況別 職業」の総数行と比べる（e-Stat の現行ファイル）。"""
import glob, io, re, openpyxl, xlrd
def rows(f):
    b = open(f,'rb').read()
    if b[:2]==b'PK': return [list(r) for r in openpyxl.load_workbook(io.BytesIO(b),data_only=True).worksheets[0].iter_rows(values_only=True)]
    s = xlrd.open_workbook(file_contents=b).sheet_by_index(0); return [s.row_values(i) for i in range(s.nrows)]
st = {}
for f in sorted(glob.glob('data/raw/hogo_toukei/hogo38/*.xls')):
    y = int(re.search(r'/(\d{4})_', f).group(1)); R = rows(f)
    hdr = [' '.join(str(R[i][j]) for i in range(min(8, len(R))) if j < len(R[i]) and R[i][j] not in (None, '')) for j in range(max(len(r) for r in R[:8]))]
    jm = [j for j, h in enumerate(hdr) if re.sub(r'\s', '', h).endswith('無職') or re.sub(r'\s','',h) in ('無職', '無　職')]
    jt = [j for j, h in enumerate(hdr) if re.sub(r'\s', '', h).startswith('総数')]
    tot = next(r for r in R if r and any(re.sub(r'[\s　]', '', str(c)) == '総数' for c in r[:3]) and any(isinstance(c, (int, float)) for c in r))
    first = next(j for j, c in enumerate(tot) if isinstance(c, (int, float)))
    st[y] = (int(tot[first]), int(tot[jm[0]]) if jm else None, hdr[jm[0]].replace('\n','') if jm else '')
wp = {}
for f in sorted(glob.glob('data/derived/saihan/*.txt')):
    ed = f.split('/')[-1][:-4]; t = open(f).read()
    for m in re.finditer(r'(平成\s*(\d\d)\s*年|令和元年|^\s+(\d)\s)\s+([\d,]{5,6})\s+([\d,]{3,4})\s+([\d,]{4,5})\s*（', t, re.M):
        if '保護観察終了者' not in t[max(0, m.start()-1500):m.start()]: continue
        y = 1988 + int(m.group(2)) if m.group(2) else 2019 if '元' in m.group(1) else 2018 + int(m.group(3))
        wp.setdefault((ed, y), (int(m.group(4).replace(',', '')), int(m.group(6).replace(',', ''))))
eds = sorted({e for e, _ in wp})
for y,(a,b,h) in sorted(st.items()): print('#', y, '無職列=', h)
print('年\t保護統計 表38 総数/無職\t' + '\t'.join(eds))
for y in sorted(st):
    a, b, _ = st[y]; cells = []
    for e in eds:
        v = wp.get((e, y))
        cells.append('' if not v else f'{v[0]}/{v[1]}' + ('' if (v[0], v[1]) == (a, b) else f' (差 {v[0]-a:+d}/' + (f'{v[1]-b:+d}' if b is not None else '?') + ')'))
    print(f'{y}\t{a}/{b}\t' + '\t'.join(cells))

# 照合の要約（lib/tally.py）：単位は（白書の版・年）の保護観察終了者（総数）。表38 の「無職」の列は読めていない（無職の値は照合していない）。
# 2019年の違い（26,184・26,183 と現行 26,185）は保護統計の正誤情報（令和5年9月・令和7年7月）で説明あり。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('saihan', 'c503', note='再犯防止推進白書 指標7の保護観察終了者（総数）と保護統計年報 表38', script=__file__)
for (e, y), v in wp.items():
    if y not in st: _t.fail(); continue
    if v[0] == st[y][0]: _t.ok()
    else: _t.ng(explained=(y == 2019 and v[0] in (26184, 26183)))
print('tally', _t.save())
