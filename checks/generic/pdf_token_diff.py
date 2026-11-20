"""2つの PDF（差し替え前・後）の本文を語の並びで比べ、変わった箇所を前後の文脈つきで出す。
使い方: python pdf_token_diff.py OLD.pdf NEW.pdf [文脈語数=6]
数字の変化だけを見たいときは環境変数 NUMONLY=1。"""
import sys, os, subprocess, difflib, re
def toks(p):
    t = subprocess.run(['pdftotext', '-layout', p, '-'], capture_output=True, text=True).stdout
    return t.split()
a, b = toks(sys.argv[1]), toks(sys.argv[2])
ctx = int(sys.argv[3]) if len(sys.argv) > 3 else 6
numonly = os.environ.get('NUMONLY') == '1'
pg = lambda x: len(x)
print(f'tokens old={len(a)} new={len(b)}')
n = 0
for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
    if op == 'equal':
        continue
    old, new = ' '.join(a[i1:i2]), ' '.join(b[j1:j2])
    if numonly and not (re.search(r'\d', old + new)):
        continue
    n += 1
    print(f'[{op}] …{" ".join(a[max(0,i1-ctx):i1])} ⟦{old}⟧→⟦{new}⟧ {" ".join(a[i2:i2+ctx])}…')
print('changes', n)
