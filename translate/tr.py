"""英語版の訳文の保管と参照（日本語が正本、英語は訳）。

訳文は translate/en/<source>.json に、日本語の原文そのもの・その sha256・訳した時点の
原文のコミット・モデル・日付とともに置く。サイトの生成（site/build_site.py）は原文の sha256 で
訳文を引くだけで、生成の時に LLM を呼ばない。訳のない原文は translate/missing.json に書き出し、
translate/translate.py がそれを訳して保管する。同じ原文からは常に同じ英語のページができる。
"""
import json, os, hashlib, re, glob

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(R, 'translate', 'en')
MISSING = os.path.join(R, 'translate', 'missing.json')
GLOSSARY = os.path.join(R, 'translate', 'glossary.tsv')
MARK = '[translation pending]'


def sha(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def store_name(src):
    return re.sub(r'[^A-Za-z0-9._-]+', '__', src) + '.json'


def load_glossary():
    g = []
    for i, l in enumerate(open(GLOSSARY, encoding='utf-8')):
        if i == 0 or not l.strip():
            continue
        p = l.rstrip('\n').split('\t')
        g.append({'group': p[0], 'ja': p[1], 'en': p[2], 'note': p[3] if len(p) > 3 else ''})
    return g


GL = {x['ja']: x['en'] for x in load_glossary()}


class Store:
    def __init__(self):
        self.idx, self.missing, self.used = {}, [], set()
        for fn in glob.glob(os.path.join(D, '*.json')):
            for k, v in json.load(open(fn, encoding='utf-8'))['entries'].items():
                self.idx[k] = v['en']

    def t(self, ja, src, group=None):
        """原文 ja の訳。訳がなければ MARK を返し、missing に積む。"""
        if ja is None:
            return ''
        if not re.search(r'[぀-ヿ㐀-鿿]', ja):
            return ja  # 日本語を含まない（ID・数値・パス）はそのまま
        if ja in GL:
            return GL[ja]
        k = sha(ja)
        self.used.add(k)
        if k in self.idx:
            return self.idx[k]
        if not any(m['sha'] == k for m in self.missing):
            self.missing.append({'sha': k, 'ja': ja, 'src': src, 'group': group or src})
        return MARK

    def save_missing(self):
        json.dump(self.missing, open(MISSING, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        return len(self.missing)


def chunks(text, limit=2200):
    """Markdown を訳の単位に切る。表の途中・箇条の途中では切らない。決まった規則なので、同じ原文からは同じ切れ目になる。"""
    lines = text.split('\n')
    blocks, cur = [], []
    def push():
        if cur:
            blocks.append('\n'.join(cur)); cur.clear()
    for i, ln in enumerate(lines):
        prev = lines[i - 1] if i else ''
        in_tbl = ln.startswith('|') and prev.startswith('|')
        cont = re.match(r'^\s+\S', ln) and cur  # 入れ子の箇条は親と一緒
        if not in_tbl and not cont and (ln.startswith('#') or ln.strip() == '' or re.match(r'^[-*]\s|^\d+\.\s', ln) or (ln.startswith('|') and not prev.startswith('|'))):
            push()
        if ln.strip() == '':
            continue
        cur.append(ln)
    push()
    out, acc = [], ''
    for b in blocks:
        if acc and (len(acc) + len(b) > limit or b.startswith('#')):
            out.append(acc); acc = ''
        acc = (acc + '\n' + b) if acc else b
    if acc:
        out.append(acc)
    return out
