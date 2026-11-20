"""PDF のテキスト（pdftotext -layout）から「01 北海道 … 47 沖縄県」「00 全国（または 計・合計）」の表を拾い、
数の列（小数点・％を含まない列）について都道府県の和＝全国を確かめる（L1）。
blocks(path) -> [(開始行, 列数, [(コード, 名前, 値の並び)], 全国の値の並び)]"""
import re
PREF = '北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 群馬県 埼玉県 千葉県 東京都 神奈川県 新潟県 富山県 石川県 福井県 山梨県 長野県 岐阜県 静岡県 愛知県 三重県 滋賀県 京都府 大阪府 兵庫県 奈良県 和歌山県 鳥取県 島根県 岡山県 広島県 山口県 徳島県 香川県 愛媛県 高知県 福岡県 佐賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県'.split()
TOK = re.compile(r'[-－‐]|[\d,]+(?:\.\d+)?%?|…|･|・|\*+|x|X|－')
def parse_line(l):
    m = re.match(r'^\s*(\d{2})?\s*(' + '|'.join(PREF + ['全国', '全 国', '計', '合計']) + r')\s+(.*)$', l)
    if not m: return None
    name = m[2].replace(' ', ''); rest = m[3]
    toks = rest.split()
    if not toks: return None
    vals = []
    for t in toks:
        t2 = t.replace(',', '')
        if re.fullmatch(r'-?\d+', t2): vals.append(int(t2))
        elif re.fullmatch(r'-?\d+\.\d+%?|\d+%', t2): vals.append(('rate', t2))
        elif t2 in ('-', '－', '‐', '…', '―', '—'): vals.append(0)
        else: return (name, None)
    return (name, vals)
def blocks(path):
    L = open(path, encoding='utf-8', errors='replace').read().split('\n')
    out = []; cur = []; start = None
    for i, l in enumerate(L):
        p = parse_line(l)
        if p and p[1] is not None and p[0] in PREF:
            if p[0] == '北海道': cur = []; start = i
            cur.append(p)
        elif p and p[1] is not None and p[0] in ('全国', '計', '合計') and len(cur) == 47:
            out.append((start + 1, cur, p[1])); cur = []
        elif p and p[0] in PREF:
            cur = []
    return out
def check(path):
    res = []; n = 0
    for start, rows, nat in blocks(path):
        w = len(nat)
        if any(len(v) != w for _, v in rows): res.append(('列数不一致', start)); continue
        for c in range(w):
            if isinstance(nat[c], tuple) or any(isinstance(v[c], tuple) for _, v in rows): continue
            s = sum(v[c] for _, v in rows); n += 1
            if s != nat[c]: res.append(('都道府県の和≠全国', start, c + 1, s, nat[c]))
    return n, res, len(blocks(path))
