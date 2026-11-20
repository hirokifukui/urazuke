"""警察庁「ストーカー事案…への対応状況」：ストーカー事案の検挙状況の表を版ごとに読み、
(1) 同じ年の値が版の間で一致するか（刑法犯等の計・殺人・傷害・住居侵入・規制法違反）、
(2) 刑法犯等の罪名の内訳の和＝計（読めた版のみ）、
(3) 検挙の数え方の注が版ごとにあるか：
    A 刑法犯等と規制法違反を同時に適用した場合を両方に含む（同時に適用）
    B 検挙した後にストーカー事案と判明したものを含む（判明したもの）
    C 規制法違反は同法違反で検挙した件数すべてを計上（件数すべて）
    D 令和5年までは基準年中に受理した相談のうち同年中に実施した検挙を計上（相談のうち）
    E 複数罪名は法定刑が最も重い罪名で計上（最も重い）
出力：results/stalker/c413_values.tsv, c413_notes.tsv
"""
import re, subprocess, unicodedata, sys, csv, io
from pathlib import Path
ROOT = Path.cwd() if (Path.cwd() / 'data/raw').is_dir() else Path(__file__).resolve().parents[2]
S = ROOT / 'data/raw/stalker'
OUT = ROOT / 'results/stalker'

ED = [  # 版, ファイル, 最終年
    ('H26', 'wayback/20150524041509_seianki26STDV.pdf', 2014),
    ('H27', 'wayback/20160528040909_seianki27STDV.pdf', 2015),
    ('H29', 'wayback/20190324035123_H29STDV_taioujoukyou_shousai.pdf', 2017),
    ('H30', 'wayback/20191218121023_H30taioujoukyou_shousai.pdf', 2018),
    ('R01', 'wayback/20200927010635_R1_STDVkouhoushiryou.pdf', 2019),
    ('R02', 'npa/R2_STDVkouhousiryou.pdf', 2020),
    ('R03', 'npa/R3_STDVRPkouhousiryou.pdf', 2021),
    ('R04', 'wayback/20230417003728_R4_STDVRPCAkouhousiryou.pdf', 2022),
    ('R05', 'npa/R5_STDVRPCAkouhousiryou_syuusei.pdf', 2023),
    ('R06', 'npa/R6_STDVRP_CA_kouhoushiryou.pdf', 2024),
    ('R07', 'npa/R7_STDVRPCA_kouhou.pdf', 2025),
]
# H26版だけ殺人は「未遂を含む」の1行
LAB = {
    '計': r'(?:刑法・特別法検挙|刑法犯・他の特別法犯|刑法犯・特別法犯)',
    '殺人既遂': r'殺人\(既遂\)', '殺人未遂': r'殺人\(未遂\)', '殺人計H26': r'殺人\(未遂を含む。\)',
    '傷害': r'傷害', '暴行': r'暴行', '脅迫': r'脅迫', '住居侵入': r'住居侵入',
    '規制法違反': r'ストーカー規制法違反(?:検挙)?',
}
KIDS = ['殺人既遂', '殺人未遂', '殺人計H26', '傷害', '暴行', '脅迫', '強要', '強制性交等', '不同意性交等',
        '強制わいせつ', '不同意わいせつ', '窃盗', '住居侵入', '器物損壊', '名誉毀損', '暴力行為等処罰法違反',
        '銃刀法違反', '軽犯罪法違反', '迷惑防止条例違反', 'その他', '逮捕監禁', '略取誘拐', '公務執行妨害', '恐喝', '放火']
NUM = r'((?:\s+[\d,]+){5})\s*$'
NOTES = {'A同時に適用': '同時に適用', 'B判明したもの': 'であることが判明したもの',
         'C件数すべて': '件数すべてを計上', 'D相談のうち': '受理した相談のうち', 'E最も重い': '法定刑が最も重い|最も法定刑が重い'}


def txt(p):
    return unicodedata.normalize('NFKC', subprocess.run(['pdftotext', '-layout', str(p), '-'], capture_output=True, text=True).stdout)


def section(t):
    """最初の「検挙状況」の表：計の行（行頭）から規制法違反の行まで"""
    L = t.splitlines()
    i0 = next(i for i, l in enumerate(L) if re.match(r'\s*' + LAB['計'] + NUM, unicodedata.normalize('NFKC', l)))
    i1 = next(i for i in range(i0, len(L)) if re.match(r'\s*' + LAB['規制法違反'] + NUM, L[i]))
    return L[i0:i1 + 1]


vals = {}  # (label, year) -> {ed: v}
rows_out = []; sums = []
for ed, f, y1 in ED:
    t = txt(S / f)
    years = list(range(y1 - 4, y1 + 1))
    sec = section(t)
    got = {}
    for l in sec:
        m = re.match(r'\s*(\S+)' + NUM, l)
        if not m: continue
        lab = m.group(1); v = [int(x.replace(',', '')) for x in m.group(2).split()]
        key = None
        for k, rx in LAB.items():
            if re.fullmatch(rx, lab): key = k; break
        if key is None:
            key = unicodedata.normalize('NFKC', lab)
        if key in got: continue
        got[key] = v
    for k, v in got.items():
        for y, x in zip(years, v):
            vals.setdefault((k, y), {})[ed] = x
            rows_out.append((ed, k, y, x))
    # 内訳の和
    kid = [k for k in got if k not in ('計', '規制法違反', 'ストーカー行為罪', '禁止命令等違反')]
    for j, y in enumerate(years):
        s = sum(got[k][j] for k in kid)
        sums.append((ed, y, got['計'][j], s, len(kid)))
    nt = re.sub(r'\s', '', t)
    notes = {k: len(re.findall(v, nt)) for k, v in NOTES.items()}
    print(ed, '読めた行', len(got), '注', notes)
    rows_out.append((ed, '_notes', y1, ';'.join(f'{k}={v}' for k, v in notes.items())))

OUT.mkdir(parents=True, exist_ok=True)
with open(OUT / 'c413_values.tsv', 'w') as fo:
    fo.write('edition\tlabel\tyear\tvalue\n')
    for r in rows_out: fo.write('\t'.join(map(str, r)) + '\n')

print('\n## (1) 版の間の一致（同じ年・同じ項目）')
ok = ng = 0
for (k, y), d in sorted(vals.items()):
    if len(d) < 2 or k not in ('計', '殺人既遂', '殺人未遂', '傷害', '住居侵入', '規制法違反'): continue
    if len(set(d.values())) == 1: ok += 1
    else: ng += 1; print('  食い違い', k, y, d)
print('  一致', ok, '食い違い', ng)

print('\n## (2) 内訳の和＝計')
ok2 = 0
for ed, y, tot, s, n in sums:
    if tot == s: ok2 += 1
    else: print('  不一致', ed, y, '計', tot, '内訳の和', s, '(行数', n, ')')
print('  一致', ok2, '/', len(sums))

print('\n## (3) 系列（各年の最新版の値）')
for k in ('計', '殺人計H26', '殺人既遂', '殺人未遂', '傷害', '住居侵入', '規制法違反'):
    ser = []
    for y in range(2010, 2026):
        d = vals.get((k, y))
        if d: ser.append(f'{y}:{d[max(d)]}')
    print(' ', k, ' '.join(ser))

# 照合の要約（lib/tally.py）：(1) 版の間の同じ年・同じ項目の値と、(2) 内訳の和＝計。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('stalker', 'c413', note='ストーカー事案の検挙状況の表：版の間の同じ年・同じ項目、内訳の和と計', script=__file__)
_t.set(compared=ok + ng + len(sums), mismatched=ng + (len(sums) - ok2)); print('tally', _t.save())
