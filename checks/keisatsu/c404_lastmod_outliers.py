#!/usr/bin/env python3
"""検算 c404（b 版の比較の補助）：MANIFEST.tsv の Last-Modified から、同じ版（フォルダ）の大多数と日付の違うファイルを拾う。
差し替えの手がかりになる（告知のある訂正＝正誤表と、告知のない差し替えを分けて記録する）。
使い方: c404_lastmod_outliers.py <MANIFEST.tsv> <出力TSV> [版のフォルダの深さ（既定2: hakusho/r06）]
判定: 版ごとに Last-Modified の日付（日単位）の最頻値をとり、7日以上離れたファイルを外れ値とする。"""
import sys, csv
from collections import Counter, defaultdict
from email.utils import parsedate_to_datetime
man, out = sys.argv[1], sys.argv[2]; depth = int(sys.argv[3]) if len(sys.argv) > 3 else 2
by = defaultdict(list)
for r in csv.DictReader(open(man), delimiter='\t'):
    if not r.get('last_modified'): continue
    ed = '/'.join(r['path'].split('/')[:depth])
    by[ed].append((r['path'], parsedate_to_datetime(r['last_modified'])))
rows = []
for ed, lst in sorted(by.items()):
    mode = Counter(d.date() for _, d in lst).most_common(1)[0][0]
    for p, d in lst:
        gap = (d.date() - mode).days
        if abs(gap) >= 7: rows.append([ed, p, mode.isoformat(), d.date().isoformat(), gap])
with open(out, 'w') as w:
    w.write('edition\tpath\tmode_date\tlast_modified\tdays_from_mode\n')
    for r in rows: w.write('\t'.join(map(str, r)) + '\n')
print(len(rows), 'outliers in', len(by), 'editions')
for r in rows: print(*r, sep='\t')
