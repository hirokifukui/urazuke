"""平易版の数字の機械確認（2026-11-19、r43）。
python3 publish/plain/check.py      → publish/plain/CHECK.tsv（id・見つからない数字）
許す数字：記録の見出し・要旨・確実さ・原文の引用・言えること・照会の問い・作業ノートにある数字と、
平易版の中に式つきで書いた計算の結果（「X（a − b）」「（1 ÷ b）」など、a・b が許す数字のとき）。1桁の数は数えない。"""
import json, os, re, sys, unicodedata
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(ROOT)
F = {f['id']: f for f in json.load(open('publish/findings.json'))}
SRC = open('publish/build_inquiries.py').read()
CAN = {l.split('\t')[0]: l for l in open('publish/can_say.tsv') if '\t' in l}
NUM = re.compile(r'\d[\d,]*(?:\.\d+)?')


def norm(t): return unicodedata.normalize('NFKC', t)
def nums(t): return {n.replace(',', '').rstrip('.') for n in NUM.findall(norm(t))}


def flat(d):
    if isinstance(d, dict): return ' '.join(flat(v) for k, v in d.items() if k != 'id')
    if isinstance(d, list): return ' '.join(flat(x) for x in d)
    return str(d)


def allowed(f):
    t = ' '.join([f['見出し'], f['要旨'], f['確実さ'], CAN.get(f['id'], '')] + [q['文'] + ' ' + q['箇所'] + ' ' + q['ラベル'] for q in f.get('原文の引用', [])])
    m = re.search(r"'%s':'([^']*)'" % re.escape(f['id']), SRC); t += ' ' + (m.group(1) if m else '')
    if os.path.exists(f['根拠']): t += ' ' + open(f['根拠']).read()
    return nums(t)


def computed(text, ok):
    """式つきの計算の結果を許す数字に足す"""
    t = norm(text).replace('−', '-').replace('－', '-').replace('×', '*').replace('÷', '/')
    add = set()
    for m in re.finditer(r'(\d[\d,]*(?:\.\d+)?)\s*([-+*/])\s*(\d[\d,]*(?:\.\d+)?)', t):
        a, op, b = float(m.group(1).replace(',', '')), m.group(2), float(m.group(3).replace(',', ''))
        if m.group(1).replace(',', '') not in ok and m.group(1).replace(',', '') != '1': continue
        if m.group(3).replace(',', '') not in ok and m.group(3).replace(',', '') != '100': continue
        v = {'-': a - b, '+': a + b, '*': a * b, '/': a / b if b else 0}[op]
        for x in (v, v * 100, abs(v)):
            for nd in range(0, 4):
                s = f'{round(x, nd):.{nd}f}'; add.add(s); add.add(s.rstrip('0').rstrip('.') if '.' in s else s)
    return add


def check(i):
    d = json.load(open(f'publish/plain/drafts/{i}.json')); f = F[i]
    ok = allowed(f); text = flat(d); ok |= computed(text, ok)
    bad = sorted(n for n in nums(text) if len(n.split('.')[0]) > 1 and n not in ok and n.lstrip('0') not in ok)
    return bad


if __name__ == '__main__':
    out = []
    for i in sorted(F):
        if not os.path.exists(f'publish/plain/drafts/{i}.json'): continue
        b = check(i); out.append(f'{i}\t{" ".join(b)}')
        if b: print(i, b)
    open('publish/plain/CHECK.tsv', 'w').write('\n'.join(out) + '\n')
    print('checked', len(out), 'with problems', sum(1 for l in out if l.split('\t')[1]))
