"""薬物の効果検証（令和4年10月）の統計値の再計算（転記値。転記の確かめは原文引用の抽出で行う）。
矯正局 表3・表4・表8、保護局 表2・表5〜7（構成比・φ・フィッシャーの正確確率）、表3・表4（HR と CI・Wald の整合）。
使い方: python3 checks/moj_yakubutsu/c4101_recalc.py （scipy を使う）"""
import math, json
from scipy.stats import fisher_exact

out = []


def rep(tab, item, stated, calc, tol):
    out.append(dict(表=tab, 項目=item, 掲載=stated, 再計算=round(calc, 4), 判定='OK' if abs(stated - calc) <= tol else 'NG'))


def phi(a, b, c, d):
    return (a * d - b * c) / math.sqrt((a + b) * (c + d) * (a + c) * (b + d))


# 矯正局：(群1 あり, 群1 なし, 群2 あり, 群2 なし, 掲載 p, 片側の向き, 掲載 φ, 掲載%1, 掲載%2)
K = [('矯正 表3 未受講', 189, 404, 36, 706, None, 0.36, 31.9, 4.9),
     ('矯正 表4 再犯', 158, 435, 155, 587, 0.01, 0.07, 26.6, 20.9),
     ('矯正 表8 1年以内', 5, 31, 80, 626, 0.40, -0.02, 13.9, 11.3),
     ('矯正 表8 2年以内', 7, 29, 148, 558, 0.51, 0.01, 19.4, 21.0)]
for t, a, b, c, d, p, f, p1, p2 in K:
    rep(t, '構成比1', p1, a / (a + b) * 100, 0.051)
    rep(t, '構成比2', p2, c / (c + d) * 100, 0.051)
    rep(t, '|φ|', abs(f), abs(phi(a, b, c, d)), 0.0051)
    if p is not None:
        one = min(fisher_exact([[a, b], [c, d]], alternative='greater')[1], fisher_exact([[a, b], [c, d]], alternative='less')[1])
        rep(t, '片側 p', p, one, 0.0051)
        out.append(dict(表=t, 項目='両側 p（参考）', 再計算=round(fisher_exact([[a, b], [c, d]])[1], 4)))
# 保護局：(受講 あり, なし, 非受講 あり, なし, 掲載 p 両側, φ, %1, %2)
H = [('保護 表2 全再犯', 718, 1668, 920, 1355, 0.001, .108, 30.1, 40.4),
     ('保護 表2 薬物再犯', 652, 1734, 816, 1459, 0.001, .092, 27.3, 35.9),
     ('保護 表5 全再犯', 474, 932, 550, 856, .003, .056, 33.7, 39.1),
     ('保護 表5 薬物再犯', 426, 980, 486, 920, .017, .046, 30.3, 34.6),
     ('保護 表6 全再犯', 409, 767, 477, 699, .004, .060, 34.8, 40.6),
     ('保護 表6 薬物再犯', 364, 812, 419, 757, .018, .050, 31.0, 35.6),
     ('保護 表7 全再犯', 58, 150, 72, 136, .169, .073, 27.9, 34.6),
     ('保護 表7 薬物再犯', 53, 155, 65, 143, .231, .064, 25.5, 31.3)]
for t, a, b, c, d, p, f, p1, p2 in H:
    rep(t, '構成比 受講', p1, a / (a + b) * 100, 0.051)
    rep(t, '構成比 非受講', p2, c / (c + d) * 100, 0.051)
    rep(t, '|φ|', f, abs(phi(a, b, c, d)), 0.0011)
    pv = fisher_exact([[a, b], [c, d]])[1]
    if p == 0.001:
        rep(t, 'p<.001', 1, 1.0 if pv < .001 else 0.0, 0)
    else:
        rep(t, '両側 p', p, pv, 0.0011)
# Cox：(係数, Wald, HR, 下限, 上限)
C = [('保護 表3 受講', -0.165, 9.797, 0.847, 0.764, 0.940), ('保護 表4 受講', -0.133, 5.569, 0.876, 0.784, 0.978)]
for t, B, W, hr, lo, hi in C:
    rep(t, 'HR=exp(B)', hr, math.exp(B), 0.0011)
    se = (math.log(hi) - math.log(lo)) / (2 * 1.959964)
    rep(t, 'Wald（CI から）', W, (B / se) ** 2, 0.3)
ng = [o for o in out if o.get('判定') == 'NG']
print(f"項目 {len([o for o in out if '判定' in o])}　NG {len(ng)}")
for o in out:
    if o.get('判定') != 'OK':
        print(json.dumps(o, ensure_ascii=False))

# 照合の要約（lib/tally.py）：単位は判定のある項目（OK・NG）。「参考」の項目（判定なし）は数えない。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('moj_yakubutsu', 'c4101', note='薬物事犯者のプログラム効果検証（矯正局・保護局）：割合・検定の再計算', script=__file__)
_j = [o for o in out if '判定' in o]; _t.set(compared=len(_j), mismatched=sum(1 for o in _j if o['判定'] == 'NG')); print('tally', _t.save())
