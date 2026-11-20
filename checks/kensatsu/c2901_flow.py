"""c2901 検察統計年報（令和7年、e-Stat）の受理・既済・未済の恒等式。
第1表（件数の累年）・第2表（人員の累年）：
  受理総数=旧受+新受、既済総数=内訳の和、未済=受理総数−既済総数、旧受(t)=未済(t−1)
第6表（検察庁別、人員）：受理総数=旧受+新受計、新受計=通常受理計+他庁から+家裁から+再起、
  通常受理計=認知・直受+司法警察員から、既済総数=起訴計+不起訴計+中止+他庁送致、
  起訴計=公判請求+略式、不起訴計=起訴猶予+嫌疑不十分+その他、未済=受理総数−既済総数、
  全国総数=最高検+高検+地検+区検
「×」は該当なしとして 0 扱いにはせず、その年の式を飛ばす。
使い方: c2901_flow.py [root] [year]   出力: results/kensatsu/c2901.tsv"""
import sys, os, re, unicodedata
root = sys.argv[1] if len(sys.argv) > 1 else '.'
Y = sys.argv[2] if len(sys.argv) > 2 else '2025'
sys.path.insert(0, os.path.join(root, 'lib'))
from seigo import raw_rows
out = []; nchk = 0

def iv(x):
    s = unicodedata.normalize('NFKC', str(x)).replace(',', '').strip()
    if s in ('-', '−', '―'): return 0
    return int(float(s)) if re.fullmatch(r'-?\d+(\.0+)?', s) else None

def data_rows(path):
    for r in raw_rows(path):
        cells = [x for x in r if x is not None and str(x).strip() != '']
        if not cells: continue
        yield cells

def era_rows(path, ncols):
    """累年表：行頭の年（元号付きか数字だけ）を西暦にし、数値列 ncols 個を返す。"""
    base = {'明治': 1867, '大正': 1911, '昭和': 1925, '平成': 1988, '令和': 2018}
    era = None
    for cells in data_rows(path):
        lab = unicodedata.normalize('NFKC', str(cells[0])).replace(' ', '')
        m = re.match(r'(明治|大正|昭和|平成|令和)?(元|\d+)$', lab)
        if not m: continue
        if m[1]: era = m[1]
        if not era: continue
        n = 1 if m[2] == '元' else int(m[2])
        vals = cells[1:1 + ncols]
        if len(vals) < ncols: continue
        yield base[era] + n, lab, [iv(v) for v in vals]

def chk(tbl, key, name, lhs, rhs_terms):
    global nchk
    if lhs is None or any(t is None for t in rhs_terms): return
    nchk += 1
    if lhs != sum(rhs_terms): out.append((tbl, key, name, lhs, sum(rhs_terms)))

D = os.path.join(root, f'data/raw/kensatsu/{Y}')
yy = Y[2:]
# 第1表: 受理(総数,旧受,新受) 既済(総数,起訴,不起訴,中止,移送) 未済
prev = None
for yr, lab, v in era_rows(f'{D}/{yy}-00-01.xlsx', 9):
    t, old, new, d, k, f, c, mv, u = v
    chk('第1表', yr, '受理総数=旧受+新受', t, [old, new])
    chk('第1表', yr, '既済総数=起訴+不起訴+中止+移送・送致', d, [k, f, c, mv])
    chk('第1表', yr, '未済=受理−既済', u, [t, -d if d is not None else None])
    if prev and prev[0] == yr - 1: chk('第1表', yr, '旧受=前年の未済', old, [prev[1]])
    prev = (yr, u)
# 第2表: 受理(総数,旧受,新受) 既済(総数,起訴,不起訴計,起訴猶予,その他,中止,移送) 未済
prev = None
for yr, lab, v in era_rows(f'{D}/{yy}-00-02.xlsx', 11):
    t, old, new, d, k, f, fy, fo, c, mv, u = v
    chk('第2表', yr, '受理総数=旧受+新受', t, [old, new])
    chk('第2表', yr, '既済総数=起訴+不起訴+中止+移送・送致', d, [k, f, c, mv])
    chk('第2表', yr, '不起訴計=起訴猶予+その他', f, [fy, fo])
    chk('第2表', yr, '未済=受理−既済', u, [t, -d if d is not None else None])
    if prev and prev[0] == yr - 1: chk('第2表', yr, '旧受=前年の未済', old, [prev[1]])
    prev = (yr, u)
# 第6表
rows6 = {}
order = []
for cells in data_rows(f'{D}/{yy}-00-06.xlsx'):
    labs = [unicodedata.normalize('NFKC', str(x)).replace(' ', '').replace('　', '') for x in cells if iv(x) is None]
    nums = [iv(x) for x in cells if iv(x) is not None]
    if len(nums) < 22 or not labs: continue
    lab = labs[0]
    key = lab if lab not in rows6 else f'{lab}#{len(order)}'
    rows6[key] = nums; order.append(key)
    t, old, newk, newt, ninchi, keisatsu, tacho, kasai, saiki, d, kk, kou, ryaku, fk, yu, kenfu, sono, chu, sochi = nums[:19]
    u = nums[19] if len(nums) > 19 else None
    chk('第6表', key, '受理総数=旧受+新受計', t, [old, newk])
    chk('第6表', key, '新受計=通常受理計+他庁から+家裁から+再起', newk, [newt, tacho, kasai, saiki])
    chk('第6表', key, '通常受理計=認知・直受+司法警察員から', newt, [ninchi, keisatsu])
    chk('第6表', key, '既済総数=起訴計+不起訴計+中止+他庁送致', d, [kk, fk, chu, sochi])
    chk('第6表', key, '起訴計=公判請求+略式', kk, [kou, ryaku])
    chk('第6表', key, '不起訴計=起訴猶予+嫌疑不十分+その他', fk, [yu, kenfu, sono])
    if u is not None: chk('第6表', key, '未済=受理総数−既済総数', u, [t, -d])
if all(k in rows6 for k in ('総数', '最高検察庁', '高等検察庁', '地方検察庁', '区検察庁')):
    for j in range(len(rows6['総数'])):
        chk('第6表', f'列{j + 1}', '総数=最高検+高検+地検+区検', rows6['総数'][j],
            [rows6[k][j] for k in ('最高検察庁', '高等検察庁', '地方検察庁', '区検察庁')])
os.makedirs(os.path.join(root, 'results/kensatsu'), exist_ok=True)
with open(os.path.join(root, 'results/kensatsu/c2901.tsv'), 'w') as f:
    f.write('表\t行\t式\t表の値\t計算値\n')
    for o in out: f.write('\t'.join(map(str, o)) + '\n')
print('式の数', nchk, '不一致', len(out))
for o in out[:40]: print(*o)

# 照合の要約（lib/tally.py）：単位は式。説明あり：第2表 昭和32〜35年の既済（注6：併合の数を内数で示す）、第1表 明治16年〜大正元年の旧受（注3などの定義の違い）。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('kensatsu', 'c2901', label=Y if Y != '2025' else '', note='検察統計年報：受理・既済・未済の恒等式', script=__file__)
_t.set(compared=nchk, mismatched=0)
for o in out:
    _e = (o[0] == '第2表' and o[2].startswith('既済総数') and 1957 <= int(o[1]) <= 1960) or (o[0] == '第1表' and o[2] == '旧受=前年の未済' and int(o[1]) <= 1912)
    _t.d['mismatched'] += 1; _t.d['explained'] = (_t.d['explained'] or 0) + (1 if _e else 0)
print('tally', _t.save())
