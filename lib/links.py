"""links.py <url> [正規表現]：ページのリンク（絶対URL）と文字列を列挙する。"""
import sys, re, urllib.request, urllib.parse, html
url = sys.argv[1]; pat = re.compile(sys.argv[2]) if len(sys.argv) > 2 else None
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
b = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60).read()
for enc in ('utf-8', 'cp932', 'euc-jp'):
    try: t = b.decode(enc); break
    except Exception: pass
for m in re.finditer(r'<a\s[^>]*href="([^"]+)"[^>]*>(.*?)</a>', t, re.S | re.I):
    u = urllib.parse.urljoin(url, html.unescape(m[1])); s = re.sub(r'<[^>]+>|\s+', ' ', m[2]).strip()
    if pat is None or pat.search(u) or pat.search(s): print(u, '\t', s[:80])
