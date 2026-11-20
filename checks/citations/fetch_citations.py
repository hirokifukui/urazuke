"""引用の追跡：見つけたページを取得し sha256 を付けて残す。Wayback の有無を確かめ、ない場合は保存を頼む（H034）。
入力 results/citations/citations_draft.tsv → 出力 data/raw/citations/<qid>.<ext>、results/citations/FETCH.tsv"""
import csv, hashlib, json, os, sys, time, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
OUT = os.path.join(ROOT, 'data/raw/citations'); os.makedirs(OUT, exist_ok=True)


def get(url, timeout=30):
    r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=timeout)
    return r.status, r.headers.get('Content-Type', ''), r.read()


rows = list(csv.DictReader(open(os.path.join(ROOT, 'results/citations/citations_draft.tsv')), delimiter='\t'))
res = []; seen = {}
for r in rows:
    url = r['url']; q = r['qid']; rec = {'qid': q, 'url': url, 'fetched_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    try:
        if url in seen:
            rec.update(seen[url])
        else:
            st, ct, b = get(url)
            ext = 'pdf' if 'pdf' in ct or url.endswith('.pdf') else 'html'
            fn = f'{q}.{ext}'; open(os.path.join(OUT, fn), 'wb').write(b)
            seen[url] = {'status': st, 'file': fn, 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}
            rec.update(seen[url])
    except Exception as e:
        rec.update({'status': f'取得できず（{type(e).__name__}: {str(e)[:60]}）', 'file': '', 'bytes': 0, 'sha256': ''})
    try:
        _, _, b = get('https://archive.org/wayback/available?url=' + urllib.parse.quote(url, safe=''), 30)
        snap = json.loads(b).get('archived_snapshots', {}).get('closest', {})
        rec['wayback'] = snap.get('url', '')
    except Exception as e:
        rec['wayback'] = ''
    if not rec['wayback'] and str(rec['status']).isdigit():
        try:
            st, _, _ = get('https://web.archive.org/save/' + url, 90)
            rec['wayback'] = f'保存を依頼（{st}）'
        except Exception as e:
            rec['wayback'] = f'保存の依頼に失敗（{type(e).__name__}）'
    res.append(rec); print(q, rec['status'], rec.get('bytes'), rec['wayback'][:60], flush=True)
    time.sleep(2)
keys = ['qid', 'url', 'fetched_utc', 'status', 'file', 'bytes', 'sha256', 'wayback']
with open(os.path.join(ROOT, 'results/citations/FETCH.tsv'), 'w') as w:
    w.write('\t'.join(keys) + '\n')
    for r in res: w.write('\t'.join(str(r.get(k, '')) for k in keys) + '\n')
print('done')
