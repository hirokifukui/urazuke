"""c3301 生活保護の被保護者調査（月次概数の報道発表資料、令和7年4月分〜令和8年8月分の17本）。
各本：対前年同月差=当月−前年同月、伸び率=差/前年同月（±0.051%）、対前月差=当月−前月、
  世帯類型：総数=高齢者+高齢者を除く、高齢者=単身+2人以上、除く=母子+障害者・傷病者+その他、構成割合（±0.051%）
版間：m月分の「当月」と、m+1月分の「前月」、m+12月分の「前年同月」が同じか
使い方: c3301_monthly.py [root]   出力: results/seiho/c3301.tsv"""
import sys, os, re, glob, subprocess, unicodedata
root = sys.argv[1] if len(sys.argv) > 1 else '.'
out = []; n = 0
ITEMS = ['実人員', '実世帯', '類型総数', '高齢者世帯', '単身世帯', '２人以上の世帯', '高齢者世帯を除く世帯', '母子世帯', '障害者・傷病者世帯計', 'その他の世帯', '申請件数', '保護開始世帯数']

def chk(f, where, what, a, b, tol=0):
    global n
    n += 1
    if abs(a - b) > tol + 1e-9: out.append((f, where, what, a, round(b, 3)))

def parse(path):
    t = unicodedata.normalize('NFKC', subprocess.run(['pdftotext', '-layout', path, '-'], capture_output=True, text=True).stdout)
    d = {}
    sec = None
    for line in t.split('\n'):
        s = line.strip()
        if s.startswith('1.被保護実人員数'): sec = '実人員'
        elif s.startswith('2.被保護実世帯数'): sec = '実世帯'
        elif s.startswith('3.世帯類型別'): sec = '類型総数'
        elif s.startswith('4.保護の申請'): sec = None
        m = re.match(r'^\s*(?:世|帯|類|型|別|内|訳)?\s*(総数|高齢者世帯を除く世帯|高齢者世帯|単身世帯|２人以上の世帯|2人以上の世帯|母子世帯|障害者・傷病者世帯計|その他の世帯|申請件数|保護開始世帯数)\s+(.*)$', line)
        if not m: continue
        name = m[1].replace('2人以上', '２人以上')
        if name == '総数':
            if not sec or sec in d: continue
            name = sec
        nums = re.findall(r'\(?-?[\d,]+\.?\d*%?\)?', m[2])
        vals = []
        for x in nums:
            pct = x.endswith('%') or x.endswith('%)')
            v = float(x.strip('()%').replace(',', ''))
            vals.append(('p', v) if pct else ('n', v))
        d[name] = vals
    return d

files = sorted(glob.glob(os.path.join(root, 'data/raw/seiho/monthly/m*.pdf')))
D = {}
for p in files:
    ym = re.search(r'm(\d{4})_(\d\d)', p); key = (int(ym[1]), int(ym[2])); f = f'{ym[1]}-{ym[2]}'
    d = parse(p); D[key] = {}
    for name in ITEMS:
        if name not in d: out.append((f, name, '行が読めない', '', '')); continue
        v = d[name]
        ns = [x for k, x in v if k == 'n']; ps = [x for k, x in v if k == 'p']
        if name in ('実人員', '実世帯', '類型総数', '申請件数', '保護開始世帯数'):
            cur, prev_y, diff, prev_m, mdiff = ns[0], ns[1], ns[2], ns[3], ns[4]
            rate = ps[-1]
        else:
            cur, prev_y, diff, prev_m, mdiff = ns[0], ns[1], ns[2], ns[3], ns[4]
            share, rate = ps[0], ps[1]
            D[key][name + '構成割合'] = share
        D[key][name] = (cur, prev_y, prev_m)
        chk(f, name, '対前年同月差', diff, cur - prev_y)
        chk(f, name, '伸び率', rate, (cur / prev_y - 1) * 100, 0.051)
        chk(f, name, '対前月差', mdiff, cur - prev_m)
    g = D[key]
    if all(k in g for k in ITEMS[2:10]):
        for j, lab in ((0, '当月'), (1, '前年同月'), (2, '前月')):
            chk(f, lab, '総数=高齢者+除く', g['類型総数'][j], g['高齢者世帯'][j] + g['高齢者世帯を除く世帯'][j])
            chk(f, lab, '高齢者=単身+2人以上', g['高齢者世帯'][j], g['単身世帯'][j] + g['２人以上の世帯'][j])
            chk(f, lab, '除く=母子+障害傷病+その他', g['高齢者世帯を除く世帯'][j], g['母子世帯'][j] + g['障害者・傷病者世帯計'][j] + g['その他の世帯'][j])
        for name in ITEMS[3:10]:
            chk(f, name, '構成割合', g[name + '構成割合'], g[name][0] / g['類型総数'][0] * 100, 0.051)
for (y, m), g in D.items():
    nk = (y, m + 1) if m < 12 else (y + 1, 1)
    yk = (y + 1, m)
    for name in ITEMS:
        if name not in g: continue
        if nk in D and name in D[nk]:
            n += 1
            if g[name][0] != D[nk][name][2]: out.append(('版間', f'{y}-{m:02d}', f'{name}：当月≠翌月分の前月', g[name][0], D[nk][name][2]))
        if yk in D and name in D[yk]:
            n += 1
            if g[name][0] != D[yk][name][1]: out.append(('版間', f'{y}-{m:02d}', f'{name}：当月≠翌年同月分の前年同月', g[name][0], D[yk][name][1]))
os.makedirs(os.path.join(root, 'results/seiho'), exist_ok=True)
with open(os.path.join(root, 'results/seiho/c3301.tsv'), 'w') as fo:
    fo.write('資料\t項目\t式\t表の値\t計算値\n')
    for o in out: fo.write('\t'.join(map(str, o)) + '\n')
print('式の数', n, '不一致', len(out), '資料', len(D))
for o in out[:40]: print(*o)

# 照合の要約（lib/tally.py）：単位は式。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('seiho', 'c3301', note='被保護者調査（月次概数）：差・伸び率、内訳の和、版間', script=__file__)
_t.set(compared=n, mismatched=len(out), read_failures=0, explained=None); print('tally', _t.save())
