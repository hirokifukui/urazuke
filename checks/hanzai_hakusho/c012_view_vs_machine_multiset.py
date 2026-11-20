"""c012 (L4, 改良版): 70版の各 Excel で、機械判読用シート群と閲覧用シート群の整数値(>=10)の出現回数を比べる。
機械判読用にだけ多く現れる値（閲覧用にない、または回数が多い）を列挙する。複製・転記ミスの検出を狙う。"""
import sys,os,glob,collections
sys.path.insert(0,'.')
from lib.xlsx import read_sheets
D=sorted(glob.glob('data/raw/hanzai_hakusho/70_*'))[-1]
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
with open('results/hanzai_hakusho/c012_view_vs_machine_multiset.tsv','w') as w:
    w.write(str(dict(st))+'\n')
    for o in out: w.write('\t'.join(map(str,o))+'\n')
print(dict(st))
for o in out[:40]: print(o[0],'extra',o[1],'/',o[2],o[3][:8],o[4][:2])
