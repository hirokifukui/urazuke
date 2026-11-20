"""c3001 医療観察法（厚生労働省の公表ページ）の表の恒等式。H009 の計画どおり。
- 入院対象者の状況：男+女=合計、各列の内訳の和=合計行、ステージ別の合計=疾病別の合計
- 指定入院医療機関：国関係・都道府県関係の病床数の和=本文の「病床数」（全国・うち国・都道府県）
- 指定通院医療機関：行（病院+診療所+薬局+訪問看護=計）と列（都道府県の和=合計）
- 地方裁判所の審判：終局処理人員総数=内訳の和
使い方: c3001_mhlw.py [root]  出力: results/iryokansatsu/c3001.tsv"""
import sys, os, re, html
root = sys.argv[1] if len(sys.argv) > 1 else '.'
sys.path.insert(0, os.path.join(root, 'lib'))
from htmltables import tables, num
D = os.path.join(root, 'data/raw/iryokansatsu/mhlw')
out = []; n = 0

def chk(page, where, what, lhs, rhs):
    global n
    if lhs is None or rhs is None: return
    n += 1
    if lhs != rhs: out.append((page, where, what, lhs, rhs))

ts = tables(f'{D}/nyuin.html')
tot = {}
for t in ts:
    rows = [r for r in t['rows'] if len(r) >= 4 and num(r[1]) is not None]
    body = [r for r in rows if r[0] != '合計']; last = [r for r in rows if r[0] == '合計']
    for r in rows: chk('入院対象者', f'{t["caption"]}/{r[0]}', '男+女=合計', num(r[3]), num(r[1]) + num(r[2]))
    if last:
        for j, nm in ((1, '男性'), (2, '女性'), (3, '合計')):
            chk('入院対象者', t['caption'], f'{nm} 内訳の和=合計行', num(last[0][j]), sum(num(r[j]) for r in body))
        tot[t['caption']] = num(last[0][3])
    else:
        tot[t['caption']] = sum(num(r[3]) for r in body)
if len(tot) == 2:
    a, b = list(tot.values()); chk('入院対象者', 'ステージ別/疾病別', '合計が同じ', a, b)

ts = tables(f'{D}/iryokikan_seibi.html')
beds = [sum(num(r[3]) for r in t['rows'] if len(r) >= 4 and num(r[3]) is not None) for t in ts]
txt = html.unescape(re.sub(r'<[^>]+>', '', open(f'{D}/iryokikan_seibi.html', encoding='utf-8').read()))
m = re.search(r'病床数：\s*([\d,]+)床\s*〔うち国関係：\s*([\d,]+)床\s*都道府県関係\s*([\d,]+)床', txt)
if m and len(beds) == 2:
    a, k, p = (int(x.replace(',', '')) for x in m.groups())
    chk('指定入院医療機関', '国関係', '表の病床数の和=本文', k, beds[0])
    chk('指定入院医療機関', '都道府県関係', '表の病床数の和=本文', p, beds[1])
    chk('指定入院医療機関', '全国', '国+都道府県=本文の全国', a, beds[0] + beds[1])

t = tables(f'{D}/iryokikan_sitei.html')[0]['rows']
body = [r for r in t[1:] if r[0] not in ('合計',) and num(r[1]) is not None]
last = [r for r in t if r[0] == '合計'][0]
for r in body + [last]: chk('指定通院医療機関', r[0], '病院+診療所+薬局+訪問看護=計', num(r[5]), sum(num(x) for x in r[1:5]))
for j in range(1, 6): chk('指定通院医療機関', t[0][j], '都道府県の和=合計', num(last[j]), sum(num(r[j]) for r in body))
chk('指定通院医療機関', '', '都道府県の行数', 47, len(body))

t = tables(f'{D}/kettei.html')[0]['rows']
vals = [(r[0], num(r[1])) for r in t if len(r) >= 2 and num(r[1]) is not None]
if vals and vals[0][0].startswith('終局処理人員総数'):
    chk('審判', t and '終局処理', '総数=内訳の和', vals[0][1], sum(v for _, v in vals[1:]))
os.makedirs(os.path.join(root, 'results/iryokansatsu'), exist_ok=True)
with open(os.path.join(root, 'results/iryokansatsu/c3001.tsv'), 'w') as f:
    f.write('ページ\t場所\t式\t公表値\t計算値\n')
    for o in out: f.write('\t'.join(map(str, o)) + '\n')
print('式の数', n, '不一致', len(out))
for o in out: print(*o)

# 照合の要約（lib/tally.py）：単位は式。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('iryokansatsu', 'c3001', note='医療観察法の入院対象者・指定医療機関（厚生労働省）：内訳の和と合計', script=__file__)
_t.set(compared=n, mismatched=len(out)); print('tally', _t.save())
