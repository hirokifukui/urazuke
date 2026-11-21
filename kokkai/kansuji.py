"""国会会議録の漢数字を算用数字に直す（2026-11-21）。「二一・九」（一字ずつ）と「十三万三千七百七十八」（位取り）の両方。"""
import re
D = dict(zip('〇一二三四五六七八九', '0123456789')); U = {'十': 10, '百': 100, '千': 1000}; B = {'万': 10**4, '億': 10**8}
def _pos(s):
    tot = sec = num = 0
    for ch in s:
        if ch in D: num = num * 10 + int(D[ch])
        elif ch in U: sec += (num or 1) * U[ch]; num = 0
        elif ch in B: tot += (sec + num) * B[ch]; sec = num = 0
    return tot + sec + num
def numbers(text):
    """文中の数を算用数字の文字列で返す（重複なし、出てきた順）。"""
    out = []
    for m in re.finditer(r'[〇一二三四五六七八九十百千万億]+(?:・[〇一二三四五六七八九]+)?', text):
        s = m.group(0)
        if '・' in s:
            a, b = s.split('・'); a = ''.join(D.get(c, '') for c in a) if not any(c in U or c in B for c in a) else str(_pos(a))
            v = f"{a}.{''.join(D[c] for c in b)}"
        elif any(c in U or c in B for c in s): v = str(_pos(s))
        else: v = ''.join(D[c] for c in s)
        if v and v not in out and len(v.replace('.', '')) >= 2: out.append(v)
    return out
if __name__ == '__main__':
    print(numbers('平成二十九年度は十三万三千七百七十八件、二一・九％と二九・六％、二千百四十七名、第十二次報告'))
