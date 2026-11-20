"""警察庁「犯罪統計資料」（e-Stat 00130001、CSV、cp932）を表ごとに読む。
返り値: [ {no:'第１表', title:str, part:int, cols:[(区分, 期間ラベル)], rows:[(c0, c1, [値 or None,...])]} ]
・「第N表」の標識（1〜3列目のどれか。第５表・第１２表は2列目）で表を区切る。
・1つの標識の下で期間の見出し行（西暦「YYYY年」を2つ以上含む行）が複数回出る場合は、見出しごとに別の部分（part）として返す。
・区分は見出し行の1行上と2行上を結合する（第13表のように3段の見出しがあるため）。左の値で埋める。
・値の列は、期間の行のセルが「YYYY年」「増減」「率」を含む列（2列目以降）。数値にできないセルは None。
・ラベル列は値の列より左。値の列が2列目から始まる表（第11・14・15表）は c1 を空にする。"""
import csv, io, re

def _num(s):
    s = (s or '').strip().replace(',', '')
    if s in ('', '-', '－', '…', '―'): return None
    try: return float(s)
    except ValueError: return None

def _mark(r):
    for x in r[:3]:
        if x.strip(): return x.strip() if re.match(r'^第[０-９0-9]+表', x.strip()) else None
    return None

def _isper(r):
    return sum(1 for x in r if re.search(r'\d{4}年', x)) >= 2

def read(path):
    rows = list(csv.reader(io.StringIO(open(path, 'rb').read().decode('cp932'))))
    starts = [i for i, r in enumerate(rows) if _mark(r)]
    out = []
    for k, s in enumerate(starts):
        e = starts[k + 1] if k + 1 < len(starts) else len(rows)
        blk = rows[s:e]
        no = _mark(blk[0]); title = ' '.join(x.strip() for x in blk[0] if x.strip() and x.strip() != no)
        pers = [i for i, r in enumerate(blk) if _isper(r)]
        for part, pi in enumerate(pers):
            end = pers[part + 1] - 2 if part + 1 < len(pers) else len(blk)
            prow = blk[pi]; crow = blk[pi - 1] if pi > 0 else []; c2row = blk[pi - 2] if pi > 1 else []
            cols, idx = [], []
            last_c = last_c2 = ''
            for j, x in enumerate(prow):
                c1_ = (crow[j] if j < len(crow) else '').replace('\n', '').strip()
                c2_ = (c2row[j] if j < len(c2row) else '').replace('\n', '').strip()
                if c2_ and not _mark(c2row): last_c2 = c2_
                if c1_: last_c = c1_
                c = (last_c2 + '/' if last_c2 and last_c2 != last_c else '') + last_c
                p = x.replace('\n', '').strip()
                if p and j >= 1 and re.search(r'\d{4}年|増減|率', p):
                    cols.append((c, p)); idx.append(j)
            if not idx: continue
            data = []
            for r in blk[pi + 1:end]:
                if not any(x.strip() for x in r) or _isper(r): continue
                c0 = r[0].strip() if r else ''
                c1 = r[1].strip() if (len(r) > 1 and idx[0] > 1) else ''
                vals = [_num(r[j]) if j < len(r) else None for j in idx]
                if all(v is None for v in vals): continue
                data.append((c0, c1, vals))
            out.append({'no': no, 'title': title, 'part': part, 'cols': cols, 'rows': data})
    return out

def year_of(label):
    m = re.search(r'(\d{4})年', label)
    return int(m[1]) if m else None
