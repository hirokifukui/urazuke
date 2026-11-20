"""seigo.py 正誤表の各訂正が現行ファイルに反映されているかを判定する共通部品（xls / xlsx）。
judge(entry, path) → '反映(列)' / '未反映(列)' / '反映' / '未反映' / '判定不能'
entry: dict(side=表側, head=表頭, wrong=誤, right=正)（いずれも norm 済み）"""
import re, io, functools, unicodedata, openpyxl, xlrd

def norm(s):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', str(s)))

def isnum(s):
    if norm(s) in ('-', '−', '―', '…'): return True
    return re.fullmatch(r'-?\d+(\.\d+)?', norm(s).replace(',', '')) is not None

def numv(s):
    v = norm(s).replace(',', '')
    if v in ('-', '−', '―', '…'): return '0'
    return str(int(float(v))) if re.fullmatch(r'-?\d+\.0+', v) else v

@functools.lru_cache(None)
def raw_rows(path):
    if open(path, 'rb').read(2) == b'PK':
        ws = openpyxl.load_workbook(io.BytesIO(open(path, 'rb').read()), data_only=True).worksheets[0]
        g = [list(r) for r in ws.iter_rows(values_only=True)]
        for mr in ws.merged_cells.ranges:  # 結合セルの値を範囲全体に広げる（見出しの親子を列ごとに連結するため）
            v = ws.cell(mr.min_row, mr.min_col).value
            for rr in range(mr.min_row, mr.max_row + 1):
                for cc in range(mr.min_col, mr.max_col + 1):
                    if rr - 1 < len(g):
                        while len(g[rr - 1]) < cc: g[rr - 1].append(None)
                        if g[rr - 1][cc - 1] is None: g[rr - 1][cc - 1] = v
        return tuple(tuple(r) for r in g)
    bk = xlrd.open_workbook(path, formatting_info=True)
    s = bk.sheet_by_index(0)
    g = [[None if x == '' else x for x in s.row_values(i)] for i in range(s.nrows)]
    for r0, r1, c0, c1 in s.merged_cells:
        v = g[r0][c0]
        for rr in range(r0, r1):
            for cc in range(c0, c1):
                if g[rr][cc] is None: g[rr][cc] = v
    return tuple(tuple(r) for r in g)

@functools.lru_cache(None)
def layout(path):
    raw = raw_rows(path)
    first = next(i for i, r in enumerate(raw) if sum(1 for x in r if x is not None and isnum(x)) >= 3)
    ncol = max(len(r) for r in raw)
    heads = [''] * ncol
    for r in raw[:first]:
        for j in range(ncol):
            x = r[j] if j < len(r) else None
            if x is not None and str(x).strip() and not isnum(x):
                t = norm(x)
                if not heads[j].endswith(t): heads[j] += t
    import os.path as _op
    ne = [h for h in heads if h]
    pre = _op.commonprefix(ne) if len(ne) > 1 else ''
    if pre: heads = [h[len(pre):] if h.startswith(pre) else h for h in heads]
    rows, parent, grand = [], '', ''
    for r in raw[first:]:
        cells = [x for x in r if x is not None and str(x).strip() != '']
        if not cells: continue
        labels = [norm(x) for x in cells if not isnum(x) and not hasattr(x, 'year')]
        nums = [numv(x) for x in cells if isnum(x)]
        if not nums: continue
        if labels and labels[0] not in ('男', '女'):
            parent = ''.join(l for l in labels if l not in ('男', '女', '総数'))
        rows.append((parent + ''.join(labels), ''.join(labels), tuple(nums), r))
    return heads, rows

def cands(e, rows, yr=None):
    s = e['side']
    m = re.fullmatch(r'(\d+)(総数|男|女)', s)
    if m and yr:
        out, inblk = [], False
        for t in rows:
            full, lab, nums = t[0], t[1], t[2]
            if lab.endswith('総数'):
                inblk = (nums and nums[0] == m[1] and m[1] == yr) or ('令和' + yr + '年' in full)
            if inblk and lab.endswith(m[2]): out.append(t)
        return out
    out = [t for t in rows if t[0] == s or t[0].endswith(s) or t[1] == s]
    if not out:
        sub = re.fullmatch(r'(.+?)(総数|男|女|計)', s)
        if sub: out = [t for t in rows if t[0].startswith(sub[1]) and t[1].endswith(sub[2])]
    return out

def judge(e, path, yr=None):
    heads, rows = layout(path)
    c = cands(e, rows, yr)
    h = e['head']
    js = [j for j, t in enumerate(heads) if t == h]
    if len(js) != 1: js = [j for j, t in enumerate(heads) if t and t.endswith(h)]
    if len(js) != 1: js = [j for j, t in enumerate(heads) if t and h.endswith(t) and len(t) >= 2]
    if len(js) == 1 and c:
        j = js[0]
        vals = [numv(t[3][j]) for t in c if j < len(t[3]) and t[3][j] is not None and isnum(t[3][j])]
        if vals:
            if e['right'] in vals and e['wrong'] not in vals: return '反映(列)'
            if e['wrong'] in vals and e['right'] not in vals: return '未反映(列)'
    return '判定不能'
