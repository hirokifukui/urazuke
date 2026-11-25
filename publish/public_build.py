"""公開の日に配備するサイトを、草案のサイト（site/out）から作る（配備はしない）。
出力は site/out_public/。noindex・robots の拒否・草案の帯・題名の（草案）を外す。.vercel は写さない（誤って配備しないため）。
使い方：python3 publish/public_build.py"""
import os, re, shutil, sys, json
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPLACE = '--inplace' in sys.argv   # 公開後（publish/LIVE がある）は build_site.py の最後に site/out をその場で書き換える
SRC = os.path.join(R, 'site', 'out'); DST = SRC if INPLACE else os.path.join(R, 'site', 'out_public')
if not INPLACE:
    if os.path.exists(DST): shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns('.vercel'))
import unicodedata
for dp, _, fs in os.walk(DST):   # Dropbox の競合コピーを配備しない（2026-11-21 に 79件が site/out に紛れた）
    for f in fs:
        if '競合コピー' in unicodedata.normalize('NFC', f) or 'conflicted copy' in f: os.remove(os.path.join(dp, f))
n = 0
for dp, _, fs in os.walk(DST):
    for f in fs:
        if not f.endswith('.html'): continue
        p = os.path.join(dp, f); s = open(p, encoding='utf-8').read(); t = s
        t = t.replace('<meta name="robots" content="noindex,nofollow">', '')
        t = re.sub(r'<div class="draft">.*?</div>', '', t, count=1, flags=re.S)
        t = t.replace(' — URAZUKE（草案）</title>', ' — URAZUKE</title>').replace(' — URAZUKE (draft)</title>', ' — URAZUKE</title>')
        if t != s: open(p, 'w', encoding='utf-8').write(t); n += 1
open(os.path.join(DST, 'robots.txt'), 'w').write('User-agent: *\nAllow: /\n\nSitemap: https://urazuke.org/sitemap.xml\n')
# sitemap.xml（2026-11-20）：公開する HTML 全部。index.html はディレクトリの URL にする（canonical と同じ形）
# 2026-11-25：lastmod は出さない（ページは毎回作り直すので、更新日にならない）。転送だけのページ（stats/index.html）は載せない
_REDIRECT = {'stats/', 'en/stats/'}; _urls = []
for dp, _, fs in os.walk(DST):
    if '/.vercel' in dp or os.sep + 'data' + os.sep in dp + os.sep: continue
    for f in sorted(fs):
        if not f.endswith('.html') or f == '404.html': continue
        rel = os.path.relpath(os.path.join(dp, f), DST).replace(os.sep, '/')
        if rel.endswith('index.html'): rel = rel[:-len('index.html')]
        if rel not in _REDIRECT: _urls.append(rel)
_urls.sort(key=lambda u: (u.count('/'), u))
open(os.path.join(DST, 'sitemap.xml'), 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + ''.join(f'<url><loc>https://urazuke.org/{u}</loc></url>\n' for u in _urls) + '</urlset>\n')
json.dump({"cleanUrls": False}, open(os.path.join(DST, 'vercel.json'), 'w'))
bad = []
for dp, _, fs in os.walk(DST):
    for f in fs:
        if f.endswith('.html'):
            s = open(os.path.join(dp, f), encoding='utf-8').read()
            if 'noindex' in s or 'class="draft"' in s or '（草案）</title>' in s or '(draft)</title>' in s: bad.append(os.path.relpath(os.path.join(dp, f), DST))
print(f'公開版を作った：{DST}（書き換えた HTML {n}、残った草案の印 {len(bad)}）')
for b in bad[:10]: print('  残り:', b)
sys.exit(1 if bad or (not INPLACE and os.path.exists(os.path.join(DST, '.vercel'))) else 0)
