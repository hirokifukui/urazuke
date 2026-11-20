"""c2702 保護統計年報：法務省「正誤情報」の訂正が、e-Stat の現行の年報ファイルに反映されているか。
対象：直近3本の正誤表（令和7年7月31日・令和7年11月28日・令和8年7月31日掲載）。正誤表はシートごとに年が違う（シート名から年を取る）。
判定は lib/seigo.py の列判定だけを使う（表側の行と表頭の列が一つに定まり、そのセルに正があって誤がない → 反映、逆 → 未反映、他は判定不能）。
同じ年・表・表側・表頭を後の正誤表が訂正し直したときは、後のものだけで判定する。
出力: results/hogo/c2702_seigo.tsv、要約は掲載日×年×表ごと。e-Stat の公開（更新）日を並べる。
使い方: c2702_seigo_applied.py [root] [--list]（--list は必要な年・表の一覧だけを出す）"""
import sys, os, re, glob, openpyxl, xlrd, unicodedata
from collections import Counter, defaultdict
root = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '.'
sys.path.insert(0, os.path.join(root, 'lib'))
from seigo import norm, numv, judge
FILES = [('001443898.xls', '2025-07-31'), ('001450763.xls', '2025-11-28'), ('001467364.xlsx', '2026-07-31')]
KIND = {'観察所': 'kansatsu', '委員会': 'iinkai'}
CLS = {'kansatsu': '000001013297', 'iinkai': '000001013296'}

def sheets(p):
    if p.endswith('xlsx'):
        wb = openpyxl.load_workbook(p, data_only=True)
        return [(ws.title, [[x for x in r if x is not None and str(x).strip() != ''] for r in ws.iter_rows(values_only=True)]) for ws in wb.worksheets]
    bk = xlrd.open_workbook(p)
    return [(s.name, [[x for x in s.row_values(i) if str(x).strip() != ''] for i in range(s.nrows)]) for s in bk.sheets()]

def entries():
    for fn, posted in FILES:
        for name, rows in sheets(os.path.join(root, 'data/raw/moj_seigo/hogo', fn)):
            m = re.search(r'(20\d\d)', unicodedata.normalize('NFKC', name))
            if not m: continue
            year = m[1]
            for r in rows:
                if not r or r[0] not in KIND: continue
                nums = [x for x in r[1:4] if re.fullmatch(r'\d+(\.0)?', str(x))]
                if not nums or len(r) < 6: continue
                tno = int(float(nums[-1]))
                rest = r[1 + r[1:].index(nums[-1]) + 1:]
                if len(rest) < 4: continue
                yield dict(src=fn, posted=posted, year=year, kind=KIND[r[0]], table=tno,
                           side=norm(rest[0]), head=norm(rest[1]), wrong=numv(rest[-2]), right=numv(rest[-1]))

ents = list(entries())
if '--list' in sys.argv:
    for k in sorted({(e['year'], e['kind'], e['table']) for e in ents}): print(*k)
    sys.exit()

pub = {}
for f in glob.glob(os.path.join(root, 'data/raw/hogo/LIST_*.txt')):
    for l in open(f):
        p = l.rstrip('\n').split('\t')
        if len(p) >= 6: pub[(p[0], p[2])] = p[5]

res = []
for e in ents:
    tid = f'{e["year"][2:]}-00-{e["table"]:02d}'
    tp = glob.glob(os.path.join(root, f'data/raw/hogo/{e["year"]}/{e["kind"]}/{tid}.xls*'))
    e['estat_date'] = pub.get((CLS[e['kind']], tid), '')
    try:
        e['status'] = judge(e, tp[0]) if tp else 'ファイルなし'
    except Exception as ex:
        e['status'] = '読めない'
    res.append(e)
last = {}
for r in res: last[(r['year'], r['kind'], r['table'], r['side'], r['head'])] = r['src']
for r in res:
    if last[(r['year'], r['kind'], r['table'], r['side'], r['head'])] != r['src']: r['status'] = '後の正誤表で再訂正'

os.makedirs(os.path.join(root, 'results/hogo'), exist_ok=True)
keys = ['posted', 'src', 'year', 'kind', 'table', 'estat_date', 'side', 'head', 'wrong', 'right', 'status']
with open(os.path.join(root, 'results/hogo/c2702_seigo.tsv'), 'w') as f:
    f.write('\t'.join(keys) + '\n')
    for r in res: f.write('\t'.join(str(r.get(k, '')) for k in keys) + '\n')
summ = defaultdict(Counter)
for r in res: summ[(r['posted'], r['year'], r['kind'], r['table'], r['estat_date'])][r['status']] += 1
print('全体', dict(Counter(r['status'] for r in res)))
for k in sorted(summ):
    c = summ[k]
    if c.get('未反映(列)'): print('TABLE', *k, dict(c))

# 照合の要約（lib/tally.py）：単位は正誤情報の訂正1件。c2701 と同じ分け方。未反映(列)の1件（令和5年 第21表「（うち女子）」）は、表側の名前が
# 複数の行に当たる読み違い（作業ノート）＝読み取りの失敗。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('hogo', 'c2702', note='保護統計年報：法務省の統計の正誤情報の訂正が現行ファイルに入っているか', script=__file__)
for r in res:
    s = r['status']
    if s.startswith('反映'): _t.ok()
    elif s != '後の正誤表で再訂正': _t.fail()
print('tally', _t.save())
