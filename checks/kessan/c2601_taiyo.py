"""c2601: 令和7年度決算検査報告「検査の概要」(1) 検査の大要 の表の内部整合（L1）。
扱い方（r08 で決めた一案）：決算検査報告は統計ではなく指摘の集まりなので、指摘の当否は扱わない。報告に載った数（件数・指摘金額）を統計表と同じく検査する。
(a) 件数：不当事項＋意見・処置要求の小計＋改善の処置＝事項計、事項計＋国会・内閣への報告＋要請事項＋特定検査対象＝総計、小計＝第34条＋第34条及び第36条＋第36条、〈指摘金額のある件数〉の和
(b) 金額：意見・処置要求の小計＝3区分の指摘金額の和（1万円未満の切捨てによる差を許す）。事項計と各事項の和の差は、注(3)の重複の控除として記録する
使い方: ~/.venvs/urazuke/bin/python checks/kessan/c2601_taiyo.py"""
import re, json, collections
t = open('data/raw/kessan/r07/fy07_01_gaiyou.txt', encoding='utf-8').read()
blk = t[t.index('(1) 検査の大要'):t.index('注(1) 金額は')]
def man(s):   # 「111 億 8636 万円」→ 万円
    m = re.fullmatch(r'\s*(?:(\d+)\s*億)?\s*(?:(\d+)\s*万円)?\s*', s); return (int(m[1] or 0) * 10000 + int(m[2] or 0)) if m else None
def grab(label):
    m = re.search(label + r'\s+(\d+)\s*件\s+((?:\d+\s*億\s*)?\d+\s*万円)', blk); return (int(m[1]), man(m[2])) if m else None
V = {k: grab(p) for k, p in [('不当', r'不\s*当\s*事\s*項'), ('34', r'第 34 条(?!及び)'), ('34+36', r'第 34 条及び第 36 条'), ('36', r'(?<!及び)第 36 条'), ('小計', r'小\s*計'), ('事項計', r'事\s*項\s*計'), ('総計', r'総\s*計')]}
m = re.search(r'〈20 件分〉\s*\n\s*(\d+)\s*件\s+((?:\d+\s*億\s*)?\d+\s*万円)', blk); V['改善'] = (int(m[1]), man(m[2])) if m else None
others = [int(x) for x in re.findall(r'(\d+)件\s+―', blk)]
kenbun = [int(x) for x in re.findall(r'〈(\d+)\s*件分〉', blk)]
st = collections.Counter(); issues = []; notes = []
def chk(name, a, b, tol=0):
    st['n'] += 1
    if abs(a - b) > tol: issues.append((name, a, b))
chk('(a)小計＝34＋34及び36＋36', V['小計'][0], V['34'][0] + V['34+36'][0] + V['36'][0])
chk('(a)事項計＝不当＋小計＋改善', V['事項計'][0], V['不当'][0] + V['小計'][0] + V['改善'][0])
chk('(a)総計＝事項計＋その他の報告', V['総計'][0], V['事項計'][0] + sum(others))
chk('(b)小計の金額＝3区分の和（切捨て 3万円まで）', V['小計'][1], V['34'][1] + V['34+36'][1] + V['36'][1], tol=3)
d = V['不当'][1] + V['小計'][1] + V['改善'][1] - V['事項計'][1]
notes.append(('事項計と各事項の和の差（注(3) 重複の控除）', d, '万円'))
json.dump({'counts': st, 'issues': issues, 'values': V, 'others': others, 'kenbun': kenbun, 'notes': notes}, open('results/kessan/c2601_taiyo.json', 'w'), ensure_ascii=False, indent=1)
print(V, others, kenbun); print(dict(st), issues, notes)

# 照合の要約（lib/tally.py）：単位は式。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('kessan', 'c2601', note='国の決算の概要：数値の照合', script=__file__)
_t.set(compared=st['n'], mismatched=len(issues), read_failures=0, explained=None); print('tally', _t.save())
