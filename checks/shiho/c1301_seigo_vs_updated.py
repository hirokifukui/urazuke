"""c1301: 司法統計年報（刑事編）の正誤表（Excel、訂正箇所を黄色で表示）と、同じ日に掲載された更新版の年報 Excel の比較（L3）。
(a) 正誤表の各シートと、更新版の同じ番号のシートを、セル位置で照合する（訂正後の表が更新版に入っているか）。
(b) 黄色のセル（訂正箇所）の数を数える。
(c) 次の年の年報（令和6・7年）の同じ表で、前年の値が訂正後の値と同じかを、年の行で照合する（第1表など年次の表）。
使い方: ~/.venvs/urazuke/bin/python checks/shiho/c1301_seigo_vs_updated.py"""
import sys, json, collections, re; sys.path.insert(0, '.')
import openpyxl
D = 'data/raw/shiho'
PAIRS = {'r05': ('r05/seigo_16607.xlsx', 'r05/keiji_16603_upd20250916.xlsx'), 'r06': ('r06/seigo_16688.xlsx', 'r06/keiji_16692_upd20260917.xlsx')}
def norm(t): return re.sub(r'[\s第表]', '', str(t))
def yellow(c):
    f = c.fill
    if not f or f.fill_type != 'solid' or f.fgColor is None: return False
    if f.fgColor.type == 'indexed': return f.fgColor.indexed in (13, 43)
    rgb = f.fgColor.rgb if f.fgColor.type == 'rgb' else ''
    return isinstance(rgb, str) and rgb[-6:].upper() in ('FFFF00', 'FFFF99', 'FFFF66', 'FFF2CC', 'FFFFCC')
out = {}
for y, (se, up) in PAIRS.items():
    S = openpyxl.load_workbook(f'{D}/{se}')
    U = openpyxl.load_workbook(f'{D}/{up}', data_only=True)
    um = {norm(w.title): w for w in U.worksheets}
    st = collections.Counter(); diffs = []; ycells = []
    for ws in S.worksheets:
        k = norm(ws.title)
        if k not in um: diffs.append((ws.title, 'NO_SHEET')); continue
        wu = um[k]; st['sheets'] += 1
        for row in ws.iter_rows():
            for c in row:
                if yellow(c): ycells.append((ws.title, c.coordinate, c.value))
                v = c.value
                if isinstance(v, (int, float)):
                    st['cells'] += 1
                    u = wu[c.coordinate].value
                    if not (isinstance(u, (int, float)) and abs(u - v) < 1e-9):
                        diffs.append((ws.title, c.coordinate, v, u, yellow(c)))
    out[y] = {'stats': st, 'yellow': len(ycells), 'yellow_cells': ycells[:400], 'diffs': diffs}
    yd = sum(1 for d in diffs if len(d) == 5 and d[4])
    print(y, dict(st), 'yellow', len(ycells), 'diffs', len(diffs), 'of which yellow', yd)
    for d in diffs[:15]: print('  ', d)
json.dump(out, open('results/shiho/c1301_seigo_vs_updated.json', 'w'), ensure_ascii=False, indent=1, default=str)

# (c) 次の年の年報で、訂正した年の行の値が訂正後の値と同じか（年次の行だけ）
NEXT = {'r05': 'r06/keiji_16692_upd20260917.xlsx', 'r06': 'r07/keiji_16676.xlsx'}
def rowlab(ws, r):
    era = ''
    for rr in range(r, 0, -1):
        a = ws.cell(rr, 1).value
        if a and str(a).strip() in ('昭和', '平成', '令和'): era = str(a).strip(); break
    b = ws.cell(r, 2).value
    sect = ''
    for rr in range(r, 0, -1):
        a = ws.cell(rr, 1).value
        if a and str(a).strip() not in ('昭和', '平成', '令和') and ws.cell(rr, 4).value is None: sect = norm(a); break
    return (sect, era, str(b).strip() if b is not None else '')
cres = {}
for y, (se, up) in PAIRS.items():
    S = openpyxl.load_workbook(f'{D}/{se}')
    N = openpyxl.load_workbook(f'{D}/{NEXT[y]}', data_only=True); nm = {norm(w.title): w for w in N.worksheets}
    chk = []; 
    for ws in S.worksheets:
        k = norm(ws.title)
        if k not in nm: continue
        wn = nm[k]
        idx = {}
        for r in range(1, wn.max_row + 1):
            lab = rowlab(wn, r)
            if lab[1] and lab[2].isdigit(): idx.setdefault(lab, r)
        for row in ws.iter_rows():
            for c in row:
                if yellow(c) and isinstance(c.value, (int, float)):
                    lab = rowlab(ws, c.row)
                    if not (lab[1] and lab[2].isdigit()): continue
                    if lab not in idx: chk.append((ws.title, c.coordinate, lab, c.value, 'NO_ROW')); continue
                    v = wn.cell(idx[lab], c.column).value
                    chk.append((ws.title, c.coordinate, lab, c.value, v))
    bad = [x for x in chk if x[4] != 'NO_ROW' and not (isinstance(x[4], (int, float)) and abs(x[4] - x[3]) < 1e-9)]
    cres[y] = {'checked': len(chk), 'no_row': sum(1 for x in chk if x[4] == 'NO_ROW'), 'mismatch': bad}
    print('(c)', y, 'checked', len(chk), 'no_row', cres[y]['no_row'], 'mismatch', len(bad)); [print('   ', b) for b in bad[:15]]
json.dump(cres, open('results/shiho/c1301c_next_year.json', 'w'), ensure_ascii=False, indent=1, default=str)

# 照合の要約（lib/tally.py）：(a) 正誤表の数値セルと更新版の同じセル、(c) 次の年の年報の同じ年の行。シート・行の対応がないものは読み取りの失敗。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('shiho', 'c1301', note='司法統計年報（刑事編）の正誤表と更新版、次の年の年報', script=__file__)
for y, v in out.items():
    nd = [d for d in v['diffs'] if len(d) == 5]
    _t.ok(v['stats']['cells'] - len(nd)); _t.ng(len(nd)); _t.fail(len(v['diffs']) - len(nd))
for y, v in cres.items():
    _t.ok(v['checked'] - v['no_row'] - len(v['mismatch'])); _t.ng(len(v['mismatch'])); _t.fail(v['no_row'])
print('tally', _t.save())
