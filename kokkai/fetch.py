"""国会会議録 API（国立国会図書館）から、記録の資料に触れた発言を集める（URAZUKE 第2弾の試行、2026-11-21）。
kokkai/queries.tsv の語で全文検索し、results/kokkai/<日付>/speeches.jsonl に保存する。1件ごとに1秒あける。"""
import csv, json, os, sys, time, urllib.parse, urllib.request, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
day = datetime.date.today().isoformat(); out = os.path.join(ROOT, 'results/kokkai', day); os.makedirs(out, exist_ok=True)
Q = list(csv.DictReader(open(os.path.join(ROOT, 'kokkai/queries.tsv'), encoding='utf-8'), delimiter='\t'))
seen = {}; stat = []
for q in Q:
    start, n = 1, 0
    while True:
        u = 'https://kokkai.ndl.go.jp/api/speech?' + urllib.parse.urlencode({'any': q['query'], 'from': '2010-01-01', 'maximumRecords': 100, 'startRecord': start, 'recordPacking': 'json'})
        try: d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'URAZUKE (contact@urazuke.org)'}), timeout=60))
        except Exception as ex: print(q['qid'], 'error', ex); break
        tot = int(d.get('numberOfRecords', 0))
        for r in d.get('speechRecord', []):
            k = r['speechID']; r.setdefault('_q', [])
            if k in seen: seen[k]['_q'].append(q['qid'])
            else: r['_q'] = [q['qid']]; seen[k] = r
            n += 1
        nxt = d.get('nextRecordPosition'); time.sleep(1)
        if not nxt or n >= 500: break
        start = nxt
    stat.append((q['qid'], q['query'], tot, n)); print(q['qid'], q['query'], tot, n, flush=True)
with open(os.path.join(out, 'speeches.jsonl'), 'w', encoding='utf-8') as w:
    for r in seen.values(): w.write(json.dumps(r, ensure_ascii=False) + '\n')
with open(os.path.join(out, 'QUERIES.tsv'), 'w', encoding='utf-8') as w:
    w.write('qid\tquery\ttotal\tfetched\n'); [w.write('\t'.join(map(str, s)) + '\n') for s in stat]
print('speeches', len(seen))
