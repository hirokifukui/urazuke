"""矯正統計年報：版（年）の間で消えた表・区分を拾う（lib/vanish.py）。
(1) 表の一覧（LIST_2006〜2025）の表題
(2) 4つの表（精神診断、休養患者の病名別 年齢（既決）、死亡者の病名別 年齢、新受刑者の罪名別 年齢）の見出し（文字のセル）
表題の言い換え（読点の違いなど）を除くため、消えた表題と同じ年に現れた表題の似かより（difflib 0.6 以上）を「名称の変更」とする。
"""
import re, sys, glob, difflib
from pathlib import Path
ROOT = Path.cwd() if (Path.cwd() / 'data/raw').is_dir() else Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'lib'))
from vanish import compare, norm
K = ROOT / 'data/raw/kyosei'


def lists():
    S, NO = {}, {}
    for y in range(2006, 2026):
        S[y] = []
        for l in open(K / f'LIST_{y}.txt'):
            if '|' in l:
                no, t = [x.strip() for x in l.split('|')[:2]]
                S[y].append(t); NO[(y, norm(t))] = no
    return S, NO


def pair(res):
    gone = [r for r in res if r['kind'] == '消えた']
    new = [r for r in res if r['kind'] == '現れた']
    out = []
    for g in gone:
        cands = [(difflib.SequenceMatcher(None, norm(g['item']), norm(n['item'])).ratio(), n) for n in new if n['back'] == g['first_missing']]
        best = max(cands, key=lambda x: x[0], default=(0, None))
        out.append((g, best[1] if best[0] >= 0.6 else None, round(best[0], 2)))
    return out


def labels(path):
    vals = []
    if open(path, 'rb').read(2) != b'PK':  # 拡張子でなく中身で判定
        import xlrd
        wb = xlrd.open_workbook(str(path))
        for sh in wb.sheets():
            for r in range(sh.nrows):
                vals += [sh.cell_value(r, c) for c in range(sh.ncols)]
    else:
        import openpyxl, shutil, tempfile
        if str(path).endswith('.xls'):  # 中身が xlsx の .xls
            tmp = Path(tempfile.mkdtemp()) / 'x.xlsx'; shutil.copy(path, tmp); path = tmp
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        for ws in wb:
            for row in ws.iter_rows(values_only=True):
                vals += list(row)
    out = set()
    for v in vals:
        if isinstance(v, str):
            s = norm(v).strip('（）()')
            if 1 < len(s) <= 40 and not re.fullmatch(r'[0-9,.\-－…年月日令和平成男女総数計（）()]+', s) and not s.startswith('注'):
                out.add(s)
    return out


TARGET = {'精神診断': r'精神診断', '休養患者（既決）': r'休養患者の病名別 年齢（既決', '死亡者': r'死亡者の病名別 年齢', '罪名別 年齢': r'新受刑者の罪名別 年齢$'}

if __name__ == '__main__':
    S, NO = lists()
    print('## 1 表の一覧（2006〜2025年）')
    for g, n, r in pair(compare(S)):
        if n:
            continue
        print(f"  消えた表：{g['last']}年まで「{g['item']}」（{NO.get((g['last'], norm(g['item'])))}）")
    print('## 2 表の見出し（区分）')
    for name, pat in TARGET.items():
        sets = {}
        for y in range(2006, 2026):
            for l in open(K / f'LIST_{y}.txt'):
                if '|' in l and re.search(pat, l.split('|')[1].strip()) and '外国人' not in l:
                    no = l.split('|')[0].strip()
                    f = [p for p in (K / f'{y}/{no}.xlsx', K / f'{y}/{no}.xls') if p.exists()]
                    if f:
                        sets[y] = labels(f[0])
        res = compare(sets)
        print(f'### {name}（{min(sets)}〜{max(sets)}年、{len(sets)}版）')
        for r in res:
            if r['kind'] == '消えた':
                print(f"  消えた区分：{r['last']}年まで「{r['item']}」")
            elif r['kind'] == '一時的に消えた':
                print(f"  一時的に消えた：{r['last']}年まで「{r['item']}」→ {r['back']}年に戻る")
        for r in res:
            if r['kind'] == '現れた':
                print(f"  現れた区分：{r['back']}年から「{r['item']}」")
