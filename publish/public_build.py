"""公開の日に配備するサイトを、草案のサイト（site/out）から作る（配備はしない）。
出力は site/out_public/。noindex・robots の拒否・草案の帯・題名の（草案）を外す。.vercel は写さない（誤って配備しないため）。
使い方：python3 publish/public_build.py"""
import os, re, shutil, sys, json
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC, DST = os.path.join(R, 'site', 'out'), os.path.join(R, 'site', 'out_public')
if os.path.exists(DST): shutil.rmtree(DST)
shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns('.vercel'))
n = 0
for dp, _, fs in os.walk(DST):
    for f in fs:
        if not f.endswith('.html'): continue
        p = os.path.join(dp, f); s = open(p, encoding='utf-8').read(); t = s
        t = t.replace('<meta name="robots" content="noindex,nofollow">', '')
        t = re.sub(r'<div class="draft">.*?</div>', '', t, count=1, flags=re.S)
        t = t.replace(' — URAZUKE（草案）</title>', ' — URAZUKE</title>').replace(' — URAZUKE (draft)</title>', ' — URAZUKE</title>')
        if t != s: open(p, 'w', encoding='utf-8').write(t); n += 1
open(os.path.join(DST, 'robots.txt'), 'w').write('User-agent: *\nAllow: /\n')
json.dump({"cleanUrls": False}, open(os.path.join(DST, 'vercel.json'), 'w'))
bad = []
for dp, _, fs in os.walk(DST):
    for f in fs:
        if f.endswith('.html'):
            s = open(os.path.join(dp, f), encoding='utf-8').read()
            if 'noindex' in s or 'class="draft"' in s or '（草案）</title>' in s or '(draft)</title>' in s: bad.append(os.path.relpath(os.path.join(dp, f), DST))
print(f'公開版を作った：{DST}（書き換えた HTML {n}、残った草案の印 {len(bad)}）')
for b in bad[:10]: print('  残り:', b)
sys.exit(1 if bad or os.path.exists(os.path.join(DST, '.vercel')) else 0)
