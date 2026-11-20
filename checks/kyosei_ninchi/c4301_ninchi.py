"""刑事施設の認知症：把握の所在と、令和6年版犯罪白書の訂正の反映を確かめる。
使い方: python checks/kyosei_ninchi/c4301_ninchi.py
出力: 標準出力（FINDINGS の数値の根拠）
"""
import glob, html, re, subprocess, sys
from pathlib import Path
import openpyxl

ROOT = Path.cwd() if (Path.cwd() / 'data/raw').is_dir() else Path(__file__).resolve().parents[2]
RAW = ROOT / 'data/raw'


def flat(s):
    return re.sub(r'\s+', '', s)


def pdftext(p):
    return subprocess.run(['pdftotext', '-layout', str(p), '-'], capture_output=True, text=True).stdout


def htmltext(paths):
    out = ''
    for f in sorted(paths):
        t = open(f, encoding='utf-8', errors='ignore').read()
        out += flat(html.unescape(re.sub(r'<[^>]+>', '', t)))
    return out


def part1_kyosei():
    print('## 1 矯正統計年報：認知症を含む表')
    hits = {}
    for f in sorted(glob.glob(str(RAW / 'kyosei/2025/*.xlsx'))):
        wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
        n = 0
        for ws in wb:
            for r in ws.iter_rows(values_only=True):
                if any(isinstance(c, str) and re.search('認知症|アルツハイマー', c) for c in r):
                    n += 1
        if n:
            hits[Path(f).name] = n
    print('2025 年の全', len(glob.glob(str(RAW / 'kyosei/2025/*.xlsx'))), 'ファイル中、認知症・アルツハイマーの行がある表:', hits)
    wb = openpyxl.load_workbook(RAW / 'kyosei/2025/25-00-37.xlsx', read_only=True, data_only=True)
    labels = sorted({c for ws in wb for r in ws.iter_rows(values_only=True) for c in r if isinstance(c, str) and len(c.strip()) < 20})
    print('第37表に「認知」を含む見出し:', [l for l in labels if '認知' in l])
    print('年次（第88表 休養患者・第93表 死亡者、男）')
    for y in range(2020, 2026):
        row = {}
        for t in ('88', '93'):
            p = RAW / f'kyosei/{y}/{str(y)[2:]}-00-{t}.xlsx'
            if not p.exists():
                continue
            wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
            for ws in wb:
                for r in ws.iter_rows(values_only=True):
                    s = [c for c in r if c is not None]
                    if s and isinstance(s[0], str) and re.search('認知症|アルツハイマー', s[0]):
                        row[(t, s[0].strip()[:6])] = s[2]
        print(y, row)


def part2_screening():
    print('## 2 認知症スクリーニング検査（白書の本文）')
    pat = re.compile(r'(\d,?\d{3}|\d{3})人に(?:対して検査|認知症スクリーニング検査等)を実施[^。]{0,80}?(?:診察を受けた者が(\d+)人、)?[^。]{0,40}?(\d+)人(?:が認知症の診断|であった)')
    for f in sorted(glob.glob(str(RAW / 'hanzai_hakusho/pdf/r0*_*.txt'))):
        t = flat(open(f).read()).replace('，', '、')
        for m in re.finditer(r'.{0,12}人に対して検査を実施.{0,90}', t):
            print('犯罪白書', Path(f).name[:3], m.group(0))
    for y in ('R04', 'R06', 'R07'):
        p = glob.glob(str(RAW / f'saihan/{y}/zentai_*.pdf'))[0]
        t = flat(pdftext(p))
        for m in re.finditer(r'.{0,40}人に認知症スクリーニング検査等を実施.{0,60}', t):
            print('再犯防止推進白書', y, m.group(0))
        if y == 'R04':
            i = t.find('特2-1-4刑事施設で認知症と診断を受けた者の数の推移', t.find('特2-1-4刑事施設で認知症') + 10)
            print('再犯防止推進白書 R04 特2-1-4', t[i:i + 200])


def part3_seigo():
    print('## 3 令和6年版犯罪白書の訂正（s_00140）の反映')
    H = htmltext(glob.glob(str(RAW / 'hanzai_hakusho/71_20261116T090659Z/honbun/*.html')))
    P = flat(open(glob.glob(str(RAW / 'hanzai_hakusho/pdf/r06_*.txt'))[0]).read())
    items = [('77頁 生調開始', '2万8,559人', '2万8,508人'), ('77頁 一部猶予', '1,325人', '1,323人'),
             ('80頁 仮釈放', '3,645人', '3,647人'), ('80頁 保護観察付', '5,964人', '5,962人'),
             ('88頁 中間処遇', '40人に対して実施', '34人に対して実施'), ('158頁 少年', '1万81人', '1万82人'),
             ('216頁 DV', '6万2,444件', '6万3,935件'), ('235頁 診察', '312人、認知症', '313人、認知症'),
             ('235頁 診断', '認知症と診断された者が125人', '認知症と診断された者が126人'),
             ('251頁 調査', '開始件数は、272件', '開始件数は、274件'),
             ('251頁 調整', '除く。）は199件', '除く。）は201件'), ('251頁 係属', '係属件数は776件', '係属件数は778件')]
    for k, g, c in items:
        print(f'{k:12s} Web本文 誤{H.count(g)} 正{H.count(c)} | PDF 誤{P.count(g)} 正{P.count(c)}')
    s = htmltext([RAW / 'hanzai_hakusho/seigohyo/s_00140.html'])
    print('訂正のお知らせに 312→313・125→126 があるか:', '誤医師による診察を受けた者が312人、認知症と診断された者が125人正医師による診察を受けた者が313人、認知症と診断された者が126人' in s)


if __name__ == '__main__':
    part1_kyosei(); part2_screening(); part3_seigo()
