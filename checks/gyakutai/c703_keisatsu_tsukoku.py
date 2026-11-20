"""児童相談所の相談経路「警察等」（福祉行政報告例 第49、年度・件数）と、
警察庁の児童相談所への通告児童数（暦年・人数）を並べる。
定義が違う（年度↔暦年、件↔人、警察等には家裁等を含む場合がある）ので、一致は期待しない。
見るのは、比の安定と、年ごとの動きの向き。"""
import sys, glob, re
sys.path.insert(0, 'lib')
import fukushi_csv
# 警察庁「ストーカー・DV・児童虐待」資料の通告児童数（令和4年版の図＝2013〜2022、令和5〜7年版の本文＝2023〜2025）
NPA = {2013:21603,2014:28923,2015:37020,2016:54227,2017:65431,2018:80252,2019:98222,2020:106991,2021:108059,2022:115762,2023:122806,2024:122378,2025:122588}
out = {}
for f in sorted(glob.glob('data/raw/gyakutai/estat/FY*_shubetsu_keiro_*.csv')):
    fy = int(re.search(r'FY(\d{4})', f).group(1))
    t = fukushi_csv.read(f)
    jk = [j for j, c in enumerate(t['cols']) if '警察' in c]
    tk = [j for j, c in enumerate(t['cols']) if c.startswith('総数')]
    row = next(r for r in t['rows'] if r[0].startswith('総数') or r[1].startswith('総数'))
    out[fy] = (row[2][tk[0]] if tk else None, row[2][jk[0]] if jk else None, t['cols'][jk[0]] if jk else '')
print('年度\t相談対応総数\t経路:警察等\t列名\t警察庁 通告児童数(同じ暦年)\t比(警察等/通告)\t警察等の割合')
for fy, (tot, pol, cn) in sorted(out.items()):
    n = NPA.get(fy)
    r = f'{pol/n:.3f}' if (pol and n) else ''
    print(f'{fy}\t{tot:.0f}\t{pol:.0f}\t{cn}\t{n or ""}\t{r}\t{pol/tot:.3f}')
