"""補助（照合ではない）：版間の改訂（c009h・c009v）の出た表ごとに、新旧の版の同じシートの注の文を書き出す。
改訂の理由が資料の中に書かれているか（説明あり）を判定するための下調べ。出力: results/hanzai_hakusho/revision_notes.tsv
使い方: python checks/hanzai_hakusho/notes_for_revisions.py"""
import sys, os, re, glob, csv, collections
sys.path.insert(0, '.')
from lib.xlsx import read_sheets
H = 'data/raw/hanzai_hakusho/'
D = {'63': '63_20261116T100633Z', '64': '64_20261116T100205Z', '65': '65_20261116T095636Z', '66': '66_20261116T095154Z', '67': '67_20261116T094520Z',
     '68': '68_20261116T085457Z', '69': '69_20261116T085457Z', '70': '70_20261116T073025Z', '71b': '71_20261116T090659Z', '72': '72'}
PAIRS = {'c009h_68to69': ('68', '69', 'h'), 'c009h_69to70': ('69', '70', 'h'), 'c009h_70to71b': ('70', '71b', 'h'), 'c009h_71bto72': ('71b', '72', 'h'),
         'c009v_63to64v': ('63', '64', 'v'), 'c009v_64to65v': ('64', '65', 'v'), 'c009v_65to66v': ('65', '66', 'v'), 'c009v_66to67v': ('66', '67', 'v'), 'c009v_67to68v': ('67', '68', 'v')}
_cache = {}
def sheet(ed, fn, sn):
    k = (ed, fn)
    if k not in _cache:
        p = [x for x in (H + D[ed] + '/zuhyo/' + fn, H + D[ed] + '/shiryo/' + fn) if os.path.exists(x)]
        try: _cache[k] = read_sheets(p[0]) if p else {}
        except Exception: _cache[k] = {}
    return _cache[k].get(sn, {})
def notes(cells):
    t = [str(v).strip() for (r, c), v in sorted(cells.items()) if isinstance(v, str)]
    return [x for x in t if re.match(r'^(注|※|\d\s|[０-９]\s|[１-９]　|\d　)', x) or len(x) > 25]
rows = []
for tag, (o, n, kind) in PAIRS.items():
    f = f'results/hanzai_hakusho/{tag}.tsv'
    L = open(f, encoding='utf-8').read().splitlines()
    L = L[1:] if kind == 'h' else L[2:]
    g = collections.defaultdict(list)
    for l in L:
        x = l.split('\t')
        if kind == 'h': g[(x[0], x[1], x[2], x[3])].append((x[4], x[5], x[6], x[7]))
        else: g[(x[0], x[1], x[3], x[4])].append((x[2], x[6], x[7], x[8]))
    for (nf, ns, of, os_), v in g.items():
        ys = sorted({w[1] for w in v})
        nn = notes(sheet(n, nf, ns)); on = notes(sheet(o, of, os_))
        rows.append((tag, nf, ns, of, os_, len(v), ys[0] + '-' + ys[-1], ' / '.join(sorted({w[0][:20] for w in v}))[:120],
                     ' || '.join(nn)[:1500], ' || '.join(x for x in on if x not in nn)[:600]))
with open('results/hanzai_hakusho/revision_notes.tsv', 'w', encoding='utf-8') as w:
    w.write('pair\tnew_file\tnew_sheet\told_file\told_sheet\tn\tyears\tcolumns\tnew_notes\told_only_notes\n')
    for r in rows: w.write('\t'.join(map(str, r)) + '\n')
print('groups', len(rows), 'values', sum(r[5] for r in rows))
