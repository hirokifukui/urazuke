"""c2101: 障害者白書 令和8年版 参考資料 図表1（障害者数（推計））の内部整合（L1、丸めの幅 0.15万人）。
各行 総数＝在宅者数＋施設入所者数（精神障害者は 外来患者＋入院患者）。総計の男女＝各年齢区分の男女の和。
使い方: ~/.venvs/urazuke/bin/python checks/shogai_hakusho/c2101_zuhyo1.py"""
import re, json, collections
t = open('data/raw/shogai_hakusho/r08/ref.txt', encoding='utf-8').read()
a = t.index('図表１'); b = t.index('図表２', a) if '図表２' in t[a:] else a + 6000
blk = t[a:b].split('\n')
st = collections.Counter(); issues = []; rows = []
grp = None
for l in blk:
    if '身体障害児' in l: grp = '身体'
    if '知的障害児' in l: grp = '知的'
    if '精神障害者' in l: grp = '精神'
    m = re.search(r'(18歳未満|18歳以上|20歳未満|20歳以上|年齢不詳|総計|男性|女性|不詳)\s+([\d.]+|－)\s+([\d.]+|－)\s+([\d.]+|－)\s*$', l)
    if m: rows.append((grp, m[1], [None if x == '－' else float(x) for x in m.group(2, 3, 4)]))
for g, lab, v in rows:
    if None not in v:
        st['row'] += 1
        if abs(v[0] - v[1] - v[2]) > 0.15: issues.append((g, lab, '総数≠内訳の和', v))
json.dump({'counts': st, 'issues': issues, 'rows': rows}, open('results/shogai_hakusho/c2101_zuhyo1.json', 'w'), ensure_ascii=False, indent=1)
print(dict(st), len(rows), issues)

# 照合の要約（lib/tally.py）：単位は式。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('shogai_hakusho', 'c2101', note='障害者白書 図表1：行の内訳の和', script=__file__)
_t.set(compared=sum(st.values()), mismatched=len(issues), read_failures=0, explained=None); print('tally', _t.save())
