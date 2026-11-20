"""c3602 公立学校教職員の人事行政状況調査 2-3-3「体罰による懲戒処分等の推移（教育職員）（過去5年間）」。
令和6年度版（令和7年12月公表）と令和5年度版（令和6年12月公表）。
(a) 67教育委員会の和=計（各年度）
(b) 版間：両版に共通の年度（R2〜R5）の値が、教育委員会ごとに同じか
同様に 2-1-2「懲戒処分等の推移」も読む（同じ形の表）。
使い方: c3602_taibatsu.py [root]   出力: results/monka_kihon/c3602.tsv"""
import sys, os, re, glob, subprocess, unicodedata
root = sys.argv[1] if len(sys.argv) > 1 else '.'
D = os.path.join(root, 'data/raw/monka_kihon/taibatsu')
out = []; n = 0

def chk(ed, where, what, a, b):
    global n
    n += 1
    if a != b: out.append((ed, where, what, a, b))

def find(prefix, title):
    for p in sorted(glob.glob(f'{D}/{prefix}*.pdf')):
        t = unicodedata.normalize('NFKC', subprocess.run(['pdftotext', '-layout', p, '-'], capture_output=True, text=True).stdout)
        if title in t.split('\n', 3)[0] + t[:200]: return p, t
    return None, None

def parse(t):
    lines = t.split('\n')
    hdr = next(l for l in lines if '年度' in l and re.search(r'R\S*年度', l))
    years = re.findall(r'R(元|\d+)年度', hdr)
    years = [1 if y == '元' else int(y) for y in years][:5]
    rows = {}; total = None
    for l in lines:
        m = re.match(r'\s*(\d+)\s+(\S+)\s+((?:[\d,]+\s+){5})', l)
        if m: rows[m[2]] = [int(x.replace(',', '')) for x in m[3].split()]
        m2 = re.match(r'\s*(合\s*計|計|全国計)\s+((?:[\d,]+\s+){5})', l)
        if m2: total = [int(x.replace(',', '')) for x in m2[2].split()]
    return years, rows, total

for title, key in (('体罰による懲戒処分等の推移', '体罰'), ('懲戒処分等の推移(教育職員)', '懲戒処分等')):
    E = {}
    for ed, prefix in (('R06', '20251217'), ('R05', '20241220')):
        p, t = find(prefix, title)
        if not p: out.append((ed, key, '表が見つからない', '', '')); continue
        years, rows, total = parse(t)
        E[ed] = (years, rows)
        if len(rows) != 67: out.append((ed, key, f'教育委員会の行数{len(rows)}', '', ''))
        if total:
            for j, y in enumerate(years): chk(ed, f'{key} R{y}', '67教委の和=計', total[j], sum(r[j] for r in rows.values()))
        else:
            out.append((ed, key, '計の行が読めない', '', ''))
    if 'R06' in E and 'R05' in E:
        (y6, r6), (y5, r5) = E['R06'], E['R05']
        for name in r6:
            if name not in r5: continue
            for y in set(y6) & set(y5):
                a, b = r5[name][y5.index(y)], r6[name][y6.index(y)]
                chk('版間', f'{key} {name} R{y}', '令和5年度版≠令和6年度版', a, b)
os.makedirs(os.path.join(root, 'results/monka_kihon'), exist_ok=True)
with open(os.path.join(root, 'results/monka_kihon/c3602.tsv'), 'w') as fo:
    fo.write('版\t場所\t式\t値1\t値2\n')
    for o in out: fo.write('\t'.join(map(str, o)) + '\n')
print('式の数', n, '不一致', len(out))
for o in out[:40]: print(*o)

# 照合の要約（lib/tally.py）：単位は式。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('monka_kihon', 'c3602', note='人事行政状況調査 体罰：67教育委員会の和と合計、版間', script=__file__)
_t.set(compared=n, mismatched=len(out), read_failures=0, explained=None); print('tally', _t.save())
