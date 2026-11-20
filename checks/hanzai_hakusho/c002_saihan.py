#!/usr/bin/env python3
"""検算 c002：再犯・再入（犯罪白書 令和7年版 第5編）

対象: 5-1-1図、5-3-1図、5-3-2図、5-3-6図〜5-3-10図、資料5-1、および資料1-1（突き合わせ用）。
すべて取得済みの元データ（data/raw/hanzai_hakusho/72/）から再計算する。外部依存なし。

検算の種類
  A  5-1-1図: 初犯者+再犯者 = 検挙人員、再犯者率、検挙人員 = 資料1-1 の刑法犯検挙人員
  B  5-3-1図・5-3-2図・資料5-1: 初入+再入 = 総数、再入者率、入所度数の内訳、男女の内訳、
     5-3-1図の再入者 = 資料5-1 の総数、構成比
  C  出所年コホート表（5-3-6図・5-3-7図・5-3-8図）: 再入率 = 再入所者/出所受刑者、
     内訳の和（満期釈放等+仮釈放、入所度数の和）、累積人員が減らないこと、表どうしの一致
  D  推移表（5-3-9図・5-3-10図）: A = B + D、F = G + I、比率、男女・年齢層の和、表どうしの一致
  E  コホート表 ↔ 推移表: 同じ出所年の 2 年以内・5 年以内の人員と比率
  F  本文・図中の数値の記述（第5編第1章・第3章の本文 HTML、5-3-9図の画像に印字された値）
     比率は小数第1位、pt 差は「丸めた値どうしの差」と「丸める前の差を丸めた値」のどちらかと一致すれば一致とし、どちらで一致したかを記す
出力: results/hanzai_hakusho/c002_saihan.tsv
"""
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "lib"))
import xlsx  # noqa: E402
from tables import sheet_rows, year, num  # noqa: E402

RAW = ROOT / "data" / "raw" / "hanzai_hakusho" / "72"
OUT = ROOT / "results" / "hanzai_hakusho" / "c002_saihan.tsv"
TOL = 1e-9
results = []


def rec(kind, check, where, expected, observed, note=""):
    if expected is None or observed is None:
        status, diff = "欠測", ""
    else:
        ok = abs(expected - observed) <= TOL * max(1.0, abs(expected))
        status, diff = ("一致" if ok else "食い違い"), f"{observed - expected:.6g}"
    f = lambda x: "" if x is None else f"{x:.10g}"
    results.append([kind, check, str(where), f(expected), f(observed), diff, status, note])


def Z(name):
    return xlsx.read_sheets(RAW / "zuhyo" / f"{name}.xlsx")


def ratio(n, d):
    return None if (n is None or not d) else n / d * 100


# ================= A: 5-1-1 =================
s11 = next(iter(Z("5-1-1").values()))
A, _ = sheet_rows(s11, key_cols=(3,))
shiryo = {}
for cells in xlsx.read_sheets(RAW / "shiryo" / "shiryo1-1.xlsx").values():
    t, _ = sheet_rows(cells, key_cols=(3,))
    shiryo.update({year(k): v for k, v in t.items() if year(k)})
for k, d in A.items():
    y = year(k)
    if not y:
        continue
    tot, sho, sai, rate = (num(d.get(c)) for c in ("検挙人員", "検挙人員_初犯者", "検挙人員_再犯者", "検挙人員_再犯者率"))
    rec("A", "5-1-1図 初犯者+再犯者 = 検挙人員", y, tot, (sho or 0) + (sai or 0) if None not in (sho, sai) else None)
    rec("A", "5-1-1図 再犯者率 = 再犯者/検挙人員×100", y, ratio(sai, tot), rate)
    rec("A", "5-1-1図 検挙人員 = 資料1-1 検挙人員_刑法犯", y, num(shiryo.get(y, {}).get("検挙人員_刑法犯")), tot)

# ================= B: 5-3-1, 5-3-2, 資料5-1 =================
s31 = Z("5-3-1")
B = {}
for nm, cells in s31.items():
    t, _ = sheet_rows(cells, key_cols=(3,))
    B["女性" if "②" in nm else "総数"] = {year(k): v for k, v in t.items() if year(k)}
for sex, t in B.items():
    for y, d in t.items():
        tot, sho, sai, rate = (num(d.get(c)) for c in ("総数", "初入者", "再入者", "再入者率"))
        rec("B", f"5-3-1図({sex}) 初入者+再入者 = 総数", y, tot, sho + sai)
        rec("B", f"5-3-1図({sex}) 再入者率 = 再入者/総数×100", y, ratio(sai, tot), rate)
for y in B["総数"]:
    if y in B["女性"]:
        for c in ("総数", "初入者", "再入者"):
            ok = B["女性"][y][c] <= B["総数"][y][c]
            rec("B", f"5-3-1図 女性 ≤ 総数（{c}）", y, 1.0, 1.0 if ok else 0.0)

s32 = Z("5-3-2")
D32 = {}
for nm, cells in s32.items():
    t, _ = sheet_rows(cells, key_cols=(3,))
    D32["総数" if "①" in nm else "男性" if "②" in nm else "女性"] = {year(k): v for k, v in t.items() if year(k)}
deg = ("１度", "２度", "３度", "４度", "５度以上")
for y, d in D32["総数"].items():
    for c in deg:
        rec("B", f"5-3-2図 男性+女性 = 総数（{c}）", y, d[c], D32["男性"][y][c] + D32["女性"][y][c])
    for sex in ("総数", "女性"):
        src = D32[sex][y]
        if y in B[sex]:
            rec("B", f"5-3-2図({sex}) １度 = 5-3-1図 初入者", y, B[sex][y]["初入者"], src["１度"])
            rec("B", f"5-3-2図({sex}) ２度〜５度以上の和 = 5-3-1図 再入者", y, B[sex][y]["再入者"],
                sum(src[c] for c in deg[1:]))

for nm, cells in xlsx.read_sheets(RAW / "shiryo" / "shiryo5-1.xlsx").items():
    y = 2024 if "Ｒ６" in nm or "R６" in nm or "R6" in nm else 2023
    t, order = sheet_rows(cells, key_cols=(2, 3))
    grand = t[("総数", "総数")]
    for key in order:
        d = t[key]
        rec("B", f"資料5-1 男性+女性 = 総数（{key[0]}・{key[1]}）", y, d["総数"], d["男性"] + d["女性"])
        for sx in ("総数", "男性", "女性"):
            rec("B", f"資料5-1 構成比_{sx}（{key[0]}・{key[1]}）", y, ratio(d[sx], grand[sx]), d[f"{sx}_構成比"])
    for kubun in ("刑法犯", "特別法犯"):
        if (kubun, "総数") in t:
            parts = [t[k]["総数"] for k in order if k[0] == kubun and k[1] != "総数"]
            rec("B", f"資料5-1 {kubun}の罪名の和 = {kubun}総数", y, t[(kubun, "総数")]["総数"], sum(parts))
    kubun_tot = [k for k in order if k[1] == "総数" and k[0] != "総数"]
    rec("B", "資料5-1 区分ごとの総数の和（" + "・".join(k[0] for k in kubun_tot) + "）= 総数", y, grand["総数"],
        sum(t[k]["総数"] for k in kubun_tot))
    rec("B", "資料5-1 総数 = 5-3-1図 再入者（総数）", y, B["総数"][y]["再入者"], grand["総数"])
    rec("B", "資料5-1 女性 = 5-3-1図 再入者（女性）", y, B["女性"][y]["再入者"], grand["女性"])


# ================= C: コホート表 =================
def cohort(t, where):
    """t: {鍵: {出所受刑者人員, 再入所者人員_X, 再入率_X, ...}} → 各行の (N, [(X, n, rate)])"""
    out = {}
    for key, d in t.items():
        N = num(d.get("出所受刑者人員"))
        # 人員列のすぐ右が再入率列（見出しの年の表記が揃っていないシートがあるため位置で対応させる）
        cols = list(d)
        ser = [(c[len("再入所者人員_"):], num(d[c]), num(d[cols[i + 1]]) if i + 1 < len(cols) and cols[i + 1].startswith("再入率") else None)
               for i, c in enumerate(cols) if c.startswith("再入所者人員_")]
        out[key] = (N, ser)
        prev = 0.0
        for lab, n, r in ser:
            rec("C", f"{where} 再入率 = 再入所者/出所受刑者×100（{key}・{lab}）", "", ratio(n, N), r)
            rec("C", f"{where} 累積再入所者が減らない（{key}・{lab}）", "", 1.0, 1.0 if n >= prev else 0.0)
            rec("C", f"{where} 再入所者 ≤ 出所受刑者（{key}・{lab}）", "", 1.0, 1.0 if n <= N else 0.0)
            prev = n
    return out


def sum_rule(co, total_key, part_keys, where):
    N0, s0 = co[total_key]
    rec("C", f"{where} 出所受刑者人員: {total_key} = " + " + ".join(map(str, part_keys)), "",
        N0, sum(co[k][0] for k in part_keys))
    for i, (lab, n, _) in enumerate(s0):
        rec("C", f"{where} 再入所者人員（{lab}）: {total_key} = 内訳の和", "", n, sum(co[k][1][i][1] for k in part_keys))


CO = {}
for fig, keycols5 in (("5-3-6", (2, 3)), ("5-3-7", (2, 3))):
    for nm, cells in Z(fig).items():
        ed = "R6" if "６" in nm else "R5"
        five = "①" in nm
        t, _ = sheet_rows(cells, key_cols=keycols5 if five else (2,))
        co = cohort(t, f"{fig}図 {ed}{'5年' if five else '10年'}")
        CO[(fig, ed, "5" if five else "10")] = co
        w = f"{fig}図 {ed}{'5年' if five else '10年'}"
        if fig == "5-3-6" and five:
            sum_rule(co, ("総数", "総数"), [("満期釈放等", "総数"), ("仮釈放", "総数")], w)
            sum_rule(co, ("総数", "一部執行猶予者"), [("実刑期終了", "一部執行猶予者"), ("仮釈放", "一部執行猶予者")], w)
        elif fig == "5-3-6":
            sum_rule(co, "総数", ["満期釈放", "仮釈放"], w)
        elif five:
            for kb in ("総数", "一部執行猶予者"):
                sum_rule(co, ("総数", kb), [(d, kb) for d in ("１度", "２度", "３度以上")], w)
        else:
            sum_rule(co, "総数", ["１度", "２度", "３度以上"], w)
for nm, cells in Z("5-3-8").items():
    ed = "R6" if "６" in nm else "R5"
    t, order = sheet_rows(cells, key_cols=(2, 3))
    co = cohort(t, f"5-3-8図 {ed}")
    for crime in dict.fromkeys(k[0] for k in order):
        if (crime, "満期釈放等") in co and (crime, "仮釈放") in co:
            sum_rule(co, (crime, "総数"), [(crime, "満期釈放等"), (crime, "仮釈放")], f"5-3-8図 {ed}")
# 5-3-6 と 5-3-7 の総数行は同じ母集団
for ed in ("R6", "R5"):
    for span, key in (("5", ("総数", "総数")), ("5", ("総数", "一部執行猶予者")), ("10", "総数")):
        a, b = CO[("5-3-6", ed, span)][key], CO[("5-3-7", ed, span)][key]
        rec("C", f"5-3-6図 = 5-3-7図 出所受刑者人員（{ed}{span}年・{key}）", "", a[0], b[0])
        for (la, na, _), (lb, nb, _) in zip(a[1], b[1]):
            rec("C", f"5-3-6図 = 5-3-7図 再入所者人員（{ed}{span}年・{key}・{la}）", "", na, nb)

# ================= D: 推移表 =================
T9 = {}
for nm, cells in Z("5-3-9").items():
    span = "2" if "①" in nm else "5"
    letters = {}
    for c in range(1, 25):
        v = str(cells.get((7, c), ""))
        for L in "ABCDEFGHIJ":
            if f"（{L}）" in v:
                letters[L] = c
            if f"({L}/" in v:
                letters[L + "%"] = c
    rows = {}
    for r in range(8, 60):
        y = year(cells.get((r, 3)))
        if y:
            rows[y] = {L: num(cells.get((r, c))) for L, c in letters.items()}
            rows[y]["_label_den"] = {L: str(cells.get((7, c)))[str(cells.get((7, c))).find("/") + 1]
                                     for L, c in letters.items() if L.endswith("%")}
    T9[span] = rows
    for y, d in rows.items():
        w = f"5-3-9図 {span}年以内"
        rec("D", f"{w} A = B + D（出所受刑者人員）", y, d["A"], (d["B"] or 0) + (d["D"] or 0))
        rec("D", f"{w} F = G + I（再入者人員）", y, d["F"], (d["G"] or 0) + (d["I"] or 0))
        for L, den in (("F", "A"), ("G", "B"), ("I", "D"), ("H", "C")):
            if d.get(L) is not None and d.get(den):
                rec("D", f"{w} {L}/{den}×100 = 比率", y, ratio(d[L], d[den]), d.get(L + "%"))
        # J の比率: 見出しは (J/D％)。分母が D か E かを両方で確かめる
        if d.get("J") is not None and d.get("E"):
            lab = d["_label_den"].get("J%")
            rec("D", f"{w} J の比率 = J/E×100（一部執行猶予ありの仮釈放者に対する比率）", y, ratio(d["J"], d["E"]), d.get("J%"),
                note=f"見出しの分母表記: J/{lab}")
            rec("D", f"{w} J の比率 = J/D×100（見出しどおりの分母）", y, ratio(d["J"], d["D"]), d.get("J%"),
                note=f"見出しの分母表記: J/{lab}")
        if d.get("C") is not None:
            rec("D", f"{w} C ≤ B、E ≤ D（一部執行猶予の内数）", y, 1.0, 1.0 if d["C"] <= d["B"] and d["E"] <= d["D"] else 0.0)

T10 = {}
for nm, cells in Z("5-3-10").items():
    t, _ = sheet_rows(cells, key_cols=(3,))
    T10[nm] = {year(k): v for k, v in t.items() if year(k)}
sx = next(v for k, v in T10.items() if "男女" in k)
ag = next(v for k, v in T10.items() if "年齢" in k)
for y, d in sx.items():
    w = "5-3-10図"
    rec("D", f"{w} 男性+女性 = 出所受刑人員", y, d["出所受刑人員"], d["出所受刑人員_男性"] + d["出所受刑人員_女性"])
    rec("D", f"{w} 男性+女性 = ２年以内再入者人員", y, d["２年以内再入者人員"],
        d["２年以内再入者人員_男性"] + d["２年以内再入者人員_女性"])
    for suf, den in (("", "出所受刑人員"), ("_男性", "出所受刑人員_男性"), ("_女性", "出所受刑人員_女性")):
        rec("D", f"{w} ２年以内再入率{suf or '_総数'}", y, ratio(d["２年以内再入者人員" + suf], d[den]),
            d["２年以内再入者人員" + suf + "_比率"])
    if y in T9["2"]:
        rec("D", f"{w} 出所受刑人員 = 5-3-9図① A", y, T9["2"][y]["A"], d["出所受刑人員"])
        rec("D", f"{w} ２年以内再入者人員 = 5-3-9図① F", y, T9["2"][y]["F"], d["２年以内再入者人員"])
    a = ag.get(y)
    if a:
        Ns = [v for c, v in a.items() if c.endswith("_出所受刑者人員") and v is not None]
        ns = [v for c, v in a.items() if c.endswith("_２年以内再入者人員") and v is not None]
        rec("D", f"{w} 年齢層の出所受刑者人員の和 = 総数", y, d["出所受刑人員"], sum(Ns), note=f"{len(Ns)}区分")
        rec("D", f"{w} 年齢層の２年以内再入者人員の和 = 総数", y, d["２年以内再入者人員"], sum(ns), note=f"{len(ns)}区分")

# ================= E: コホート表 ↔ 推移表 =================
# 出所年を 1 年目として、2 年以内 = 2 年目の年末、5 年以内 = 5 年目の年末までの累積
for (fig, ed, span), co in CO.items():
    if fig != "5-3-6":
        continue
    cy = {("R6", "5"): 2020, ("R5", "5"): 2019, ("R6", "10"): 2015, ("R5", "10"): 2014}[(ed, span)]
    if span == "5":
        rowmap = {"A": ("総数", "総数"), "B": ("満期釈放等", "総数"), "D": ("仮釈放", "総数"),
                  "C": ("実刑期終了", "一部執行猶予者"), "E": ("仮釈放", "一部執行猶予者")}
    else:
        rowmap = {"A": "総数", "B": "満期釈放", "D": "仮釈放"}
    numer = {"A": "F", "B": "G", "D": "I", "C": "H", "E": "J"}
    for k_years in (2, 5):
        t9 = T9[str(k_years)].get(cy)
        if not t9:
            continue
        for L, key in rowmap.items():
            N, ser = co[key]
            rec("E", f"{fig}図 {ed}{span}年（{cy}年出所）出所受刑者人員 = 5-3-9図 {L}", cy, t9[L], N)
            if k_years - 1 < len(ser):
                lab, n, _ = ser[k_years - 1]
                rec("E", f"{fig}図 {ed}{span}年（{cy}年出所）{k_years}年以内再入者（{lab}年末）= 5-3-9図 {numer[L]}",
                    cy, t9[numer[L]], n)

# ================= F: 本文・図中の数値 =================
# 出典: honbun/n72_2_5_1_0_1.html（5-1-1）, n72_2_5_3_0_1.html（5-3-1）, n72_2_5_3_0_2.html（5-3-6）,
#       n72_2_5_3_0_3.html（5-3-9, 5-3-10）, images/h5-3-9.jpg（図中の表示値）
def r1(x):
    from decimal import Decimal, ROUND_HALF_UP
    return float(Decimal(repr(x)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def claim(text, where, stated, value):
    rec("F", text, where, float(stated), float(value))


def claim_pct(text, where, stated, value):
    claim(text, where, stated, r1(value))


def claim_pt(text, where, stated, a, b):
    """a - b の pt 差（stated は符号つき）。丸めた値どうしの差と、丸める前の差の丸めの両方を試す。"""
    m1 = round(r1(a) - r1(b), 1)
    m2 = r1(a - b)
    if abs(m1 - stated) < 1e-9 or abs(m2 - stated) < 1e-9:
        how = "丸めた値どうしの差" if abs(m1 - stated) < 1e-9 else "丸める前の差を丸めた値"
        if abs(m1 - stated) < 1e-9 and abs(m2 - stated) < 1e-9:
            how = "どちらの方法でも"
        rec("F", text, where, float(stated), float(stated), note=how)
    else:
        rec("F", text, where, float(stated), m1, note=f"丸める前の差を丸めた値は {m2}")


def growth(a, b):
    return (a / b - 1) * 100


def runs(series, y0, y1, cmp):
    return all(cmp(series[y], series[y - 1]) for y in range(y0, y1 + 1))


sai = {y: A[k]["検挙人員_再犯者"] for k in A for y in [year(k)] if y}
sho = {y: A[k]["検挙人員_初犯者"] for k in A for y in [year(k)] if y}
rr = {y: A[k]["検挙人員_再犯者率"] for k in A for y in [year(k)] if y}
claim("5-1 本文: 平成8年の再犯者 8万1,776人", 1996, 81776, sai[1996])
claim("5-1 本文: 平成18年の再犯者 14万9,164人", 2006, 149164, sai[2006])
claim("5-1 本文: 再犯者は平成18年がピーク（平成8年以降の最大）", 2006, 2006, max((y for y in sai if y >= 1996), key=sai.get))
claim("5-1 本文: 令和6年の再犯者 8万8,697人", 2024, 88697, sai[2024])
claim_pct("5-1 本文: 再犯者 前年比3.0%増", 2024, 3.0, growth(sai[2024], sai[2023]))
claim("5-1 本文: 再犯者は令和5年から2年連続で増加", 2024, 1, runs(sai, 2023, 2024, lambda a, b: a > b))
claim("5-1 本文: 平成12年の初犯者 20万5,645人", 2000, 205645, sho[2000])
claim("5-1 本文: 平成16年の初犯者 25万30人（ピーク）", 2004, 250030, sho[2004])
claim("5-1 本文: 初犯者は平成16年がピーク（平成12年以降の最大）", 2004, 2004, max((y for y in sho if y >= 2000), key=sho.get))
claim("5-1 本文: 令和6年の初犯者 10万3,129人", 2024, 103129, sho[2024])
claim_pct("5-1 本文: 初犯者 前年比6.1%増", 2024, 6.1, growth(sho[2024], sho[2023]))
claim_pct("5-1 本文: 令和6年の再犯者率 46.2%", 2024, 46.2, rr[2024])
claim_pt("5-1 本文: 再犯者率 前年比0.7pt低下", 2024, -0.7, rr[2024], rr[2023])
claim("5-1 本文: 再犯者率は令和3年から4年連続で低下", 2024, 1, runs(rr, 2021, 2024, lambda a, b: a < b))

for sex, lab in (("総数", "総数"), ("女性", "女性")):
    t = B[sex]
    sa = {y: t[y]["再入者"] for y in t}
    ra = {y: t[y]["再入者率"] for y in t}
    if sex == "総数":
        claim("5-3 本文: 令和6年の再入者 7,957人", 2024, 7957, sa[2024])
        claim_pct("5-3 本文: 再入者 前年比2.7%増", 2024, 2.7, growth(sa[2024], sa[2023]))
        last_up = max(y for y in sa if y < 2024 and y - 1 in sa and sa[y] > sa[y - 1])
        claim("5-3 本文: 再入者は令和6年に16年ぶりに増加（直前の増加年が平成20年）", 2024, 16, 2024 - last_up)
        claim("5-3 本文: 再入者は平成18年がピーク（平成元年以降の最大）", 2006, 2006, max(sa, key=sa.get))
        claim("5-3 本文: 再入者は平成21年以降 令和5年まで減少し続けた", 2023, 1, runs(sa, 2009, 2023, lambda a, b: a < b))
        ini = {y: t[y]["初入者"] for y in t}
        claim_pct("5-3 本文: 初入者 前年比8.3%増", 2024, 8.3, growth(ini[2024], ini[2023]))
        claim_pct("5-3 本文: 令和6年の再入者率 53.7%", 2024, 53.7, ra[2024])
        claim_pt("5-3 本文: 再入者率 前年比1.3pt低下", 2024, -1.3, ra[2024], ra[2023])
    else:
        claim("5-3 本文: 女性の再入者 平成26年 996人", 2014, 996, sa[2014])
        claim("5-3 本文: 女性の再入者は平成26年がピーク（平成11年以降の最大）", 2014, 2014, max((y for y in sa if y >= 1999), key=sa.get))
        claim("5-3 本文: 女性の再入者 令和6年 730人", 2024, 730, sa[2024])
        claim_pct("5-3 本文: 女性の再入者 前年比2.2%増", 2024, 2.2, growth(sa[2024], sa[2023]))
        last_up = max(y for y in sa if y < 2024 and y - 1 in sa and sa[y] > sa[y - 1])
        claim("5-3 本文: 女性の再入者は令和6年に10年ぶりに増加（直前の増加年が平成26年）", 2024, 10, 2024 - last_up)
        claim_pct("5-3 本文: 女性の再入者率 46.9%", 2024, 46.9, ra[2024])
        claim_pt("5-3 本文: 女性の再入者率 前年比1.2pt低下", 2024, -1.2, ra[2024], ra[2023])

N20, ser20 = CO[("5-3-6", "R6", "5")][("総数", "総数")]
claim_pct("5-3 本文: 令和2年出所 総数の2年以内再入率 15.1%", 2020, 15.1, ser20[1][1] / N20 * 100)
claim_pct("5-3 本文: 令和2年出所 総数の5年以内再入率 34.0%", 2020, 34.0, ser20[4][1] / N20 * 100)

t2, t5 = T9["2"], T9["5"]
pct = lambda t, y, L: t[y][L + "%"]
for L, nm, h11, r5, d1, d16 in (("F", "総数", 23.4, 13.8, 0.8, -7.4), ("G", "満期釈放者等", 33.9, 20.8, 0.7, -11.5),
                                ("I", "仮釈放者", 15.6, 9.6, 1.0, -2.9)):
    claim_pct(f"5-3 本文: {nm}の2年以内再入率 平成11年 {h11}%", 1999, h11, pct(t2, 1999, L))
    claim_pct(f"5-3 本文: {nm}の2年以内再入率 令和5年 {r5}%", 2023, r5, pct(t2, 2023, L))
    claim_pt(f"5-3 本文: {nm}の2年以内再入率 前年比{d1}pt上昇", 2023, d1, pct(t2, 2023, L), pct(t2, 2022, L))
    claim_pt(f"5-3 本文: {nm}の2年以内再入率 平成16年比{-d16}pt低下", 2023, d16, pct(t2, 2023, L), pct(t2, 2004, L))
claim_pct("5-3 本文: 総数の2年以内再入率 令和元年 15.7%", 2019, 15.7, pct(t2, 2019, "F"))
claim("5-3 本文: 令和元年に初めて16%を下回った（それ以前はすべて16%以上）", 2019, 1,
      r1(pct(t2, 2019, "F")) < 16 and all(r1(pct(t2, y, "F")) >= 16 for y in t2 if y < 2019))
for L, nm, v in (("G", "満期釈放等", 20.8), ("F", "総数", 13.8), ("I", "仮釈放", 9.6)):
    claim_pct(f"5-3-9図① 図中の表示値 令和5年 {nm} {v}", 2023, v, pct(t2, 2023, L))
for L, nm, v in (("G", "満期釈放等", 43.2), ("F", "総数", 34.0), ("I", "仮釈放", 27.7)):
    claim_pct(f"5-3-9図② 図中の表示値 令和2年 {nm} {v}", 2020, v, pct(t5, 2020, L))

m = {y: sx[y]["２年以内再入者人員_男性_比率"] for y in sx}
f_ = {y: sx[y]["２年以内再入者人員_女性_比率"] for y in sx}
claim_pct("5-3 本文: 男性の2年以内再入率 令和5年 14.1%", 2023, 14.1, m[2023])
claim_pt("5-3 本文: 男性 前年比0.9pt上昇", 2023, 0.9, m[2023], m[2022])
claim_pt("5-3 本文: 男性 平成16年比7.6pt低下", 2023, -7.6, m[2023], m[2004])
claim("5-3 本文: 男性は女性より一貫して高い（平成16年〜令和5年）", 2023, 1, all(m[y] > f_[y] for y in range(2004, 2024)))
claim_pct("5-3 本文: 女性 平成21年 14.4%", 2009, 14.4, f_[2009])
claim("5-3 本文: 女性は平成21年が平成16年以降で最も高い", 2009, 2009, max(range(2004, 2024), key=f_.get))
claim_pct("5-3 本文: 女性 令和5年 10.8%", 2023, 10.8, f_[2023])
claim_pt("5-3 本文: 女性 前年比0.1pt低下", 2023, -0.1, f_[2023], f_[2022])
claim_pct("5-3 本文: 女性 平成28年 14.2%", 2016, 14.2, f_[2016])
claim("5-3 本文: 平成28年は平成21年に次いで高い（平成16年以降）", 2016, 2016,
      sorted(range(2004, 2024), key=f_.get, reverse=True)[1])
claim_pt("5-3 本文: 女性 平成28年比3.4pt低下", 2023, -3.4, f_[2023], f_[2016])

cr = next(v for k, v in T10.items() if "罪名" in k)
for crime, r5, d1, d16 in (("窃盗", 19.7, 0.3, -9.4), ("傷害・暴行", 15.6, 4.1, -2.4),
                           ("覚醒剤取締法", 12.8, 2.2, -8.1), ("詐欺", 8.4, 1.4, -19.5)):
    col = f"{crime}_２年以内再入者人員_比率"
    v = {y: cr[y][col] for y in cr}
    claim_pct(f"5-3 本文: {crime}の2年以内再入率 令和5年 {r5}%", 2023, r5, v[2023])
    claim_pt(f"5-3 本文: {crime} 前年比{d1}pt上昇", 2023, d1, v[2023], v[2022])
    claim_pt(f"5-3 本文: {crime} 平成16年比{-d16}pt低下", 2023, d16, v[2023], v[2004])
claim("5-3 本文: 窃盗は他の罪名より一貫して最も高い（平成16年〜令和5年）", 2023, 1,
      all(cr[y]["窃盗_２年以内再入者人員_比率"] == max(cr[y][c] for c in cr[y] if c.endswith("_比率")) for y in range(2004, 2024)))

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("kind\tcheck\twhere\texpected\tobserved\tdiff\tstatus\tnote\n")
    for r in results:
        fh.write("\t".join(r) + "\n")
for k in "ABCDEF":
    print(k, dict(Counter(r[6] for r in results if r[0] == k)))
bad = [r for r in results if r[6] != "一致"]
print("not-matching:", len(bad))
for r in bad[:60]:
    print("  ", r[0], r[2], r[1], "| exp", r[3], "obs", r[4], "diff", r[5], r[7])

# 照合の要約（lib/tally.py）：一致・食い違いを照合の数に、欠測（値が読めない・対応なし）を読み取りの失敗に数える。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('hanzai_hakusho', 'c002', note='犯罪白書 令和7年版 第5編：再犯・再入の図表の内部整合と突き合わせ', script=__file__)
for _r in results:
    _st = _r[6]
    if _st == '一致': _t.ok()
    elif _st == '食い違い': _t.ng(explained=bool(False))
    else: _t.fail()
print('tally', _t.save())
