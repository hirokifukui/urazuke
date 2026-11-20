"""高齢の入所受刑者（窃盗を中心に）：矯正統計年報 第22表と犯罪白書 4-8-2-2図・4-8-2-3図を突き合わせる。
使い方: python checks/kyosei_ninchi/c4401_settou_korei.py
"""
import glob, re
from pathlib import Path
import openpyxl

ROOT = Path.cwd() if (Path.cwd() / 'data/raw').is_dir() else Path(__file__).resolve().parents[2]
RAW = ROOT / 'data/raw'
AGES = ['15歳以下', '16・17歳', '18・19歳', '20～24歳', '25～29歳', '30～34歳', '35～39歳', '40～44歳', '45～49歳',
        '50～54歳', '55～59歳', '60～64歳', '65～69歳', '70歳以上']
GRP = {'20歳未満': AGES[0:3], '20～29歳': AGES[3:5], '30～39歳': AGES[5:7], '40～49歳': AGES[7:9],
       '50～59歳': AGES[9:11], '60～64歳': [AGES[11]], '65～69歳': [AGES[12]], '70歳以上': [AGES[13]]}
nng = ok = 0


def chk(label, a, b):
    global nng, ok
    if a == b:
        ok += 1
    else:
        nng += 1
        print('  不一致', label, a, b)


def kyosei22(y):
    """{罪名: {列名: 男女計}}（その年の罪名別の部分）、内訳の和の照合も行う"""
    p = RAW / f'kyosei/{y}/{str(y)[2:]}-00-22.xlsx'
    rows = list(openpyxl.load_workbook(p, read_only=True, data_only=True).active.iter_rows(values_only=True))
    hdr = next(r for r in rows if r and '総数' in r and '70歳以上' in r)
    ci = {h: i for i, h in enumerate(hdr) if h in AGES + ['総数']}
    out, cur, started = {}, None, False
    for r in rows:
        lab = [c for c in r[:ci['総数']] if isinstance(c, str) and c.strip()]
        if not lab or not isinstance(r[ci['総数']], (int, float)):
            continue
        names = [c for c in lab if not re.fullmatch(r'[（(]?\s*[男女]', c.strip()) and c.strip() not in ('令和', '年', '平成')
                 and not re.fullmatch(r'\d+', c.strip())]
        if names and names[0] == '刑法犯':
            started = True
        if not started:
            if names and names[-1] == '総数':
                cur = '総数'
            if cur == '総数' and re.search(rf"(^|\D){int(str(y)[2:]) if y < 2019 else y - 2018}$", ''.join(str(c) for c in r[:3] if c is not None)):
                pass
            continue
        if names:
            cur = names[0].strip()
        d = out.setdefault(cur, {k: 0 for k in ci})
        for k, i in ci.items():
            d[k] += r[i] or 0
    for k, d in out.items():
        chk(f'{y} 第22表 {k} 年齢の和', sum(d[a] for a in AGES), d['総数'])
    # 年の総数（表の上の年次の部分の最後の年）
    tot = {k: 0 for k in ci}
    for r in rows:
        lab = [str(c) for c in r[:ci['総数']] if c is not None]
        if '総数' in lab and str(y - 2018) in lab and isinstance(r[ci['総数']], (int, float)):
            tot = {k: r[i] or 0 for k, i in ci.items()}
    out['__年の総数'] = tot
    return out


def hakusho_823(ed, sheet):
    ws = openpyxl.load_workbook(RAW / f'hanzai_hakusho/{ed}/zuhyo/4-8-2-3.xlsx', read_only=True, data_only=True)[sheet]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    hdr = next(r for r in rows if r and '罪名' in r)
    o = hdr.index('区分')
    out = {}
    for r in rows:
        r = r[o:]
        if len(r) > 2 and isinstance(r[2], (int, float)) and isinstance(r[1], str):
            out[(r[0], r[1])] = dict(zip(hdr[o + 2:], r[2:]))
    return out


print('## 1 第22表 内部（年齢の和＝総数）')
K = {y: kyosei22(y) for y in range(2020, 2026)}
print('式', ok, '不一致', nng)

print('## 2 犯罪白書 4-8-2-3図 と 第22表（窃盗・総数・刑法犯総数・詐欺・覚醒剤）')
MAP = {('総数', '総数'): '__年の総数', ('刑法犯', '窃盗'): '窃盗', ('刑法犯', '詐欺'): '詐欺',
       ('特別法犯', '覚醒剤取締法'): '覚醒剤取締法', ('刑法犯', '殺人'): '殺人', ('刑法犯', '放火'): '放火'}
for ed, sheet, y in ((72, '4-8-2-3図（R６）', 2024), (72, '4-8-2-3図（R５）', 2023)):
    H = hakusho_823(ed, sheet)
    for (a, b), d in H.items():
        s = sum(v for k, v in d.items() if k in GRP)
        chk(f'白書{ed} {sheet} {b} 年齢の和', s, d['総数'])
        if '65歳以上_男性' in d:
            chk(f'白書{ed} {sheet} {b} 65歳以上の男女', d['65歳以上_男性'] + d['65歳以上_女性'], d['65～69歳'] + d['70歳以上'])
    for key, kk in MAP.items():
        if key not in H:
            continue
        kd = K[y].get(kk)
        if not kd:
            print('  第22表に罪名なし', kk); continue
        for g, cols in GRP.items():
            chk(f'{y} {key[1]} {g} 白書{ed}↔第22表', H[key][g], sum(kd[c] for c in cols))
        chk(f'{y} {key[1]} 総数 白書{ed}↔第22表', H[key]['総数'], kd['総数'])
    print(sheet, '窃盗 65歳以上', H[('刑法犯', '窃盗')]['65～69歳'] + H[('刑法犯', '窃盗')]['70歳以上'],
          '/ 65歳以上の総数', H[('総数', '総数')]['65～69歳'] + H[('総数', '総数')]['70歳以上'])
print('式', ok, '不一致', nng)

print('## 3 犯罪白書 4-8-2-2図（入所受刑者の年齢層別）と第22表、版間')
def fig822(ed):
    wb = openpyxl.load_workbook(RAW / f'hanzai_hakusho/{ed}/zuhyo/4-8-2-2.xlsx', read_only=True, data_only=True)
    res = {}
    for sh in wb.sheetnames:
        rows = [list(r) for r in wb[sh].iter_rows(values_only=True)]
        hdr = next((r for r in rows if r and '総数' in r and '70歳以上' in r), None)
        if not hdr:
            continue
        o = next(i for i, c in enumerate(hdr) if isinstance(c, str) and '西暦' in c)
        for r in rows:
            v = r[o] if len(r) > o else None
            m = re.match(r'(\d{4})年', str(v)) if v is not None else None
            if m and r is not hdr:
                res[(sh, int(m.group(1)))] = {h: x for h, x in zip(hdr, r) if isinstance(h, str)}
    return res, wb.sheetnames
F72, sh72 = fig822(72)
print('4-8-2-2 シート', sh72, '列', list(next(iter(F72.values())).keys())[:10] if F72 else None)
for (sh, y), d in sorted(F72.items()):
    if y >= 2020 and '①' in sh:
        t = K[y]['__年の総数']
        for g, cols in GRP.items():
            chk(f'4-8-2-2 {y} {g} 白書72↔第22表', d.get(g), sum(t[c] for c in cols))
        chk(f'4-8-2-2 {y} 総数 白書72↔第22表', d.get('総数'), t['総数'])
for (sh, y), d in sorted(F72.items()):
    if isinstance(d.get('高齢者率'), (int, float)) and d.get('総数'):
        chk(f'4-8-2-2 {sh} {y} 高齢者率の再計算', round(d['高齢者率'], 1), round((d['65～69歳'] + d['70歳以上']) / d['総数'] * 100, 1))
        chk(f'4-8-2-2 {sh} {y} 年齢の和', sum(d[g] for g in GRP), d['総数'])
def load_ts(f, sh):
    rows = [list(r) for r in openpyxl.load_workbook(RAW / 'hanzai_hakusho' / f, read_only=True, data_only=True)[sh].iter_rows(values_only=True)]
    hdr = next(r for r in rows if r and '総数' in r)
    o = hdr.index('総数')
    out = {}
    for r in rows:
        y = next((m.group(1) for c in r[:o] if c is not None for m in [re.match(r'(\d{4})年', str(c))] if m), None)
        if y:
            out[int(y)] = dict(zip(hdr[o:], r[o:]))
    return out
print('## 4 4-8-2-2図（総数）の版間：令和5年版の「50～64歳」と令和6・7年版の「50～59歳」＋「60～64歳」')
A = load_ts('70_20261116T073025Z/zuhyo/4-8-2-2.xlsx', '4-8-2-2図（総数）※機械判読用')
for ed, f, sh in (('令和6年版', '71_20261116T090659Z/zuhyo/4-8-2-2.xlsx', '4-8-2-2図（総数）'), ('令和7年版', '72/zuhyo/4-8-2-2.xlsx', '4-8-2-2図①')):
    B = load_ts(f, sh)
    for y in sorted(A):
        if y in B:
            chk(f'{ed} {y} 50～64歳', A[y]['50～64歳'], B[y]['50～59歳'] + B[y]['60～64歳'])
            for k in ('総数', '20歳未満', '20～29歳', '30～39歳', '40～49歳', '65～69歳', '70歳以上'):
                chk(f'{ed} {y} {k}', A[y][k], B[y][k])
print('式', ok, '不一致', nng)

# 照合の要約（lib/tally.py）：単位は式。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('kyosei_ninchi', 'c4401', note='矯正統計 第22表と犯罪白書 4-8-2-2図・4-8-2-3図：年齢の和、高齢者率、版間', script=__file__)
_t.set(compared=ok + nng, mismatched=nng, read_failures=0, explained=None); print('tally', _t.save())
