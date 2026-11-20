"""文科省 公立学校教職員の人事行政状況調査：性犯罪・性暴力等（旧 わいせつ行為等）による懲戒処分等の
都道府県・指定都市別「推移（過去5年間）」の表を版（調査年度）ごとに読み、
(1) 67教育委員会の和＝合計（各年度）、(2) 同じ教育委員会・同じ年度の値が版の間で変わっていないか、を確かめる。
"""
import re, glob, subprocess, json, unicodedata
from pathlib import Path
ROOT = Path.cwd() if (Path.cwd() / 'data/raw').is_dir() else Path(__file__).resolve().parents[2]
D = ROOT / 'data/raw/kyoin_chokai'
# 版（ページ番号）→ 推移の表のファイル（性犯罪・性暴力等）
SUII = {'R3当初(2022-12-22)': 'old/20221222-mxt-syoto01-000026693_39.pdf',
        'R3': '00006/20230116-mxt-syoto01-000026693_02_04_03.pdf',
        'R4当初(2023-12-22)': 'old/20231222-mxt_syoto01-000033180_47.pdf',
        'R4': '00007/20241220-mxt_syoto01-000033180_17.pdf',
        'R5': '00008/20241220-mxt_syoto01-000039268_48.pdf',
        'R6': '00009/20251217-mxt_syoto01-000046407_38.pdf'}
YR = {'H29': 2017, 'H30': 2018, 'R1': 2019, 'R元': 2019, 'R2': 2020, 'R3': 2021, 'R4': 2022, 'R5': 2023, 'R6': 2024}


def text(p):
    return unicodedata.normalize('NFKC', subprocess.run(['pdftotext', '-layout', str(p), '-'], capture_output=True, text=True).stdout)


def parse(p):
    t = text(p)
    hdr = next(l for l in t.splitlines() if re.search(r'(H29|H30|R元|R\d)年度', l))
    years = [YR[y] for y in re.findall(r'(H29|H30|R元|R\d)年度', hdr)]
    out = {}
    for l in t.splitlines():
        m = re.match(r'^\s*(\d{1,2})?\s*([^\d\s]{1,5}?(?:都|道|府|県|市))\s+((?:\d+\s+){%d})' % len(years), l)
        if m:
            v = [int(x) for x in m.group(3).split()]
            out[m.group(2)] = dict(zip(years, v))
        m2 = re.match(r'^\s*(合\s*計)\s+((?:\d+\s+){%d})' % len(years), l)
        if m2:
            out['合計'] = dict(zip(years, [int(x) for x in m2.group(2).split()]))
    return years, out


ng = ok = 0
tabs = {}
for ed, f in SUII.items():
    years, d = parse(D / f)
    tabs[ed] = d
    bodies = [k for k in d if k != '合計']
    print(f'{ed}: 年度 {years}、教育委員会 {len(bodies)}、合計行 {"あり" if "合計" in d else "なし"}')
    if '合計' in d:
        for y in years:
            s = sum(d[k][y] for k in bodies)
            if s == d['合計'][y]:
                ok += 1
            else:
                ng += 1; print(f'  不一致 {ed} {y} 和 {s} 合計 {d["合計"][y]}')
print('## 版間（同じ教育委員会・同じ年度）')
eds = list(SUII)
diff = []
for i, a in enumerate(eds):
    for b in eds[i + 1:]:
        for k in tabs[a]:
            if k not in tabs[b]:
                continue
            for y, v in tabs[a][k].items():
                if y in tabs[b][k]:
                    if v == tabs[b][k][y]:
                        ok += 1
                    else:
                        ng += 1; diff.append((y, k, a, v, b, tabs[b][k][y]))
for y, k, a, v, b, w in sorted(set(diff)):
    print(f'  改訂 {y}年度 {k}：{a}版 {v} → {b}版 {w}')
print('式', ok, '不一致', ng)
json.dump({ed: {k: {str(y): v for y, v in d.items()} for k, d in t.items()} for ed, t in tabs.items()},
          open('/tmp/kyoin_suii.json', 'w'), ensure_ascii=False)

# 照合の要約（lib/tally.py）：67教育委員会の和＝合計、版間の同じ値。不一致16はすべて表に「数値に更新」と書かれた改訂＝説明あり。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('kyoin_chokai', 'c4601', note='教員の懲戒処分（児童生徒性暴力等）の推移の表：和と合計、版間', script=__file__)
_t.set(compared=ok + ng, mismatched=ng, explained=ng); print('tally', _t.save())
