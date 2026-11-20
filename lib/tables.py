"""犯罪白書の Excel（見出しは 6 行目、7 行目に補助見出しがあることもある）を扱う補助関数。"""
import re
import xlsx


def is_note(v):
    return isinstance(v, str) and (v.strip().startswith("注") or v.startswith("　") or v.startswith("  "))


def sheet_rows(cells, key_cols, hdr_rows=(6,), first=None, stop_at_note=True):
    """見出し行を結合して列名を作り、key_cols の値の組を鍵にした {鍵: {列名: 値}} を返す。"""
    C = max(c for _, c in cells)
    names = {}
    for c in range(1, C + 1):
        parts = [str(cells.get((r, c), "")).strip() for r in hdr_rows]
        name = "_".join(p for p in parts if p)
        if name:
            names[c] = name
    start = first or (max(hdr_rows) + 1)
    out, order = {}, []
    R = max(r for r, _ in cells)
    for r in range(start, R + 1):
        k0 = cells.get((r, key_cols[0]))
        if k0 in (None, ""):
            continue
        if stop_at_note and is_note(k0):
            break
        key = tuple(cells.get((r, c)) for c in key_cols)
        key = key[0] if len(key) == 1 else key
        out[key] = {names[c]: cells.get((r, c)) for c in names if c not in key_cols}
        order.append(key)
    return out, order


def year(v):
    m = re.match(r"(\d{4})年", str(v))
    return int(m.group(1)) if m else None


def num(v):
    return v if isinstance(v, float) else None
