"""c3002 保護統計年報の医療観察法の3表（生活環境調査・生活環境調整・精神保健観察）。H009 の計画どおり。
- L1：繰越+開始総数−終結総数=年末、開始総数=開始の内訳の和、終結総数=終結の内訳の和、観察所の和=その年の総数
- 版間：累年の行（各版にある過去5年）の同じ年の値が、版ごとに同じか。前年の版の年末=当年の版の繰越
使い方: c3002_hogo_mhoa.py [root]   出力: results/iryokansatsu/c3002.tsv"""
import sys, os, re, glob, unicodedata
from collections import defaultdict
root = sys.argv[1] if len(sys.argv) > 1 else '.'
sys.path.insert(0, os.path.join(root, 'lib'))
from seigo import layout, raw_rows, isnum, numv, norm
D = os.path.join(root, 'data/raw/iryokansatsu/hogo')
KINDS = {'調査': ('前年からの繰越し', '開始', '終結総数', '年末現在調査中'),
         '調整': ('前年からの繰越し', '開始総数', '総数', '年末現在調整中'),
         '観察': ('前年からの繰越し', '開始総数', '総数', '年末現在観察中')}
out = []; n = 0
hist = defaultdict(dict)  # (kind, year) -> {edition: vals}

def kind_of(heads):
    hs = ''.join(heads)
    if '年末現在調査中' in hs: return '調査'
    if '年末現在調整中' in hs: return '調整'
    if '年末現在観察中' in hs: return '観察'

def chk(ed, kind, where, what, a, b):
    global n
    n += 1
    if a != b: out.append((ed, kind, where, what, a, b))

for path in sorted(glob.glob(f'{D}/*/*.xls*')):
    ed = int(path.split('/')[-2])
    heads, _ = layout(path)
    kind = kind_of(heads)
    if not kind: continue
    raw = raw_rows(path)
    title = unicodedata.normalize('NFKC', next(str(x) for row in raw[:4] for x in row if x))
    base_kind = kind
    if kind == '調査': kind = '調査49・50条' if '49' in title else '調査33条'
    col = {h: j for j, h in enumerate(heads) if h}
    def jc(name):
        js = [j for j, h in enumerate(heads) if h == name]
        return js[0] if js else None
    c_carry, c_open, c_close, c_end = (jc(x) for x in KINDS[base_kind])
    open_parts = [j for j, h in enumerate(heads) if h.startswith('開始') and h not in ('開始', '開始総数')]
    close_parts = [j for j, h in enumerate(heads) if (h.startswith('終結') and h != '終結総数') or h in ('退院許可決定', '医療を終了する決定', '入院決定の取消し', 'その他', '移送', '期間満了', '(再)入院決定', '通院決定等の取消し')]
    era_y = None; office_sum = None; total_row = None
    for r in raw:
        vals = {}
        for j in [c_carry, c_open, c_close, c_end] + open_parts + close_parts:
            if j is not None and j < len(r) and r[j] is not None and isnum(r[j]): vals[j] = int(numv(r[j]))
        if c_carry not in vals or c_end not in vals: continue
        first = next((x for x in r[:c_carry] if x is not None and str(x).strip()), '')
        lab = re.sub(r'\s+', '', unicodedata.normalize('NFKC', str(first)))
        m = re.match(r'(平成|令和)(元|\d+)年', lab)
        y = None
        if m:
            era = m[1]; y = (1988 if era == '平成' else 2018) + (1 if m[2] == '元' else int(m[2])); era_y = era
        elif re.fullmatch(r'\d+(\.0)?', lab) and era_y:
            y = (1988 if era_y == '平成' else 2018) + int(float(lab))
            if era_y == '平成' and int(float(lab)) <= 2: y = 2018 + int(float(lab))  # 令和へ切り替わった行の数字
        where = str(y) if y else lab[:12]
        chk(ed, kind, where, '繰越+開始−終結=年末', vals.get(c_end), vals.get(c_carry, 0) + vals.get(c_open, 0) - vals.get(c_close, 0))
        op = [vals[j] for j in open_parts if j in vals]
        if op and len(op) == len(open_parts): chk(ed, kind, where, '開始総数=内訳の和', vals.get(c_open), sum(op))
        cp = [vals[j] for j in close_parts if j in vals]
        if cp and len(cp) == len(close_parts): chk(ed, kind, where, '終結総数=内訳の和', vals.get(c_close), sum(cp))
        if y:
            hist[(kind, y)][ed] = (vals.get(c_carry), vals.get(c_open), vals.get(c_close), vals.get(c_end))
            total_row = (y, vals); office_sum = defaultdict(int)
        elif office_sum is not None and '委員会' not in lab and lab not in ('総数', '計', '') and not lab.startswith('('):
            for j, v in vals.items(): office_sum[j] += v
    if total_row and office_sum:
        y, tv = total_row
        for j in (c_carry, c_open, c_close, c_end):
            if j in tv: chk(ed, kind, f'{y}観察所の和', heads[j], tv[j], office_sum.get(j))

for (kind, y), eds in sorted(hist.items()):
    vs = set(eds.values())
    if len(vs) > 1:
        out.append(('版間', kind, str(y), '同じ年の値が版で違う', str(sorted(eds.items())), ''))
    n += 1
    nxt = hist.get((kind, y + 1), {})
    for ed, v in eds.items():
        for ed2, v2 in nxt.items():
            n += 1
            if v[3] is not None and v2[0] is not None and v[3] != v2[0]:
                out.append(('版間', kind, f'{y}→{y + 1}', f'{ed}版の年末≠{ed2}版の翌年繰越', v[3], v2[0]))
os.makedirs(os.path.join(root, 'results/iryokansatsu'), exist_ok=True)
with open(os.path.join(root, 'results/iryokansatsu/c3002.tsv'), 'w') as f:
    f.write('版\t表\t場所\t式\t表の値\t計算値\n')
    for o in out: f.write('\t'.join(map(str, o)) + '\n')
print('式の数', n, '不一致', len(out))
for o in out[:40]: print(*o)

# 照合の要約（lib/tally.py）：単位は式（内部整合と版間）。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('iryokansatsu', 'c3002', note='保護統計の医療観察の表：受理・終結・繰越の式、版間', script=__file__)
_t.set(compared=n, mismatched=len(out)); print('tally', _t.save())
