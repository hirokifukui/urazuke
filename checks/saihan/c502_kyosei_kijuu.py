"""再犯防止推進白書「刑務所出所者の帰住先がない者の数」の表の刑務所出所者総数を、
矯正統計年報「出所受刑者の出所事由、入所度数及び出所時の保護別 帰住先」（表84）の総数と比べる。"""
import glob, re, io, openpyxl, xlrd
kyo = {}
for f in sorted(glob.glob('data/raw/kyosei_toukei/kijuu/*.xls')):
    y = int(re.search(r'/(\d{4})_', f).group(1))
    b = open(f, 'rb').read()
    if b[:2] == b'PK':
        rows = [list(r) for r in openpyxl.load_workbook(io.BytesIO(b), data_only=True).worksheets[0].iter_rows(values_only=True)]
    else:
        s = xlrd.open_workbook(file_contents=b).sheet_by_index(0); rows = [s.row_values(i) for i in range(s.nrows)]
    hdr = next(r for r in rows if any(str(c).strip() == '総数' for c in r if c is not None) and any('のもと' in str(c) for c in r if c))
    jt = [j for j, c in enumerate(hdr) if str(c).strip() == '総数'][0]
    tot = next(r for r in rows if r and any(str(c).strip() == '総数' for c in r[:3] if c is not None) and isinstance(r[jt], (int, float)))
    kyo[y] = int(tot[jt])
# 白書の表（data/derived/saihan/R0x.txt）から「年次 刑務所出所者総数 帰住先がない者」の行を拾う
wp = {}
for f in sorted(glob.glob('data/derived/saihan/*.txt')):
    ed = f.split('/')[-1][:-4]
    t = open(f).read()
    i = t.find('帰住先がない者')
    for m in re.finditer(r'(平成\s*30|令和\s*元|^\s*[2-9])\s*年?\s+([\d,]{5,6})\s+([\d,]{3,5})\s*（', t, re.M):
        if '帰住先' not in t[max(0, m.start()-3000):m.start()]:
            continue
        g = re.sub(r'\s', '', m.group(1)); y = 2018 if '30' in g else 2019 if '元' in g else 2018 + int(g)
        wp.setdefault((ed, y), int(m.group(2).replace(',', '')))
print('年\t矯正統計 表84 総数\t' + '\t'.join(sorted({e for e, _ in wp})))
eds = sorted({e for e, _ in wp})
for y in sorted(kyo):
    cells = []
    for e in eds:
        v = wp.get((e, y))
        cells.append('' if v is None else (str(v) + ('' if v == kyo[y] else f'(差{v-kyo[y]:+d})')))
    print(f'{y}\t{kyo[y]}\t' + '\t'.join(cells))

# 照合の要約（lib/tally.py）：単位は（白書の版・年）の刑務所出所者総数。2022年の令和5年版 17,142 は矯正統計の正誤情報（令和6年7月31日）で説明あり。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('saihan', 'c502', note='再犯防止推進白書の刑務所出所者総数と矯正統計年報 表84', script=__file__)
for (e, y), v in wp.items():
    if y not in kyo: _t.fail(); continue
    if v == kyo[y]: _t.ok()
    else: _t.ng(explained=(e, y, v) == ('R05', 2022, 17142))
print('tally', _t.save())
