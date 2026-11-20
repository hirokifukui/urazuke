"""c1202: 問題行動・不登校等調査 結果 PDF の都道府県別の表で、都道府県の和＝全国（L1）。令和3〜6年度（令和6年度は修正版と当初版の両方）。
使い方: ~/.venvs/urazuke/bin/python checks/futoko/c1202_pref_sums.py"""
import sys, json; sys.path.insert(0, '.')
from lib.pref_blocks import check
D = 'data/raw/futoko'
out = {}
for f in ['r03/kekka', 'r04/kekka', 'r05/kekka', 'r06/kekka_20260116', 'r06/wayback_kekka_20251029']:
    n, res, nb = check(f'{D}/{f}.txt'); out[f] = {'tables': nb, 'columns_checked': n, 'issues': res}
    print(f, 'tables', nb, 'cols', n, 'issues', len(res)); [print('  ', r) for r in res[:12]]
json.dump(out, open('results/futoko/c1202_pref_sums.json', 'w'), ensure_ascii=False, indent=1)

# 照合の要約（lib/tally.py）：単位は都道府県別の表の列（都道府県の和＝全国）。令和6年度の PDF は大半の頁の文字が抽出できず、照合できていない。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('futoko', 'c1202', note='問題行動・不登校等調査：都道府県別の表の和と全国', script=__file__)
_t.set(compared=sum(v['columns_checked'] for v in out.values()), mismatched=sum(len(v['issues']) for v in out.values())); print('tally', _t.save())
