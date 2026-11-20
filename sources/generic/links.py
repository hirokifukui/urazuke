#!/usr/bin/env python3
"""ページを取得し、リンク（href と表示文字列）を TSV で出す。URL 探索用（取得はしない）。
使い方: python3 links.py <URL> [正規表現（href か表示文字列に当てる）]
出力: status / final_url を1行目に、続いて href<TAB>text。"""
import sys,re,urllib.request,urllib.parse,html
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
url=sys.argv[1]; pat=re.compile(sys.argv[2]) if len(sys.argv)>2 else None
try:
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA}),timeout=60) as r:
        b=r.read(); st=r.status; fin=r.geturl(); ct=r.headers.get_content_charset()
except urllib.error.HTTPError as e:
    print(f"#status\t{e.code}\t{url}"); sys.exit()
for enc in ([ct] if ct else [])+['utf-8','cp932','euc-jp']:
    try: t=b.decode(enc); break
    except Exception: continue
print(f"#status\t{st}\t{fin}")
seen=set()
for m in re.finditer(r'<a\b[^>]*?href\s*=\s*["\']?([^"\'\s>]+)["\']?[^>]*>(.*?)(?=</a>|<a\b)',t,re.S|re.I):
    h=urllib.parse.urljoin(fin,html.unescape(m[1])); x=re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>','',m[2]))).strip()
    if (h,x) in seen: continue
    seen.add((h,x))
    if pat is None or pat.search(h) or pat.search(x): print(f"{h}\t{x}")
# 画像マップ（<area href=... alt=...>）も拾う
for m in re.finditer(r'<area\b[^>]*?href\s*=\s*["\']([^"\']+)["\'][^>]*>',t,re.I):
    h=urllib.parse.urljoin(fin,html.unescape(m[1])); a=re.search(r'alt\s*=\s*["\']([^"\']*)',m[0]); x=a[1] if a else ''
    if (h,x) in seen: continue
    seen.add((h,x))
    if pat is None or pat.search(h) or pat.search(x): print(f"{h}\t{x}")
