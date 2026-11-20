"""福祉行政報告例（e-Stat）の統計表 CSV を読む。
形：冒頭に年度・表題・注・「（報告表 ４９）」、続いて見出し（1〜3段）、単位の行（「件」「人」が並ぶ）、データ。
返り値: {'title': str, 'cols': [列名（段を「/」で結合、左の値で埋める）], 'rows': [(c0, c1, [値])]}
値：'-' は 0、'…' や空は None。列名に「再掲」を含む列は内訳の和から除くこと（呼び出し側で判断）。"""
import csv, io, re

def _dec(b):
    for enc in ('cp932', 'utf-8-sig', 'utf-8'):
        try: return b.decode(enc)
        except UnicodeDecodeError: pass
    return b.decode('cp932', errors='replace')

def _v(s):
    s = (s or '').strip().replace(',', '')
    if s in ('-', '－'): return 0.0
    try: return float(s)
    except ValueError: return None

def read(path):
    rows = list(csv.reader(io.StringIO(_dec(open(path, 'rb').read()))))
    title = next((''.join(r) for r in rows[:4] if '表' in ''.join(r) and ('児童' in ''.join(r))), '')
    hi = next(i for i in range(len(rows)) if '報告表' in ''.join(rows[i])) + 1
    isnum = lambda x: _v(x) is not None and x.strip() not in ('',)
    di = next(i for i in range(hi, len(rows)) if sum(1 for x in rows[i][1:] if isnum(x)) >= 2)
    first = next(j for j in range(1, len(rows[di])) if isnum(rows[di][j]) or rows[di][j].strip() in ('-', '…'))
    hdr = [r for r in rows[hi:di] if any(x.strip() for x in r) and not all(x.strip() in ('', '件', '人', '所', '世帯') for x in r)]
    ncol = max(len(r) for r in rows[di:di + 5])
    ui = di - 1
    cols = []
    for j in range(first, ncol):   # 結合セルは値が繰り返されているので、左埋めはしない。空でない段を「/」で結合
        parts = []
        for r in hdr:
            v = re.sub(r'[\s　]', '', r[j]) if j < len(r) else ''
            if v and (not parts or parts[-1] != v): parts.append(v)
        cols.append('/'.join(parts))
    data = []
    for r in rows[ui + 1:]:
        if not any(x.strip() for x in r): continue
        c0 = re.sub(r'[\s　]', '', r[0]); c1 = re.sub(r'[\s　]', '', r[1]) if first > 1 and len(r) > 1 else ''
        vals = [_v(r[j]) if j < len(r) else None for j in range(first, ncol)]
        if all(v is None for v in vals): continue
        data.append((c0, c1, vals))
    return {'title': title, 'cols': cols, 'rows': data}
