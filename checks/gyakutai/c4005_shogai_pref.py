"""障害者虐待 令和6年度 結果報告書の都道府県別の表（表1・8-2・32・44-2 など）：
47都道府県の値の和＝合計を確かめ、令和6年度の報道発表の値（通報件数・判断件数）とも突き合わせる。
"""
import re, json
from pathlib import Path

P = Path("data/raw/shogai_gyakutai/R06_houkoku.txt")
PREF = "北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 群馬県 埼玉県 千葉県 東京都 神奈川県 新潟県 富山県 石川県 福井県 山梨県 長野県 岐阜県 静岡県 愛知県 三重県 滋賀県 京都府 大阪府 兵庫県 奈良県 和歌山県 鳥取県 島根県 岡山県 広島県 山口県 徳島県 香川県 愛媛県 高知県 福岡県 佐賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県".split()
PRESS = {"1": 11656, "32": 5870, "8-2": 2503, "44-2": 1267}


def main():
    L = P.read_text().replace("\f", "\n").split("\n")
    T, cur = [], None
    for s in L:
        m = re.match(r"^\s*表\s*([0-9]+(?:-[0-9]+)?)\s+(.*)", s)
        if m:
            cur = dict(id=m.group(1), title=m.group(2), text=[])
            T.append(cur)
        elif cur is not None:
            cur["text"].append(s)
    mism, nf, done = [], 0, []
    for t in T:
        if "都道府県別" not in t["title"]:
            continue
        txt = "\n".join(t["text"][:30])
        vals = {}
        for p in PREF + ["合計"]:
            m = re.search(re.escape(p) + r"\s+([0-9][0-9,]*)", txt)
            if m:
                vals[p] = int(m.group(1).replace(",", ""))
        if len([p for p in PREF if p in vals]) != 47 or "合計" not in vals:
            mism.append(dict(表=t["id"], 検査="読み取り", 都道府県=len([p for p in PREF if p in vals]), 合計="合計" in vals))
            continue
        done.append(t["id"])
        s = sum(vals[p] for p in PREF)
        nf += 1
        if s != vals["合計"]:
            mism.append(dict(表=t["id"], 題=t["title"][:30], 検査="47の和＝合計", 和=s, 合計=vals["合計"]))
        if t["id"] in PRESS:
            nf += 1
            if vals["合計"] != PRESS[t["id"]]:
                mism.append(dict(表=t["id"], 検査="合計＝報道発表", 合計=vals["合計"], 発表=PRESS[t["id"]]))
    print(f"表 {len(done)}（{'・'.join(done)}）　式 {nf}　不一致 {len(mism)}")
    # 照合の要約（lib/tally.py）：単位は式。不一致はそのまま資料どうしの食い違いに数える（「読み取り」は読み取りの失敗）。
    import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
    _F = ['読み取り']; _nf = sum(1 for x in mism if isinstance(x, dict) and x.get('検査') in _F)
    _t = Tally('gyakutai', 'c4005', note='障害者虐待の調査結果報告書：都道府県の和と合計、合計と報道発表', script=__file__); _t.set(compared=nf, mismatched=len(mism) - _nf, read_failures=_nf); print('tally', _t.save())
    for m in mism:
        print(json.dumps(m, ensure_ascii=False))


if __name__ == "__main__":
    main()
