"""各記録の原文の該当箇所（PDF は頁、Excel はシートとセル）を機械で探す。
入力：checks/quotes/targets.tsv（id, ラベル, ファイルの glob, 同じ頁・同じシートに現れるべき語を | 区切り）
出力：results/quotes/quotes.json・quotes.tsv
使い方: ~/.venvs/urazuke/bin/python checks/quotes/locate.py"""
import csv, glob, json, os, re, subprocess, io
import openpyxl, xlrd
B = 'data/raw'
def norm(s): return re.sub(r'[,\s，]', '', str(s))
def num(s):
    try: return float(norm(s))
    except: return None
def pdf_pages(p):
    t = subprocess.run(['pdftotext', '-layout', p, '-'], capture_output=True, text=True, errors='ignore').stdout
    return t.split('\f')
def colname(c):
    s = ''
    while c: c, r = divmod(c - 1, 26); s = chr(65 + r) + s
    return s
def sheets(p):
    b = open(p, 'rb').read()
    if b[:2] == b'PK':
        wb = openpyxl.load_workbook(io.BytesIO(b), read_only=True, data_only=True)
        for ws in wb.worksheets:
            yield ws.title, [list(r) for r in ws.iter_rows(values_only=True)]
    else:
        wb = xlrd.open_workbook(file_contents=b)
        for s in wb.sheets(): yield s.name, [s.row_values(i) for i in range(s.nrows)]
def match_cell(v, tok):
    if v is None: return False
    tn = num(tok)
    if tn is not None and isinstance(v, (int, float)): return abs(v - tn) < 1e-6 or (abs(tn) < 100 and abs(round(v * 100, 2) - tn) < 0.006)
    return norm(tok) in norm(v)
def find(rid, label, g, toks, mode='page'):
    hits = []; want_sheet = None
    if '::' in g: g, want_sheet = g.split('::')
    for p in sorted(glob.glob(os.path.join(B, g))):
        rel = os.path.relpath(p, B)
        if p.lower().endswith(('.pdf', '.html', '.htm', '.txt', '.csv')):
            if p.lower().endswith('.csv'):   # e-Stat の CSV（Shift_JIS）。行の位置は「CSV n行」で示す
                L0 = open(p, encoding='cp932', errors='ignore').read().splitlines()
                k = next((j for j, l in enumerate(L0) if all(norm(t) in norm(l) for t in toks)), None)
                if k is not None: hits.append({'file': rel, 'where': f'CSV {k+1}行', 'text': L0[k][:200]}); break
                continue
            pages = pdf_pages(p) if p.lower().endswith('.pdf') else [re.sub(r'<[^>]+>', ' ', open(p, errors='ignore').read())]
            for i, pg in enumerate(pages, 1):
                if mode == 'line':
                    L = pg.splitlines(); k = next((j for j, l in enumerate(L) if all(norm(t) in norm(l) for t in toks)), None)
                    if k is not None:
                        ctx = ' '.join(x.strip() for x in L[max(0, k - 2):k + 1] if x.strip()) if len(norm(L[k])) < 30 else L[k].strip()
                        hits.append({'file': rel, 'where': f'{i}頁' if p.lower().endswith('.pdf') else 'ページ本文', 'text': re.sub(r'\s+', ' ', ctx)[:200]}); break
                    continue
                n = norm(pg)
                if all(norm(t) in n for t in toks):
                    line = next((l.strip() for l in pg.splitlines() if norm(toks[0]) in norm(l)), '')
                    hits.append({'file': rel, 'where': f'{i}頁' if p.lower().endswith('.pdf') else 'ページ本文', 'text': re.sub(r'\s+', ' ', line)[:160]})
                    break
        elif re.search(r'\.xlsx?$', p, re.I):
            for sn, rows in sheets(p):
                if want_sheet and sn != want_sheet: continue
                if mode == 'rowno':
                    rr = int(toks[0]) - 1
                    if rr < len(rows):
                        hits.append({'file': rel, 'where': f'シート「{sn}」{rr+1}行', 'text': '行：' + ' '.join(str(x) for x in rows[rr] if x not in (None, ''))[:160]}); break
                    continue
                if mode == 'yearcell':
                    name, year = toks
                    hdr = next(((r, c) for r, row in enumerate(rows[:10]) for c, v in enumerate(row) if isinstance(v, (int, float)) and v == float(year)), None)
                    rr = next((r for r, row in enumerate(rows) if row and str(row[0]).strip() == name), None)
                    if hdr and rr is not None:
                        c = hdr[1]; hits.append({'file': rel, 'where': f'シート「{sn}」{colname(c+1)}{rr+1}', 'text': f'{name}・{year}年：{rows[rr][c]}'}); break
                    continue
                if mode == 'row':
                    def mc(v, t): return match_cell(v, t) if num(t) is not None else (v is not None and re.sub(r"[\s　]", "", str(v)) == re.sub(r"[\s　]", "", t))
                    rr = next((r for r, row in enumerate(rows) if all(any(mc(v, t) for v in row) for t in toks)), None)
                    if rr is not None:
                        cs = [next(c for c, v in enumerate(rows[rr]) if mc(v, t)) for t in toks]
                        hits.append({'file': rel, 'where': f'シート「{sn}」' + '・'.join(f'{colname(c+1)}{rr+1}' for c in cs), 'text': '行：' + ' '.join(str(x) for x in rows[rr] if x not in (None, ''))[:160]}); break
                    continue
                locs = []
                for t in toks:
                    loc = next(((r, c) for r, row in enumerate(rows) for c, v in enumerate(row) if match_cell(v, t)), None)
                    locs.append(loc)
                if all(locs):
                    r, c = locs[0]; row = rows[r]
                    lab = ' '.join(str(x) for x in row[:4] if x not in (None, ''))[:60]
                    hits.append({'file': rel, 'where': f'シート「{sn}」' + '・'.join(f'{colname(cc+1)}{rr+1}' for rr, cc in locs), 'text': f'行の見出し：{lab}／値：' + '・'.join(str(rows[rr][cc]) for rr, cc in locs)})
                    break
        if hits and len(hits) >= 1: break
    return {'id': rid, 'label': label, 'glob': g, 'tokens': toks, 'hits': hits}
out = []
for row in csv.DictReader(open('checks/quotes/targets.tsv'), delimiter='\t'):
    out.append(find(row['id'], row['label'], row['glob'], row['tokens'].split('|'), row.get('mode') or 'page'))
os.makedirs('results/quotes', exist_ok=True)
json.dump(out, open('results/quotes/quotes.json', 'w'), ensure_ascii=False, indent=1)
with open('results/quotes/quotes.tsv', 'w') as w:
    w.write('id\tlabel\tfile\twhere\ttext\n')
    for o in out:
        h = o['hits'][0] if o['hits'] else {'file': '', 'where': '見つからない', 'text': ''}
        w.write('\t'.join([o['id'], o['label'], h['file'], h['where'], h['text']]) + '\n')
for o in out: print(o['id'], o['label'], '→', (o['hits'][0]['file'] + ' ' + o['hits'][0]['where']) if o['hits'] else '見つからない')
