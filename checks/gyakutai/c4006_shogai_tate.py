"""障害者虐待対応状況調査 令和6年度 結果報告書（R06_houkoku.txt）の縦長の表：
各行「項目  件数  構成割合」を読み、
(1) 本行（括弧なしの割合）：構成割合＝件数/分母（分母は注の「N件（人）に対するもの」、なければ合計）
(2) 小行（(x%)）：直前の本行の件数に対する割合、[x%]：直前の小行に対する割合
(3) 複数回答でない表：本行の和＝合計。小行の割合の和が100％の組は、小行の和＝親の件数
を確かめる。c4004（横長の表）・c4005（都道府県別）で読んだ表は除く。
"""
import re, json
from pathlib import Path

P = Path('data/raw/shogai_gyakutai/R06_houkoku.txt')
ROW = re.compile(r'^(?P<lab>\S.*?\S)\s+(?P<n>[0-9][0-9,]*)\s+(?P<o>[\(\[（]?)\s*(?P<p>[0-9]+\.[0-9])\s*%\s*[\)\]）]?\s*$')
SKIP = {'1', '8-2', '32', '44-2'}


def blocks():
    L = P.read_text().replace('\f', '\n').split('\n')
    cur = None
    for i, s in enumerate(L):
        m = re.match(r'^\s*表\s*([0-9]+(?:-[0-9]+)?)\s+(.*)', s)
        if m:
            if cur:
                yield cur
            cur = dict(id=m.group(1), title=m.group(2).strip(), line=i + 1, rows=[], note='', total=None)
            continue
        if cur is None:
            continue
        st = s.strip()
        if st.startswith('（注') or st.startswith('※'):
            cur['note'] += st
            continue
        mt = re.match(r'^合計\s+([0-9][0-9,]*)', st)
        if mt:
            cur['total'] = (i + 1, int(mt.group(1).replace(',', '')))
            cur['rows'].append(dict(line=i + 1, lab='合計', n=cur['total'][1], p=None, lvl='T'))
            continue
        m = ROW.match(st)
        if m:
            lvl = {'': 0, '(': 1, '（': 1, '[': 2}[m.group('o')]
            cur['rows'].append(dict(line=i + 1, lab=m.group('lab')[:30], n=int(m.group('n').replace(',', '')), p=float(m.group('p')), lvl=lvl))
    if cur:
        yield cur


def main():
    nt = nf = 0
    mism = []
    for b in blocks():
        if b['id'] in SKIP or len(b['rows']) < 2:
            continue
        nt += 1
        multi = '複数回答' in b['title']
        m = re.search(r'([0-9][0-9,]*)\s*(?:件|人|事業所|か所|市区町村|自治体)に対する', b['note'])
        den = int(m.group(1).replace(',', '')) if m else (b['total'][1] if b['total'] else None)
        parent = {0: None, 1: None}
        kids = {}
        for r in b['rows']:
            if r['lvl'] == 'T':
                parent[0] = r; parent[1] = None
                continue
            d = den if r['lvl'] == 0 else (parent[0]['n'] if r['lvl'] == 1 and parent[0] else (parent[1]['n'] if r['lvl'] == 2 and parent[1] else None))
            if d:
                nf += 1
                calc = round(r['n'] / d * 100, 1)
                if abs(calc - r['p']) > 0.11:
                    mism.append(dict(表=b['id'], 行=r['line'], 項目=r['lab'], 検査='構成割合', 件数=r['n'], 分母=d, 掲載=r['p'], 再計算=calc))
            if r['lvl'] == 0:
                parent[0] = r; parent[1] = None
            elif r['lvl'] == 1:
                parent[1] = r
                if parent[0] and parent[0]['lvl'] != 'T':
                    kids.setdefault(parent[0]['line'], [parent[0], []])[1].append(r)
        if not multi and b['total'] and not m:
            top = [r['n'] for r in b['rows'] if r['lvl'] == 0]
            nf += 1
            if sum(top) != b['total'][1]:
                mism.append(dict(表=b['id'], 行=b['total'][0], 検査='本行の和＝合計', 合計=b['total'][1], 和=sum(top)))
        if not multi:
            for pr, ks in kids.values():
                if abs(sum(k['p'] for k in ks) - 100) <= 0.2:
                    nf += 1
                    if sum(k['n'] for k in ks) != pr['n']:
                        mism.append(dict(表=b['id'], 行=pr['line'], 項目=pr['lab'], 検査='小行の和＝親', 親=pr['n'], 和=sum(k['n'] for k in ks)))
    print(f'表 {nt}　式 {nf}　不一致 {len(mism)}')
    # 照合の要約（lib/tally.py）：単位は式。不一致はそのまま資料どうしの食い違いに数える。
    import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
    _F = []; _nf = sum(1 for x in mism if isinstance(x, dict) and x.get('検査') in _F)
    _t = Tally('gyakutai', 'c4006', note='障害者虐待の調査結果報告書（縦の表）：構成割合と内訳の和', script=__file__); _t.set(compared=nf, mismatched=len(mism) - _nf, read_failures=_nf); print('tally', _t.save())
    for x in mism:
        print(json.dumps(x, ensure_ascii=False))


if __name__ == '__main__':
    main()
