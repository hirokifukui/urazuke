"""c011 (L4): 令和5年版(70)の各 Excel で「※閲覧用」と「※機械判読用」を照合する。
機械判読用の各データ行の数値の組 M について、閲覧用の全行から多重集合の一致数が最大の行 R を探す。
一致が過半数かつ全一致でない行を、食い違いとして記録する（値は整数なら完全一致、小数なら差0.05以内で一致とみなす）。"""
import sys,os,glob,collections
sys.path.insert(0,'.')
from lib.xlsx import read_sheets
V=sys.argv[1]
def rowvals(s):
    rows=collections.defaultdict(list)
    for (r,c),v in sorted(s.items()):
        if isinstance(v,float): rows[r].append(v)
    return rows
def inter(M,R):
    R=list(R); hit=[]; miss=[]
    for m in M:
        j=next((i for i,x in enumerate(R) if (abs(x-m)<0.5e-6 if m==int(m) else abs(x-m)<0.05)),None)
        if j is None: miss.append(m)
        else: hit.append(m); R.pop(j)
    return hit,miss
out=[]; st=collections.Counter()
for x in sorted(glob.glob(V+'/zuhyo/*.xlsx')+glob.glob(V+'/shiryo/*.xlsx')):
    try: S=read_sheets(x)
    except Exception: continue
    view=[s for n,s in S.items() if '閲覧用' in n]; mach=[(n,s) for n,s in S.items() if '機械判読' in n]
    if not view or not mach: st['no_pair']+=1; continue
    st['files']+=1
    VR=[]
    for s in view: VR+=list(rowvals(s).values())
    for n,s in mach:
        for r,M in rowvals(s).items():
            if len(M)<4: continue
            st['rows']+=1
            best=max(VR,key=lambda R: len(inter(M,R)[0])) if VR else []
            hit,miss=inter(M,best)
            if len(hit)==len(M): st['rows_ok']+=1; continue
            if len(hit)>=len(M)/2:
                st['rows_diff']+=1
                key=[s.get((r,c)) for c in (2,3) if isinstance(s.get((r,c)),str)]
                out.append((os.path.basename(x),n,r,'|'.join(key),len(M),len(hit),miss[:6]))
            else: st['rows_nomatch']+=1
with open('results/hanzai_hakusho/c011_view_vs_machine.tsv','w') as w:
    w.write(str(dict(st))+'\n')
    for o in out: w.write('\t'.join(map(str,o))+'\n')
print('done',dict(st))
