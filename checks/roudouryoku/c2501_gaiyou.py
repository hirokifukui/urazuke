"""c2501: 労働力調査（基本集計）2025年平均 結果の要約・概要 PDF の文中の数の内部整合（L1、万人単位の丸めで差 1 まで許す）と、要約と概要の一致（L4）。
(a) 労働力人口＝就業者＋完全失業者（男女計・男・女）
(b) 非正規の割合＝非正規／（正規＋非正規）（役員を除く雇用者に占める割合、差 0.1 ポイントまで）
(c) 要約 PDF と概要 PDF の就業者数・完全失業者数・就業率の一致
使い方: ~/.venvs/urazuke/bin/python checks/roudouryoku/c2501_gaiyou.py"""
import re, json, collections
D = 'data/raw/roudouryoku/2025'
G = re.sub(r'\s+', '', open(f'{D}/gaiyou.txt', encoding='utf-8').read()); Y = re.sub(r'\s+', '', open(f'{D}/youyaku.txt', encoding='utf-8').read())
def n(p, t=G):
    m = re.search(p, t); return float(m[1]) if m else None
st = collections.Counter(); issues = []; vals = {}
vals['労働力'] = n(r'2025年平均で(\d+)万人と、前年に比べ\d+万人の増加（３年連続'); vals['労働力男'] = n(r'男性は(\d+)万人と５万人の増加、女性は'); vals['労働力女'] = n(r'男性は3805万人と５万人の増加、女性は(\d+)万人')
vals['就業者'] = n(r'就業者数は、2025年平均で(\d+)万人'); vals['就業者男'] = n(r'男性は(\d+)万人と３万人の増加、女性は', Y); vals['就業者女'] = n(r'男性は3702万人と３万人の増加、女性は(\d+)万人', Y)
vals['失業者'] = n(r'完全失業者数は(\d+)万人', Y); vals['失業者男'] = n(r'男性は(\d+)万人と１万人の増加', Y); vals['失業者女'] = n(r'女性は(\d+)万人と２万人の減少', Y)
for s in ('', '男', '女'):
    a, b, c = vals['労働力' + s], vals['就業者' + s], vals['失業者' + s]
    if None in (a, b, c): issues.append(('値を読めない', s, a, b, c)); continue
    st['a'] += 1
    if abs(a - b - c) > 1: issues.append(('(a)労働力≠就業者+完全失業者', s, a, b, c))
sei = n(r'正規の職員・従業員数は、2025年平均で(\d+)万人'); hi = n(r'非正規の職員・従業員数は、(\d+)万人'); rate = n(r'非正規の職員・従業員の割合は([\d.]+)％')
st['b'] += 1
if abs(hi / (sei + hi) * 100 - rate) > 0.1: issues.append(('(b)非正規の割合', sei, hi, rate, round(hi / (sei + hi) * 100, 2)))
for k, pg, py in [('就業者', r'就業者数は、2025年平均で(\d+)万人', r'就業者数は(\d+)万人'), ('就業率', r'就業率（[^）]*）は、2025年平均で([\d.]+)％', r'就業率（[^）]*）は([\d.]+)％')]:
    a, b = n(pg), n(py, Y); st['c'] += 1
    if a is None or b is None or a != b: issues.append(('(c)概要≠要約', k, a, b))
json.dump({'counts': st, 'issues': issues, 'values': vals}, open('results/roudouryoku/c2501_gaiyou.json', 'w'), ensure_ascii=False, indent=1)
print(dict(st), vals); print(issues)

# 照合の要約（lib/tally.py）：単位は式。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('roudouryoku', 'c2501', note='労働力調査：概要の数値の再計算', script=__file__)
_t.set(compared=sum(st.values()), mismatched=len(issues), read_failures=0, explained=None); print('tally', _t.save())
