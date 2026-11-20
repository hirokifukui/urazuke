"""c2801 人口推計（各年10月1日現在、2023年・2024年）の点検。単位は千人で四捨五入されているため、許容幅を置く。
(a) 第2表 男+女=男女計（±1）、都道府県の和=全国（±24）
(b) 第3表 3区分の和=第2表の男女計（±2）、男+女=男女計（±1）
(c) 第1表 各歳の男+女=男女計（±1）
(d) 版間：参考表2（男女別人口の累年）の同じ年の値が 2023年版と2024年版で同じか
使い方: c2801_suikei.py [root]  出力: results/jinko_suikei/c2801.tsv"""
import sys, os, re, unicodedata, openpyxl
root = sys.argv[1] if len(sys.argv) > 1 else '.'
D = os.path.join(root, 'data/raw/jinko_suikei')
out = []

def n(x):
    try: return float(str(x).replace(',', ''))
    except: return None

def rows(path):
    ws = openpyxl.load_workbook(path, data_only=True).worksheets[0]
    return [[x for x in r if x is not None and str(x).strip() != ''] for r in ws.iter_rows(values_only=True) if any(x is not None and str(x).strip() for x in r)]

def label(r):
    return unicodedata.normalize('NFKC', ''.join(str(x) for x in r if n(x) is None)).replace(' ', '').replace('　', '')

_C = [0]  # 照合の要約用：比べた式の数
for y in ('2023', '2024'):
    t2 = {}
    for r in rows(f'{D}/{y}np/05k{y}-2.xlsx'):
        nums = [n(x) for x in r if n(x) is not None]
        lab = label(r)
        if lab == '全国' or re.match(r'^\d\d', str(r[0])) and len(nums) >= 9:
            if re.match(r'^\d\d', str(r[0])): nums = nums[1:]
            if len(nums) < 8: continue
            t2[lab] = nums
            for k, off in (('総人口', 0), ('日本人人口', 4)):
                _C[0] += 1
                if abs(nums[off + 1] + nums[off + 2] - nums[off]) > 1:
                    out.append((y, '第2表', lab, k, '男+女≠男女計', nums[off], nums[off + 1] + nums[off + 2]))
    prefs = [v for k, v in t2.items() if k != '全国']
    if len(prefs) == 47:
        for j, nm in enumerate(['総人口男女計', '総人口男', '総人口女', '', '日本人男女計', '日本人男', '日本人女']):
            if not nm: continue
            s = sum(p[j] for p in prefs); _C[0] += 1
            if abs(s - t2['全国'][j]) > 24:
                out.append((y, '第2表', '全国', nm, '都道府県和≠全国', t2['全国'][j], s))
    else:
        out.append((y, '第2表', '', '', f'都道府県の行数{len(prefs)}', '', ''))
    for r in rows(f'{D}/{y}np/05k{y}-3.xlsx'):
        nums = [n(x) for x in r if n(x) is not None]
        lab = label(r)
        if re.match(r'^\d\d', str(r[0])): nums = nums[1:]
        if lab in t2 and len(nums) >= 12:
            tot = nums[0] + nums[1] + nums[2]; _C[0] += 5
            if abs(tot - t2[lab][0]) > 2:
                out.append((y, '第3表', lab, '3区分和', '≠第2表男女計', t2[lab][0], tot))
            for j in range(4):
                a, b, c = nums[j], nums[4 + j], nums[8 + j]
                if abs(b + c - a) > 1:
                    out.append((y, '第3表', lab, ['15歳未満', '15～64歳', '65歳以上', '75歳以上'][j], '男+女≠男女計', a, b + c))
    for r in rows(f'{D}/{y}np/05k{y}-1.xlsx'):
        if len(r) not in (9, 18): continue
        for i in range(0, len(r), 9):
            blk = r[i:i + 9]
            v = [n(x) for x in blk[1:]]
            if None in v: continue
            for off, k in ((0, '総人口'), (4, '日本人人口')):
                _C[0] += 1
                if abs(v[off + 1] + v[off + 2] - v[off]) > 1:
                    out.append((y, '第1表', label([blk[0]]) or str(blk[0]).strip(), k, '男+女≠男女計', v[off], v[off + 1] + v[off + 2]))

def ref2(y):
    d = {}
    for r in rows(f'{D}/{y}np/05k{y}-5.xlsx'):
        for i, x in enumerate(r):
            if re.fullmatch(r'(19|20)\d\d', str(x).strip()):
                vals = [n(v) for v in r[i + 1:i + 6] if n(v) is not None and n(v) > 1000][:3]
                if len(vals) == 3: d[int(str(x))] = vals
    return d
a, b = ref2('2023'), ref2('2024')
common = sorted(set(a) & set(b))
for yr in common:
    if a[yr] != b[yr]:
        out.append(('2023→2024', '参考表2', str(yr), '', '版間で値が違う', a[yr], b[yr]))
os.makedirs(os.path.join(root, 'results/jinko_suikei'), exist_ok=True)
with open(os.path.join(root, 'results/jinko_suikei/c2801.tsv'), 'w') as f:
    f.write('版\t表\t行\t項目\t内容\t表の値\t計算値\n')
    for o in out: f.write('\t'.join(map(str, o)) + '\n')
print('参考表2 共通年', len(common), '範囲', common[:1], common[-1:])
print('不一致', len(out))
for o in out[:40]: print(*o)

# 照合の要約（lib/tally.py）：単位は式（男＋女、都道府県の和、3区分の和）と参考表2の版間の年。都道府県の行が47でない表は読み取りの失敗。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('jinko_suikei', 'c2801', note='人口推計：表の内部整合と版間', script=__file__)
_rf = sum(1 for o in out if str(o[4]).startswith('都道府県の行数'))
_t.set(compared=_C[0] + len(common), mismatched=len(out) - _rf, read_failures=_rf); print('tally', _t.save())
