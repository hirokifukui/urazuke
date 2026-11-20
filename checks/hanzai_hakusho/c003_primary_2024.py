#!/usr/bin/env python3
"""検算 c003（探索）：犯罪白書 令和7年版 ↔ 一次資料（矯正統計年報・検察統計年報、2024年）

一次資料（e-Stat、法務省）
  矯正 24-00-23  新受刑者の罪名別 入所度数及び累犯・非累犯   data/raw/kyosei_toukei/2024/24-00-23.xlsx
  検察 24-00-49  罪名別 起訴した事件の被疑者の初犯者、前科者別及び前科の種類別人員  data/raw/kensatsu_toukei/2024/24-00-49.xlsx
白書の表
  5-3-1図・5-3-2図・資料5-1・資料5-2（矯正と対応）、5-2-1表（検察と対応）

種類
  K0  矯正の表の内部整合（男+女、入所度数の和、累犯・非累犯・不該当の和、罪名の和）
  K   白書 ↔ 矯正（罪名の対応は MAP_K。白書の「その他」は残差として計算）
  S0  検察の表の内部整合（総数 = 初犯 + 前科 + 不詳、刑名の和、罪名の和）
  S   白書 5-2-1表 ↔ 検察（白書の注2: 法人・前科不詳を除く → 起訴人員 = 初犯 + 前科）
"""
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "lib"))
import xlsx  # noqa: E402
from tables import sheet_rows, year  # noqa: E402

OUT = ROOT / "results" / "hanzai_hakusho" / "c003_primary_2024.tsv"
WP = ROOT / "data" / "raw" / "hanzai_hakusho" / "72"
results = []


def rec(kind, check, expected, observed, note=""):
    if expected is None or observed is None:
        st, d = "欠測", ""
    else:
        st = "一致" if abs(expected - observed) <= 1e-9 * max(1, abs(expected)) else "食い違い"
        d = f"{observed - expected:.6g}"
    f = lambda x: "" if x is None else f"{x:.10g}"
    results.append([kind, check, f(expected), f(observed), d, st, note])


def clean(s):
    return str(s or "").replace("　", "").replace(" ", "").replace("\n", "").strip()


# ======================= 矯正 24-00-23 =======================
kc = next(iter(xlsx.read_sheets(ROOT / "data/raw/kyosei_toukei/2024/24-00-23.xlsx").values()))
DEG = ["総数", "１度", "２度", "３度", "４度", "５度", "６～９度", "10度以上", "総数2", "累犯", "非累犯", "不該当"]


def vals(r):
    return [kc.get((r, k)) or 0.0 for k in range(11, 23)]


# 年ごとの総数ブロック（令和2〜6年）
YB = {}
cur = None
for r in range(8, 30):
    v4 = str(kc.get((r, 4)) or "").strip()
    if v4.replace(".0", "").isdigit():  # 令和の年（文字列のこともある）
        cur = 2018 + int(float(v4))
    sx = clean(kc.get((r, 7)))
    if cur and sx in ("総数", "男", "女"):
        YB.setdefault(cur, {})[sx] = dict(zip(DEG, vals(r)))
# 2024年の罪名別（男・女）。「（男」は女性の行がない（0人）罪名
K = defaultdict(lambda: {"男": dict.fromkeys(DEG, 0.0), "女": dict.fromkeys(DEG, 0.0)})
name = None
for r in range(28, 120):
    n = clean(kc.get((r, 2)))
    if n:
        name = n
    sx = clean(kc.get((r, 9))).replace("（", "")
    if name and sx in ("男", "女"):
        K[name][sx] = dict(zip(DEG, vals(r)))
    elif name and n and not sx:
        pass  # 男女とも 0 の罪名
crimes_k = [n for n in K if not n.startswith("（うち")]
i_kei, i_toku = crimes_k.index("刑法犯"), crimes_k.index("特別法犯")
kei_items, toku_items = crimes_k[i_kei + 1:i_toku], crimes_k[i_toku + 1:]

for y, b in YB.items():
    for c in DEG:
        rec("K0", f"矯正 {y}年 男+女 = 総数（{c}）", b["総数"][c], b["男"][c] + b["女"][c])
    for sx in ("総数", "男", "女"):
        rec("K0", f"矯正 {y}年 入所度数の和 = 総数（{sx}）", b[sx]["総数"], sum(b[sx][c] for c in DEG[1:8]))
        rec("K0", f"矯正 {y}年 累犯+非累犯+不該当 = 総数（{sx}）", b[sx]["総数"], b[sx]["累犯"] + b[sx]["非累犯"] + b[sx]["不該当"])
for sx in ("男", "女"):
    for c in DEG[:8]:
        rec("K0", f"矯正 2024年 刑法犯 = 罪名の和（{sx}・{c}）", K["刑法犯"][sx][c], sum(K[n][sx][c] for n in kei_items))
        rec("K0", f"矯正 2024年 特別法犯 = 罪名の和（{sx}・{c}）", K["特別法犯"][sx][c], sum(K[n][sx][c] for n in toku_items))
        rec("K0", f"矯正 2024年 総数 = 刑法犯 + 特別法犯（{sx}・{c}）", YB[2024][sx][c], K["刑法犯"][sx][c] + K["特別法犯"][sx][c])

# 白書の罪名 → 矯正の罪名（白書の「刑法犯」は過失運転致死傷等を含まない）
MAP_K = {
    ("刑法犯", "公務執行妨害"): ["公務執行妨害"],
    ("刑法犯", "放火"): ["放火"],
    ("刑法犯", "住居侵入"): ["住居侵入"],
    ("刑法犯", "不同意わいせつ"): ["不同意わいせつ・同致死傷"],
    ("刑法犯", "不同意性交等"): ["不同意性交等・同致死傷"],
    ("刑法犯", "殺人"): ["殺人"],
    ("刑法犯", "傷害"): ["傷害", "傷害致死"],
    ("刑法犯", "暴行"): ["暴行"],
    ("刑法犯", "危険運転致死傷"): ["危険運転致死傷"],
    ("刑法犯", "脅迫"): ["脅迫"],
    ("刑法犯", "窃盗"): ["窃盗"],
    ("刑法犯", "強盗"): ["強盗", "強盗致死傷", "強盗・不同意性交等及び同致死"],
    ("刑法犯", "詐欺"): ["詐欺"],
    ("刑法犯", "恐喝"): ["恐喝"],
    ("刑法犯", "横領・背任"): ["横領・背任"],
    ("刑法犯", "暴力行為等処罰法"): ["暴力行為等処罰に関する法律"],
    ("過失運転致死傷等", "総数"): ["過失運転致死傷"],
    ("特別法犯", "総数"): ["特別法犯"],
    ("特別法犯", "銃刀法"): ["銃砲刀剣類所持等取締法"],
    ("特別法犯", "売春防止法"): ["売春防止法"],
    ("特別法犯", "麻薬取締法"): ["麻薬及び向精神薬取締法(大麻関連)", "麻薬及び向精神薬取締法(大麻関連除く)"],
    ("特別法犯", "覚醒剤取締法"): ["覚醒剤取締法"],
    ("特別法犯", "道路交通法"): ["道路交通法"],
}


def ksum(names, sx, col):
    s = ["男", "女"] if sx == "総数" else [sx]
    return sum(K[n][x][col] for n in names for x in s)


def kei_total(sx, col):  # 白書の刑法犯 = 矯正の刑法犯 − 過失運転致死傷
    return ksum(["刑法犯"], sx, col) - ksum(MAP_K[("過失運転致死傷等", "総数")], sx, col)


# 資料5-2（入所度数別人員、罪名別、2024）
for nm, cells in xlsx.read_sheets(WP / "shiryo/shiryo5-2.xlsx").items():
    if "６" not in nm:
        continue
    t, order = sheet_rows(cells, key_cols=(2, 3))
    for key in order:
        d = t[key]
        for wcol, kcols in (("総数", ["総数"]), ("１度", ["１度"]), ("２度", ["２度"]), ("３度", ["３度"]),
                            ("４度", ["４度"]), ("５度以上", ["５度", "６～９度", "10度以上"])):
            if key == ("総数", "総数"):
                obs = sum(YB[2024]["総数"][c] for c in kcols)
            elif key == ("刑法犯", "総数"):
                obs = sum(kei_total("総数", c) for c in kcols)
            elif key in MAP_K:
                obs = sum(ksum(MAP_K[key], "総数", c) for c in kcols)
            elif key == ("刑法犯", "その他"):
                listed = [n for k, v in MAP_K.items() if k[0] == "刑法犯" for n in v]
                obs = sum(kei_total("総数", c) - ksum(listed, "総数", c) for c in kcols)
            elif key == ("特別法犯", "その他"):
                listed = [n for k, v in MAP_K.items() if k[0] == "特別法犯" and k[1] != "総数" for n in v]
                obs = sum(ksum(["特別法犯"], "総数", c) - ksum(listed, "総数", c) for c in kcols)
            else:
                obs = None
            rec("K", f"資料5-2 {key[0]}・{key[1]}・{wcol} = 矯正", d[wcol], obs)

# 資料5-1（再入者 = 総数 − １度、罪名別・男女別、2024）
for nm, cells in xlsx.read_sheets(WP / "shiryo/shiryo5-1.xlsx").items():
    if "６" not in nm:
        continue
    t, order = sheet_rows(cells, key_cols=(2, 3))
    for key in order:
        for sx in ("総数", "男性", "女性"):
            s = sx.replace("性", "")
            sai = lambda f: f(s, "総数") - f(s, "１度")
            if key == ("総数", "総数"):
                obs = sum(YB[2024][x]["総数"] - YB[2024][x]["１度"] for x in (["男", "女"] if s == "総数" else [s]))
            elif key == ("刑法犯", "総数"):
                obs = sai(kei_total)
            elif key in MAP_K:
                obs = ksum(MAP_K[key], s, "総数") - ksum(MAP_K[key], s, "１度")
            elif key == ("刑法犯", "その他"):
                listed = [n for k, v in MAP_K.items() if k[0] == "刑法犯" for n in v]
                obs = sai(kei_total) - (ksum(listed, s, "総数") - ksum(listed, s, "１度"))
            elif key == ("特別法犯", "その他"):
                listed = [n for k, v in MAP_K.items() if k[0] == "特別法犯" and k[1] != "総数" for n in v]
                obs = (ksum(["特別法犯"], s, "総数") - ksum(["特別法犯"], s, "１度")) - (ksum(listed, s, "総数") - ksum(listed, s, "１度"))
            else:
                obs = None
            rec("K", f"資料5-1 再入者 {key[0]}・{key[1]}・{sx} = 矯正（総数−１度）", t[key][sx], obs)

# 5-3-1図・5-3-2図（2020〜2024年の総数・女性）
for nm, cells in xlsx.read_sheets(WP / "zuhyo/5-3-1.xlsx").items():
    sx = "女" if "②" in nm else "総数"
    t, _ = sheet_rows(cells, key_cols=(3,))
    for k, d in t.items():
        y = year(k)
        if y in YB:
            rec("K", f"5-3-1図 {y}年 {sx} 入所受刑者 = 矯正 総数", d["総数"], YB[y][sx]["総数"])
            rec("K", f"5-3-1図 {y}年 {sx} 初入者 = 矯正 １度", d["初入者"], YB[y][sx]["１度"])
            rec("K", f"5-3-1図 {y}年 {sx} 再入者 = 矯正 総数−１度", d["再入者"], YB[y][sx]["総数"] - YB[y][sx]["１度"])
for nm, cells in xlsx.read_sheets(WP / "zuhyo/5-3-2.xlsx").items():
    sx = "総数" if "①" in nm else "男" if "②" in nm else "女"
    t, _ = sheet_rows(cells, key_cols=(3,))
    for k, d in t.items():
        y = year(k)
        if y in YB:
            for wcol, kcols in (("１度", ["１度"]), ("２度", ["２度"]), ("３度", ["３度"]), ("４度", ["４度"]),
                                ("５度以上", ["５度", "６～９度", "10度以上"])):
                rec("K", f"5-3-2図 {y}年 {sx} {wcol} = 矯正", d[wcol], sum(YB[y][sx][c] for c in kcols))

# ======================= 検察 24-00-49 =======================
sc = xlsx.read_sheets(ROOT / "data/raw/kensatsu_toukei/2024/24-00-49.xlsx")["24-00-49"]
COLS = {"総数": 5, "初犯": 6, "初犯男": 7, "初犯女": 8, "前科": 9, "懲計": 10, "懲実男": 11, "懲実女": 12, "懲一男": 13,
        "懲一女": 14, "懲全男": 15, "懲全女": 16, "禁計": 17, "禁実男": 18, "禁実女": 19, "禁一男": 20, "禁一女": 21,
        "禁全男": 22, "禁全女": 23, "罰計": 24, "罰実男": 25, "罰実女": 26, "罰全男": 27, "罰全女": 28, "不詳": 29}
S, parent, level = {}, {}, {}
top = None
for r in range(9, 110):
    a, b = clean(sc.get((r, 2))), clean(sc.get((r, 3)))
    nm = a or b
    if not nm or nm.startswith("注"):
        continue
    if b and nm in S:  # 大分類と同名の細分類（例: 傷害 の中の 傷害）は「_細」を付けて区別する
        nm = nm + "_細"
    S[nm] = {k: (sc.get((r, c)) or 0.0) for k, c in COLS.items()}
    if a:
        top = a
        level[nm] = 1
    else:
        parent[nm] = top
        level[nm] = 2
names = list(S)
for nm, d in S.items():
    rec("S0", f"検察 {nm}: 総数 = 初犯 + 前科 + 不詳", d["総数"], d["初犯"] + d["前科"] + d["不詳"])
    rec("S0", f"検察 {nm}: 初犯 = 男 + 女", d["初犯"], d["初犯男"] + d["初犯女"])
    for g in ("懲", "禁"):
        rec("S0", f"検察 {nm}: {g}計 = 実刑+一部+全部", d[g + "計"], sum(d[g + x] for x in ("実男", "実女", "一男", "一女", "全男", "全女")))
    rec("S0", f"検察 {nm}: 罰計 = 実刑+全部", d["罰計"], sum(d["罰" + x] for x in ("実男", "実女", "全男", "全女")))
    rec("S0", f"検察 {nm}: 前科 = 懲計+禁計+罰計", d["前科"], d["懲計"] + d["禁計"] + d["罰計"])
i_k, i_t = names.index("刑法犯"), names.index("特別法犯")
kk = [n for n in names[i_k + 1:i_t] if level[n] == 1]
tt = [n for n in names[i_t + 1:] if level[n] == 1]
for col in ("総数", "初犯", "前科", "懲計", "罰計"):
    rec("S0", f"検察 刑法犯 = 大分類の和（{col}）", S["刑法犯"][col], sum(S[n][col] for n in kk))
    rec("S0", f"検察 特別法犯 = 罪名の和（{col}）", S["特別法犯"][col], sum(S[n][col] for n in tt))
    rec("S0", f"検察 総数 = 刑法犯 + 特別法犯（{col}）", S["総数"][col], S["刑法犯"][col] + S["特別法犯"][col])
    for p in set(parent.values()):
        kids = [n for n in parent if parent[n] == p]
        rec("S0", f"検察 {p} = 細分類の和（{'・'.join(kids)}）（{col}）", S[p][col], sum(S[n][col] for n in kids))


def sv(names_, key):
    d = lambda n: S[n]
    f = {"起訴人員": lambda n: d(n)["初犯"] + d(n)["前科"],
         "有前科者": lambda n: d(n)["前科"],
         "実刑": lambda n: d(n)["懲実男"] + d(n)["懲実女"] + d(n)["禁実男"] + d(n)["禁実女"],
         "一部執行猶予": lambda n: d(n)["懲一男"] + d(n)["懲一女"] + d(n)["禁一男"] + d(n)["禁一女"],
         "全部執行猶予": lambda n: d(n)["懲全男"] + d(n)["懲全女"] + d(n)["禁全男"] + d(n)["禁全女"],
         "罰金": lambda n: d(n)["罰計"]}[key]
    return sum(f(n) for n in names_)


MAP_S = {
    ("総数",): ["総数"], ("刑法犯", "総数"): ["刑法犯"], ("放火",): ["放火"], ("住居侵入",): ["住居侵入"],
    ("不同意わいせつ",): ["不同意わいせつ"], ("不同意性交等",): ["不同意性交等"], ("贈収賄",): ["収賄", "贈賄"],
    ("殺人",): ["殺人", "嬰児殺", "自殺関与"], ("傷害",): ["傷害_細"], ("暴行",): ["暴行"], ("脅迫",): ["脅迫"],
    ("窃盗",): ["窃盗"], ("強盗",): ["強盗", "強盗致死傷", "強盗・不同意性交等"], ("詐欺",): ["詐欺"], ("恐喝",): ["恐喝"],
    ("横領",): ["横領"], ("暴力行為等処罰法",): ["暴力行為等処罰に関する法律"],
    ("性的姿態撮影等処罰法",): [n for n in names if n.startswith("性的な姿態を撮影する行為等の処罰")],
    ("特別法犯", "総数"): ["特別法犯"], ("公職選挙法",): ["公職選挙法"], ("軽犯罪法",): ["軽犯罪法"],
    ("風営適正化法",): [n for n in names if n.startswith("風俗営業等の規制")], ("銃刀法",): ["銃砲刀剣類所持等取締法"],
    ("売春防止法",): ["売春防止法"], ("児童福祉法",): ["児童福祉法"],
    ("医薬品医療機器等法",): [n for n in names if n.startswith("医薬品、医療機器等")],
    ("大麻取締法",): ["大麻取締法", "大麻草の栽培の規制に関する法律"], ("麻薬取締法",): ["麻薬及び向精神薬取締法"],
    ("覚醒剤取締法",): ["覚醒剤取締法"], ("毒劇法",): ["毒物及び劇物取締法"],
}
# 「傷害」は大分類（傷害・暴行・凶器準備集合）と細分類が同名。白書の「傷害」は細分類の傷害（読み込み時に「傷害_細」）

for nm, cells in xlsx.read_sheets(WP / "zuhyo/5-2-1.xlsx").items():
    if "６" not in nm:
        continue
    t, order = sheet_rows(cells, key_cols=(2, 3), hdr_rows=(6, 7))
    hdr = list(next(iter(t.values())).keys())
    col = {"起訴人員": hdr[0], "有前科者": hdr[1], "実刑": hdr[2], "一部執行猶予": hdr[3], "全部執行猶予": hdr[4],
           "罰金": hdr[5], "率": hdr[6]}
    listed_k = [n for k, v in MAP_S.items() if len(k) == 1 and k != ("総数",) for n in v]
    for key in order:
        kub, crime = key
        if crime == "総数":
            mk = ("総数",) if kub.startswith("刑法犯・") else ("刑法犯", "総数") if kub == "刑法犯" else ("特別法犯", "総数")
        else:
            mk = (crime,)
        d = t[key]
        for q in ("起訴人員", "有前科者", "実刑", "一部執行猶予", "全部執行猶予", "罰金"):
            if mk in MAP_S:
                obs = sv(MAP_S[mk], q)
            elif crime == "その他":
                grp = "刑法犯" if kub == "刑法犯" else "特別法犯"
                items = [n for (k2, v) in MAP_S.items() if len(k2) == 1 for n in v]
                rows_in = [k2 for k2 in order if k2[0] == kub and k2[1] not in ("総数", "その他")]
                obs = sv([grp], q) - sum(sv(MAP_S[(k2[1],)], q) for k2 in rows_in)
            else:
                obs = None
            rec("S", f"5-2-1表 {kub[:6]}・{crime}・{q} = 検察", d[col[q]], obs)
        rec("S", f"5-2-1表 {kub[:6]}・{crime}・有前科者率 = 有前科者/起訴人員×100", d[col["有前科者"]] / d[col["起訴人員"]] * 100, d[col["率"]])
    # 白書の起訴人員と検察の総数（法人・前科不詳を含む）の差 = 検察の「不詳」列
    for mk, lab in ((("総数",), "総数"), (("刑法犯", "総数"), "刑法犯"), (("特別法犯", "総数"), "特別法犯")):
        n = MAP_S[mk][0]
        rec("S", f"検察 {lab} 総数 − 白書の起訴人員 = 検察の前科不詳（白書注2で除外）", S[n]["不詳"],
            S[n]["総数"] - sv(MAP_S[mk], "起訴人員"))

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("kind\tcheck\texpected\tobserved\tdiff\tstatus\tnote\n")
    for r in results:
        fh.write("\t".join(r) + "\n")
for k in ("K0", "K", "S0", "S"):
    print(k, dict(Counter(r[5] for r in results if r[0] == k)))
bad = [r for r in results if r[5] != "一致"]
print("not-matching:", len(bad))
for r in bad[:60]:
    print("  ", r[0], r[1], "| exp", r[2], "obs", r[3], "diff", r[4])

# 照合の要約（lib/tally.py）：一致・食い違いを照合の数に、欠測（値が読めない・対応なし）を読み取りの失敗に数える。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('hanzai_hakusho', 'c003', note='犯罪白書 令和7年版と矯正統計年報・検察統計年報（2024年）', script=__file__)
for _r in results:
    _st = _r[5]
    if _st == '一致': _t.ok()
    elif _st == '食い違い': _t.ng(explained=bool(False))
    else: _t.fail()
print('tally', _t.save())
