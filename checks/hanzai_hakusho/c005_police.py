#!/usr/bin/env python3
"""検算 c005（探索）：警察庁の犯罪統計 ↔ 犯罪白書

A  令和6年 犯罪統計【確定値】第1表（e-Stat、CSV）の刑法犯総数・窃盗犯（令和6年・令和5年の列）↔ 白書 令和7年版 資料1-1・1-1-1-1図
B  警察庁の訂正（平成31年3月8日「犯罪統計数値(平成29年)の一部訂正について」：強制わいせつの被害者の性別 1 件）が、
   白書の各版の平成29年の値に反映されているか（6-1-1-1図 人が被害者となった刑法犯（男女別）、
   6-1-3-1表 強制性交等・強制わいせつ（不同意性交等・不同意わいせつ）の男女別）
"""
import csv, io, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "lib"))
import xlsx  # noqa: E402
from tables import sheet_rows, year  # noqa: E402

OUT = ROOT / "results/hanzai_hakusho/c005_police.tsv"
RAW = ROOT / "data/raw"
res = []


def rec(kind, check, exp, obs, note=""):
    st = "欠測" if exp is None or obs is None else ("一致" if abs(exp - obs) < 1e-9 else "食い違い")
    res.append([kind, check, "" if exp is None else f"{exp:.10g}", "" if obs is None else f"{obs:.10g}", st, note])


# ---------- A ----------
rows = list(csv.reader(io.StringIO((RAW / "keisatsu_hanzai_toukei/2024/R06_kakutei.csv").read_bytes().decode("cp932"))))
t1 = next(i for i, r in enumerate(rows) if r and r[0].startswith("第１表"))
P = {}
for r in rows[t1:t1 + 60]:
    if len(r) > 14 and r[0] in ("刑法犯総数", "窃盗犯") and (r[0] == "刑法犯総数" or r[1] == "計"):
        f = lambda x: float(x.strip())
        P[r[0]] = {2024: {"認知件数": f(r[2]), "検挙件数": f(r[6]), "検挙人員": f(r[13])},
                   2023: {"認知件数": f(r[3]), "検挙件数": f(r[7]), "検挙人員": f(r[14])}}
S = {}
for cells in xlsx.read_sheets(RAW / "hanzai_hakusho/72/shiryo/shiryo1-1.xlsx").values():
    t, _ = sheet_rows(cells, key_cols=(3,))
    S.update({year(k): v for k, v in t.items() if year(k)})
Z = next(iter(xlsx.read_sheets(RAW / "hanzai_hakusho/72/zuhyo/1-1-1-1.xlsx").values()))
zr = {year(Z.get((r, 3))): r for r in range(8, 100) if year(Z.get((r, 3)))}
for y in (2024, 2023):
    for q in ("認知件数", "検挙件数", "検挙人員"):
        rec("A", f"警察 第1表 刑法犯総数 {q}（{y}）= 白書 資料1-1", S[y][f"{q}_刑法犯"], P["刑法犯総数"][y][q])
    for q, col in (("認知件数", 5), ("検挙件数", 9), ("検挙人員", 13)):
        rec("A", f"警察 第1表 窃盗犯 {q}（{y}）= 白書 1-1-1-1図 窃盗", Z[(zr[y], col)], P["窃盗犯"][y][q])

# ---------- B ----------
LAB = {65: "平成30年版", 66: "令和元年版", 67: "令和2年版", 68: "令和3年版", 69: "令和4年版", 70: "令和5年版", 71: "令和6年版", 72: "令和7年版"}
BEFORE = {"女性被害（刑法犯）": 242141, "強制わいせつ 女性": 5609, "強制わいせつ 男性": 200}
AFTER = {"女性被害（刑法犯）": 242142, "強制わいせつ 女性": 5610, "強制わいせつ 男性": 199}


def row2017(path):
    c = next(iter(xlsx.read_sheets(path).values()))
    for r in range(7, 60):
        v2, v3 = str(c.get((r, 2), "")).replace("　", "").strip(), str(c.get((r, 3), ""))
        if v3.startswith("2017") or v2 in ("29", "29年", "29.0", "平成29年"):
            return [c.get((r, j)) for j in range(3, 12)]


for ed in range(65, 73):
    a = row2017(RAW / f"hanzai_hakusho/{ed}/bytitle/higai_danjo.xlsx")
    b = row2017(RAW / f"hanzai_hakusho/{ed}/bytitle/seihanzai_higai.xlsx")
    off_a = 1 if isinstance(a[0], str) else 0  # 西暦の列があれば 1 つずれる
    off_b = 1 if isinstance(b[0], str) else 0
    got = {"女性被害（刑法犯）": a[4 + off_a], "強制わいせつ 女性": b[4 + off_b], "強制わいせつ 男性": b[6 + off_b]}
    for k in got:
        state = "訂正後" if got[k] == AFTER[k] else "訂正前" if got[k] == BEFORE[k] else "不明"
        rec("B", f"{LAB[ed]} 平成29年 {k} = 警察庁の訂正後の値", AFTER[k], got[k], note=state)

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("kind\tcheck\texpected\tobserved\tstatus\tnote\n")
    for r in res:
        fh.write("\t".join(r) + "\n")
for k in "AB":
    print(k, dict(Counter(r[4] for r in res if r[0] == k)))
for r in res:
    if r[4] != "一致":
        print("  ", r)

# 照合の要約（lib/tally.py）：一致・食い違いを照合の数に、欠測（値が読めない・対応なし）を読み取りの失敗に数える。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('hanzai_hakusho', 'c005', note='犯罪統計資料と犯罪白書、警察庁の訂正の反映', script=__file__)
for _r in res:
    _st = _r[4]
    if _st == '一致': _t.ok()
    elif _st == '食い違い': _t.ng(explained=bool('訂正前' in _r[5]))
    else: _t.fail()
print('tally', _t.save())
