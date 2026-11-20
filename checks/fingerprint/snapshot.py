"""取得元の指紋の一括記録（2026-11-18、アイデア8）。
  python3 checks/fingerprint/snapshot.py local <日付>   … 全 MANIFEST をまとめ、手元の写しの sha256 を計算し直して照らす
  python3 checks/fingerprint/snapshot.py head  <日付>   … 各 URL に HEAD を1回送り、状態・長さ・Last-Modified・ETag を控える
出力：results/fingerprint/<日付>/SOURCES.tsv・HEAD.tsv・SUMMARY.md。
HEAD は本文を取らない。ホストごとに1本・1秒の間隔。robots.txt で拒否される URL は送らない。web.archive.org は送らない（固定された写し）。
途中で止めても、HEAD.tsv にある URL は飛ばして続きから回る。"""
import csv, glob, hashlib, os, sys, time, threading, urllib.parse, urllib.request, urllib.robotparser, collections, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(ROOT, 'data/raw')
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15 URAZUKE-fingerprint (+https://urazuke.org)'


def rows():
    for fn in sorted(glob.glob(os.path.join(ROOT, 'publish/source_manifests/*.tsv'))):
        man = os.path.basename(fn)
        for r in csv.DictReader(open(fn, encoding='utf-8'), delimiter='\t'):
            url = r.get('url', '')
            if not url.startswith('http'): continue
            if 'edition' in r:   # 再犯防止推進白書の HTML 版
                path = os.path.join('data/raw/saihan/html', r['edition'], r['file']); fetched = ''; size = ''
            else:
                p = r.get('path', ''); path = p if p.startswith('data/raw/') else os.path.join('data/raw', p)
                if not p.startswith('data/raw/') and not os.path.exists(os.path.join(ROOT, path)):
                    alt = os.path.join('data/raw', man.split('__')[0], p)
                    if os.path.exists(os.path.join(ROOT, alt)): path = alt
                fetched = r.get('fetched_utc') or r.get('fetched_at_utc') or ''; size = r.get('bytes', '')
            yield dict(url=url, manifest=man, path=path, bytes=size, sha256=r.get('sha256', ''), fetched=fetched,
                       last_modified=r.get('last_modified', ''))


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def local(day):
    out = os.path.join(ROOT, 'results/fingerprint', day); os.makedirs(out, exist_ok=True)
    cols = ['url', 'host', 'manifest', 'path', 'bytes', 'sha256', 'fetched', 'last_modified', 'local']
    n = collections.Counter(); w = csv.writer(open(os.path.join(out, 'SOURCES.tsv'), 'w', encoding='utf-8'), delimiter='\t', lineterminator='\n'); w.writerow(cols)
    for r in rows():
        p = os.path.join(ROOT, r['path'])
        if not os.path.exists(p): st = '写しなし'
        elif not r['sha256']: st = 'sha256なし'
        else: st = '一致' if sha(p) == r['sha256'] else '不一致'
        n[st] += 1; r['host'] = urllib.parse.urlparse(r['url']).netloc; r['local'] = st
        w.writerow([r[c] for c in cols])
    print(dict(n)); return n


def head(day):
    out = os.path.join(ROOT, 'results/fingerprint', day); os.makedirs(out, exist_ok=True)
    hp = os.path.join(out, 'HEAD.tsv')
    done = set()
    if os.path.exists(hp): done = {l.split('\t', 1)[0] for l in open(hp, encoding='utf-8')}
    else: open(hp, 'w', encoding='utf-8').write('url\tchecked_utc\tstatus\tcontent_length\tlast_modified\tetag\tfinal_url\n')
    urls = sorted({r['url'] for r in rows()} - done)
    by = collections.defaultdict(list)
    for u in urls:
        h = urllib.parse.urlparse(u).netloc
        if h != 'web.archive.org': by[h].append(u)
    lock = threading.Lock()

    def put(vals):
        with lock: open(hp, 'a', encoding='utf-8').write('\t'.join(str(v).replace('\t', ' ').replace('\n', ' ') for v in vals) + '\n')

    def run(host, us):
        rp = urllib.robotparser.RobotFileParser(f'https://{host}/robots.txt')
        try: rp.read()
        except Exception: rp = None
        for u in us:
            now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            if rp is not None and not rp.can_fetch(UA, u): put([u, now, 'robots', '', '', '', '']); continue
            try:
                req = urllib.request.Request(u, method='HEAD', headers={'User-Agent': UA})
                with urllib.request.urlopen(req, timeout=30) as res:
                    H = res.headers; put([u, now, res.status, H.get('Content-Length', ''), H.get('Last-Modified', ''), H.get('ETag', ''), res.geturl() if res.geturl() != u else ''])
            except urllib.error.HTTPError as ex: put([u, now, ex.code, '', '', '', ''])
            except Exception as ex: put([u, now, 'error:' + type(ex).__name__, '', '', '', ''])
            time.sleep(1)
    ts = [threading.Thread(target=run, args=(h, us)) for h, us in by.items()]
    print('hosts', {h: len(us) for h, us in by.items()}, flush=True)
    for t in ts: t.start()
    for t in ts: t.join()
    print('done', flush=True)


def summary(day):
    out = os.path.join(ROOT, 'results/fingerprint', day)
    S = list(csv.DictReader(open(os.path.join(out, 'SOURCES.tsv'), encoding='utf-8'), delimiter='\t'))
    H = {r['url']: r for r in csv.DictReader(open(os.path.join(out, 'HEAD.tsv'), encoding='utf-8'), delimiter='\t')} if os.path.exists(os.path.join(out, 'HEAD.tsv')) else {}
    loc = collections.Counter(r['local'] for r in S)
    st = collections.Counter(H[u]['status'] for u in {r['url'] for r in S} if u in H)
    # 長さの食い違い：手元の bytes と HEAD の Content-Length が両方あって違うもの
    diff = [(r['url'], r['bytes'], H[r['url']]['content_length']) for r in S if r['url'] in H and r['bytes'] and H[r['url']]['content_length'] and r['bytes'] != H[r['url']]['content_length']]
    L = [f'# 取得元の指紋（{day}）', '', f'- 行（MANIFEST の行）：{len(S)}。URL の種類：{len({r["url"] for r in S})}。',
         '- 手元の写しと MANIFEST の sha256：' + '、'.join(f'{k} {v}' for k, v in loc.most_common()),
         '- HEAD の結果：' + ('、'.join(f'{k} {v}' for k, v in st.most_common()) if st else '未実施'),
         f'- 取得時の大きさと HEAD の Content-Length が違う URL：{len(diff)}（中身の差し替えか、配信時の圧縮・動的な生成の違いかは、これだけでは決まらない）', '']
    if diff:
        L += ['| URL | 取得時 | HEAD |', '|---|---|---|'] + [f'| {u} | {a} | {b} |' for u, a, b in diff[:200]]
    open(os.path.join(out, 'SUMMARY.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L[:6]))


if __name__ == '__main__':
    mode, day = sys.argv[1], sys.argv[2]
    {'local': local, 'head': head, 'summary': summary}[mode](day)
