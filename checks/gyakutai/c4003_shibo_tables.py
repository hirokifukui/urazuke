"""死亡事例検証報告（第21・22次）の「個別調査票」章の縦長の表：
各行を「人数(疑義) 構成割合 [有効割合]」の組に分け、列ごとに
(1) 内訳の和＝小計／計（値と括弧）、(2) 構成割合＝人数/計、有効割合＝人数/小計（注記のある行は除く）を確かめる。
複数回答の表（題・注に「複数回答」）は和を確かめない。
使い方: python checks/gyakutai/c4003_shibo_tables.py [版 ...]
"""
import re, sys, json
from pathlib import Path

BASE = Path("data/raw/shibo_jirei")
TOK = re.compile(r"(-|－|[\d,]+)\s*(?:[（(]\s*(\d+)\s*[)）])?|([\d.]+)\s*[%％]")
CELL = re.compile(r"(?:(?<![0-9.])([0-9,]+)\s*[（(]\s*(\d+)\s*[)）])|(?:(?<![0-9.,])([0-9.]+)\s*[%％])|(?:(?<=\s)(-|－)(?=\s|$))|(?:(?<![0-9.,(（])([0-9,]+)(?![0-9.,%％(（]))")


def parse_row(s):
    """行 → (ラベル, [('n', v, p) | ('pct', x) | ('dash',)])"""
    pre = re.match(r"^\s*[0-9]+\s*(?:か月|歳|日|か所|回|件|人|年|時間|週|～|〜|-|－)\S*", s)
    off = pre.end() if pre else 0
    m = re.search(r"\s(?:-|－|[0-9])", s[off:])
    if not m:
        return None
    m0 = m.start() + off
    label = s[:m0].strip()
    if "次" in label or "区分" in label or "人数" in label or "割合" in label:
        return None
    if not label or re.fullmatch(r"[\d\s.,%％()（）-]+", label):
        return None
    toks = []
    for c in CELL.finditer(s, m0):
        if c.group(1):
            toks.append(("n", int(c.group(1).replace(",", "")), int(c.group(2))))
        elif c.group(3):
            toks.append(("pct", float(c.group(3))))
        elif c.group(4):
            toks.append(("dash",))
        elif c.group(5):
            toks.append(("n", int(c.group(5).replace(",", "")), None))
    return label, toks


def groups(toks):
    """[人数, 割合...] の組に分ける"""
    g = []
    for t in toks:
        if t[0] in ("n", "dash"):
            g.append([t])
        elif g:
            g[-1].append(t)
    return g


def tables(n):
    fn = "04_kobetsu.txt" if n >= 20 else "05_kobetsu.txt"
    L = [s.replace("\f", "") for s in (BASE / str(n) / fn).read_text().split("\n")]
    T, cur = [], None
    for i, s in enumerate(L):
        if re.match(r"^\s{0,3}表\s*\d+", s):
            cur = {"title": s.strip(), "line": i + 1, "rows": [], "notes": ""}
            T.append(cur)
            continue
        if cur is None:
            continue
        if s.strip().startswith("※") or s.strip().startswith("注"):
            cur["notes"] += s
            continue
        r = parse_row(s)
        if r and r[1]:
            cur["rows"].append((i + 1, r[0], groups(r[1])))
    return T


def check(n):
    out, nf = [], 0
    for t in tables(n):
        rows = t["rows"]
        tot = [r for r in rows if re.sub(r"\s", "", r[1]) in ("計", "合計")]
        if not tot:
            continue
        tot = tot[-1]
        body = [r for r in rows if r[0] < tot[0]]
        sub = [r for r in body if re.sub(r"\s", "", r[1]) == "小計"]
        multi = "複数回答" in t["title"] or "複数回答" in t["notes"]
        ng = len(tot[2])
        for k in range(ng):
            T = tot[2][k][0]
            if T[0] != "n":
                continue

            def col(rs):
                v = p = 0
                ok = True
                for r in rs:
                    if k >= len(r[2]):
                        ok = False
                        break
                    c = r[2][k][0]
                    if c[0] == "n":
                        v += c[1]
                        p += c[2] or 0
                return ok, v, p
            if not multi:
                if sub:
                    s0 = sub[0]
                    before = [r for r in body if r[0] < s0[0]]
                    after = [r for r in body if r[0] > s0[0]]
                    ok1, v1, p1 = col(before)
                    S = s0[2][k][0] if k < len(s0[2]) else None
                    ok2, v2, p2 = col([s0] + after)
                    checks = [("内訳の和＝小計", ok1, v1, p1, S), ("小計＋その他＝計", ok2, v2, p2, T)]
                else:
                    ok, v, p = col(body)
                    checks = [("内訳の和＝計", ok, v, p, T)]
                for name, ok, v, p, ref in checks:
                    if not ok or ref is None or ref[0] != "n":
                        continue
                    nf += 1
                    if v != ref[1] or (ref[2] is not None and p != ref[2]):
                        out.append(dict(版=n, 表=t["title"][:40], 行=t["line"], 列=k, 検査=name, 掲載=[ref[1], ref[2]], 和=[v, p]))
            # 構成割合
            den = T[1]
            for r in body:
                if k >= len(r[2]) or "※" in r[1]:
                    continue
                g = r[2][k]
                if g[0][0] != "n" or len(g) < 2 or den == 0 or multi:
                    continue
                nf += 1
                calc = round(g[0][1] / den * 100, 1)
                if abs(calc - g[1][1]) > 0.11:
                    out.append(dict(版=n, 表=t["title"][:40], 行=r[0], 列=k, 検査="構成割合", 区分=r[1], 人数=g[0][1], 計=den, 掲載=g[1][1], 再計算=calc))
    return nf, out


if __name__ == "__main__":
    vs = [int(x) for x in sys.argv[1:]] or [21, 22]
    tot_f, allm = 0, []
    for n in vs:
        nf, m = check(n)
        tot_f += nf
        allm += m
    print(f"式 {tot_f}　不一致 {len(allm)}")
    # 照合の要約（lib/tally.py）：単位は式。
    import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
    # 作業ノートで原文を確かめ、資料の不一致と残したのは第22次の表14・16・22・44・45・59（SD-A3）。それ以外の不一致（第21次の全部を含む）は
    # 読み取りの誤り（見出しの行を値として読む、ラベルが2行に分かれる、入れ子の二重計上、横に並んだ表）＝読み取りの失敗。
    import re as _re
    _REAL = {14, 16, 22, 44, 45, 59}
    _nf = sum(1 for x in allm if not (x['版'] == 22 and (_m := _re.match(r'表\s*(\d+)', x['表'])) and int(_m.group(1)) in _REAL))
    _t = Tally('gyakutai', 'c4003', note='子ども虐待による死亡事例等の検証結果：各表の和と構成割合', script=__file__); _t.set(compared=tot_f - _nf, mismatched=len(allm) - _nf, read_failures=_nf); print('tally', _t.save())
    for x in allm:
        print(json.dumps(x, ensure_ascii=False))
