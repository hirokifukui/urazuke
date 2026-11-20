"""版間の比較（L3）の共通部品。
行ラベル（年など）×列見出し（上位の見出しを連結）でセルを鍵にし、二つの版の重なる鍵の値を比べる。
見出しの衝突（METHODS の教訓 c009）を避けるため、列の鍵は上位の見出しを左から引き継いで連結し、さらに列番号を付けない代わりに同名の重複には連番を付ける。"""
import re, openpyxl
def norm(s):
    return re.sub(r'[\s　（）()]', '', str(s)) if s is not None else ''
def num(v):
    if isinstance(v, (int, float)): return float(v)
    if isinstance(v, str):
        t = v.replace(',', '').strip()
        try: return float(t)
        except ValueError: return None
    return None
def sheet_grid(ws):
    return [list(r) for r in ws.iter_rows(values_only=True)]
def keyed(grid, label_cols=1, header_rows=None, label_re=r'(昭和|平成|令和|元|\d{4}|総数|男|女|全年齢|～|歳)'):
    """データ行＝先頭列のラベルが label_re に合い、数値を1つ以上含む行。見出し行＝最初のデータ行より上。"""
    rows = grid; first = None
    for i, r in enumerate(rows):
        lab = norm(''.join(norm(x) for x in r[:label_cols]))
        if lab and re.search(label_re, lab) and any(num(x) is not None for x in r[label_cols:]):
            first = i; break
    if first is None: return {}
    hdr = rows[max(0, first - (header_rows or 4)):first]
    ncol = max(len(r) for r in rows)
    colkey = []
    carry = [''] * len(hdr)
    for c in range(label_cols, ncol):
        parts = []
        for h, r in enumerate(hdr):
            v = norm(r[c]) if c < len(r) else ''
            if v: carry[h] = v
            elif h < len(hdr) - 1 and c > label_cols: v = carry[h]   # 上位の結合見出しを引き継ぐ
            parts.append(v)
        colkey.append('|'.join(p for p in parts if p))
    seen = {}
    for j, k in enumerate(colkey):
        seen[k] = seen.get(k, 0) + 1
        if seen[k] > 1: colkey[j] = f'{k}#{seen[k]}'
    out = {}; sect = ''
    for r in rows[first:]:
        lab = '/'.join(norm(x) for x in r[:label_cols] if norm(x))
        vals = [num(x) for x in r[label_cols:]]
        if not lab: continue
        if not any(v is not None for v in vals):
            sect = re.sub(r'[0-9０-９昭和平成令和年～\-－]', '', lab)[:8]; continue
        L = f'{sect}/{lab}' if sect else lab
        k0 = L; n = 2
        while any(kk[0] == L for kk in out) and n < 50:
            L = f'{k0}#{n}'; n += 1
        for j, v in enumerate(vals):
            if v is not None and j < len(colkey): out[(L, colkey[j])] = v
    return out
def wb_keyed(path, **kw):
    wb = openpyxl.load_workbook(path, data_only=True)
    return {re.sub(r'\s', '', ws.title.replace('２', '2')): keyed(sheet_grid(ws), **kw) for ws in wb.worksheets}
def compare(a, b, tol=1e-9):
    common = set(a) & set(b); diff = []
    for k in sorted(common):
        if abs(a[k] - b[k]) > tol * max(1, abs(a[k])): diff.append((k, a[k], b[k]))
    return len(common), diff
