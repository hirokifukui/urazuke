"""c3101 建設工事受注動態統計 令和6年度計（令和8年6月12日一部訂正の版）の時系列表の恒等式。単位は百万円（推計値で小数あり）、許容は ±1。
受注高時系列（Ⅰ-1）：5区分（受注高合計・元請・公共・民間・下請）×（計・土木・建築・機械）
  計=土木+建築+機械、元請=公共+民間、受注高合計=元請+下請
  年度=四半期の和=月の和、暦年=月の和
公共工事時系列（Ⅱ-1）：合計=国の機関+地方の機関、国の機関=国+独法+政府関連企業等、地方=都道府県+市区町村+地方公営企業+その他
使い方: c3101_nendo.py [root]   出力: results/kensetsu_juchu/c3101.tsv"""
import sys, os, re, unicodedata, xlrd
root = sys.argv[1] if len(sys.argv) > 1 else '.'
D = os.path.join(root, 'data/raw/kensetsu_juchu/nendo')
out = []; n = 0
TOL = 1.0

def chk(f, where, what, a, b):
    global n
    n += 1
    if abs(a - b) > TOL: out.append((f, where, what, round(a, 3), round(b, 3)))

def rows(fn):
    s = xlrd.open_workbook(os.path.join(D, fn)).sheet_by_index(0)
    for i in range(s.nrows):
        v = s.row_values(i)
        lab = unicodedata.normalize('NFKC', str(v[0] if str(v[0]).strip() else (v[1] if len(v) > 1 else ''))).strip()
        nums = [x for x in v if isinstance(x, float)]
        yield i, lab, nums, v

def months_by_fy(rs, width):
    """月の行（『令和6年 4月』『5月』…）を (年, 月) にそろえる。"""
    cur_y = None; out_m = {}
    for i, lab, nums, v in rs:
        m = re.match(r'(平成|令和)(元|\d+)年\s*(\d+)月$', lab.replace(' ', ''))
        m2 = re.match(r'(\d+)月$', lab.replace(' ', ''))
        if m:
            cur_y = (1988 if m[1] == '平成' else 2018) + (1 if m[2] == '元' else int(m[2])); mo = int(m[3])
        elif m2 and cur_y: mo = int(m2[1])
        else: continue
        if len(nums) >= width and abs(nums[0]) >= 1000 and (cur_y, mo) not in out_m: out_m[(cur_y, mo)] = nums[:width]
    return out_m

# Ⅰ-1 受注高時系列：金額の部（最初の「前年比」見出しまで）
rs = []
for r in rows('R06_jikeiretsu.xls'):
    if any('前年比' in str(x) or '前年同期比' in str(x) for x in r[3]): break
    rs.append(r)
fy = {}; q = {}
for i, lab, nums, v in rs:
    if len(nums) < 20 or abs(nums[0]) < 1000: continue  # 前年比（%）の行を除く
    g = [nums[k:k + 4] for k in range(0, 20, 4)]  # 合計・元請・公共・民間・下請
    for name, x in zip(['受注高合計', '元請', '公共', '民間', '下請'], g):
        chk('受注高時系列', lab, f'{name} 計=土木+建築+機械', x[0], x[1] + x[2] + x[3])
    for k in range(4):
        chk('受注高時系列', lab, f'元請=公共+民間 列{k}', g[1][k], g[2][k] + g[3][k])
        chk('受注高時系列', lab, f'受注高合計=元請+下請 列{k}', g[0][k], g[1][k] + g[4][k])
    m = re.match(r'R(\d+)年度$', lab.replace(' ', ''))
    if m and 2018 + int(m[1]) not in fy: fy[2018 + int(m[1])] = nums[:20]
    m = re.match(r'R(\d+)\.\s*(\d+)-\s*(\d+)$', lab.replace(' ', ''))
    if m and (2018 + int(m[1]), int(m[2])) not in q: q[(2018 + int(m[1]), int(m[2]))] = nums[:20]
mon = months_by_fy(rs, 20)
for y in fy:
    qs = [q.get((y, 4)), q.get((y, 7)), q.get((y, 10)), q.get((y + 1, 1))]
    if all(qs):
        for k in range(20): chk('受注高時系列', f'{y}年度', f'年度=四半期の和 列{k}', fy[y][k], sum(x[k] for x in qs))
    ms = [mon.get((y, mo)) for mo in range(4, 13)] + [mon.get((y + 1, mo)) for mo in range(1, 4)]
    if all(ms):
        for k in range(20): chk('受注高時系列', f'{y}年度', f'年度=月の和 列{k}', fy[y][k], sum(x[k] for x in ms))
for (y, m0), x in q.items():
    ms = [mon.get((y, m0 + d)) for d in range(3)]
    if all(ms):
        for k in range(20): chk('受注高時系列', f'{y}.{m0}-', f'四半期=月の和 列{k}', x[k], sum(z[k] for z in ms))

# Ⅱ-1 公共工事時系列：金額と前年比が交互。金額だけ取る（偶数位置）
for i, lab, nums, v in rows('R06_koukyou_jikeiretsu.xls'):
    if len(nums) < 20 or abs(nums[0]) < 1000: continue
    a = nums[0::2][:10]
    tot, kuni, k1, k2, k3, chiho, c1, c2, c3, c4 = a
    chk('公共工事時系列', lab, '合計=国の機関+地方の機関', tot, kuni + chiho)
    chk('公共工事時系列', lab, '国の機関=国+独法+政府関連企業等', kuni, k1 + k2 + k3)
    chk('公共工事時系列', lab, '地方=都道府県+市区町村+地方公営企業+その他', chiho, c1 + c2 + c3 + c4)
os.makedirs(os.path.join(root, 'results/kensetsu_juchu'), exist_ok=True)
with open(os.path.join(root, 'results/kensetsu_juchu/c3101.tsv'), 'w') as f:
    f.write('表\t行\t式\t表の値\t計算値\n')
    for o in out: f.write('\t'.join(map(str, o)) + '\n')
print('式の数', n, '不一致', len(out), '年度', sorted(fy), '四半期', len(q), '月', len(mon))
for o in out[:30]: print(*o)

# 照合の要約（lib/tally.py）：単位は式。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('kensetsu_juchu', 'c3101', note='建設工事受注動態統計：計と内訳、年度・四半期・月の和', script=__file__)
_t.set(compared=n, mismatched=len(out), read_failures=0, explained=None); print('tally', _t.save())
