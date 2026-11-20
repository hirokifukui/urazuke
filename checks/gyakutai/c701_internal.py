#!/usr/bin/env python3
"""検算 c701（a 内部の整合）：福祉行政報告例 児童相談所の児童虐待相談の対応件数（e-Stat CSV、平成26〜令和6年度）
 R 行：「総数」列＝「再掲」を除く他の列の和（各行）
 C 列：総数の行（「総数」「全国」）＝他の行の和。都道府県表は (i) 全行の和 (ii) 指定都市・中核市・特別区（別掲）を除く都道府県の和、の両方を試す
 X 表どうし：同じ年度の全国総数・種別の総数・経路の総数が、表の間で一致するか
出力: results/gyakutai/c701_internal.tsv（食い違いと X の全件）、c701_summary.tsv"""
import sys, glob, re
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT / 'lib'))
import fukushi_csv as F
OUT = ROOT / 'results/gyakutai'; OUT.mkdir(parents=True, exist_ok=True)
PREF = ['北海道','青森','岩手','宮城','秋田','山形','福島','茨城','栃木','群馬','埼玉','千葉','東京','神奈川','新潟','富山','石川','福井','山梨','長野','岐阜','静岡','愛知','三重','滋賀','京都','大阪','兵庫','奈良','和歌山','鳥取','島根','岡山','広島','山口','徳島','香川','愛媛','高知','福岡','佐賀','長崎','熊本','大分','宮崎','鹿児島','沖縄']
ispref = lambda s: s in PREF or (s[:-1] in PREF and s[-1] in '都道府県')
det, cnt, X = [], Counter(), defaultdict(dict)
for f in sorted(glob.glob(str(ROOT / 'data/raw/gyakutai/estat/FY*.csv'))):
    nm = Path(f).name; fy = int(nm[2:6]); kind = re.match(r'FY\d+_(.+)_\d+\.csv', nm)[1]
    T = F.read(f); cols = T['cols']; rows = T['rows']
    ti = cols.index('総数') if '総数' in cols else 0
    leaf = [j for j, c in enumerate(cols) if j != ti and '再掲' not in c]
    for c0, c1, v in rows:
        if v[ti] is None: continue
        s = sum(v[j] or 0 for j in leaf); ok = abs(s - v[ti]) < 1e-9
        cnt[(kind, 'R行の和', ok)] += 1
        if not ok: det.append([fy, kind, 'R行の和', c0 + c1, s, v[ti]])
    top = next((i for i, (c0, c1, v) in enumerate(rows) if c0 in ('総数', '全国')), None)
    if top is not None:
        others = [r for i, r in enumerate(rows) if i != top and '再掲' not in r[0] + r[1]]   # 「市町村と重複（再掲）」の行は除く
        prefs = [r for r in others if ispref(r[0])]
        for j, c in enumerate(cols):
            if rows[top][2][j] is None: continue
            sa = sum(r[2][j] or 0 for r in others)
            sp = sum(r[2][j] or 0 for r in prefs)
            o = rows[top][2][j]
            if kind.startswith('ken'):
                # 都道府県の行は指定都市・中核市・特別区を含まない（別掲）ので、全国＝全行の和
                oka = abs(sa - o) < 1e-9; cnt[(kind, 'C全国＝全行の和', oka)] += 1
                if not oka: det.append([fy, kind, 'C全国＝全行の和', c, sa, o])
            else:
                ok = abs(sa - o) < 1e-9; cnt[(kind, 'C総数＝他の行の和', ok)] += 1
                if not ok: det.append([fy, kind, 'C総数＝他の行の和', c, sa, o])
        # 表どうしの比較用
        X[fy][(kind, '総数')] = rows[top][2][ti]
        for j, c in enumerate(cols):
            if re.fullmatch(r'(身体的虐待|性的虐待|心理的虐待|保護の怠慢・拒否（ネグレクト）)', c): X[fy][(kind, '種別:' + c)] = rows[top][2][j]
        if 'keiro' in kind:
            for j, c in enumerate(cols):
                if j != ti: X[fy][(kind, '経路:' + c.split('/')[-1] + '@' + c)] = rows[top][2][j]
    if kind in ('shubetsu_keiro', 'shubetsu_gyakutaisha'):
        for c0, c1, v in rows:
            if c0 != '総数': X[fy][(kind, '種別:' + c0)] = v[ti]
xs = []
for fy, d in sorted(X.items()):
    by = defaultdict(dict)
    for (k, item), v in d.items():
        key = item.split('@')[0] if not item.startswith('経路') else item.split('@')[1].split('/', 1)[-1] if False else item.split('@')[1]
        by[item.split('@')[0] if item.startswith('経路') else item][k] = v
    for item, kv in sorted(by.items()):
        if len(kv) < 2: continue
        vals = set(kv.values()); ok = len(vals) == 1
        cnt[('表どうし', 'X', ok)] += 1
        xs.append([fy, item, ' '.join(f'{k}={v:g}' for k, v in sorted(kv.items())), '一致' if ok else '食い違い'])
with open(OUT / 'c701_internal.tsv', 'w') as w:
    w.write('# 食い違い\nfy\ttable\tcheck\tkey\tsum\tstated\n')
    for d in det: w.write('\t'.join(map(str, d)) + '\n')
    w.write('# 表どうし（全件）\nfy\titem\tvalues\tstatus\n')
    for x in xs: w.write('\t'.join(map(str, x)) + '\n')
with open(OUT / 'c701_summary.tsv', 'w') as w:
    w.write('table\tcheck\tok\tng\n')
    for (k, c) in sorted({(a, b) for a, b, _ in cnt}): w.write(f"{k}\t{c}\t{cnt[(k, c, True)]}\t{cnt[(k, c, False)]}\n")
agg = Counter()
for (k, c, ok), n in cnt.items(): agg[(c, ok)] += n
print(dict(agg)); print('食い違い', len(det), ' 表どうしの不一致', sum(1 for x in xs if x[-1] != '一致'))

# 照合の要約（lib/tally.py）
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('gyakutai', 'c701', note='福祉行政報告例（児童虐待）：行・列の和と総数、表どうしの総数', script=__file__)
for (k, c, ok), n in cnt.items(): (_t.ok if ok else _t.ng)(n)
print('tally', _t.save())
