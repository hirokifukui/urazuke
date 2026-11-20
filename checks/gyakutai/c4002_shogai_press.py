"""障害者虐待対応状況調査（令和3〜6年度）：
(1) 報道発表の全体像の表：各年度の「前回調査」の値と前年度の発表の値
(2) 令和6年度 経年グラフの表と各年度の発表の値
(3) 令和6年度 発表の「N件（対前年度 D件（P％）増/減）」の文と「N件（P％）」の構成割合
入力: data/raw/shogai_gyakutai/*.txt（pdftotext -layout）
"""
import re, sys, json
from pathlib import Path

B = Path("data/raw/shogai_gyakutai")
n = lambda s: int(s.replace(",", ""))


def zentai(y):
    t = (B / f"press_R{y:02d}.txt").read_text()
    t = t[t.index("全体像"):t.index("（注１）")]
    nums = [n(x) for x in re.findall(r"([\d,]+)\s*(?:件|人|事業所)", t)]
    assert len(nums) == 18, (y, nums)
    # 行順：通報(当年3) 通報(前3) 判断(当3) 判断(前3) 被虐待(当3) 被虐待(前3)
    cur = nums[0:3] + nums[6:9] + nums[12:15]
    prev = nums[3:6] + nums[9:12] + nums[15:18]
    return cur, prev


def keinen():
    L = (B / "R06_keinen.txt").read_text().splitlines()
    rows = {}
    for s in L:
        for k in ("相談・通報件数", "虐待判断件数", "被虐待者数"):
            if s.strip().startswith(k) and re.search(r"\d,\d{3}\s+\d", s):
                v = [n(x) for x in re.findall(r"[\d,]+", s.split("）", 1)[1])]
                rows.setdefault(k, []).append(v)
    return rows  # 各キー [養護者, 施設]，H24..R6 の 13 年度


def main():
    mism, nf = [], 0
    Z = {y: zentai(y) for y in (3, 4, 5, 6)}
    for y in (4, 5, 6):
        for i, (a, b) in enumerate(zip(Z[y][1], Z[y - 1][0])):
            nf += 1
            if a != b:
                mism.append(dict(検査="前回調査", 年度=y, 位置=i, 前回欄=a, 前年度発表=b))
    K = keinen()
    for j, k in enumerate(("相談・通報件数", "虐待判断件数", "被虐待者数")):
        for who in (0, 1):
            for y in (3, 4, 5, 6):
                nf += 1
                kv = K[k][who][12 - (6 - y)]
                pv = Z[y][0][j * 3 + who]
                if kv != pv:
                    mism.append(dict(検査="経年グラフ", 年度=y, 項目=k, 主体=who, 経年=kv, 発表=pv))
    # (3) 文の再計算
    t = re.sub(r"\s+", "", (B / "press_R06.txt").read_text())
    for m in re.finditer(r"([\d,]+)(件|人)（対前年度([\d,]+)(?:件|人)（([\d.]+)％）(増|減)", t):
        N, D, P, sgn = n(m.group(1)), n(m.group(3)), float(m.group(4)), m.group(5)
        prev = N - D if sgn == "増" else N + D
        nf += 1
        if abs(round(D / prev * 100, 1) - P) > 0.051:
            mism.append(dict(検査="増減率", 文=m.group(0), 再計算=round(D / prev * 100, 2)))
    print(f"式 {nf}　不一致 {len(mism)}")
    # 照合の要約（lib/tally.py）：単位は式。不一致はそのまま資料どうしの食い違いに数える。
    import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
    _F = []; _nf = sum(1 for x in mism if isinstance(x, dict) and x.get('検査') in _F)
    _t = Tally('gyakutai', 'c4002', note='障害者虐待の対応状況：報道発表の前回調査欄・経年グラフ・増減率', script=__file__); _t.set(compared=nf, mismatched=len(mism) - _nf, read_failures=_nf); print('tally', _t.save())
    for x in mism:
        print(json.dumps(x, ensure_ascii=False))


if __name__ == "__main__":
    main()
