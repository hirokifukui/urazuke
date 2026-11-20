"""c008: c007 で NG/NF の記述を、前年版(71)の同じ表・同じセル位置で裏づける。
72 の値 N の位置 (ファイル, シート, 行, 列) と同名ファイルの 71 版シートで、同じ位置の値 X を前年値とみなす。
X が表記と整合すれば OK71。71 の同位置に数値がなければ不明。"""
import sys,os,re,ast,glob,collections
sys.path.insert(0,'.')
from lib.xlsx import read_sheets
exec(open('checks/hanzai_hakusho/c007_text_vs_excel.py').read().split('# Excel 索引')[0])  # claims, val, PAT
V72='data/raw/hanzai_hakusho/72'; V71='data/raw/hanzai_hakusho/71_20261116T070137Z'
def load(v):
    d={}
    for x in glob.glob(v+'/zuhyo/*.xlsx')+glob.glob(v+'/shiryo/*.xlsx'):
        try: d[os.path.basename(x)]=read_sheets(x)
        except Exception: pass
    return d
A,B=load(V72),load(V71)
def norm(s): return re.sub(r'[（(].*?[)）]|\s','',s)
def tol(p):
    nd=len(p.split('.')[1]) if '.' in p else 0
    return 0.5*10**-nd+1e-9
prev={r.split('\t')[4]:r.split('\t')[0] for r in open('results/hanzai_hakusho/c007_text_vs_excel.tsv')}
out=collections.Counter(); lines=[]
for f,k,m,ctx in claims:
    if prev.get(ctx)=='OK': continue
    if k=='A': N,M,P,s=val(m[1]),val(m[4]),m[5],m[6]
    elif k=='B': N,M,P,s=val(m[1]),None,m[4],m[5]
    elif k=='C': N,M,P,s=val(m[1]),val(m[4]),None,m[5]
    else: N,M,P,s=float(m[1]),None,m[3],m[4]
    sg=1 if s in('増','上昇') else -1
    def ok(X):
        if k=='A': return abs(X-(N-sg*M))<0.5 and abs(M/X*100-float(P))<=tol(P)
        if k=='B': return X>0 and abs(sg*(N-X)/X*100-float(P))<=tol(P)
        if k=='C': return abs(X-(N-sg*M))<0.5
        return abs(sg*(N-X)-float(P))<=0.15
    st='NOPOS'; info=''
    for fn,S in A.items():
        for sn,cells in S.items():
            for rc,v in cells.items():
                if isinstance(v,float) and abs(v-N)<0.05 and fn in B:
                    # 71 の対応シート: 名前を正規化して一致、なければ同じ順番
                    cand=[s2 for s2 in B[fn] if norm(s2)==norm(sn)] or list(B[fn])[list(S).index(sn):list(S).index(sn)+1]
                    for s2 in cand:
                        X=B[fn][s2].get(rc)
                        if isinstance(X,float):
                            if ok(X): st='OK71'; info=f'{fn}|{sn}|{rc}|X={X}'; break
                            elif st!='OK71': st='MISMATCH'; info=info or f'{fn}|{sn}|{rc}|X={X}'
                    if st=='OK71': break
            if st=='OK71': break
        if st=='OK71': break
    out[st]+=1; lines.append((st,f,ctx,info))
with open('results/hanzai_hakusho/c008_prev_edition.tsv','w') as w:
    for l in lines: w.write('\t'.join(l)+'\n')
print(out)
for l in lines:
    if l[0]!='OK71': print(l)
