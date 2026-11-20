"""c1302: 司法統計年報（刑事編）正誤表の訂正セル（黄色。赤字＝変更後、取消線＝変更前）を読み、
(a) 訂正後の値＝同じ日の更新版年報の同じセル、
(b) 年次の行（第1表など）では、次の年の年報の同じ年の行の値が訂正後の値か訂正前の値か、
を照合する（L3）。訂正の大きさ（訂正前→後の差）も集計する。
使い方: ~/.venvs/urazuke/bin/python checks/shiho/c1302_seigo_cells.py"""
import sys, json, collections, re; sys.path.insert(0, '.')
import openpyxl
D = 'data/raw/shiho'
SETS = {'r05': ('r05/seigo_16607.xlsx', 'r05/keiji_16603_upd20250916.xlsx', 'r06/keiji_16692_upd20260917.xlsx'),
        'r06': ('r06/seigo_16688.xlsx', 'r06/keiji_16692_upd20260917.xlsx', 'r07/keiji_16676.xlsx')}
def norm(t): return re.sub(r'[\s第表]', '', str(t))
def yellow(c):
    f = c.fill
    return bool(f and f.fill_type == 'solid' and f.fgColor is not None and f.fgColor.type == 'indexed' and f.fgColor.indexed in (13, 43))
def num(s):
    try: return float(str(s).replace(',', '').strip())
    except ValueError: return None
ERAS = ('昭和', '平成', '令和')
def rowkey(ws, r):
    """(区分の見出し, 元号, 年) 年次の行でなければ None"""
    yr = None
    for c in (2, 3):
        v = ws.cell(r, c).value
        if isinstance(v, (int, float)) or (isinstance(v, str) and v.strip().isdigit()): yr = int(float(v)); break
        if isinstance(v, str) and v.strip() == '元': yr = 1; break
    if yr is None: return None
    era = ''; sect = ''
    for rr in range(r, 0, -1):
        for c in (1, 2):
            v = ws.cell(rr, c).value
            if not era and isinstance(v, str) and v.strip() in ERAS: era = v.strip()
        a = ws.cell(rr, 1).value
        if not sect and isinstance(a, str) and a.strip() and a.strip() not in ERAS and len(a.strip()) > 1 and ws.cell(rr, 6).value is None:
            sect = norm(a)
        if era and sect: break
    return (sect, era, yr)
out = {}
for y, (se, up, nx) in SETS.items():
    S = openpyxl.load_workbook(f'{D}/{se}'); SR = openpyxl.load_workbook(f'{D}/{se}', rich_text=True)
    U = {norm(w.title): w for w in openpyxl.load_workbook(f'{D}/{up}', data_only=True).worksheets}
    N = {norm(w.title): w for w in openpyxl.load_workbook(f'{D}/{nx}', data_only=True).worksheets}
    st = collections.Counter(); bad_a = []; res_b = []; mags = []
    for ws in S.worksheets:
        k = norm(ws.title)
        nidx = {}
        if k in N:
            wn = N[k]
            for r in range(1, wn.max_row + 1):
                rk = rowkey(wn, r)
                if rk: nidx.setdefault(rk, r)
        for row in ws.iter_rows():
            for c in row:
                if not yellow(c): continue
                # 赤字＝変更後、取消線＝変更前（正誤表の注記）。リッチテキストの書式で判別する
                v = SR[ws.title][c.coordinate].value
                runs = list(v) if hasattr(v, '__iter__') and not isinstance(v, str) else []
                struck = [r.text for r in runs if hasattr(r, 'font') and r.font is not None and r.font.strike]
                plain = [r.text if hasattr(r, 'text') else str(r) for r in runs if not (hasattr(r, 'font') and r.font is not None and r.font.strike)]
                if len(struck) != 1 or len(''.join(plain).strip()) == 0: st['yellow_not_pair'] += 1; continue
                old, new = num(struck[0]), num(''.join(plain))
                if old is None or new is None: st['yellow_nonnum'] += 1; continue
                st['corr'] += 1; mags.append((ws.title, c.coordinate, old, new, new - old))
                u = U[k][c.coordinate].value if k in U else None
                if not (isinstance(u, (int, float)) and abs(u - new) < 1e-9): bad_a.append((ws.title, c.coordinate, old, new, u))
                rk = rowkey(ws, c.row)
                if rk and rk in nidx:
                    v = N[k].cell(nidx[rk], c.column).value
                    tag = 'new' if isinstance(v, (int, float)) and abs(v - new) < 1e-9 else ('old' if isinstance(v, (int, float)) and abs(v - old) < 1e-9 else 'other')
                    st['b_' + tag] += 1; res_b.append((ws.title, c.coordinate, rk, old, new, v, tag))
    big = sorted(mags, key=lambda m: -abs(m[4]) / max(1, abs(m[2])))[:10]
    out[y] = {'stats': st, 'a_mismatch': bad_a, 'b': res_b, 'largest_rel': big}
    print(y, dict(st), 'a_mismatch', len(bad_a)); [print('  big', b) for b in big[:5]]
    [print('  b', r) for r in res_b if r[-1] != 'new'][:10]
json.dump(out, open('results/shiho/c1302_seigo_cells.json', 'w'), ensure_ascii=False, indent=1, default=str)

# 照合の要約（lib/tally.py）：(a) 正誤表の訂正後の値（赤字）と更新版、(b) 次の年の年報の同じ行。(b) で訂正前の値なら食い違い、
# 訂正前とも訂正後とも違う値は行の対応の取り違えの可能性があり読み取りの失敗。書式で訂正の前後を読み分けられないセルも読み取りの失敗。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('shiho', 'c1302', note='司法統計年報（刑事編）の正誤表の訂正セル：訂正後の値と更新版、次の年の年報', script=__file__)
for y, v in out.items():
    s = v['stats']
    _t.ok(s['corr'] - len(v['a_mismatch'])); _t.ng(len(v['a_mismatch']))
    _t.ok(s['b_new']); _t.ng(s['b_old']); _t.fail(s['b_other'] + s['yellow_not_pair'] + s['yellow_nonnum'])
print('tally', _t.save())
