"""c2001: こども白書 令和8年版（第2部第1章 PDF）の数値と、引用元の統計の突き合わせ（L4）。
(1) 児童虐待相談対応件数 2024年度 ＝ こども家庭庁 令和6年度の資料（2026-01-30、data/raw/gyakutai）
(2) 小中高生の自殺者数 2025年 ＝ 自殺対策白書 令和8年版 参考資料2-15表（小＋中＋高）
(3) いじめの重大事態の発生件数 2015〜2024年度の推移 ＝ 問題行動・不登校等調査 令和6年度（2026-01-16 修正版）の＜参考9＞
使い方: ~/.venvs/urazuke/bin/python checks/kodomo_hakusho/c2001_vs_sources.py"""
import re, json, subprocess, collections, openpyxl
st = collections.Counter(); res = []
K = open('data/raw/kodomo_hakusho/r08/2-1.txt', encoding='utf-8').read()
def num(s): return int(str(s).replace(',', '').replace(' ', ''))
# (1)
m = re.search(r'児童虐待相談対応件数は、22 万\s*([\d,]+)\s*件', K); v = 220000 + num(m[1])
g = subprocess.run(['pdftotext', '-layout', 'data/raw/gyakutai/sokuhou/R6_sokuhou_cfa_20260130.pdf', '-'], capture_output=True, text=True).stdout
src = num(re.search(r'(22\d,\d{3})', g)[1])
res.append(('児童虐待相談対応件数 2024年度', v, src, v == src))
# (2)
m = re.search(r'2025 年の小中高生の自殺者数は\s*([\d,]+)\s*人', K); v = num(m[1])
ws = openpyxl.load_workbook('data/raw/jisatsu_hakusho/r2026/sanko2_001760475.xlsx', data_only=True)['参考資料2-15表']
r7 = next(r for r in ws.iter_rows(values_only=True) if r[0] == '令和７年')
src = num(r7[2]) + num(r7[3]) + num(r7[4])
res.append(('小中高生の自殺者数 2025年', v, src, v == src, '白書2-15の令和7年の合計欄', r7[1]))
# (3)
m = re.search(r'発生件数\s+((?:[\d,]+\s+){9}[\d,]+)', K); wpv = [num(x) for x in m[1].split()]
F = open('data/raw/futoko/r06/kekka_20260116.txt', encoding='utf-8').read()
srcv = [num(x) for x in re.findall(r'計\s+(20\d\d)年度\s+\S+年度\s+[\d,]+\s+([\d,]+)\s+[\d,]+\s+[\d,]+', F) and [y for _, y in re.findall(r'計\s+(20\d\d)年度\s+\S+年度\s+[\d,]+\s+([\d,]+)\s+[\d,]+\s+[\d,]+', F)]][-10:]
res.append(('いじめの重大事態 2015〜2024年度', wpv, srcv, wpv == srcv))
st['n'] = len(res)
json.dump({'counts': st, 'results': res}, open('results/kodomo_hakusho/c2001_vs_sources.json', 'w'), ensure_ascii=False, indent=1)
print(dict(st)); [print(r) for r in res]

# 照合の要約（lib/tally.py）：単位は式。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('kodomo_hakusho', 'c2001', note='こども白書の数値と元の統計', script=__file__)
_t.set(compared=len(res), mismatched=sum(1 for r in res if r[3] is not True), read_failures=0, explained=None); print('tally', _t.save())
