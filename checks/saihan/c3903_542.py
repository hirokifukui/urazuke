"""犯罪白書 5-4-2図（保護観察終了者の再処分率・取消率等）：
各シートで (1) 再処分人員＝再処分の内容の和、(2) 再処分率＝再処分人員/終了人員、
(3) 令和5・6・7年版の間で同じ年の値が同じか、を確かめる。列は見出しの行の位置で決める。
"""
import openpyxl, re, json, os, sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else '.'
ED = {'令和5年版': '70_20261116T073025Z', '令和6年版': '71_20261116T090659Z', '令和7年版': '72'}


def sheet(ws):
    R = [list(r) for r in ws.iter_rows(values_only=True)]
    h = next(i for i, r in enumerate(R) if '保護観察終了人員' in [c for c in r if isinstance(c, str)])
    hdr = R[h]
    col = lambda name: [j for j, c in enumerate(hdr) if c == name]
    N, Rr = col('保護観察終了人員')[0], [j for j, c in enumerate(hdr) if c in ('再処分人員', '再処分人員_計')][0]
    cont = [j for j, c in enumerate(hdr) if isinstance(c, str) and (c.startswith('再処分の内容') or c.startswith('再処分人員_再処分の内容'))]
    rate = [j for j, c in enumerate(hdr) if isinstance(c, str) and c.startswith('再処分率')][0]
    out = {}
    for r in R[h + 1:]:
        ys = [c for c in r[:N] if isinstance(c, str) and re.match(r'^(平成|令和)', c)]
        if ys and isinstance(r[N], (int, float)):
            out[ys[0]] = dict(N=r[N], R=r[Rr], cont=[r[j] for j in cont], rate=r[rate], raw=[c for c in r if isinstance(c, (int, float))])
    return out


def main():
    mism, nf, D = [], 0, {}
    for ed, d in ED.items():
        wb = openpyxl.load_workbook(os.path.join(ROOT, f'data/raw/hanzai_hakusho/{d}/zuhyo/5-4-2.xlsx'), data_only=True)
        D[ed] = {}
        for ws in wb.worksheets:
            if '閲覧用' in ws.title:
                continue
            key = re.sub(r'^.*図', '', ws.title)
            try:
                S = sheet(ws)
            except (StopIteration, IndexError):
                continue
            D[ed][key] = S
            for y, v in S.items():
                c = [x for x in v['cont'] if isinstance(x, (int, float))]
                nf += 1
                if sum(c) != v['R']:
                    mism.append(dict(版=ed, シート=key, 年=y, 検査='内容の和＝再処分人員', 和=sum(c), 再処分=v['R']))
                if v['N'] and isinstance(v['rate'], (int, float)):
                    nf += 1
                    if abs(v['R'] / v['N'] * 100 - v['rate']) > 1e-6:
                        mism.append(dict(版=ed, シート=key, 年=y, 検査='再処分率', 再計算=v['R'] / v['N'] * 100, 掲載=v['rate']))
    eds = list(ED)
    for a, b in zip(eds, eds[1:]):
        for key, S in D[a].items():
            for y, v in S.items():
                w = D[b].get(key, {}).get(y)
                if w is None:
                    continue
                nf += 1
                ia = [x for x in v['raw'] if isinstance(x, int)]
                ib = [x for x in w['raw'] if isinstance(x, int)]
                if ia != ib:
                    mism.append(dict(検査='版間', シート=key, 版=f'{a}→{b}', 年=y, 前=ia, 後=ib))
    print(f'シート {sum(len(x) for x in D.values())}　式 {nf}　不一致 {len(mism)}')
    # 照合の要約（lib/tally.py）：単位は式。不一致9（3か所×3版）は再処分率のセルと同じ行の人数（HK-A8）
    import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
    _t = Tally('saihan', 'c3903', note='犯罪白書 5-4-2図：再処分の内容の和、再処分率の再計算、版間', script=__file__); _t.set(compared=nf, mismatched=len(mism)); print('tally', _t.save())
    for m in mism:
        print(json.dumps(m, ensure_ascii=False))


if __name__ == '__main__':
    main()
