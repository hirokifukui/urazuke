"""c3701 国民経済計算 年次推計（2024年度）主要系列表 1.国内総生産（支出側、名目、年度）の恒等式。単位10億円・小数1位のため ±0.25。
行は表の上からの順で決まる（行番号は 2024年度版の行の並びを、見出しの文字で確かめてから使う）。
- 民間最終消費=家計+対家計民間非営利団体、家計=国内家計+居住者家計の海外での直接購入−非居住者家計の国内での直接購入
- 総資本形成=総固定資本形成+在庫変動、総固定=民間+公的、民間=住宅+企業設備、公的=住宅+企業設備+一般政府
- 在庫変動=民間企業+公的、民間企業=4内訳の和、公的=2内訳の和
- 純輸出=輸出−輸入、輸出=財貨+サービス、輸入=財貨+サービス
- GDP=1+2+3+4、海外からの所得の純受取=受取−支払、国民総所得=GDP+純受取
- 国内需要=民間需要+公的需要、民間需要=民間最終消費+民間住宅+民間企業設備+民間在庫、公的需要=政府最終消費+公的固定資本形成+公的在庫（注1・2）
- 版間（記録にしない。改定は年次推計の通常の手順）：2023年度版と2024年度版で同じ年度の GDP がどれだけ違うかを数える
使い方: c3701_ffm1n.py [root]  出力: results/sna/c3701.tsv"""
import sys, os, re, unicodedata, openpyxl
root = sys.argv[1] if len(sys.argv) > 1 else '.'
out = []; n = 0; TOL = 0.25

def load(path):
    ws = openpyxl.load_workbook(path, data_only=True).worksheets[0]
    rows = []; years = None
    for r in ws.iter_rows(values_only=True):
        c = [x for x in r if x is not None and str(x).strip() != '']
        if not c: continue
        if years is None and sum(1 for x in c if re.fullmatch(r'(19|20)\d\d', str(x))) >= 5:
            years = [int(x) for x in c if re.fullmatch(r'(19|20)\d\d', str(x))]; continue
        lab = unicodedata.normalize('NFKC', str(c[0])).strip()
        nums = [x for x in c[1:] if isinstance(x, (int, float))]
        rows.append((lab, nums))
        if lab.startswith('(参考)国内需要'): pass
        if lab.startswith('(注)'): break
    return years, rows

def find(rows, pat, start=0):
    for i in range(start, len(rows)):
        if re.search(pat, rows[i][0]): return i
    raise KeyError(pat)

def chk(where, what, a, b):
    global n
    n += 1
    if abs(a - b) > TOL: out.append((where, what, round(a, 1), round(b, 1)))

years, R = load(os.path.join(root, 'data/raw/sna/2024/2024ffm1n_jp.xlsx'))
i1 = find(R, r'^1\. 民間最終消費支出'); i11 = find(R, r'家計最終消費支出', i1)
ia, ib, ic = i11 + 1, i11 + 2, i11 + 3
i12 = find(R, r'対家計民間非営利', ic)
i2 = find(R, r'^2\. 政府最終消費支出'); i3 = find(R, r'^3\. 総資本形成')
ifc = find(R, r'総固定資本形成', i3); ipv = ifc + 1; ipv_a, ipv_b = ipv + 1, ipv + 2
ipb = ipv + 3; ipb_a, ipb_b, ipb_c = ipb + 1, ipb + 2, ipb + 3
iiv = find(R, r'在庫変動', ipb_c); iivp = iiv + 1; iivp_x = [iivp + k for k in range(1, 5)]
iivg = iivp + 5; iivg_x = [iivg + 1, iivg + 2]
i4 = find(R, r'^4\. 財貨・サービスの純輸出'); iex = i4 + 1; iexg, iexs = iex + 1, iex + 2
iim = iex + 3; iimg, iims = iim + 1, iim + 2
i5 = find(R, r'^5\. 国内総生産'); inet = find(R, r'海外からの所得の純受取', i5); irec, ipay, igni = inet + 1, inet + 2, inet + 3
idd = find(R, r'国内需要', igni); ipr, ipu = idd + 1, idd + 2
assert '民間' in R[ipv][0] and '公的' in R[ipb][0] and '民間企業' in R[iivp][0] and '公的' in R[iivg][0], [R[k][0] for k in (ipv, ipb, iivp, iivg)]
assert '輸出' in R[iex][0] and '輸入' in R[iim][0], (R[iex][0], R[iim][0])
v = lambda i, j: R[i][1][j]
for j, y in enumerate(years):
    w = f'{y}年度'
    chk(w, '民間最終消費=家計+非営利', v(i1, j), v(i11, j) + v(i12, j))
    chk(w, '家計=国内家計+居住者の海外購入−非居住者の国内購入', v(i11, j), v(ia, j) + v(ib, j) - v(ic, j))
    chk(w, '総資本形成=総固定+在庫', v(i3, j), v(ifc, j) + v(iiv, j))
    chk(w, '総固定=民間+公的', v(ifc, j), v(ipv, j) + v(ipb, j))
    chk(w, '民間=住宅+企業設備', v(ipv, j), v(ipv_a, j) + v(ipv_b, j))
    chk(w, '公的=住宅+企業設備+一般政府', v(ipb, j), v(ipb_a, j) + v(ipb_b, j) + v(ipb_c, j))
    chk(w, '在庫=民間企業+公的', v(iiv, j), v(iivp, j) + v(iivg, j))
    chk(w, '民間企業在庫=4内訳', v(iivp, j), sum(v(k, j) for k in iivp_x))
    chk(w, '公的在庫=2内訳', v(iivg, j), sum(v(k, j) for k in iivg_x))
    chk(w, '純輸出=輸出−輸入', v(i4, j), v(iex, j) - v(iim, j))
    chk(w, '輸出=財貨+サービス', v(iex, j), v(iexg, j) + v(iexs, j))
    chk(w, '輸入=財貨+サービス', v(iim, j), v(iimg, j) + v(iims, j))
    chk(w, 'GDP=1+2+3+4', v(i5, j), v(i1, j) + v(i2, j) + v(i3, j) + v(i4, j))
    chk(w, '純受取=受取−支払', v(inet, j), v(irec, j) - v(ipay, j))
    chk(w, '国民総所得=GDP+純受取', v(igni, j), v(i5, j) + v(inet, j))
    chk(w, '国内需要=民間需要+公的需要', v(idd, j), v(ipr, j) + v(ipu, j))
    chk(w, '民間需要=民間消費+民間住宅+民間設備+民間在庫', v(ipr, j), v(i1, j) + v(ipv_a, j) + v(ipv_b, j) + v(iivp, j))
    chk(w, '公的需要=政府消費+公的固定+公的在庫', v(ipu, j), v(i2, j) + v(ipb, j) + v(iivg, j))
    chk(w, '国内需要+純輸出=GDP', v(i5, j), v(idd, j) + v(i4, j))
# 版間（数えるだけ）
y3, R3 = load(os.path.join(root, 'data/raw/sna/2023/2023ffm1n_jp.xlsx'))
g3 = dict(zip(y3, R3[find(R3, r'^5\. 国内総生産')][1])); g4 = dict(zip(years, R[i5][1]))
rev = [(y, g3[y], g4[y]) for y in sorted(set(g3) & set(g4)) if abs(g3[y] - g4[y]) > 0.05]
os.makedirs(os.path.join(root, 'results/sna'), exist_ok=True)
with open(os.path.join(root, 'results/sna/c3701.tsv'), 'w') as fo:
    fo.write('年度\t式\t表の値\t計算値\n')
    for o in out: fo.write('\t'.join(map(str, o)) + '\n')
with open(os.path.join(root, 'results/sna/c3701_revisions.tsv'), 'w') as fo:
    fo.write('年度\t2023年度版GDP\t2024年度版GDP\n')
    for r in rev: fo.write('\t'.join(map(str, r)) + '\n')
print('年度', years[0], '〜', years[-1], '式の数', n, '不一致', len(out), '版間で改定された年度', len(rev), '/', len(set(g3) & set(g4)))
for o in out[:30]: print(*o)

# 照合の要約（lib/tally.py）：単位は式と、版間（2023年度推計と2024年度推計）の同じ年度の GDP。版間の違いは年次推計の通常の改定＝説明あり。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('sna', 'c3701', note='国民経済計算 主要系列表1：支出側の恒等式、版間のGDP', script=__file__)
_t.set(compared=n + len(set(g3) & set(g4)), mismatched=len(out) + len(rev), read_failures=0, explained=len(rev)); print('tally', _t.save())
