"""職業訓練の効果検証（令和5年3月）と SIB 事業総括（令和7年9月）の数値の再計算（転記値）。
使い方: python3 checks/moj_kensho2/c4201_recalc.py"""
import json
from scipy.stats import chi2_contingency, fisher_exact

out = []


def rep(t, item, stated, calc, tol):
    out.append(dict(表=t, 項目=item, 掲載=stated, 再計算=round(calc, 3), 判定='OK' if abs(stated - calc) <= tol else 'NG'))


# 職業訓練 表1・表2：(区分, 人数, 有職, 有職率, 一致, 一致率)
T = [('全体', 2575, 1990, 77.3, 450, 17.5), ('男性', 2123, 1729, 81.4, 433, 20.4), ('女性', 452, 261, 57.7, 17, 3.8),
     ('小型建設機械科', 96, 76, 79.2, 58, 60.4), ('溶接科', 139, 120, 86.3, 79, 56.8), ('建設機械科', 62, 52, 83.9, 35, 56.5),
     ('フォークリフト運転科', 269, 210, 78.1, 110, 40.9), ('農業園芸科', 53, 41, 77.4, 17, 32.1), ('ビルハウスクリーニング科', 51, 40, 78.4, 14, 27.5),
     ('販売サービス科', 109, 82, 75.2, 23, 21.1), ('ホームヘルパー科', 99, 77, 77.8, 19, 19.2), ('CAD技術科', 98, 86, 87.8, 3, 3.1),
     ('情報処理科', 252, 204, 81.0, 1, 0.4), ('ビル設備管理科', 157, 122, 77.7, 1, 0.6)]
for k, n, e, er, m, mr in T:
    rep('職業訓練 表1・2 ' + k, '有職率', er, e / n * 100, 0.051)
    rep('職業訓練 表1・2 ' + k, '一致率', mr, m / n * 100, 0.051)
rep('職業訓練 表1', '男+女=全体（人数）', 2575, 2123 + 452, 0)
rep('職業訓練 表1', '男+女=全体（有職）', 1990, 1729 + 261, 0)
rep('職業訓練 表1', '男+女=全体（一致）', 450, 433 + 17, 0)
a, b = round(.787 * 2218), round(.740 * 2218)
p = chi2_contingency([[a, 2218 - a], [b, 2218 - b]], correction=False)[1]
rep('職業訓練 検証1', 'χ² の p<.05（人数は率から逆算）', 1, 1.0 if p < .05 else 0.0, 0)
# SIB：(指標, 分子, 分母, 掲載%)
S = [('策定数 2021', 5, 5, 100), ('策定数 2022', 23, 23, 100), ('策定数 2023', 29, 29, 100),
     ('継続率 2021', 11, 12, 92), ('継続率 2022', 78, 91, 86), ('継続率 2023', 150, 176, 85),
     ('見直し 2023', 48, 48, 100), ('目標達成率', 17, 23, 74), ('YNPS', 16, 20, 80), ('再処分 指数', 5, 8.7, 57)]
for k, x, n, pc in S:
    rep('SIB ' + k, '割合', pc, x / n * 100, 0.51)
rep('SIB 対照群', '8.7％ を与える整数（379人）', 8.7, round(33 / 379 * 100, 1), 0.0)
ks = [k for k in range(30) if round(k / 29 * 100) == 5]
out.append(dict(表='SIB 支援対象者', 項目='29人で 5％（四捨五入で整数%）になる人数', 再計算=ks))
for n in (20, 29):
    out.append(dict(表='SIB', 項目=f'1人/{n} 対 33/379 の両側 p', 再計算=round(fisher_exact([[1, n - 1], [33, 346]])[1], 3)))
ng = [o for o in out if o.get('判定') == 'NG']
print(f"項目 {len([o for o in out if '判定' in o])}　NG {len(ng)}")
for o in out:
    if o.get('判定') != 'OK':
        print(json.dumps(o, ensure_ascii=False))

# 照合の要約（lib/tally.py）：単位は判定のある項目（OK・NG）。「参考」の項目（判定なし）は数えない。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('moj_kensho2', 'c4201', note='職業訓練・刑務作業の効果検証（矯正局）と SIB 事業総括：割合・検定の再計算', script=__file__)
_j = [o for o in out if '判定' in o]; _t.set(compared=len(_j), mismatched=sum(1 for o in _j if o['判定'] == 'NG')); print('tally', _t.save())
