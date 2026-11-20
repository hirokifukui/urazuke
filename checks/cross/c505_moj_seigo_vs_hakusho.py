"""c505: 法務省「統計の正誤情報」（矯正統計・保護統計）の訂正値が、犯罪白書・再犯防止推進白書のどの版に
訂正前（誤）・訂正後（正）の形で載っているかを数える。
対象：誤・正がともに数値で、誤≠正、かつ 1,000 以上（3桁以下は偶然の一致が多すぎるため除外）。
白書のテキスト：再犯防止 data/derived/saihan/*.txt、犯罪白書 data/raw/hanzai_hakusho/pdf/*.txt。数値は「17,142」の形で探す（前後が数字・カンマでないこと）。
出力は候補。一致した箇所は文脈を目で確かめて、同じ量かどうかを判定する。"""
import glob, io, re, os, csv, openpyxl, xlrd, collections
def sheets(f):
    b = open(f, 'rb').read()
    if b[:2] == b'PK':
        wb = openpyxl.load_workbook(io.BytesIO(b), data_only=True); return [(w.title, [list(r) for r in w.iter_rows(values_only=True)]) for w in wb.worksheets]
    wb = xlrd.open_workbook(file_contents=b); return [(s.name, [s.row_values(i) for i in range(s.nrows)]) for s in wb.sheets()]
# 掲載日：ページの並び（日付 → 直後の Excel リンク）
date = {}
for p, src in (('data/raw/moj_seigo/housei05_00010.html', 'kyosei'), ('data/raw/moj_seigo/housei05_00012.html', 'hogo')):
    t = open(p, encoding='utf-8', errors='replace').read()
    cur = None
    for m in re.finditer(r'((?:平成|令和)[０-９0-9元]+年[０-９0-9]+月[０-９0-9]+日)|/content/(\d+)\.xlsx?', t):
        if m.group(1): cur = m.group(1)
        elif cur: date.setdefault(m.group(2), cur)
def num(x):
    if isinstance(x, (int, float)): return int(x) if float(x).is_integer() else None
    s = str(x).replace(',', '').strip()
    return int(s) if re.fullmatch(r'\d+', s) else None
rows = []
for f in sorted(glob.glob('data/raw/moj_seigo/*/*')):
    src = f.split('/')[-2]; cid = re.sub(r'\.xlsx?$', '', os.path.basename(f))
    try: S = sheets(f)
    except Exception: continue
    for name, R in S:
        for r in R:
            cells = [c for c in r if c not in (None, '')]
            if len(cells) < 4: continue
            a, b = num(cells[-2]), num(cells[-1])
            if a is None or b is None or a == b or max(a, b) < 1000: continue
            rows.append((src, cid, date.get(cid, ''), name, re.sub(r'\s+', ' ', ' / '.join(str(c) for c in cells[:-2]))[:80], a, b))
texts = {}
for f in sorted(glob.glob('data/derived/saihan/*.txt')): texts['再犯防止' + os.path.basename(f)[:-4]] = open(f, errors='replace').read()
for f in sorted(glob.glob('data/raw/hanzai_hakusho/pdf/*.txt')): texts['犯罪白書' + os.path.basename(f)[:3]] = open(f, errors='replace').read()
def fmt(n): return f'{n:,}'
NUMS = {k: set(re.findall(r'(?<![\d,])\d{1,3}(?:,\d{3})+(?![\d,])', t)) for k, t in texts.items()}
def hits(n):
    f = fmt(n)
    return [k for k, ns in NUMS.items() if f in ns]
uniq = {}
for r in rows: uniq.setdefault((r[5], r[6]), r)
out = []
for (a, b), r in uniq.items():
    ha, hb = hits(a), hits(b)
    if ha or hb: out.append(r + (','.join(ha), ','.join(hb)))
with open('results/saihan/c505_moj_seigo_vs_hakusho.tsv', 'w') as w:
    w.write('統計\t正誤表\t掲載日\t年報\t箇所\t誤\t正\t誤が載る白書\t正が載る白書\n')
    for o in out: w.write('\t'.join(map(str, o)) + '\n')
print('正誤の行（1000以上）', len(rows), '異なる組', len(uniq), '白書に出る組', len(out))
for o in out[:60]: print(*o, sep='\t')
