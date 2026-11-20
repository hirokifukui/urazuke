"""厚労省「医療観察法の入院対象者の状況」の過去の版（Internet Archive の写し、2014〜2026年）：
各版で (1) 男＋女＝合計（行ごと）、(2) ステージ別の和＝合計、(3) 疾病別の和＝ステージ別の合計、を確かめ、
基準日と合計の時系列を出す。基準日が同じで数値が違う版があれば挙げる。
"""
import re, glob, json, os, sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else '.'
files = sorted(glob.glob(os.path.join(ROOT, 'data/raw/iryokansatsu/wayback/nyuin_*.html'))) + [os.path.join(ROOT, 'data/raw/iryokansatsu/mhlw/nyuin.html')]


def text(f):
    b = open(f, 'rb').read()
    try:
        t = b.decode('utf-8')
    except UnicodeDecodeError:
        t = b.decode('cp932', errors='ignore')  # 2014〜2017年の写しは Shift_JIS
    s = re.sub(r'<[^>]+>', ' ', t)
    s = s.replace('&#160;', ' ').replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>')
    return re.sub(r'\s+', ' ', s)


def rows(seg):
    out = []
    for m in re.finditer(r'([^\d名]+?)\s*([\d,]+)\s*名\s*([\d,]+)\s*名\s*([\d,]+)\s*名', seg):
        out.append((m.group(1).strip(), *[int(x.replace(',', '')) for x in m.groups()[1:]]))
    return out


mism, nf, series = [], 0, {}
for f in files:
    s = text(f)
    d = re.search(r'（\s*([HR平令][^）]{1,14}?)現在\s*）', s)
    if not d:
        continue
    date = re.sub(r'\s', '', d.group(1))
    i = s.find('ステージ別'); j = s.find('疾病別'); k = s.find('疾病名は')
    if i < 0 or j < 0:
        continue
    st, ds = rows(s[i:j]), rows(s[j:k if k > 0 else j + 3000])
    if re.search(r'急性期\s*回復期\s*社会復帰期\s*[\d,]+\s*名', s[i:j]):  # 2014〜2016年の版：ステージの表が列ごと（男性3つ・女性3つ・合計3つ、続いて合計行）
        mm = re.search(r'急性期\s*回復期\s*社会復帰期\s*((?:[\d,]+\s*名\s*){9})合計\s*([\d,]+)\s*名\s*([\d,]+)\s*名\s*([\d,]+)\s*名', s[i:j])
        if mm:
            v = [int(x.replace(',', '')) for x in re.findall(r'[\d,]+', mm.group(1))]
            st = [(lab, v[n], v[3 + n], v[6 + n]) for n, lab in enumerate(('急性期', '回復期', '社会復帰期'))]
            st.append(('合計', *[int(mm.group(c).replace(',', '')) for c in (2, 3, 4)]))
    name = os.path.basename(f)
    for lab, m, w, t in st + ds:
        nf += 1
        if m + w != t:
            mism.append(dict(版=name, 基準日=date, 検査='男+女=合計', 行=lab, 値=[m, w, t]))
    body = [r for r in st if not r[0].endswith('合計')]
    tot = [r for r in st if r[0].endswith('合計')]
    if tot:
        T = tot[-1]
        for c in (1, 2, 3):
            nf += 1
            if sum(r[c] for r in body) != T[c]:
                mism.append(dict(版=name, 基準日=date, 検査='ステージの和=合計', 列=c, 和=sum(r[c] for r in body), 合計=T[c]))
        if ds:
            for c in (1, 2, 3):
                nf += 1
                if sum(r[c] for r in ds) != T[c]:
                    mism.append(dict(版=name, 基準日=date, 検査='疾病の和=合計', 列=c, 和=sum(r[c] for r in ds), 合計=T[c], 疾病の行数=len(ds)))
        series.setdefault(date, set()).add((T[1], T[2], T[3], name))
for date, v in series.items():
    vals = {x[:3] for x in v}
    if len(vals) > 1:
        mism.append(dict(検査='同じ基準日で値が違う', 基準日=date, 値=sorted(v)))
print(f'版 {len(files)}　基準日 {len(series)}　式 {nf}　不一致 {len(mism)}')
# 照合の要約（lib/tally.py）：単位は式。不一致はそのまま資料どうしの食い違いに数える。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_F = []; _nf = sum(1 for x in mism if isinstance(x, dict) and x.get('検査') in _F)
_t = Tally('iryokansatsu', 'c3003', note='医療観察法の入院対象者の状況（Wayback', script=__file__); _t.set(compared=nf, mismatched=len(mism) - _nf, read_failures=_nf); print('tally', _t.save())
for date in series:
    print('  ', date, sorted({x[:3] for x in series[date]}))
for m in mism:
    print(json.dumps(m, ensure_ascii=False, default=list))
