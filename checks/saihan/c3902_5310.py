"""犯罪白書 5-3-10図（2年以内再入率：男女別・年齢層別・罪名別）と 5-3-11図（再犯期間別）：
(1) 比率＝再入者/出所受刑者、男＋女＝計、年齢層の和＝計（5-3-10①の総数）
(2) 5-3-10①の総数（出所・再入）＝5-3-9①の総数（同じ版）
(3) 令和5・6・7年版の間で、同じ年の値が同じか
(4) 5-3-11図：区分の和＝総数、版間
"""
import openpyxl, re, json, os, sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else '.'
ED = {'令和5年版': '70_20261116T073025Z', '令和6年版': '71_20261116T090659Z', '令和7年版': '72'}


def rows(path, idx):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = [w for w in wb.worksheets if '閲覧用' not in w.title][idx]
    out = []
    for r in ws.iter_rows(values_only=True):
        r = list(r)
        while r and r[0] is None:
            r.pop(0)
        if r and isinstance(r[0], str) and re.match(r'^(平成|令和|昭和)', r[0]) and any(isinstance(c, (int, float)) for c in r[2:]):
            out.append([r[0]] + list(r[1:]))
    return out


def num(x):
    return x if isinstance(x, (int, float)) else None


def main():
    mism, nf = [], 0
    data = {}
    for ed, d in ED.items():
        p = os.path.join(ROOT, f'data/raw/hanzai_hakusho/{d}/zuhyo/5-3-10.xlsx')
        p9 = os.path.join(ROOT, f'data/raw/hanzai_hakusho/{d}/zuhyo/5-3-9.xlsx')
        p11 = os.path.join(ROOT, f'data/raw/hanzai_hakusho/{d}/zuhyo/5-3-11.xlsx')
        sx, ag, cr = rows(p, 0), rows(p, 1), rows(p, 2)
        n9 = {r[0]: r for r in rows(p9, 0)}
        data[ed] = dict(sx={r[0]: r for r in sx}, ag={r[0]: r for r in ag}, cr={r[0]: r for r in cr})
        for r in sx:
            y = r[0]
            out_t, out_m, out_f, re_t, rt, re_m, rm, re_f, rf = [num(x) for x in r[2:11]]
            for a, b, nm in ((out_m + out_f, out_t, '出所 男+女'), (re_m + re_f, re_t, '再入 男+女')):
                nf += 1
                if a != b:
                    mism.append(dict(版=ed, 図='5-3-10①', 年=y, 検査=nm, 和=a, 計=b))
            for n, dnm, p_, nm in ((re_t, out_t, rt, '比率 計'), (re_m, out_m, rm, '比率 男'), (re_f, out_f, rf, '比率 女')):
                nf += 1
                if abs(n / dnm * 100 - p_) > 1e-6:
                    mism.append(dict(版=ed, 図='5-3-10①', 年=y, 検査=nm, 再計算=n / dnm * 100, 掲載=p_))
            if y in n9:
                q = n9[y]
                nf += 2
                if q[2] != out_t or q[7] != re_t:
                    mism.append(dict(版=ed, 検査='5-3-10①と5-3-9①', 年=y, 出所=[out_t, q[2]], 再入=[re_t, q[7]]))
        for r in ag:
            y = r[0]
            v = [num(x) for x in r[2:]]
            while v and v[-1] is None:
                v.pop()
            outs, res, rts = v[0::3], v[1::3], v[2::3]
            if None in outs or None in res:
                mism.append(dict(版=ed, 図='5-3-10②', 年=y, 検査='空欄', 値=v))
                continue
            for o, n, p_ in zip(outs, res, rts):
                if o:
                    nf += 1
                    if abs(n / o * 100 - p_) > 1e-6:
                        mism.append(dict(版=ed, 図='5-3-10②', 年=y, 検査='比率', 再計算=n / o * 100, 掲載=p_))
            s = data[ed]['sx'].get(y)
            if s:
                nf += 2
                if sum(outs) != s[2] or sum(res) != s[5]:
                    mism.append(dict(版=ed, 図='5-3-10②', 年=y, 検査='年齢層の和＝計', 出所=[sum(outs), s[2]], 再入=[sum(res), s[5]]))
        for r in cr:
            v = [num(x) for x in r[2:]]
            for o, n, p_ in zip(v[0::3], v[1::3], v[2::3]):
                if o and n is not None and p_ is not None:
                    nf += 1
                    if abs(n / o * 100 - p_) > 1e-6:
                        mism.append(dict(版=ed, 図='5-3-10③', 年=r[0], 検査='比率', 再計算=n / o * 100, 掲載=p_))
        r11 = rows(p11, 0)
        data[ed]['r11'] = {r[0]: r for r in r11}
        for r in r11:
            v = [num(x) for x in r[2:] if num(x) is not None]
            nf += 1
            if sum(v[1:]) != v[0]:
                mism.append(dict(版=ed, 図='5-3-11', 年=r[0], 検査='区分の和＝総数', 和=sum(v[1:]), 総数=v[0]))
    eds = list(ED)
    for a, b in zip(eds, eds[1:]):
        for key in ('sx', 'ag', 'cr', 'r11'):
            for y, ra in data[a][key].items():
                rb = data[b][key].get(y)
                if rb is None:
                    continue
                va = [x for x in ra[2:] if isinstance(x, int)]
                vb = [x for x in rb[2:] if isinstance(x, int)]
                nf += 1
                if va != vb:
                    diff = [(i, x, z) for i, (x, z) in enumerate(zip(va, vb)) if x != z]
                    mism.append(dict(検査='版間', 図=key, 版=f'{a}→{b}', 年=y, 違い=diff[:6], 長さ=[len(va), len(vb)]))
    print(f'式 {nf}　不一致 {len(mism)}')
    # 照合の要約（lib/tally.py）：単位は式
    import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
    _t = Tally('saihan', 'c3902', note='犯罪白書 5-3-10図・5-3-11図：比率・男女・年齢層の和、5-3-9図との一致、版間', script=__file__); _t.set(compared=nf, mismatched=len(mism)); print('tally', _t.save())
    for m in mism:
        print(json.dumps(m, ensure_ascii=False))


if __name__ == '__main__':
    main()
