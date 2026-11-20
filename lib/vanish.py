"""vanish.py：版（年）ごとの「項目の集合」を比べ、ある版で消えた項目・現れた項目を出す。
入力は {版: [項目, ...]}（版は並べ替えられる鍵）。項目は norm() で正規化して比べる。
消えた項目は、その版の次の版から最後の版まで一度も現れないもの（途中で戻ったものは「一時的に消えた」）。
"""
import re, unicodedata


def norm(s):
    s = unicodedata.normalize('NFKC', str(s))
    s = re.sub(r'\s+', '', s)
    return s


def compare(sets):
    keys = sorted(sets)
    N = {k: {norm(x): x for x in sets[k]} for k in keys}
    out = []
    for i, k in enumerate(keys[:-1]):
        nxt = keys[i + 1]
        for n, raw in N[k].items():
            if n not in N[nxt]:
                later = [kk for kk in keys[i + 2:] if n in N[kk]]
                out.append(dict(kind='消えた' if not later else '一時的に消えた', last=k, first_missing=nxt,
                                back=later[0] if later else None, item=raw))
        for n, raw in N[nxt].items():
            if n not in N[k]:
                earlier = [kk for kk in keys[:i] if n in N[kk]]
                if not earlier:
                    out.append(dict(kind='現れた', last=None, first_missing=None, back=nxt, item=raw))
    return out
