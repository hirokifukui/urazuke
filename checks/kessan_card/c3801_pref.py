"""c3801 都道府県決算カード（令和6年度・令和5年度、総務省、Excel 47シート）の収支の恒等式と版間。
各シートで、見出しの右に並ぶ数値（当年度・前年度）を読む。
- 歳入歳出差引 = 歳入総額 − 歳出総額
- 実質収支 = 歳入歳出差引 − 翌年度に繰り越すべき財源
- 単年度収支 = 実質収支（当年度） − 実質収支（前年度）
- 実質単年度収支 = 単年度収支 + 積立金 + 繰上償還金 − 積立金取崩し額
- 「歳入の状況」の歳入合計 = 歳入総額
- 版間：令和6年度カードの「令和5年度」欄 = 令和5年度カードの「令和5年度」欄（収支の8項目）
使い方: c3801_pref.py [root]   出力: results/kessan_card/c3801.tsv"""
import sys, os, re, unicodedata, openpyxl
root = sys.argv[1] if len(sys.argv) > 1 else '.'
D = os.path.join(root, 'data/raw/kessan_card/pref')
out = []; n = 0
ITEMS = ['歳入総額', '歳出総額', '歳入歳出差引', '翌年度に繰り越すべき', '実質収支', '単年度収支', '積立金', '繰上償還金', '積立金取崩し額', '実質単年度収支']

def val(x):
    if x is None: return None
    s = unicodedata.normalize('NFKC', str(x)).strip().replace(',', '')
    if s in ('-', '−', '―'): return 0
    try: return int(float(s))
    except: return None

def card(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    res = {}
    for ws in wb.worksheets[1:]:
        name = re.sub(r'^\d+', '', ws.title)
        g = [list(r) for r in ws.iter_rows(values_only=True)]
        d = {}
        for r in g:
            for j, x in enumerate(r):
                if x is None: continue
                lab = re.sub(r'\s+', '', unicodedata.normalize('NFKC', str(x)))
                if lab.startswith('翌年度に繰り越すべき'): lab = '翌年度に繰り越すべき'
                if lab in ITEMS and lab not in d:
                    nums = [val(y) for y in r[j + 1:j + 25] if val(y) is not None]
                    if len(nums) >= 2: d[lab] = nums[:2]
                if lab == '歳入合計' and '歳入合計' not in d:
                    nums = [val(y) for y in r[j + 1:j + 12] if val(y) is not None]
                    if nums: d['歳入合計'] = nums[:1]
        res[name] = d
    return res

def chk(ed, pref, what, a, b):
    global n
    n += 1
    if a != b: out.append((ed, pref, what, a, b))

C = {'R06': card(f'{D}/R06_pref_card.xlsx'), 'R05': card(f'{D}/R05_pref_card.xlsx')}
for ed, cards in C.items():
    if len(cards) != 47: out.append((ed, '', f'シート数{len(cards)}', '', ''))
    for pref, d in cards.items():
        miss = [k for k in ITEMS if k not in d]
        if miss: out.append((ed, pref, '読めない項目', ','.join(miss), '')); continue
        for j, col in ((0, '当年度'), (1, '前年度')):
            g = lambda k: d[k][j]
            chk(ed, pref, f'{col} 差引=歳入−歳出', g('歳入歳出差引'), g('歳入総額') - g('歳出総額'))
            chk(ed, pref, f'{col} 実質収支=差引−翌年度繰越財源', g('実質収支'), g('歳入歳出差引') - g('翌年度に繰り越すべき'))
            chk(ed, pref, f'{col} 実質単年度収支', g('実質単年度収支'), g('単年度収支') + g('積立金') + g('繰上償還金') - g('積立金取崩し額'))
        chk(ed, pref, '単年度収支=実質収支の差', d['単年度収支'][0], d['実質収支'][0] - d['実質収支'][1])
        if '歳入合計' in d: chk(ed, pref, '歳入の状況の合計=歳入総額', d['歳入合計'][0], d['歳入総額'][0])
for pref, d6 in C['R06'].items():
    d5 = C['R05'].get(pref)
    if not d5: continue
    for k in ITEMS:
        if k in d6 and k in d5:
            chk('版間', pref, f'{k}：R6カードの前年度欄=R5カードの当年度欄', d5[k][0], d6[k][1])
os.makedirs(os.path.join(root, 'results/kessan_card'), exist_ok=True)
with open(os.path.join(root, 'results/kessan_card/c3801.tsv'), 'w') as fo:
    fo.write('版\t都道府県\t式\t値1\t値2\n')
    for o in out: fo.write('\t'.join(map(str, o)) + '\n')
print('式の数', n, '不一致', len(out))
for o in out[:40]: print(*o)

# 照合の要約（lib/tally.py）：単位は式。不一致1（KC-A1）は資料どうしの食い違い。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('kessan_card', 'c3801', note='都道府県決算カード：収支の式、歳入の合計、版間', script=__file__)
_t.set(compared=n, mismatched=len(out), read_failures=0, explained=None); print('tally', _t.save())
