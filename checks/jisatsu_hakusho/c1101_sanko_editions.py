"""c1101: 自殺対策白書 参考資料2（Excel）の版間比較（L3）：令和6・7・8年版の重なる年の値。
使い方: ~/.venvs/urazuke/bin/python checks/jisatsu_hakusho/c1101_sanko_editions.py"""
import sys, collections; sys.path.insert(0, '.')
from lib.edition_diff import wb_keyed, compare
D = 'data/raw/jisatsu_hakusho'
E = {'r2024': f'{D}/r2024/sanko2_001332662.xlsx', 'r2025': f'{D}/r2025/sanko2_001593171.xlsx', 'r2026': f'{D}/r2026/sanko2_001760475.xlsx'}
K = {y: wb_keyed(p) for y, p in E.items()}
tot = 0; out = []; _N = collections.Counter()  # _N：照合の要約用（表ごとの比べた数）
for a, b in [('r2024', 'r2025'), ('r2025', 'r2026')]:
    for sh in K[b]:
        if sh not in K[a]: continue
        n, d = compare(K[a][sh], K[b][sh]); tot += n; _N[sh] += n
        print(a, b, sh, 'common', n, 'diff', len(d))
        for k, x, y in d: out.append((a, b, sh, k[0], k[1], x, y))
open('results/jisatsu_hakusho/c1101_sanko_editions.tsv', 'w').write('from\tto\tsheet\trow\tcol\told\tnew\n' + ''.join('\t'.join(map(str, r)) + '\n' for r in out))
print('TOTAL compared', tot, 'diff', len(out))

# 照合の要約（lib/tally.py）：単位は年を行の鍵にした表の重なる値。2-9〜2-12表は単年の表（版ごとに対象年が違う）で対応が取れない＝読み取りの失敗。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_SINGLE = ('参考資料2-9表', '参考資料2-10表', '参考資料2-11表', '参考資料2-12表')
_t = Tally('jisatsu_hakusho', 'c1101', note='自殺対策白書 参考資料2：令和6・7・8年版の重なる年の値', script=__file__)
_ns = sum(n for sh, n in _N.items() if sh in _SINGLE); _ds = sum(1 for o in out if o[2] in _SINGLE)
_t.set(compared=tot - _ns, mismatched=len(out) - _ds, read_failures=_ns); print('tally', _t.save())
