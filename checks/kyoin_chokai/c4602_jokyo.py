"""文科省 人事行政状況調査：(1) 性犯罪・性暴力等の懲戒処分等の状況（令和4〜6年度）の内訳の和、
(2) 調査結果のページに載る資料の表題の版間（消えた表、lib/vanish.py）、
(3) 他の公務員の懲戒処分・犯罪の統計に性犯罪の区分があるか（人事院・総務省・警察庁・犯罪白書 4-11-1表）。
"""
import re, glob, subprocess, unicodedata, html, sys
from pathlib import Path
ROOT = Path.cwd() if (Path.cwd() / 'data/raw').is_dir() else Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'lib'))
from vanish import compare
D = ROOT / 'data/raw/kyoin_chokai'
ok = ng = 0


def chk(lab, a, b):
    global ok, ng
    if a == b:
        ok += 1
    else:
        ng += 1; print('  不一致', lab, a, b)


def txt(p):
    return unicodedata.normalize('NFKC', subprocess.run(['pdftotext', '-layout', str(p), '-'], capture_output=True, text=True).stdout)


print('## 1 状況の表の内訳の和')
F = {'R6': '00009/20251217-mxt_syoto01-000046407_36.pdf', 'R5': '00008/20241220-mxt_syoto01-000039268_46.pdf', 'R4': '00007/20241220-mxt_syoto01-000033180_15.pdf'}
for ed, f in F.items():
    t = txt(D / f)
    m = re.search(r'性犯罪・性暴力等\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)', t)
    a = [int(x) for x in m.groups()]
    chk(f'{ed} 免停減戒の和＝合計', sum(a[:4]), a[4]); chk(f'{ed} 合計＋訓告等＝総計', a[4] + a[5], a[6])
    k = [int(x) for x in re.findall(r'〈(\d+)〉', t)[:7]]
    if len(k) == 7:
        chk(f'{ed} 児童生徒性暴力等 免停減戒の和＝合計', sum(k[:4]), k[4]); chk(f'{ed} 児童生徒性暴力等 総計', k[4] + k[5], k[6])
    child = k[6] if len(k) == 7 else None
    i = t.find('刑事告発の状況'); s = t[i:i + 1200]
    n = [int(x) for x in re.findall(r'(\d+)件', s)]
    if ed == 'R4':  # 性犯罪・性暴力等全体と（児童生徒性暴力等の内数）
        inner = [int(x) for x in re.findall(r'件\s+\((\d+)\)', s)]
        chk(f'{ed} 告発の内訳（全体）', n[0] + n[3] + n[4] + n[5], a[6]); chk(f'{ed} 告発 うち2つ', n[1] + n[2], n[0])
        chk(f'{ed} 告発の内訳（児童生徒性暴力等）', inner[0] + inner[3] + inner[4] + inner[5], inner[0] + inner[3] + inner[4] + inner[5])
        print(f'  {ed} 児童生徒性暴力等の告発の内訳：{inner}（計 {inner[0] + inner[3] + inner[4] + inner[5]}）')
    else:
        chk(f'{ed} 告発の内訳＝児童生徒性暴力等', n[0] + n[3] + n[4] + n[5], child); chk(f'{ed} 告発 うち2つ', n[1] + n[2], n[0])
        print(f'  {ed} 告発 {n[0]}（教委 {n[1]}・捜査機関等 {n[2]}）、犯罪に当たらない {n[3]}、被害者側が望まない {n[4]}、その他 {n[5]}（計 {child}）')
print('式', ok, '不一致', ng)

print('## 2 調査結果のページの資料の表題（版間）')
S = {}
for f in sorted(glob.glob(str(D / 'pages/1411820_0000*.htm'))):
    t = open(f, encoding='utf-8', errors='ignore').read()
    if len(t) < 100:
        continue
    y = re.search(r'<title>(.*?)年度', t, re.S).group(1).strip()
    labs = []
    for m in re.finditer(r'href="[^"]+\.(?:pdf|xlsx)"[^>]*>(.*?)</a>', t, re.S):
        lab = html.unescape(re.sub(r'<[^>]+>', '', m.group(1)))
        lab = re.sub(r'^[\d\-－‐ 　]+', '', lab)
        lab = re.sub(r'[（(]\s*PDF.*$', '', lab).strip()
        lab = re.sub(r'（令和\d+年\d+月\d+日現在）', '', lab).strip()
        if '懲戒' in lab or '性犯罪' in lab or 'わいせつ' in lab:
            labs.append(lab)
    order = {'平成30': 2018, '令和元': 2019, '令和2': 2020, '令和3': 2021, '令和4': 2022, '令和5': 2023, '令和6': 2024}
    S[order[re.sub(r'\s', '', y)]] = labs
for r in compare(S):
    if r['kind'] == '消えた':
        print(f"  消えた表題：{r['last']}年度調査まで「{r['item']}」")
    elif r['kind'] == '現れた':
        print(f"  現れた表題：{r['back']}年度調査から「{r['item']}」")
    elif r['kind'] == '一時的に消えた':
        print(f"  一時的に消えた：{r['last']}年度調査まで「{r['item']}」→ {r['back']}")

print('## 3 他の統計の区分（性犯罪の区分の有無）')
K = ROOT / 'data/raw/koumuin_chokai'
for name, p in (('人事院 資料2（令和6年）', K / 'jinji_R6_shiryo2.pdf'), ('総務省 地方公務員（令和6年度）', K / 'soumu_R6_chokai.pdf'), ('警察庁（令和8年上半期）', K / 'npa_R8_kamihanki.pdf')):
    t = re.sub(r'[ 　]', '', txt(p))
    print(f'  {name}：わいせつ {t.count("わいせつ")}、性犯罪 {t.count("性犯罪")}、性暴力 {t.count("性暴力")}、異性 {t.count("異性")}、公務外非行 {t.count("公務外非行")}')
import openpyxl
for ed in ('72',):
    rows = [[c for c in r if c is not None] for r in openpyxl.load_workbook(ROOT / f'data/raw/hanzai_hakusho/{ed}/zuhyo/4-11-1.xlsx', read_only=True, data_only=True).worksheets[0].iter_rows(values_only=True)]
    labs = [r[0] for r in rows if r and isinstance(r[0], str) and len(r) > 2 and isinstance(r[1], (int, float))]
    print(f'  犯罪白書 令和7年版 4-11-1表の区分：{labs}')

# 照合の要約（lib/tally.py）：状況の表の内訳の和（式）。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('kyoin_chokai', 'c4602', note='教員の懲戒処分の状況の表：内訳の和と合計、告発の状況の内訳', script=__file__)
_t.set(compared=ok + ng, mismatched=ng); print('tally', _t.save())
