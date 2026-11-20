#!/usr/bin/env python3
"""検算 c004（探索）：同じ年の数字が、白書の版によって変わっていないか（遡及改訂・転記の揺れ）

対象（表題で版ごとに特定。sources/hanzai_hakusho/find_by_title.py で取得）
  keihouhan_ninchi : 資料「刑法犯 認知件数・発生率・検挙件数・検挙率・検挙人員」（平成29年版〜令和7年版）
  saihansha        : 図「刑法犯（一般刑法犯）検挙人員中の再犯者人員・再犯者率」（平成26年版〜令和7年版）
方法
  年次は、西暦の列があればそれを使い、なければ和暦の数字の並び（数字が戻ったら次の元号）から求める。
  比べる列は、令和7年版の値を「錨」にして各版で探す（錨: ある年の値が一致する列）。列の見出しの書き方が版ごとに違っても追える。
  版 A と版 B に同じ年があり、値が違えば「改訂」として記録する（誤りとは限らない。遡及修正・定義変更の可能性）。
出力: results/hanzai_hakusho/c004_revisions.tsv
"""
import re, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "lib"))
import xlsx  # noqa: E402

RAW = ROOT / "data/raw/hanzai_hakusho"
OUT = ROOT / "results/hanzai_hakusho/c004_revisions.tsv"
ERA = {"昭和": 1925, "平成": 1988, "令和": 2018}
ORDER = ["昭和", "平成", "令和"]
ED_LABEL = {72: "令和7年版", 71: "令和6年版", 70: "令和5年版", 69: "令和4年版", 68: "令和3年版", 67: "令和2年版",
            66: "令和元年版", 65: "平成30年版", 64: "平成29年版", 63: "平成28年版", 62: "平成27年版", 61: "平成26年版"}


def era_num(lbl):
    s = str(lbl).replace("年", "").replace("　", "").strip()
    for e in ERA:
        s = s.replace(e, "")
    s = s.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    if s == "元":
        return 1
    try:
        v = float(s)
        return int(v) if v == int(v) else None
    except ValueError:
        return None


def rows_by_year(path):
    """{年: [その行の数値セル (列, 値)]}。シートを順にたどり、元号の切り替えを推定する。"""
    out = {}
    for name, cells in xlsx.read_sheets(path).items():
        R = max(r for r, _ in cells)
        texts = " ".join(str(v) for (r, c), v in cells.items() if r <= 6 and isinstance(v, str))
        era = next((e for e in ORDER if e in name), None)
        m = re.search(r"（(昭和|平成|令和)", texts) or re.search(r"(昭和|平成|令和)", texts)
        if not era and m:
            era = m.group(1)
        prev = None
        for r in range(1, R + 1):
            lab, ycol = None, None
            for c in (2, 3):  # 年次の列
                v = cells.get((r, c))
                if v is None:
                    continue
                sv = str(v)
                if re.fullmatch(r"\d{4}年", sv.strip()):
                    ycol = int(sv.strip()[:4])
                for e in ORDER:
                    if e in sv and ("年" in sv or "元" in sv) and c == 2:
                        era = e
                    if re.match(r"^[①-⑨]\s*" + e, sv.strip()):
                        era, prev = e, None
                if lab is None and c == 2 and era_num(v) is not None:
                    lab = era_num(v)
            if ycol is None and lab is None:
                continue
            if ycol is None:
                if prev is not None and lab < prev and era != "令和":
                    era = ORDER[ORDER.index(era) + 1]
                if era is None:
                    continue
                ycol = ERA[era] + lab
                prev = lab
            nums = [(c, v) for (rr, c), v in cells.items() if rr == r and isinstance(v, float) and c >= 3]
            if nums:
                out.setdefault(ycol, {}).update({c: v for c, v in nums})  # 同じファイルのシートは列の並びが同じ前提
    return out


def column_by_anchor(rows, year, value):
    hit = [k for k, v in rows.get(year, {}).items() if v == value]
    return hit[0] if hit else None


SERIES = {
    # 系列名: (保存名, [(錨の年, 令和7年版の値の取り方)])
    "刑法犯 認知件数": ("keihouhan_ninchi", 1946, 1384222.0),
    "認知件数 総数（参考値）": ("keihouhan_ninchi", 1946, 1387080.0),
    "刑法犯 検挙件数": ("keihouhan_ninchi", 1946, 800431.0),
    "刑法犯 検挙人員": ("keihouhan_ninchi", 1946, 442579.0),
    "刑法犯 検挙人員 男性": ("keihouhan_ninchi", 1946, 408760.0),
    "刑法犯 発生率（人口10万人当たり）": ("keihouhan_ninchi", 1946, 1827.3557755775578),
    "再犯者 検挙人員（総数）": ("saihansha", 1989, 312992.0),
    "再犯者 人員": ("saihansha", 1989, 99852.0),
}

rows_ed = {}
for ed in range(60, 73):
    for save in {s[0] for s in SERIES.values()}:
        p = RAW / str(ed) / "bytitle" / f"{save}.xlsx"
        if p.exists():
            rows_ed[(ed, save)] = rows_by_year(p)

res, summary = [], []
_C = {'cmp': 0, 'fail': 0}  # 照合の要約用
for sname, (save, ay, av) in SERIES.items():
    vals = defaultdict(dict)  # 年 -> 版 -> 値
    for (ed, sv), rows in rows_ed.items():
        if sv != save:
            continue
        col = column_by_anchor(rows, ay, av)
        if col is None:
            summary.append([sname, ED_LABEL.get(ed, ed), "錨の値が見つからない（定義や範囲が違う可能性）"]); _C['fail'] += 1
            continue
        for y, d in rows.items():
            if col in d:
                vals[y][ed] = d[col]
    nrev = 0
    _C['cmp'] += sum(1 for y in vals if len(vals[y]) > 1)
    for y in sorted(vals):
        eds = sorted(vals[y])
        distinct = sorted(set(vals[y].values()))
        if len(distinct) > 1:
            nrev += 1
            res.append([sname, str(y), " / ".join(f"{ED_LABEL.get(e, e)}={vals[y][e]:.10g}" for e in eds)])
            first = {}
            for e in eds:  # 値が変わった版（最初にその値が出た版）
                first.setdefault(vals[y][e], e)
            res[-1].append("値が変わった版: " + ", ".join(ED_LABEL.get(e, str(e)) for v, e in sorted(first.items(), key=lambda x: x[1])[1:]))
    summary.append([sname, f"{len(vals)}年分", f"版によって値が違う年: {nrev}"])

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("series\tyear\tvalues_by_edition\tchanged_in\n")
    for r in res:
        fh.write("\t".join(r) + "\n")
for s in summary:
    print(" | ".join(s))
print("--- 改訂のあった年（先頭 40 件）")
from collections import Counter
print(Counter((r[0], r[3]) for r in res))

# 照合の要約（lib/tally.py）：単位は（系列・年）のうち2つ以上の版に値があるもの。版で値が違えば食い違い（改訂。誤りとは限らない）。
# 錨の値が見つからない（系列・版）は読み取りの失敗。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('hanzai_hakusho', 'c004', note='犯罪白書 平成26〜令和7年版：刑法犯の資料と再犯者の図の、同じ年の値の版どうしの比較', script=__file__)
from lib.hanzai_explained import explained_c004 as _ex  # R1（lib/hanzai_explained.py）
_t.set(compared=_C['cmp'], mismatched=len(res), read_failures=_C['fail'], explained=sum(1 for r in res if _ex(r[0], r[1]))); print('tally', _t.save())
