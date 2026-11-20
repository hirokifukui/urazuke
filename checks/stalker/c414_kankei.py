"""犯罪統計書 第56表（罪種別 被疑者と被害者との関係別 検挙件数）と第39表（動機・原因別）を、
ストーカー事案・配偶者からの暴力事案等の検挙状況（警察庁）と並べる。
(1) 第56表の関係の区分の版間（令和元〜6年）：区分の名前の変化
(2) 第56表の内部：各行で 区分の和（「うち女」の列を除く）＝総数
(3) 凡例（R01・R02・R06 の全ページ PDF）に関係の区分の定義があるか
(4) 年ごとの比較表：殺人・傷害・住居侵入について
    第56表の 配偶者／元配偶者／交際相手、第39表の痴情、DV 統計の検挙、ストーカー統計の検挙
出力：results/stalker/c414_kankei.tsv
"""
import re, csv, io, unicodedata, sys
from pathlib import Path
import openpyxl
ROOT = Path.cwd() if (Path.cwd() / 'data/raw').is_dir() else Path(__file__).resolve().parents[2]
D = ROOT / 'data/raw/keisatsu_hanzai_toukei/sho'
S = ROOT / 'data/raw/stalker'
OUT = ROOT / 'results/stalker'
YRS = {'R01': 2019, 'R02': 2020, 'R03': 2021, 'R04': 2022, 'R05': 2023, 'R06': 2024}
N = lambda s: unicodedata.normalize('NFKC', str(s)).replace('\n', '').replace(' ', '').replace('　', '')


def lab(r):
    return ' '.join(N(c) for c in r[:7] if c is not None and N(c))


def t56(ed):
    ws = openpyxl.load_workbook(D / f'{ed}_056.xlsx', data_only=True).active
    hdr = {c.column: N(c.value) for c in ws[4] if c.value is not None and 8 <= c.column <= 26}
    hdr.pop(max(hdr), None) if '罪種' in hdr[max(hdr)] else None
    rows = {}
    for r in ws.iter_rows(min_row=6, max_row=ws.max_row, values_only=True):
        l = lab(r)
        if not l or l.startswith('確認用') or not isinstance(r[7], (int, float)): continue
        if l in rows: continue  # 最初の出現（「確認用」の下の行を読まない）
        rows[l] = {hdr[k]: r[k - 1] for k in hdr}
        rows[l]['_women'] = r[12]  # 13列目：配偶者のうち女
        rows[l]['_cols'] = {k: r[k - 1] for k in hdr}
        if l.split()[-1] == '殺人' and '殺人_sub' not in rows and len(rows) > 3:
            pass
    return hdr, rows, ws


def t39(ed):
    ws = openpyxl.load_workbook(D / f'{ed}_039.xlsx', data_only=True).worksheets[0]
    col = {N(c.value): c.column for c in ws[5] if c.value}
    out = {}
    for r in ws.iter_rows(min_row=6, max_row=ws.max_row, values_only=True):
        l = lab(r)
        if not l or l.startswith('確認用') or l in out or not isinstance(r[7], (int, float)): continue
        out[l] = {'総数': r[7], '痴情': r[col['痴情'] - 1]}
    return out


def first(rows, name, nth=0):
    ks = [k for k in rows if k.split()[-1] == name]
    return rows[ks[nth]] if len(ks) > nth else None


print('## (1) 関係の区分（第56表の見出し）')
prev = None
for ed in YRS:
    hdr, rows, ws = t56(ed)
    cats = [v for v in hdr.values() if v not in ('計', '総数')]
    if prev is not None and cats != prev:
        print(f'  {ed}: 変化 追加={[c for c in cats if c not in prev]} 削除={[c for c in prev if c not in cats]}')
    else:
        print(f'  {ed}: {"／".join(cats)}' if prev is None else f'  {ed}: 変化なし')
    prev = cats

print('\n## (2) 区分の和＝総数（各行）')
ok = ng = 0
for ed in YRS:
    hdr, rows, ws = t56(ed)
    tk = min(hdr)
    for l, d in rows.items():
        c = d['_cols']
        s = sum(v for k, v in c.items() if k != tk and isinstance(v, (int, float)))
        if s == c[tk]: ok += 1
        else: ng += 1; print('  不一致', ed, l, c[tk], s)
print('  一致', ok, '不一致', ng)

print('\n## (3) 凡例に関係の区分の定義があるか')
for ed in ('R01', 'R02', 'R06'):
    p = D / f'{ed}_ALL.txt'
    if not p.exists(): print('  ', ed, '未取得'); continue
    t = p.read_text(errors='ignore')
    head = t[:t.find('別表')] if '別表' in t else t[:30000]
    print(f'  {ed}: 凡例中「交際相手」{head.count("交際相手")} 「元配偶者」{head.count("元配偶者")} 「内縁」{head.count("内縁")} ／全体で「交際相手」{t.count("交際相手")}')


def csvrows(path):
    b = path.read_bytes()
    for e in ('utf-8-sig', 'cp932'):
        try: return list(csv.reader(io.StringIO(b.decode(e))))
        except UnicodeDecodeError: pass


def kenkyo(path, head):
    """CSV の「…検挙状況」の小節から {項目: {年: 値}}"""
    R = csvrows(path); out = {}; yrs = None; on = False
    for r in R:
        j = ''.join(r)
        if head in j and '検挙状況' in j: on = True; continue
        if on and yrs is None and any('令和' in c for c in r):
            yrs = {i: 2018 + int(unicodedata.normalize('NFKC', c).replace('令和', '').replace('年', '').replace('元', '1')) for i, c in enumerate(r) if re.fullmatch(r'令和[\d０-９元]+年', c.strip())}
            continue
        if on and yrs:
            if not any(c.strip() for c in r) or (r[0].strip() and r[0].strip()[0] in '５5６6'): break
            k = (r[2] or r[1]).strip()
            if not k: continue
            out.setdefault(k, {})
            for i, y in yrs.items():
                v = r[i].replace(',', '').strip() if i < len(r) else ''
                if re.fullmatch(r'\d+', v): out[k][y] = int(v)
    return out


ST = kenkyo(S / 'npa/01_R7_ST.csv', 'ストーカー事案')
DV = kenkyo(S / 'npa/02_R7_DV.csv', '配偶者からの暴力事案等')
ST6 = kenkyo(S / 'npa/R6_ST.csv', 'ストーカー事案'); DV6 = kenkyo(S / 'npa/R6_DV.csv', '配偶者からの暴力事案等')
for src, add in ((ST, ST6), (DV, DV6)):
    for k, d in add.items():
        for y, v in d.items(): src.setdefault(k, {}).setdefault(y, v)

print('\n## (4) 比較（年ごと）')
OUT.mkdir(parents=True, exist_ok=True)
fo = open(OUT / 'c414_kankei.tsv', 'w')
fo.write('year\t罪種\t第56表_総数\t配偶者\t元配偶者\t交際相手\t第39表_痴情\tDV統計_検挙\tストーカー統計_検挙\n')
for ed, y in YRS.items():
    hdr, rows, ws = t56(ed); m = t39(ed)
    for name, nth, stk, dvk in (('殺人', 1, ('殺人（既遂）', '殺人（未遂）'), ('殺人（既遂）', '殺人（未遂）')),
                                ('傷害', 0, ('傷害',), ('傷害',)), ('住居侵入', 0, ('住居侵入',), ('住居侵入',))):
        d = first(rows, name, nth) or first(rows, name, 0)
        mm = [v for k, v in m.items() if k.split()[-1] == name]
        mm = mm[nth] if len(mm) > nth else (mm[0] if mm else {})
        stv = sum(ST.get(k, {}).get(y, 0) for k in stk) if all(y in ST.get(k, {}) for k in stk) else ''
        dvv = sum(DV.get(k, {}).get(y, 0) for k in dvk) if all(y in DV.get(k, {}) for k in dvk) else ''
        haig = d.get('配偶者') if d.get('配偶者') is not None else d.get('配偶者(内縁含む)')
        row = [y, name, d.get('総数', d.get('計')), haig, d.get('元配偶者', ''), d.get('交際相手', ''), mm.get('痴情', ''), dvv, stv]
        fo.write('\t'.join(map(str, row)) + '\n'); print(' ', row)
fo.close()
