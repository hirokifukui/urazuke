"""移行用：「print(f'… 式 {nf} … 不一致 {len(mism)}')」の形で終わる検査に、照合の要約（lib/tally.py）を書く行を足す。
使い方: python checks/generic/add_tally_after_print.py <検査.py> <dir> <check> <note> [失敗とみなす検査名,...]
  mism の各要素が dict で「検査」が失敗とみなす名前のものは読み取りの失敗に数える（式の数に入っていないことを確かめてから使う）。既に要約の行があれば何もしない。"""
import re, sys
fn, d, chk, note = sys.argv[1:5]
fails = sys.argv[5].split(',') if len(sys.argv) > 5 and sys.argv[5] else []
s = open(fn, encoding='utf-8').read()
if 'lib.tally' in s:
    print('skip (already)', fn); sys.exit()
lines = s.split('\n')
for i, l in enumerate(lines):
    m = re.search(r'print\(f[\'"].*式 \{(\w+)\}.*不一致 \{len\((\w+)\)\}', l)
    if m:
        ind = re.match(r'\s*', l).group(0)
        nf, ms = m.group(1), m.group(2)
        add = [
            f"{ind}# 照合の要約（lib/tally.py）：単位は式。不一致はそのまま資料どうしの食い違いに数える" + ("（「" + "・".join(fails) + "」は読み取りの失敗）" if fails else '') + "。",
            f"{ind}import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally",
            f"{ind}_F = {fails!r}; _nf = sum(1 for x in {ms} if isinstance(x, dict) and x.get('検査') in _F)",
            f"{ind}_t = Tally({d!r}, {chk!r}, note={note!r}, script=__file__); _t.set(compared={nf}, mismatched=len({ms}) - _nf, read_failures=_nf); print('tally', _t.save())",
        ]
        lines[i + 1:i + 1] = add
        open(fn, 'w', encoding='utf-8').write('\n'.join(lines))
        print('ok', fn, nf, ms); break
else:
    print('NO MATCH', fn)
