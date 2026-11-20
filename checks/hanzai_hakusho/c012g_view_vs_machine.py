"""c012g (L4): 指定した版の各 Excel で、機械判読用シート群と閲覧用シート群の整数値(>=10)の出現回数を比べる。
機械判読用にだけ多く現れる値（閲覧用にない、または回数が多い）を列挙する。複製・転記ミスの検出を狙う。"""
import sys,os,glob,collections
sys.path.insert(0,'.')
from lib.xlsx import read_sheets
D,TAG=sys.argv[1],sys.argv[2]
out=[]; st=collections.Counter()
for x in sorted(glob.glob(D+'/zuhyo/*.xlsx')+glob.glob(D+'/shiryo/*.xlsx')):
    try: S=read_sheets(x)
    except Exception: continue
    V=collections.Counter(); M=collections.Counter(); where=collections.defaultdict(list)
    for n,s in S.items():
        tgt = V if '閲覧用' in n else (M if '機械判読' in n else None)
        if tgt is None: continue
        for (r,c),v in s.items():
            if isinstance(v,float) and v==int(v) and v>=10:
                tgt[int(v)]+=1
                if tgt is M: where[int(v)].append((n,r,c))
    if not V or not M: continue
    st['files']+=1; st['mvals']+=sum(M.values())
    extra={k:M[k]-V.get(k,0) for k in M if M[k]>V.get(k,0)}
    if extra:
        st['files_with_extra']+=1; st['extra_vals']+=sum(extra.values())
        out.append((os.path.basename(x),sum(extra.values()),sum(M.values()),sorted(extra.items())[:12],[where[k][0] for k in sorted(extra)[:3]]))
out.sort(key=lambda o:-o[1])
with open(f'results/hanzai_hakusho/c012g_{TAG}.tsv','w') as w:
    w.write(str(dict(st))+'\n')
    for o in out: w.write('\t'.join(map(str,o))+'\n')
print(dict(st))
for o in out[:40]: print(o[0],'extra',o[1],'/',o[2],o[3][:8],o[4][:2])

# 照合の要約（lib/tally.py）：単位は、閲覧用と機械判読用の両方を持つ Excel ファイル。余分な値のないファイルは一致。
# 余分な値があるファイルのうち、作業ノートで資料の誤りと確かめたもの（2-2-3-2＝A4、5-4-4＝A1、4-7-2-3＝A2）は食い違い、それ以外（年のシートの数の違いなど）は読み取りの失敗。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_REAL = {'2-2-3-2.xlsx', '5-4-4.xlsx', '4-7-2-3.xlsx'}
_t = Tally('hanzai_hakusho', 'c012g', label=TAG, note='犯罪白書：同じ Excel の閲覧用シートと機械判読用シートの値の出現回数', script=__file__)
_ng = sum(1 for o in out if o[0] in _REAL); _fl = len(out) - _ng
_t.set(compared=st['files'] - _fl, mismatched=_ng, read_failures=_fl); print('tally', _t.save())
