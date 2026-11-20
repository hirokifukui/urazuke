# Perplexity の検索（results/citations/perplexity/）で出た候補を取得する。robots.txt で拒否されるページは取得しない（H034）。
import os, re, csv, hashlib, gzip, datetime, urllib.request, urllib.robotparser, urllib.parse, html, subprocess
C = [  # (候補 ID, 記録, URL)
 ('P-GY-01', 'GY-Q1', 'https://news.ntv.co.jp/category/society/a10aad1acaca4833801ce6ea32f55391'),
 ('P-GY-02', 'GY-Q1', 'https://fukushishimbun.com/series07/37138'),
 ('P-GY-03', 'GY-Q1', 'https://www.kyobun.co.jp/article/2024092405'),
 ('P-GY-04', 'GY-Q1', 'https://fukushishimbun.com/topics/31075'),
 ('P-JH-01', 'JH-A1', 'https://jen.jiji.com/jc/eng?g=eco&k=2025102400373'),
 ('P-JH-02', 'JH-A1', 'https://www.kyobun.co.jp/article/2025102405'),
 ('P-JH-03', 'JH-A1', 'https://www.kyobun.co.jp/article/2025032803'),
 ('P-JH-04', 'JH-A1', 'https://www.sentankyo.jp/articles/200a089a-2419-4ec7-b0d0-90b77c259c35'),
 ('P-JH-05', 'JH-A1', 'https://news.tv-asahi.co.jp/news_society/articles/000414203.html'),
 ('P-JH-06', 'JH-A1', 'https://jpjj.jp/articles/suicide-white-paper-2026-children/'),
 ('P-ST-01', 'ST-I2', 'https://www.jiji.com/jc/article?k=2025060500369&g=soc'),
 ('P-ST-02', 'ST-I2', 'https://www.fnn.jp/articles/-/882375'),
 ('P-ST-03', 'ST-I2', 'https://news.yahoo.co.jp/articles/97b21ba7bf2113e7ec4a3c2a26a325f18ed8780e'),
 ('P-ST-04', 'ST-I2', 'https://news.ntv.co.jp/category/society/624a38986ea54fcc97d848f66893edee'),
 ('P-ST-05', 'ST-I2', 'https://news.tv-asahi.co.jp/news_politics/articles/000548663.html'),
 ('P-NK-01', 'NK-K1', 'https://info.ninchisho.net/archives/7328'),
 ('P-NK-02', 'NK-K1', 'https://minjob.com/news/kaigogaku/no474/'),
 ('P-NK-03', 'NK-K1', 'https://www.nippon.com/ja/features/h00195/'),
 ('P-YK-01', 'YK-C1', 'https://www.jstage.jst.go.jp/article/jjcp/62/S/62_62S15/_pdf/-char/ja'),
 ('P-630-01', '630-D1', 'https://journal.jspn.or.jp/jspn/openpdf/1250090762.pdf'),
]
# 使い方: fetch_candidates.py [候補の TSV（cid rec url） 出力の TSV]（週1回の巡回で足す候補。引数がなければ上の C と CANDIDATES_R030.tsv）
import sys as _s
OUTF = 'results/citations/CANDIDATES_R030.tsv'
if len(_s.argv) > 2:
    C = [tuple(l.rstrip('\n').split('\t')[:3]) for l in open(_s.argv[1], encoding='utf-8') if l.strip() and not l.startswith('cid')]; OUTF = _s.argv[2]
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
RAW = 'data/raw/citations'; os.makedirs(RAW, exist_ok=True)
rows = []
for cid, rec, url in C:
    u = urllib.parse.urlparse(url); rp = urllib.robotparser.RobotFileParser(f'{u.scheme}://{u.netloc}/robots.txt')
    try: rp.read(); ok = rp.can_fetch(UA, url)
    except Exception: ok = True
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    if not ok:
        rows.append([cid, rec, url, now, 'robots.txt で拒否（取得しない）', '', '', '']); print(cid, 'robots'); continue
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Encoding': 'identity'}), timeout=40)
        b = r.read(); ct = r.headers.get('Content-Type', '')
        if b[:2] == b'\x1f\x8b': b = gzip.decompress(b)
        ext = 'pdf' if (b[:4] == b'%PDF' or 'pdf' in ct) else 'html'
        fn = f'{cid}.{ext}'; open(os.path.join(RAW, fn), 'wb').write(b)
        if ext == 'pdf': t = subprocess.run(['pdftotext', os.path.join(RAW, fn), '-'], capture_output=True, text=True).stdout
        else:
            s = b.decode('utf-8', 'ignore'); m = re.search(r'"datePublished"\s*:\s*"([^"]+)"', s) or re.search(r'published_time"\s+content="([^"]+)"', s)
            t = m.group(1) if m else ''
        rows.append([cid, rec, url, now, '200', fn, hashlib.sha256(b).hexdigest(), (t[:25] if ext == 'html' else '')]); print(cid, 'ok', len(b))
    except Exception as ex:
        rows.append([cid, rec, url, now, f'取得できず（{type(ex).__name__}: {str(ex)[:60]}）', '', '', '']); print(cid, 'err', ex)
with open(OUTF, 'w', newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\n'); w.writerow(['cid', 'rec', 'url', 'fetched_utc', 'status', 'file', 'sha256', 'datePublished']); w.writerows(rows)
