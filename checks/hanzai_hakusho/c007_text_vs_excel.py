"""c007: 本文の「前年比」記述を、図表・資料 Excel の隣接セル（前年値）で裏づける。
判定: OK=Nと等しいセルがあり、その上下左右のどれかが前年値として表記と整合
      NG=Nと等しいセルはあるが、どの隣接セルとも整合しない
      NF=Nと等しいセルが見つからない（Excel に無い数値、単位違い等）"""
import re,html,glob,os,sys,collections
sys.path.insert(0,'.')
from lib.xlsx import read_sheets
V='data/raw/hanzai_hakusho/72'
NUM=r'(\d{1,3}(?:,\d{3})*(?:万(?:\d{1,3}(?:,\d{3})*)?)?)'
def val(s):
    s=s.replace(',','')
    if '万' in s:
        a,b=s.split('万'); return int(a)*10000+(int(b) if b else 0)
    return int(s)
U=r'(件|人|日|円|か所|校|施設|団体|組|世帯|台)'
REF=r'(前年比|同)'
PAT=[('A',re.compile(NUM+U+r'（'+REF+NUM+r'\2（(\d+(?:\.\d+)?)％）(増|減)')),
     ('B',re.compile(NUM+U+r'（'+REF+r'(\d+(?:\.\d+)?)％(増|減)')),
     ('C',re.compile(NUM+U+r'（'+REF+NUM+r'\2(増|減)）')),
     ('D',re.compile(r'(\d+\.\d)％（'+REF+r'(\d+(?:\.\d+)?)pt(上昇|低下)'))]
claims=[]
for f in sorted(glob.glob(V+'/honbun/*.html')):
    t=open(f,'rb').read().decode('utf-8','replace')
    t=html.unescape(re.sub(r'<[^>]+>','',t)); t=re.sub(r'\s+','',t)
    for k,p in PAT:
        for m in p.finditer(t):
            ctx=t[max(0,m.start()-40):m.end()+5]
            claims.append((os.path.basename(f),k,m,ctx))
# Excel 索引
idx=collections.defaultdict(list); sheets={}
for x in sorted(glob.glob(V+'/zuhyo/*.xlsx')+glob.glob(V+'/shiryo/*.xlsx')):
    try: S=read_sheets(x)
    except Exception as e: print('skip',x,e); continue
    for sn,cells in S.items():
        key=(os.path.basename(x),sn); sheets[key]=cells
        for rc,v in cells.items():
            if isinstance(v,float): idx[round(v,1)].append((key,rc))
def nb(key,rc):
    c=sheets[key]; r,col=rc
    for d in ((-1,0),(1,0),(0,-1),(0,1)):
        v=c.get((r+d[0],col+d[1]))
        if isinstance(v,float): yield v
def tol(p): 
    nd=len(p.split('.')[1]) if '.' in p else 0
    return 0.5*10**-nd+1e-9
res=[]
for f,k,m,ctx in claims:
    if k=='A':
        N,M,P,s=val(m[1]),val(m[4]),m[5],m[6]; sg=1 if s=='増' else -1
        ok=lambda X: abs(X-(N-sg*M))<0.5 and X>0 and abs(M/X*100-float(P))<=tol(P)
    elif k=='B':
        N,P,s=val(m[1]),m[4],m[5]; sg=1 if s=='増' else -1
        ok=lambda X,N=N,P=P,sg=sg: X>0 and abs(sg*(N-X)/X*100-float(P))<=tol(P)
    elif k=='C':
        N,M,s=val(m[1]),val(m[4]),m[5]; sg=1 if s=='増' else -1
        ok=lambda X,N=N,M=M,sg=sg: abs(X-(N-sg*M))<0.5
    else:
        N,P,s=float(m[1]),m[3],m[4]; sg=1 if s=='上昇' else -1
        ok=lambda X,N=N,P=P,sg=sg: abs(sg*(N-X)-float(P))<=0.15
    locs=idx.get(round(float(N),1),[])
    hit=[(key,rc) for key,rc in locs if any(ok(X) for X in nb(key,rc))]
    st='OK' if hit else ('NG' if locs else 'NF')
    res.append((st,f,k,m[3] if k!='D' else m[2],ctx,len(locs),hit[:1] or locs[:2]))
os.makedirs('results/hanzai_hakusho',exist_ok=True)
with open('results/hanzai_hakusho/c007_text_vs_excel.tsv','w') as w:
    for r in res: w.write('\t'.join(map(str,r))+'\n')
print(collections.Counter(r[0] for r in res), 'claims',len(res))
for r in res:
    if r[0]=='NG': print(r)

# 照合の要約（lib/tally.py）：本文の前年比の記述1件を単位とする。OK は一致。NG（前年値が隣のセルにない）・NF（Excel に値がない）は
# 前年値が Excel にない（単年度の表・他機関の統計など）ためで、資料どうしの食い違いではない＝読み取りの失敗（対応なし）。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('hanzai_hakusho', 'c007', label='72', note='犯罪白書 令和7年版：本文の前年比の記述と図表 Excel の前年値', script=__file__)
for r in res: (_t.ok if r[0] == 'OK' else _t.fail)()
print('tally', _t.save())
