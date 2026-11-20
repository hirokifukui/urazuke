"""c3401 令和7年度「過労死等の労災補償状況」別添資料（PDF 6本）の表の内訳の和。
pdftotext -layout の行を表（「表n－m」で始まる）ごとに分け、
「件数 ( 女性 )」が3組以上並ぶ行を本行、「〈 件数 ( 女性 ) 〉」の行を死亡（自殺）行として読む。
「合計」の直前の本行・死亡行を合計とし、その表のそれより前の行の列ごとの和と比べる。
小計を含む表（中分類など）は和が合わないことがあるため、その表は作業ノートで目で確かめる（記録には使わない）。
あわせて、表n-1 の認定率 = 支給決定件数 / 決定件数（小数1位、±0.051%）。
使い方: c3401_tables.py [root]   出力: results/karoshi/c3401.tsv"""
import sys, os, re, glob, subprocess, unicodedata
root = sys.argv[1] if len(sys.argv) > 1 else '.'
out = []; n = 0; tables_seen = []
PAIR = re.compile(r'(\d+)\s*\(\s*(\d+)\s*\)')

def chk(f, t, what, a, b, tol=0):
    global n
    n += 1
    if abs(a - b) > tol + 1e-9: out.append((f, t, what, a, b))

for p in sorted(glob.glob(os.path.join(root, 'data/raw/karoshi/R07/b*.pdf'))):
    f = os.path.basename(p)
    txt = unicodedata.normalize('NFKC', subprocess.run(['pdftotext', '-layout', p, '-'], capture_output=True, text=True).stdout)
    lines = txt.split('\n')
    tabs = []; cur = None
    for l in lines:
        m = re.match(r'\s*(表\s*\d+\s*[-－ー]\s*\d+(?:\s*[-－ー]\s*\d+)?)\s*(.*)', l)
        if m:
            cur = {'name': re.sub(r'\s', '', m[1]), 'title': m[2].strip(), 'lines': []}; tabs.append(cur); continue
        if cur is not None: cur['lines'].append(l)
    for t in tabs:
        main, death, total_main, total_death = [], [], None, None
        pending_main = pending_death = None
        for l in t['lines']:
            if l.strip().startswith('注'): break
            if '〈' in l:
                d = [(int(a), int(b)) for a, b in PAIR.findall(l)]
                if len(d) >= 3: pending_death = d; death.append(d)
            else:
                mm = [(int(a), int(b)) for a, b in PAIR.findall(l)]
                if len(mm) >= 3: pending_main = mm; main.append(mm)
            if re.search(r'合\s*計', l):
                if main and total_main is None:
                    total_main = main.pop()
                    if death and len(death) > len(main): total_death = death.pop()
                break
        if total_main is None or not main: continue
        tables_seen.append((f, t['name']))
        w = len(total_main)
        rows = [r for r in main if len(r) == w]
        for j in range(w):
            chk(f, t['name'], f'列{j + 1} 件数の和=合計', total_main[j][0], sum(r[j][0] for r in rows))
            chk(f, t['name'], f'列{j + 1} 女性の和=合計', total_main[j][1], sum(r[j][1] for r in rows))
        if total_death:
            drows = [r for r in death if len(r) == len(total_death)]
            for j in range(len(total_death)):
                chk(f, t['name'], f'列{j + 1} 死亡の和=合計', total_death[j][0], sum(r[j][0] for r in drows))
                chk(f, t['name'], f'列{j + 1} 死亡女性の和=合計', total_death[j][1], sum(r[j][1] for r in drows))
    # 認定率（表n-1）
    for t in tabs:
        if not re.fullmatch(r'表\d+[-－ー]1', t['name']): continue
        dec = sup = None
        for l in t['lines']:
            if '決定件数' in l and 'うち' not in l:
                dec = [(int(a), int(b)) for a, b in PAIR.findall(l)]
            elif re.search(r'^\s*件数', l) or ('支給決定' in l and PAIR.search(l)):
                s = [(int(a), int(b)) for a, b in PAIR.findall(l)]
                if s: sup = s
            elif '認定率' in l and dec and sup:
                rates = [float(x) for x in re.findall(r'\[(\d+\.\d)%\]', l)]
                for j, r in enumerate(rates):
                    if j < len(dec) and j < len(sup) and dec[j][0]:
                        chk(f, t['name'], f'認定率 列{j + 1}', r, round(sup[j][0] / dec[j][0] * 100, 2), 0.051)
                dec = sup = None
os.makedirs(os.path.join(root, 'results/karoshi'), exist_ok=True)
with open(os.path.join(root, 'results/karoshi/c3401.tsv'), 'w') as fo:
    fo.write('資料\t表\t式\t表の値\t計算値\n')
    for o in out: fo.write('\t'.join(map(str, o)) + '\n')
print('表', len(tables_seen), '式の数', n, '不一致', len(out))
from collections import Counter
print(Counter((o[0], o[1]) for o in out))
for o in out[:30]: print(*o)

# 照合の要約（lib/tally.py）：単位は式。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('karoshi', 'c3401', note='過労死等の労災補償状況 別添資料：内訳の和と合計', script=__file__)
_t.set(compared=n, mismatched=len(out), read_failures=0, explained=None); print('tally', _t.save())
