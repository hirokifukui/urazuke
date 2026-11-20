#!/usr/bin/env python3
"""c700（準備）：厚労省「令和３年度以前の福祉行政報告例（児童福祉関係の一部）の訂正方針等について」（令和7年10月31日、e-Stat）
の別紙1・2（年度×自治体×報告表の訂正予定の○）を表にする。pdftotext -bbox の座標で、○を見出し（第43〜第57）の列に、
行を自治体名の行に割り当てる（文字位置による推定は1列ずれたため座標を使う。令和3年度の頁を画像で目視し、群馬・埼玉・富山が第49であることを確かめた）。
出力: results/gyakutai/c700_teisei_yotei.tsv（年度・自治体・報告表）。標準出力に第49（児童相談所の児童虐待相談）の年度別自治体。"""
import re, subprocess, html
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / 'data/raw/gyakutai/teisei/R3izen_teisei_houshin_000040137339.pdf'
OUT = ROOT / 'results/gyakutai'; OUT.mkdir(parents=True, exist_ok=True)
x = subprocess.run(['pdftotext', '-bbox', str(PDF), '-'], capture_output=True, text=True).stdout
res = []
for page in re.findall(r'<page.*?</page>', x, re.S):
    words = [(float(a), float(b), float(c), float(d), html.unescape(t)) for a, b, c, d, t in
             re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>', page)]
    text = ''.join(w[4] for w in words)
    m = re.search(r'○?(令和|平成)(\d+|元)年度福祉行政報告例', text)
    if not m or '訂正予定' not in text: continue
    n = 1 if m[2] == '元' else int(m[2]); fy = (2018 + n) if m[1] == '令和' else (1988 + n)
    # 見出し（第43…第57、「第49の２」は「第49の」「２」に分かれることがある）
    heads = []
    for i, w in enumerate(words):
        if re.fullmatch(r'第\d+(の２?)?', w[4]):
            lab = w[4] if not w[4].endswith('の') else w[4] + '２'
            heads.append(((w[0] + w[2]) / 2, lab.replace('の２', 'の２')))
    heads = sorted(set(heads))
    # 自治体名の行：番号の後の名前
    names = [(w[1], w[3], w[4]) for w in words if re.fullmatch(r'.+(都|道|府|県|市|区)', w[4]) and w[0] < 150]
    for w in words:
        if w[4] != '○': continue
        cx, cy = (w[0] + w[2]) / 2, (w[1] + w[3]) / 2
        h = min(heads, key=lambda t: abs(t[0] - cx))[1]
        row = min(names, key=lambda t: abs((t[0] + t[1]) / 2 - cy))
        res.append((fy, row[2], h))
with open(OUT / 'c700_teisei_yotei.tsv', 'w') as f:
    f.write('fiscal_year\tauthority\treport_table\n')
    for r in sorted(set(res)): f.write('\t'.join(map(str, r)) + '\n')
by = defaultdict(set)
for fy, n, h in res:
    if h == '第49': by[fy].add(n)
for fy in range(2015, 2024): print(fy, '第49の訂正予定', len(by[fy]), ' '.join(sorted(by[fy])))
