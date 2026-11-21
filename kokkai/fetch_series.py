"""国会の答弁がよく引く、手元にない版の資料を集める（2026-11-21）。いまは死亡事例検証報告の第1〜18次（国立国会図書館 WARP の写し）。
data/raw/kokkai_src/shibo/<次>/ に PDF を置き、pdftotext で .txt を作る。MANIFEST.tsv に URL・ハッシュを残す。1件ごとに2秒あける。"""
import hashlib, os, re, subprocess, time, urllib.parse, urllib.request, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data/raw/kokkai_src/shibo'); os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'URAZUKE (contact@urazuke.org)'}
def get(u): return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120).read()
page = open(os.path.join(ROOT, 'data/raw/shibo_jirei/pages/kekka.html'), encoding='utf-8', errors='ignore').read()
eds = {}
for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', page, re.S):
    s = re.sub('<[^>]+>', '', m.group(2)); n = re.search(r'第(\d+)次報告）', s)
    if n and int(n.group(1)) <= 18 and 'warp.ndl.go.jp' in m.group(1): eds[int(n.group(1))] = m.group(1)
man = open(os.path.join(OUT, 'MANIFEST.tsv'), 'a', encoding='utf-8')
for n, u in sorted(eds.items()):
    d = os.path.join(OUT, f'{n:02d}'); os.makedirs(d, exist_ok=True)
    try: h = get(u).decode('utf-8', 'ignore')
    except Exception as ex: print(n, 'page error', ex); continue
    open(os.path.join(d, 'page.html'), 'w', encoding='utf-8').write(h)
    fr = re.search(r'<iframe[^>]+src="([^"]+)"', h)   # WARP は中身を iframe で出す
    if fr:
        u = urllib.parse.urljoin('https://warp.ndl.go.jp/', fr.group(1))
        try: h = get(u).decode('utf-8', 'ignore'); open(os.path.join(d, 'inner.html'), 'w', encoding='utf-8').write(h)
        except Exception as ex: print(n, 'inner error', ex); continue
    pdfs = []
    for m in re.finditer(r'href="([^"]+\.pdf)"[^>]*>(.*?)</a>', h, re.S):
        pdfs.append((urllib.parse.urljoin(u, m.group(1)), re.sub('<[^>]+>', '', m.group(2)).strip()))
    print(n, len(pdfs), flush=True)
    pick = [x for x in pdfs if any(k in x[1] for k in ('概要', '全体', '本文', '報告書'))] or pdfs[:12]   # 概要版と全体版があればそれだけ
    for pu, label in pick:
        fn = os.path.join(d, os.path.basename(urllib.parse.urlparse(pu).path))
        if os.path.exists(fn): continue
        try: b = get(pu)
        except Exception as ex: print('  error', pu, ex); continue
        open(fn, 'wb').write(b); subprocess.run(['pdftotext', '-layout', fn, fn[:-4] + '.txt'], capture_output=True)
        man.write(f"{pu}\tshibo/{n:02d}/{os.path.basename(fn)}\t{len(b)}\t{hashlib.sha256(b).hexdigest()}\t{label[:60]}\t{datetime.datetime.utcnow().isoformat(timespec='seconds')}Z\n"); man.flush()
        time.sleep(2)
    time.sleep(2)
print('done')
