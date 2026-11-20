# 再犯防止推進白書の正誤表の訂正が、HTML 版に入っているかを照合する（H039）。
# 1) HTML 版（2020〜2025年版）の全ページを取得（data/raw/saihan/html/<版>/、手元のみ）。2) 正誤表（data/raw/saihan/<版>/seigo_*.pdf）の「誤」「正」を抜き出す。
# 3) 各訂正について、同じ版の HTML 版の中に「誤」「正」の文字列があるかを数える。
import os, re, time, json, glob, hashlib, subprocess, urllib.request, urllib.parse, csv
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
ED = {'R02': 'https://www.moj.go.jp/hisho/saihanboushi/index.html', 'R03': 'https://www.moj.go.jp/hisho/saihanboushi3/index.html',
      'R04': 'https://www.moj.go.jp/hisho/saihanboushi4/r04/index.html', 'R05': 'https://www.moj.go.jp/hisho/saihanboushi/r05/index.html',
      'R06': 'https://www.moj.go.jp/hisho/saihanboushi/r06/index.html', 'R07': 'https://www.moj.go.jp/hisho/saihanboushi/r07/index.html'}
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': UA}), timeout=40).read()
def text(b):
    s = b.decode('utf-8', 'ignore'); s = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', s, flags=re.S)
    return re.sub(r'\s+', '', re.sub(r'<[^>]+>', ' ', s))
man = []
for ed, top in ED.items():
    d = f'data/raw/saihan/html/{ed}'; os.makedirs(d, exist_ok=True)
    idx = get(top); open(f'{d}/index.html', 'wb').write(idx)
    links = sorted(set(re.findall(r'href="(html/n[^"#]+\.html)"', idx.decode('utf-8', 'ignore'))))
    for l in links:
        fn = f'{d}/{os.path.basename(l)}'
        if not os.path.exists(fn):
            try: b = get(urllib.parse.urljoin(top, l)); open(fn, 'wb').write(b); time.sleep(0.4)
            except Exception as ex: print(ed, l, ex); continue
        man.append([ed, urllib.parse.urljoin(top, l), os.path.basename(fn), hashlib.sha256(open(fn, 'rb').read()).hexdigest()])
    print(ed, len(links), flush=True)
with open('data/raw/saihan/html/MANIFEST.tsv', 'w') as f:
    f.write('edition\turl\tfile\tsha256\n'); f.writelines('\t'.join(r) + '\n' for r in man)
# 正誤表の「誤」「正」
def entries(pdf):
    t = subprocess.run(['pdftotext', '-layout', pdf, '-'], capture_output=True, text=True).stdout
    out = []; cur = {}
    for ln in t.splitlines():
        m = re.match(r'\s*(ページ|該当箇所|誤|正)\s+(.*)', ln)
        if m:
            k, v = m.groups(); cur.setdefault(k, ''); cur[k] += v.strip(); last = k
            if k == '正': out.append(dict(cur)); cur = {} if False else {'ページ': cur.get('ページ', ''), '該当箇所': ''}
        elif ln.strip() and 'last' in dir() and last in ('誤', '正', '該当箇所') and ln.startswith('        '):
            if last == '正' and out: out[-1]['正'] += ln.strip()
            else: cur[last] = cur.get(last, '') + ln.strip()
    return out
def variants(s):
    s = re.sub(r'\s+', '', s); v = {s}
    for m in re.finditer(r'(\d{1,3}),(\d{3})', s):
        n = int(m.group(1) + m.group(2))
        if n >= 10000: v.add(s.replace(m.group(0), f'{n // 10000}万{n % 10000:,}' if n % 10000 >= 1000 else f'{n // 10000}万{n % 10000}'))
    return v
pages = {ed: {os.path.basename(f): text(open(f, 'rb').read()) for f in glob.glob(f'data/raw/saihan/html/{ed}/n*.html')} for ed in ED}
rows = []
for ed in ED:
    for pdf in glob.glob(f'data/raw/saihan/{ed}/seigo_*.pdf'):
        for e in entries(pdf):
            w, r = e.get('誤', ''), e.get('正', '')
            if not w or not r: continue
            hw = [p for p, t in pages[ed].items() if any(v in t for v in variants(w))]
            hr = [p for p, t in pages[ed].items() if any(v in t for v in variants(r))]
            rows.append([ed, os.path.basename(pdf), e.get('ページ', ''), e.get('該当箇所', '')[:80], w[:80], r[:80], len(hw), len(hr), ' '.join(hw[:5]), ' '.join(hr[:5])])
os.makedirs('results/saihan/seigo_html', exist_ok=True)
with open('results/saihan/seigo_html/check.tsv', 'w', newline='') as f:
    wr = csv.writer(f, delimiter='\t', lineterminator='\n'); wr.writerow(['版', '正誤表', '頁', '該当箇所', '誤', '正', '誤のある頁数', '正のある頁数', '誤のある頁', '正のある頁']); wr.writerows(rows)
print('entries', len(rows))
