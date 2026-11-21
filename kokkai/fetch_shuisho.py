"""質問主意書と答弁書（閣議決定）を衆参のサイトから集める（2026-11-21）。URAZUKE の範囲の語を件名に含むものだけ。
出力：data/raw/kokkai_src/shuisho/index.tsv と <院>/<回次>/<番号>_q.txt・_a.txt。1件ごとに1秒あける。既に取ったものは取り直さない。
python3 kokkai/fetch_shuisho.py [最初の回次=174]"""
import html, os, re, sys, time, urllib.parse, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT, 'data/raw/kokkai_src/shuisho'); os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'URAZUKE (contact@urazuke.org)'}
KW = re.compile(r'性犯罪|性暴力|わいせつ|再犯|刑務所|刑事施設|矯正|保護観察|更生保護|受刑者|少年院|少年法|非行|児童虐待|虐待|精神科|精神保健|精神障害|措置入院|医療保護入院|身体拘束|身体的拘束|自殺|ストーカー|配偶者からの暴力|ＤＶ|DV|薬物|覚醒剤|大麻|認知症|障害者|犯罪白書|犯罪被害|検挙|懲戒|児童相談所|こども家庭|死亡事例')
def get(u, enc=None):
    b = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read(); time.sleep(1)
    for e in ([enc] if enc else []) + ['utf-8', 'cp932']:
        try: return b.decode(e)
        except Exception: pass
    return b.decode('utf-8', 'ignore')
def text(h):
    h = re.sub(r'<(script|style).*?</\1>', '', h, flags=re.S | re.I); h = re.sub(r'<br\s*/?>|</p>|</div>|</tr>', '\n', h, flags=re.I)
    t = html.unescape(re.sub(r'<[^>]+>', '', h)); return '\n'.join(l.strip() for l in t.splitlines() if l.strip())
idx = os.path.join(OUT, 'index.tsv'); have = set()
if os.path.exists(idx): have = {tuple(l.split('\t')[:3]) for l in open(idx, encoding='utf-8')}
W = open(idx, 'a', encoding='utf-8')
first = int(sys.argv[1]) if len(sys.argv) > 1 else 174
def save(house, ses, num, title, who, qu, au):
    if (house, str(ses), str(num)) in have: return
    d = os.path.join(OUT, house, str(ses)); os.makedirs(d, exist_ok=True)
    try:
        q = text(get(qu)) if qu else ''; a = text(get(au)) if au else ''
    except Exception as ex: print('  error', house, ses, num, ex, flush=True); return
    open(os.path.join(d, f'{num:03d}_q.txt'), 'w', encoding='utf-8').write(q); open(os.path.join(d, f'{num:03d}_a.txt'), 'w', encoding='utf-8').write(a)
    W.write(f'{house}\t{ses}\t{num}\t{title}\t{who}\t{qu}\t{au}\n'); W.flush()
for ses in range(first, 230):
    # 衆議院
    base = 'https://www.shugiin.go.jp/internet/itdb_shitsumon.nsf/html/shitsumon/'
    try: s = get(base + f'kaiji{ses}_l.htm', 'cp932')
    except Exception: s = ''
    n_s = 0
    for row in re.findall(r'<TR VALIGN=top>(.*?)</TR>', s, re.S | re.I):
        cells = [text(c) for c in re.findall(r'<TD[^>]*>(.*?)</TD>', row, re.S | re.I)]
        if len(cells) < 3 or not cells[0].isdigit() or not KW.search(cells[1]): continue
        num = int(cells[0]); a = re.search(r'HREF="(a\d+\.htm)"', row); b = re.search(r'HREF="(b\d+\.htm)"', row)
        save('shu', ses, num, cells[1], cells[2], base + a.group(1) if a else '', base + b.group(1) if b else ''); n_s += 1
    # 参議院
    sb = f'https://www.sangiin.go.jp/japanese/joho1/kousei/syuisyo/{ses}/'
    try: s = get(sb + 'syuisyo.htm')
    except Exception: s = ''
    n_k = 0
    rows = re.findall(r'<tr.*?</tr>', s, re.S | re.I)
    for i, row in enumerate(rows):
        m = re.search(r'href="(meisai/m\d+\.htm)"[^>]*>(.*?)</a>', row, re.S)
        if not m: continue
        title = text(m.group(2))
        if not KW.search(title): continue
        num = int(re.search(r'm\d{3}(\d+)\.htm', m.group(1)).group(1))
        try: mp = get(sb + m.group(1))
        except Exception: continue
        q = re.search(r'href="(\.\./syuh/s\d+\.htm)"', mp); a = re.search(r'href="(\.\./touh/t\d+\.htm)"', mp)
        who = text(re.search(r'提出者</t[hd]>\s*<td[^>]*>(.*?)</td>', mp, re.S).group(1)) if re.search(r'提出者</t[hd]>\s*<td[^>]*>(.*?)</td>', mp, re.S) else ''
        save('san', ses, num, title, who, urllib.parse.urljoin(sb + m.group(1), q.group(1)) if q else '', urllib.parse.urljoin(sb + m.group(1), a.group(1)) if a else ''); n_k += 1
    print(ses, '衆', n_s, '参', n_k, flush=True)
    if not s and ses > 222: break
print('done')
