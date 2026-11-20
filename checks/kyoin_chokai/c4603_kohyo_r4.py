"""文科省 人事行政状況調査 令和4年度 資料2-6（令和5年11月1日現在）の「懲戒処分の公表」を教育委員会ごとに読み、
公表内容と公表の例外（公表を控える内容）の記述に含まれる語で数える。
列は pdftotext -layout の文字位置で分ける（見出し「(1)公表内容」「(2)公表の例外」の位置）。
出力：教育委員会ごとの判定の TSV（results/kyoin_chokai/c4603_kohyo_r4.tsv）と集計。
"""
import re, subprocess, unicodedata, csv
from pathlib import Path
ROOT = Path.cwd() if (Path.cwd() / 'data/raw').is_dir() else Path(__file__).resolve().parents[2]
P = ROOT / 'data/raw/kyoin_chokai/00007/20231222-mxt_syoto01-000033180_50.pdf'
import html as _h
xml = subprocess.run(['pdftotext', '-bbox', str(P), '-'], capture_output=True, text=True).stdout
boards = []
NAMES = re.compile(r'^(北海道|東京都|京都府|大阪府|.{1,3}県|.{1,4}市)$')
for pg in xml.split('<page ')[1:]:
    W = [(float(a), float(b), float(c), _h.unescape(d)) for a, b, c, d in re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="[\d.]+">(.*?)</word>', pg)]
    hdr = [w for w in W if w[3].startswith('(1)公表内容') or w[3].startswith('(2)公表の例外')]
    if not hdr:
        continue
    ytop = max(w[1] for w in hdr) + 3
    names = sorted([w for w in W if w[0] < 110 and NAMES.match(w[3]) and w[1] > ytop], key=lambda w: w[1])
    if not names:
        continue
    bounds = [ytop] + [(names[k][1] + names[k + 1][1]) / 2 for k in range(len(names) - 1)] + [10 ** 6]
    for k, nm in enumerate(names):
        ws = sorted([w for w in W if bounds[k] <= w[1] < bounds[k + 1]], key=lambda w: (round(w[1]), w[0]))
        boards.append(dict(no=len(boards) + 1, name=nm[3],
                           naiyo=''.join(w[3] for w in ws if 225 <= w[0] < 380),
                           reigai=''.join(w[3] for w in ws if w[0] >= 380)))


def has(s, *ws):
    s = unicodedata.normalize('NFKC', s).replace('・', '').replace(' ', '')
    return any(w in s for w in ws)


rows = []
for b in boards:
    n, r = b['naiyo'], b['reigai']
    rows.append(dict(
        no=b['no'], 教育委員会=b['name'],
        氏名を公表する場合の記載=has(n, '氏名'),
        例外の記載あり=len(r.replace('-', '').replace('―', '')) > 3,
        例外に被害者=has(r, '被害者', '被害を受けた'),
        例外に児童生徒=has(r, '児童生徒', '児童生徒等', '生徒', '児童'),
        例外にプライバシー等=has(r, 'プライバシー', '人権', '権利利益', '個人情報'),
        例外に教育的配慮=has(r, '教育的配慮', '教育上', '教育的な配慮'),
        例外で全部を公表しない=has(r, '全部又は一部', '全部もしくは一部', '全部若しくは一部', '公表しないことができる', '公表しない'),
        例外に性的事案の語=has(r, 'わいせつ', '性犯罪', '性暴力', 'セクシュアル', 'セクハラ', '性的'),
        公表内容に性的事案の語=has(n, 'わいせつ', '性犯罪', '性暴力', 'セクシュアル', 'セクハラ', '性的'),
        公表内容=n, 例外=r))
out = ROOT / 'results/kyoin_chokai/c4603_kohyo_r4.tsv'
with open(out, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter='\t'); w.writeheader(); w.writerows(rows)
print('教育委員会', len(rows), '（番号の連続', [r['no'] for r in rows] == list(range(1, len(rows) + 1)), '）')
for k in [k for k in rows[0] if k not in ('no', '教育委員会', '公表内容', '例外')]:
    print(f'  {k}: {sum(1 for r in rows if r[k])}')
both = [r['教育委員会'] for r in rows if r['例外に被害者'] and r['例外に児童生徒']]
print('  例外に「被害者」と「児童生徒」の両方:', len(both))
print('  例外に性的事案の語がある教育委員会:', [r['教育委員会'] for r in rows if r['例外に性的事案の語']])
print('  例外の記載がない教育委員会:', [r['教育委員会'] for r in rows if not r['例外の記載あり']])
