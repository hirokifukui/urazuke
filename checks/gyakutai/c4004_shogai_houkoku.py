"""障害者虐待対応状況調査 令和6年度 結果報告書（R06_houkoku.txt）の横長の表：
表ごとに「件数」（または人数）の行と「構成割合」の行を順に読み、
(1) 構成割合＝件数/分母（分母は注の「N件に対するもの」、なければ合計）、
(2) 複数回答でない表は、内訳の和＝合計、を確かめる。
"""
import re, sys, json
from pathlib import Path

P = Path("data/raw/shogai_gyakutai/R06_houkoku.txt")
NUM = re.compile(r"(?<![0-9.,])-?[0-9][0-9,]*(?:\.[0-9]+)?%?|(?<=\s)-(?=\s|$)")


def nums(s):
    out = []
    for t in NUM.findall(s):
        if t == "-":
            out.append(None)
        elif t.endswith("%"):
            out.append(("p", float(t[:-1])))
        else:
            out.append(float(t.replace(",", "")) if "." in t else int(t.replace(",", "")))
    return out


def tables():
    L = P.read_text().replace("\f", "\n").split("\n")
    T, cur = [], None
    for i, s in enumerate(L):
        m = re.match(r"^\s*表\s*([0-9]+(?:-[0-9]+)?)\s+(.*)", s)
        if m:
            cur = dict(id=m.group(1), title=m.group(2).strip(), line=i + 1, cnt=[], pct=[], head="", note="")
            T.append(cur)
            continue
        if cur is None:
            continue
        st = s.strip()
        if re.match(r"^(件数|人数|事業所数|事例数)\s", st):
            cur["cnt"].append((i + 1, nums(st.split(None, 1)[1] if " " in st else "")))
        elif st.startswith("構成割合"):
            cur["pct"].append((i + 1, nums(st[4:])))
        elif st.startswith("（注") or st.startswith("※"):
            cur["note"] += st
        elif not cur["cnt"]:
            cur["head"] += st
    return T


def main():
    mism, nf, nt = [], 0, 0
    for t in tables():
        if not t["cnt"] or len(t["cnt"]) != len(t["pct"]):
            continue
        nt += 1
        multi = "複数回答" in t["title"]
        cnt = [x for _, r in t["cnt"] for x in r]
        pct = [x for _, r in t["pct"] for x in r]
        if len(cnt) != len(pct):
            continue
        has_total = "合計" in t["head"] or "計" in t["head"].replace("合計", "計")
        m = re.search(r"([0-9][0-9,]*)\s*(?:件|人|事業所)に対する", t["note"])
        den = int(m.group(1).replace(",", "")) if m else (cnt[-1] if has_total and isinstance(cnt[-1], int) else None)
        if den:
            for k, (c, p) in enumerate(zip(cnt, pct)):
                if not isinstance(c, int) or not (isinstance(p, tuple)):
                    continue
                nf += 1
                calc = round(c / den * 100, 1)
                if abs(calc - p[1]) > 0.11:
                    mism.append(dict(表=t["id"], 題=t["title"][:30], 行=t["cnt"][0][0], 位置=k, 検査="構成割合", 件数=c, 分母=den, 掲載=p[1], 再計算=calc))
        if not multi and has_total and isinstance(cnt[-1], int):
            body = [c for c in cnt[:-1] if isinstance(c, int)]
            nf += 1
            if sum(body) != cnt[-1]:
                mism.append(dict(表=t["id"], 題=t["title"][:30], 行=t["cnt"][0][0], 検査="内訳の和＝合計", 合計=cnt[-1], 和=sum(body)))
    print(f"表 {nt}　式 {nf}　不一致 {len(mism)}")
    # 照合の要約（lib/tally.py）：単位は式。不一致はそのまま資料どうしの食い違いに数える。
    import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
    _F = []; _nf = sum(1 for x in mism if isinstance(x, dict) and x.get('検査') in _F)
    _t = Tally('gyakutai', 'c4004', note='障害者虐待の調査結果報告書：構成割合と内訳の和', script=__file__); _t.set(compared=nf, mismatched=len(mism) - _nf, read_failures=_nf); print('tally', _t.save())
    for x in mism:
        print(json.dumps(x, ensure_ascii=False))


if __name__ == "__main__":
    main()
