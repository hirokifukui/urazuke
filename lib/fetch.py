"""汎用の取得：fetch.py <slug> <list.tsv>
list.tsv: url<TAB>relpath（data/raw/<slug>/ 以下）。既にあるファイルは取り直さない。
MANIFEST.tsv（url, path, bytes, sha256, status, last_modified, fetched_utc）に追記する。"""
import sys, os, hashlib, urllib.request, datetime, time, ssl
slug, lst = sys.argv[1], sys.argv[2]
base = f'data/raw/{slug}'; os.makedirs(base, exist_ok=True)
man = f'{base}/MANIFEST.tsv'
have = set()
if os.path.exists(man):
    have = {l.split('\t')[1] for l in open(man) if not l.startswith('url\t')}
else:
    open(man, 'w').write('url\tpath\tbytes\tsha256\tstatus\tlast_modified\tfetched_utc\n')
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
ctx = ssl.create_default_context()
for line in open(lst):
    line = line.rstrip('\n')
    if not line or line.startswith('#'): continue
    url, rel = line.split('\t')[:2]
    if rel in have: continue
    p = f'{base}/{rel}'; os.makedirs(os.path.dirname(p), exist_ok=True)
    st, lm, data = 'ERR', '', b''
    for k in range(3):
        import subprocess, tempfile
        tf = tempfile.mktemp(); hf = tempfile.mktemp()
        rc = subprocess.run(['curl', '-sSL', '--max-time', '300', '-A', UA, '-D', hf, '-o', tf, '-w', '%{http_code}', url], capture_output=True, text=True)
        st = rc.stdout.strip() or f'ERR:{rc.returncode}'
        if os.path.exists(hf):
            for h in open(hf, errors='replace'):
                if h.lower().startswith('last-modified:'): lm = h.split(':', 1)[1].strip()
        if st == '200' and os.path.exists(tf):
            data = open(tf, 'rb').read(); break
        time.sleep(3)
    if data and st == '200':
        open(p, 'wb').write(data)
    sha = hashlib.sha256(data).hexdigest() if data else ''
    with open(man, 'a') as w:
        w.write(f'{url}\t{rel}\t{len(data)}\t{sha}\t{st}\t{lm}\t{datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}\n')
    print(st, rel, len(data), flush=True)
    time.sleep(0.5)
print('DONE')
