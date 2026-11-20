#!/usr/bin/env python3
"""検算 c405：警察白書 統計資料2-1「都道府県別刑法犯の認知件数、検挙件数、検挙人員」（平成28年版〜令和8年版＝2015〜2025年）
 (a) 白書の内部：全国総数＝都道府県（北海道は計、方面を除く）の和、刑法犯総数＝包括罪種6区分の和（各都道府県）
 (c) 白書 ↔ 犯罪統計資料（警察庁、同じ年。令和2年以降は CSV、それ以前は PDF）第3表の刑法犯総数（認知・検挙件数・検挙人員）
出力: results/keisatsu/c405_hakusho_vs_toukei.tsv（食い違い）、c405_summary.tsv"""
import sys, re, importlib.util
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT / 'lib'))
import xlsx, xls
spec = importlib.util.spec_from_file_location('c403', ROOT / 'checks/keisatsu/c403_pdf_prev_year.py')
HK = ROOT / 'data/raw/keisatsu/hakusho'; RAW = ROOT / 'data/raw/keisatsu/estat'; OUT = ROOT / 'results/keisatsu'
# c403 の読み取り関数を流用する（モジュールの実行部分は避けるため、関数定義までを読む）
src = (ROOT / 'checks/keisatsu/c403_pdf_prev_year.py').read_text().split('src = {}')[0].replace("ROOT = Path(__file__).resolve().parents[2]", f"ROOT = Path({str(ROOT)!r})")
ns = {}; exec(src, ns)
pdf_tables, csv_tables, norm = ns['pdf_tables'], ns['csv_tables'], ns['norm']
EDS = {'h28': ('H27', 2015), 'h29': ('H28', 2016), 'h30': ('H29', 2017), 'r01': ('H30', 2018), 'r02': ('R01', 2019), 'r03': ('R02', 2020),
       'r04': ('R03', 2021), 'r05': ('R04', 2022), 'r06': ('R05', 2023), 'r07': ('R06', 2024), 'r08': ('R07', 2025)}
CRIMES = ['凶悪犯', '粗暴犯', '窃盗犯', '知能犯', '風俗犯']
def pref(s):
    s = re.sub(r'\s', '', s)
    if s.endswith(('県', '府')) and len(s) > 2: s = s[:-1]
    if s == '東京都': s = '東京'
    return norm(s)

det, cnt = [], Counter()
def rec(kind, ed, key, a, b):
    ok = a is not None and b is not None and abs(a - b) < 1e-9
    cnt[(kind, ed, '一致' if ok else '食い違い')] += 1
    if not ok: det.append([kind, ed, key, a, b])

for hk, (ted, year) in EDS.items():
    # 表題で選ぶ（章番号は版によって違う）。取得一覧の表題（list_keisatsu_hakusho_titles.tsv）から
    files = []
    for l in open(ROOT / 'sources/generic/list_keisatsu_hakusho_titles.tsv'):
        e, u, t = (l.rstrip('\n').split('\t') + [''])[:3]
        if e == hk and '都道府県別刑法犯の認知件数' in t:
            a = u.rsplit('/', 2); files.append(HK / hk / f'{a[1]}_{a[2]}')
    if not files: cnt[('欠測', hk, '2-1なし')] += 1; continue
    f = files[0]; S = (xls if f.suffix == '.xls' else xlsx).read_sheets(f)
    # 文字列の空白を除いて扱う（「認 知 件 数」のような表記があるため）
    S = {n: {k: (re.sub(r'\s', '', v) if isinstance(v, str) else v) for k, v in cc.items()} for n, cc in S.items()}
    c = next((cc for cc in S.values() if any(v == '認知件数' for v in cc.values())), None)
    if c is None: cnt[('欠測', hk, '見出しが読めない')] += 1; continue
    # 見出し：「認知件数」の行と、罪種名の行
    hr = next(r for r in range(1, 15) if any(c.get((r, j)) == '認知件数' for j in range(1, 40)))
    groups = {}; last = None
    for j in range(1, 60):
        for r in range(hr - 3, hr):
            v = c.get((r, j))
            if isinstance(v, str) and v.strip() and v.strip() not in ('区分',) and not v.startswith('区分'):
                last = re.sub(r'\s', '', v)
        lab = c.get((hr, j))
        if lab in ('認知件数', '検挙件数', '検挙人員') and last: groups[(last, lab)] = j
    # 行
    rows = {}; cur_top = None
    for r in range(hr + 1, hr + 80):
        a, b = c.get((r, 1)), c.get((r, 2))
        a = re.sub(r'\s', '', a) if isinstance(a, str) else None; b = re.sub(r'\s', '', b) if isinstance(b, str) else None
        if a is None and b is None: continue
        if a: cur_top = a
        name = a if (a and (b in (None, '計'))) else b
        is_sub = (a is None and b is not None)          # 方面（札幌など）
        vals = {k: c.get((r, j)) for k, j in groups.items()}
        if not any(isinstance(v, (int, float)) for v in vals.values()): continue
        rows[(name, is_sub)] = vals
    tot = next((v for (n, s), v in rows.items() if n and n.startswith('全国')), None)
    prefs = {n: v for (n, s), v in rows.items() if n and not n.startswith('全国') and not s}
    # (a) 全国＝都道府県の和
    if tot:
        for k in [k for k in groups if k[0] == '刑法犯総数']:
            rec('a全国＝都道府県の和', hk, '/'.join(k), sum(v[k] or 0 for v in prefs.values()), tot[k])
    # (a) 総数＝包括罪種の和（その他の刑法犯を含む）
    oth = next((g for g in {k[0] for k in groups} if g.startswith('その他')), None)
    for n, v in list(prefs.items()) + ([('全国総数', tot)] if tot else []):
        for lab in ('認知件数', '検挙件数', '検挙人員'):
            parts = [v.get((g, lab)) for g in CRIMES + ([oth] if oth else [])]
            if any(p is None for p in parts) or v.get(('刑法犯総数', lab)) is None: continue
            rec('a総数＝包括罪種の和', hk, f'{n}/{lab}', sum(parts), v[('刑法犯総数', lab)])
    # (c) 犯罪統計資料 第3表
    csvs = sorted(RAW.glob(f'{ted}_kakutei_*.csv')); pdfs = sorted(RAW.glob(f'{ted}_kakutei_*.pdf'))
    T3 = (csv_tables(str(csvs[0])) if csvs else pdf_tables(str(pdfs[0])))[3]
    for (n, s), v in rows.items():
        key = norm('総数') if n.startswith('全国') else pref(n)
        if s: key = norm(n)
        t = T3.get(key) or next((T3.get(norm(re.sub(r'\s', '', n) + x)) for x in ('県', '府', '都') if T3.get(norm(re.sub(r'\s', '', n) + x))), None)
        if t is None: cnt[('c白書↔犯罪統計', hk, '対応なし')] += 1; continue
        for lab in ('認知件数', '検挙件数', '検挙人員'):
            if v.get(('刑法犯総数', lab)) is None: continue
            rec('c白書↔犯罪統計', hk, f'{n}/{lab}', v[('刑法犯総数', lab)], t[lab][0])
with open(OUT / 'c405_hakusho_vs_toukei.tsv', 'w') as w:
    w.write('kind\tedition\tkey\thakusho_or_sum\tother\n')
    for d in det: w.write('\t'.join(map(str, d)) + '\n')
with open(OUT / 'c405_summary.tsv', 'w') as w:
    w.write('kind\tedition\tstatus\tn\n')
    for k, n in sorted(cnt.items()): w.write('\t'.join(k) + f'\t{n}\n')
agg = Counter()
for (k, e, s), n in cnt.items(): agg[(k, s)] += n
print(dict(agg)); print('食い違い', len(det))

# 照合の要約（lib/tally.py）
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('keisatsu', 'c405', note='警察白書の統計表：包括罪種の和と総数、白書と犯罪統計資料 第3表', script=__file__)
for (k, e, s), n in cnt.items(): {'一致': _t.ok, '食い違い': _t.ng}.get(s, _t.fail)(n)
print('tally', _t.save())
