"""死亡事例検証報告（第20〜22次）の 表1・表2：
各回の値の合計と「総数」、括弧内（疑義事例）の合計と「総数」の括弧、
表1 = 表2（こども）+ 表2（自殺を伴う）、各報告の間での過去の回の値の一致を調べる。
入力: data/raw/shibo_jirei/<n>/04_kobetsu.txt（pdftotext -layout）
"""
import re, sys, json
from pathlib import Path

BASE = Path("data/raw/shibo_jirei")
NUM = re.compile(r"(-|[\d,]+)\s*[（(]\s*(\d+)\s*[)）]|(-|[\d,]+)")


def cells(line):
    out = []
    for m in NUM.finditer(line):
        if m.group(1) is not None:
            v, p = m.group(1), int(m.group(2))
        else:
            v, p = m.group(3), None
        out.append((None if v == "-" else int(v.replace(",", "")), p))
    return out


def parse_block(lines, start):
    """start 行から、区分/例数/人数 の組を読み、総数の行まで返す"""
    cols, rows = [], {"例数": [], "人数": []}
    i = start
    while i < len(lines):
        s = lines[i]
        if s.strip().startswith("区分"):
            heads = re.findall(r"第\s*(\d+|[１-９])\s*次|総数", s)
            hs = []
            for m in re.finditer(r"第\s*([\d１-９]+)\s*次|総数", s):
                if m.group(0) == "総数":
                    hs.append("総数")
                else:
                    hs.append(int(m.group(1).translate(str.maketrans("１２３４５６７８９", "123456789"))))
            cols += hs
            for k in ("例数", "人数"):
                j = i + 1
                while not lines[j].strip().startswith(k):
                    j += 1
                rows[k] += cells(lines[j].split(k, 1)[1])
            if "総数" in hs:
                return cols, rows, i
        i += 1
    raise ValueError("総数なし")


def tables(n):
    L = [s.lstrip("\f") for s in (BASE / str(n) / "04_kobetsu.txt").read_text().splitlines()]
    if n >= 22:
        idx1 = next(i for i, s in enumerate(L) if s.startswith("表1") and "死亡事例数及び人数" in s)
        idx2 = next(i for i, s in enumerate(L) if s.startswith("表2") and "内訳" in s)
        t1 = parse_block(L, idx1)
        t2a = parse_block(L, idx2)
        t2b = parse_block(L, t2a[2] + 1)
        return {"表1": t1[:2], "表2こども": t2a[:2], "表2自殺": t2b[:2]}
    # 第21次まで：表1＝心中以外、表2＝心中
    idx1 = next(i for i, s in enumerate(L) if s.startswith("表1") and "心中以外" in s)
    idx2 = next(i for i, s in enumerate(L) if s.startswith("表2") and "心中による" in s)
    return {"表2こども": parse_block(L, idx1)[:2], "表2自殺": parse_block(L, idx2)[:2]}


def main():
    res, mism, nform = {}, [], 0
    for n in (20, 21, 22):
        T = tables(n)
        res[n] = T
        for name, (cols, rows) in T.items():
            for k, vals in rows.items():
                assert len(vals) == len(cols), (n, name, k, len(vals), len(cols))
                d = dict(zip(cols, vals))
                tot = d["総数"]
                s = sum(v for c, (v, p) in d.items() if c != "総数" and v is not None)
                sp = sum(p for c, (v, p) in d.items() if c != "総数" and p is not None)
                nform += 2
                if s != tot[0]:
                    mism.append(dict(版=n, 表=name, 行=k, 種類="値の合計", 総数=tot[0], 合計=s))
                if tot[1] is not None and sp != tot[1]:
                    mism.append(dict(版=n, 表=name, 行=k, 種類="括弧の合計", 総数=tot[1], 合計=sp))
        # 表1 = 表2こども + 表2自殺
        if "表1" not in T:
            continue
        c1, r1 = T["表1"]
        for k in ("例数", "人数"):
            a = dict(zip(c1, r1[k]))
            b = dict(zip(T["表2こども"][0], T["表2こども"][1][k]))
            c = dict(zip(T["表2自殺"][0], T["表2自殺"][1][k]))
            for col in c1:
                nform += 1
                v = (b[col][0] or 0) + (c[col][0] or 0)
                if a[col][0] != v:
                    mism.append(dict(版=n, 表="表1対表2", 行=k, 列=col, 種類="値", 表1=a[col][0], 表2の和=v))
                if a[col][1] is not None:
                    nform += 1
                    pv = (b[col][1] or 0) + (c[col][1] or 0)
                    if a[col][1] != pv:
                        mism.append(dict(版=n, 表="表1対表2", 行=k, 列=col, 種類="括弧", 表1=a[col][1], 表2の和=pv))
    # 版間
    for name in ("表1", "表2こども", "表2自殺"):
        for k in ("例数", "人数"):
            for a, b in ((20, 21), (21, 22)):
                if name not in res[a] or name not in res[b]:
                    continue
                da = dict(zip(res[a][name][0], res[a][name][1][k]))
                db = dict(zip(res[b][name][0], res[b][name][1][k]))
                for col in da:
                    if col == "総数" or col not in db:
                        continue
                    nform += 1
                    if da[col] != db[col]:
                        mism.append(dict(版=f"{a}→{b}", 表=name, 行=k, 列=col, 種類="版間", 前=da[col], 後=db[col]))
    print(f"式 {nform}　不一致 {len(mism)}")
    # 照合の要約（lib/tally.py）：単位は式。不一致はそのまま資料どうしの食い違いに数える。
    import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
    _F = []; _nf = sum(1 for x in mism if isinstance(x, dict) and x.get('検査') in _F)
    _t = Tally('gyakutai', 'c4001', note='子ども虐待による死亡事例等の検証結果：表1・表2の和と総数、版間', script=__file__); _t.set(compared=nform, mismatched=len(mism) - _nf, read_failures=_nf); print('tally', _t.save())
    for m in mism:
        print(json.dumps(m, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
