"""c2701 矯正統計年報：法務省「正誤情報」の各訂正が、e-Stat の現行の年報ファイルに反映されているか。
正誤表の各行（表番号・表側・表頭・誤・正）について、現行ファイルの中で表側が一致する行を探し、
その行に「正」の値があり「誤」の値がない → 反映、「誤」があり「正」がない → 未反映、それ以外 → 判定不能。
使い方: c2701_seigo_applied.py [root]   出力: results/kyosei/c2701_seigo.tsv と要約
"""
import sys, os, re, glob, unicodedata, openpyxl, functools
from collections import Counter
root = sys.argv[1] if len(sys.argv) > 1 else '.'
SEIGO = {'001472579.xlsx': '2025', '001410833.xlsx': '2022', '001422546.xlsx': '2022', '001443818.xlsx': '2022'}

def norm(s):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', str(s)))

def isnum(s):
    if norm(s) in ('-', '−', '―'): return True
    return re.fullmatch(r'-?\d+(\.\d+)?', norm(s).replace(',', '')) is not None

def numv(s):
    v = norm(s).replace(',', '')
    if v in ('-', '−', '―', '…'): return '0'
    return str(int(float(v))) if re.fullmatch(r'-?\d+\.0+', v) else v

def seigo_rows(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    out = []
    for ws in wb.worksheets:
        for r in ws.iter_rows(values_only=True):
            v = [x for x in r if x is not None and str(x).strip() != '']
            if len(v) >= 5 and re.match(r'第\d+表', norm(v[0])):
                sd = norm(v[1])
                sd = re.sub(r'^総数(男|女)$', r'\1', sd)
                out.append(dict(table=int(re.search(r'\d+', norm(v[0]))[0]), side=sd,
                                head=norm(v[2]), wrong=numv(v[-2]), right=numv(v[-1])))
    return out

@functools.lru_cache(None)
def table_rows(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    rows, parent = [], ''
    for ws in wb.worksheets:
        for r in ws.iter_rows(values_only=True):
            cells = [x for x in r if x is not None and str(x).strip() != '']
            if not cells: continue
            labels = [norm(x) for x in cells if not isnum(x) and not hasattr(x, 'year')]
            nums = [numv(x) for x in cells if isnum(x)]
            if not nums: continue
            if labels and labels[0] not in ('男', '女'):
                parent = ''.join(l for l in labels if l not in ('男', '女', '総数'))
                # 年の行（例 '令和','7','年','総数'）は数値の 7 が nums に入るため、先頭の小さな数を年として扱う
            full = parent + ''.join(labels)
            rows.append((full, ''.join(labels), nums))
    return rows

@functools.lru_cache(None)
def colmap(path):
    """列ごとの見出し文字列（上の行の見出しを横に引き継いで連結）。データ行は raw の列位置で返す。"""
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.worksheets[0]
    raw = [list(r) for r in ws.iter_rows(values_only=True)]
    first = next(i for i, r in enumerate(raw) if sum(1 for x in r if x is not None and isnum(x)) >= 3)
    ncol = max(len(r) for r in raw)
    heads = [''] * ncol
    for r in raw[:first]:
        carry = ''
        for j in range(ncol):
            x = r[j] if j < len(r) else None
            if x is not None and str(x).strip() and not isnum(x):
                carry = norm(x)
                heads[j] += carry
            elif carry and j < ncol:
                heads[j] += carry if False else ''
    return heads, raw[first:]

def colcheck(e, path, year):
    heads, data = colmap(path)
    h = e['head'].replace('　', '')
    js = [j for j, t in enumerate(heads) if t and (t == h or t.endswith(h) or h.endswith(t) and len(t) >= 2)]
    if len(js) != 1: return None
    j = js[0]
    rows = table_rows_raw(data)
    c = cands(e, [(f, l, n) for f, l, n, _ in rows], year)
    keys = {id(n) for _, _, n in c}
    vals = [numv(raw[j]) if j < len(raw) and raw[j] is not None else '' for f, l, n, raw in rows if id(n) in keys]
    if not vals: return None
    if e['right'] in vals and e['wrong'] not in vals: return '反映'
    if e['wrong'] in vals and e['right'] not in vals: return '未反映'
    return None

def table_rows_raw(data):
    rows, parent = [], ''
    for r in data:
        cells = [x for x in r if x is not None and str(x).strip() != '']
        if not cells: continue
        labels = [norm(x) for x in cells if not isnum(x) and not hasattr(x, 'year')]
        nums = [numv(x) for x in cells if isnum(x)]
        if not nums: continue
        if labels and labels[0] not in ('男', '女'):
            parent = ''.join(l for l in labels if l not in ('男', '女', '総数'))
        rows.append((parent + ''.join(labels), ''.join(labels), nums, r))
    return rows

def cands(e, trs, year):
    yr = {'2025': '7', '2022': '4'}[year]
    m = re.fullmatch(r'(\d+)(総数|男|女)', e['side'])
    if m:  # 年ブロック：「総数」行の nums 先頭が年、男・女はその直後の行
        out, inblk = [], False
        for full, lab, nums in trs:
            if lab.endswith('総数'):
                inblk = (nums and nums[0] == m[1] and m[1] == yr) or ('令和' + yr + '年' in full)
            if inblk and lab.endswith(m[2]):
                out.append((full, lab, nums))
        return out
    s = e['side']
    sub = re.fullmatch(r'(.+?)(総数|男|女|計)', s)
    out = [t for t in trs if t[0] == s or t[0].endswith(s)]
    if not out and sub:
        out = [t for t in trs if t[0].startswith(sub[1]) and t[1].endswith(sub[2])]
    return out

res = []
for fn, year in sorted(SEIGO.items()):
    p = os.path.join(root, 'data/raw/moj_seigo/kyosei', fn)
    if not os.path.exists(p): continue
    for e in seigo_rows(p):
        tp = glob.glob(os.path.join(root, f'data/raw/kyosei/{year}/{year[2:]}-00-{e["table"]:02d}.xlsx'))
        if not tp:
            res.append({**e, 'year': year, 'src': fn, 'status': 'ファイルなし', 'n_cand': 0}); continue
        c = cands(e, table_rows(tp[0]), year)
        st = '判定不能'
        try:
            cc = colcheck(e, tp[0], year)
        except StopIteration:
            cc = None
        if cc:
            st = cc + '(列)'
        elif c:
            hasR = any(e['right'] in t[2] for t in c)
            hasW = any(e['wrong'] in t[2] for t in c)
            if hasR and not hasW: st = '反映'
            elif hasW and not hasR: st = '未反映'
        res.append({**e, 'year': year, 'src': fn, 'status': st, 'n_cand': len(c)})

# 同じ箇所を後の正誤表が訂正し直した場合は、最後のものだけで判定する
last = {}
for i, r in enumerate(res):
    last[(r['year'], r['table'], r['side'], r['head'])] = r['src']
for i, r in enumerate(res):
    if last[(r['year'], r['table'], r['side'], r['head'])] != r['src']:
        r['status'] = '後の正誤表で再訂正'
os.makedirs(os.path.join(root, 'results/kyosei'), exist_ok=True)
keys = ['year', 'src', 'table', 'side', 'head', 'wrong', 'right', 'status', 'n_cand']
with open(os.path.join(root, 'results/kyosei/c2701_seigo.tsv'), 'w') as f:
    f.write('\t'.join(keys) + '\n')
    for r in res: f.write('\t'.join(str(r.get(k, '')) for k in keys) + '\n')
for y in ('2025', '2022'):
    print(y, dict(Counter(r['status'] for r in res if r['year'] == y)))
for r in res:
    if r['status'].startswith('未反映'):
        print('NOT_APPLIED', r['year'], r['src'], r['table'], r['side'], r['head'], r['wrong'], '->', r['right'])

# 照合の要約（lib/tally.py）：単位は正誤情報の訂正1件。現行ファイルに訂正後の値が入っていれば一致、訂正前の値なら食い違い。
# 判定不能（表側の書き方が現行の行と合わない）・ファイルなしは読み取りの失敗。後の正誤表で同じ箇所が再訂正されたものは、後の訂正で判定するので数えない。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('kyosei', 'c2701', note='矯正統計年報：法務省の統計の正誤情報の訂正が現行ファイルに入っているか', script=__file__)
for r in res:
    s = r['status']
    if s.startswith('反映'): _t.ok()
    elif s.startswith('未反映'): _t.ng()
    elif s != '後の正誤表で再訂正': _t.fail()
print('tally', _t.save())
