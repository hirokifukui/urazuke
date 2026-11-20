#!/usr/bin/env python3
"""検算 c001：刑法犯の認知件数・検挙件数・検挙人員・検挙率・発生率（犯罪白書 令和7年版）

対象: 資料1-1（資料編）と 1-1-1-1図（図表データ）、および本文の数値の記述。
すべて取得済みの元データ（data/raw/hanzai_hakusho/72/）から再計算する。外部依存なし。

検算の種類
  A  資料1-1 の内部整合: 検挙率 = 検挙件数/認知件数×100、発生率 = 認知件数/総人口×10万、
     男性+女性 = 検挙人員、女性比 = 女性/検挙人員×100、総数（参考値） ≥ 刑法犯
  B  1-1-1-1図 の内部整合: 刑法犯 = 窃盗 + 窃盗を除く刑法犯（認知件数・検挙件数・検挙人員）、
     検挙率・発生率の再計算
  C  資料1-1 と 1-1-1-1図 の突き合わせ（同じ年・同じ量）
  D  総数（参考値） = 刑法犯 + 危険運転致死傷・過失運転致死傷等（参考値）（資料1-1 注の定義）
  E  本文の数値の記述（令和7年版・令和6年版の本文）を、令和7年版のデータから再計算

出力: results/hanzai_hakusho/c001_keihouhan.tsv（1 行 1 検算）と標準出力の要約
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "lib"))
import xlsx  # noqa: E402

RAW = ROOT / "data" / "raw" / "hanzai_hakusho" / "72"
OUT = ROOT / "results" / "hanzai_hakusho" / "c001_keihouhan.tsv"
REL_TOL = 1e-9      # 保存値どうし・再計算値との比較（丸めのない値）
results = []


def rec(kind, check, year, expected, observed, tol=REL_TOL, note=""):
    if expected is None or observed is None:
        status = "欠測"
        diff = ""
    else:
        d = abs(expected - observed)
        ok = d <= tol * max(1.0, abs(expected)) if tol < 1 else d <= tol
        status = "一致" if ok else "食い違い"
        diff = f"{observed - expected:.6g}"
    results.append([kind, check, str(year), _fmt(expected), _fmt(observed), diff, status, note])


def _fmt(x):
    if x is None:
        return ""
    return f"{x:.10g}" if isinstance(x, float) else str(x)


def year_of(v):
    return int(str(v).replace("年", "")) if v not in ("", None) else None


# ---------- 資料1-1：シートをまたいで年ごとの辞書に ----------
def load_shiryo():
    rows = {}
    for name, cells in xlsx.read_sheets(RAW / "shiryo" / "shiryo1-1.xlsx").items():
        hdr = {c: v for (r, c), v in cells.items() if r == 6}
        for r in sorted({r for r, _ in cells if r >= 7}):
            y = cells.get((r, 3))
            if not (isinstance(y, str) and y.endswith("年") and y[:-1].isdigit()):
                continue
            rows[year_of(y)] = {hdr[c]: cells.get((r, c)) for c in hdr if c >= 4}
    return rows


# ---------- 1-1-1-1図：二段の見出しを結合 ----------
def load_zuhyo():
    cells = next(iter(xlsx.read_sheets(RAW / "zuhyo" / "1-1-1-1.xlsx").values()))
    cols = {c: f"{cells.get((6, c), '')}_{cells.get((7, c), '')}" for c in range(4, 25)}
    rows = {}
    for r in range(8, 200):
        y = cells.get((r, 3))
        if not (isinstance(y, str) and y.endswith("年") and y[:-1].isdigit()):
            continue
        rows[year_of(y)] = {cols[c]: cells.get((r, c)) for c in cols}
    return rows


S = load_shiryo()
Z = load_zuhyo()
K = "刑法犯"
T = "総数（参考値）"
KIKEN = "危険運転致死傷・過失運転致死傷等（参考値）"

# ---------- A ----------
for y, d in sorted(S.items()):
    pop = d.get("総人口（千人）")
    for g in (K, T):
        nin, ken, ritsu, hassei = (d.get(f"{q}_{g}") for q in ("認知件数", "検挙件数", "検挙率", "発生率"))
        if nin and ken is not None and ritsu is not None:
            rec("A", f"資料1-1 検挙率_{g} = 検挙件数/認知件数×100", y, ken / nin * 100, ritsu)
        if nin and pop and hassei is not None:
            rec("A", f"資料1-1 発生率_{g} = 認知件数/総人口×10万", y, nin / (pop * 1000) * 1e5, hassei)
    m, f, tot = d.get("検挙人員_刑法犯_男性_人員"), d.get("検挙人員_刑法犯_女性_人員"), d.get("検挙人員_刑法犯")
    if None not in (m, f, tot):
        rec("A", "資料1-1 男性+女性 = 検挙人員_刑法犯", y, tot, m + f)
        if d.get("検挙人員_刑法犯_女性比") is not None and tot:
            rec("A", "資料1-1 女性比 = 女性/検挙人員×100", y, f / tot * 100, d["検挙人員_刑法犯_女性比"])
    for q in ("認知件数", "検挙件数", "検挙人員"):
        a, b = d.get(f"{q}_{T}"), d.get(f"{q}_{K}")
        if a is not None and b is not None:
            rec("A", f"資料1-1 {q}: 総数（参考値） ≥ 刑法犯", y, 1.0, 1.0 if a >= b else 0.0)

# ---------- B ----------
for y, d in sorted(Z.items()):
    for q in ("認知件数", "検挙件数", "検挙人員"):
        a, b, c = d.get(f"{q}_刑法犯"), d.get(f"{q}_窃盗"), d.get(f"{q}_窃盗を除く刑法犯")
        if None not in (a, b, c):
            rec("B", f"1-1-1-1図 {q}: 刑法犯 = 窃盗 + 窃盗を除く刑法犯", y, a, b + c)
    pop = d.get("総人口_（千人）")
    for g in ("刑法犯", "窃盗", "窃盗を除く刑法犯", KIKEN):
        nin, ken, ritsu, hassei = (d.get(f"{q}_{g}") for q in ("認知件数", "検挙件数", "検挙率", "発生率"))
        if nin and ken is not None and ritsu is not None:
            rec("B", f"1-1-1-1図 検挙率_{g} = 検挙件数/認知件数×100", y, ken / nin * 100, ritsu)
        if nin and pop and hassei is not None:
            rec("B", f"1-1-1-1図 発生率_{g} = 認知件数/総人口×10万", y, nin / (pop * 1000) * 1e5, hassei)

# ---------- C, D ----------
for y in sorted(set(S) | set(Z)):
    s, z = S.get(y), Z.get(y)
    if s is None or z is None:
        rec("C", "年次が両方の資料にある", y, 1.0, 0.0, note="資料1-1" if z is None else "1-1-1-1図")
        continue
    for q in ("認知件数", "検挙件数", "検挙人員", "検挙率", "発生率"):
        rec("C", f"{q}_刑法犯: 資料1-1 = 1-1-1-1図", y, s.get(f"{q}_{K}"), z.get(f"{q}_刑法犯"))
    rec("C", "総人口（千人）: 資料1-1 = 1-1-1-1図", y, s.get("総人口（千人）"), z.get("総人口_（千人）"))
    for q in ("認知件数", "検挙件数", "検挙人員"):
        a, b, c = s.get(f"{q}_{T}"), s.get(f"{q}_{K}"), z.get(f"{q}_{KIKEN}")
        if None not in (a, b, c):
            rec("D", f"{q}: 総数（参考値） = 刑法犯 + 危険運転致死傷・過失運転致死傷等", y, a, b + c)

# ---------- E：本文の記述 ----------
# 出典: 令和7年版 第1編第1章第1節（www.moj.go.jp/content/001455849.pdf）
#       令和6年版 第1編第1章第1節（www.moj.go.jp/content/001432733.pdf）
n = lambda y: S[y]["認知件数_刑法犯"]
r = lambda y: S[y]["発生率_刑法犯"]
claims = [
    ("令和7年版本文", "令和6年の認知件数 73万7,679件", 2024, 737679, n(2024), 0),
    ("令和7年版本文", "前年比 3万4,328件増", 2024, 34328, n(2024) - n(2023), 0),
    ("令和7年版本文", "前年比 4.9%増（小数第1位）", 2024, 4.9, round((n(2024) / n(2023) - 1) * 100, 1), 0),
    ("令和7年版本文", "平成14年に 285万3,739件", 2002, 2853739, n(2002), 0),
    ("令和7年版本文", "令和6年は令和元年の 98.5% の水準（小数第1位）", 2024, 98.5, round(n(2024) / n(2019) * 100, 1), 0),
    ("令和7年版本文", "平成14年が戦後最多（昭和21年以降の最大）", 2002, 2002, max(S, key=n), 0),
    ("令和6年版本文", "令和5年の認知件数 70万3,351件", 2023, 703351, n(2023), 0),
    ("令和6年版本文", "前年比 10万2,020件増", 2023, 102020, n(2023) - n(2022), 0),
    ("令和6年版本文", "前年比 17.0%増（小数第1位）", 2023, 17.0, round((n(2023) / n(2022) - 1) * 100, 1), 0),
    ("令和6年版本文", "平成8年の発生率 1,439.8（小数第1位）", 1996, 1439.8, round(r(1996), 1), 0),
    ("令和6年版本文", "平成14年の発生率 2,238.5 は戦後最高（小数第1位）", 2002, 2238.5, round(r(2002), 1), 0),
    ("令和6年版本文", "発生率の最高は平成14年", 2002, 2002, max(S, key=r), 0),
]
for src, text, y, exp, obs, tol in claims:
    rec("E", f"{src}: {text}", y, float(exp), float(obs), tol=1e-12, note="本文の数値と令和7年版データからの再計算")

# ---------- 出力 ----------
OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("kind\tcheck\tyear\texpected\tobserved\tdiff\tstatus\tnote\n")
    for row in results:
        fh.write("\t".join(row) + "\n")

from collections import Counter  # noqa: E402
print(f"years: 資料1-1 {min(S)}–{max(S)} ({len(S)}年), 1-1-1-1図 {min(Z)}–{max(Z)} ({len(Z)}年)")
for k in "ABCDE":
    c = Counter(r[6] for r in results if r[0] == k)
    print(k, dict(c))
bad = [r for r in results if r[6] != "一致"]
print(f"not-matching: {len(bad)}")
for r_ in bad[:40]:
    print("  ", r_[0], r_[2], r_[1], "expected", r_[3], "observed", r_[4], "diff", r_[5], r_[7])

# 照合の要約（lib/tally.py）：一致・食い違いを照合の数に、欠測（値が読めない・対応なし）を読み取りの失敗に数える。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('hanzai_hakusho', 'c001', note='犯罪白書 令和7年版：資料1-1・1-1-1-1図の内部整合と突き合わせ', script=__file__)
for _r in results:
    _st = _r[6]
    if _st == '一致': _t.ok()
    elif _st == '食い違い': _t.ng(explained=bool(False))
    else: _t.fail()
print('tally', _t.save())
