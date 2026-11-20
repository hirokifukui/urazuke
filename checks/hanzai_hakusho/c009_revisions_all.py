"""c009: 71版と72版の全時系列表で、同じ（表, シート, 列見出し, 西暦年）の値を比べ、遡及改訂を検出する。
西暦年セル（例 '2019年'）を持つ列を年の列とし、その上方の見出し行（年の列と同じ行の文字列群）で列を同定する。"""
import sys,os,re,glob,collections
sys.path.insert(0,'.')
from lib.xlsx import read_sheets
V72='data/raw/hanzai_hakusho/72'; V71=sorted(glob.glob('data/raw/hanzai_hakusho/71_*'))[-1]
YR=re.compile(r'^(\d{4})年$')
def norm(s): return re.sub(r'[（(][^）)]*[RHＲＨ][^）)]*[）)]|\s','',str(s))
def series(cells):
    """{(見出し, 年): 値} を返す。"""
    yc=collections.Counter()
    for (r,c),v in cells.items():
        if isinstance(v,str) and YR.match(v): yc[c]+=1
    if not yc: return {}
    col,n=yc.most_common(1)[0]
    if n<3: return {}
    rows=[r for (r,c),v in cells.items() if c==col and isinstance(v,str) and YR.match(v)]
    hr=min(rows)-1
    while hr>0 and not any(isinstance(cells.get((hr,c)),str) for c in range(col+1,col+60)): hr-=1
    hdr={}; seen=collections.Counter()
    for c in range(col+1,col+80):
        if cells.get((hr,c)) is None: continue
        g=cells.get((hr-1,c)); lab=(str(g)+'/' if isinstance(g,str) else '')+str(cells.get((hr,c)))
        seen[lab]+=1; hdr[c]=lab+('#%d'%seen[lab] if seen[lab]>1 else '')
    out={}
    for r in rows:
        y=YR.match(cells[(r,col)])[1]
        for c,h in hdr.items():
            v=cells.get((r,c))
            if isinstance(v,float): out[(h,y)]=v
    return out
res=[]; stats=collections.Counter()
for x72 in sorted(glob.glob(V72+'/zuhyo/*.xlsx')+glob.glob(V72+'/shiryo/*.xlsx')):
    fn=os.path.basename(x72); sub=os.path.basename(os.path.dirname(x72))
    x71=os.path.join(V71,sub,fn)
    if not os.path.exists(x71): stats['no71']+=1; continue
    A,B=read_sheets(x72),read_sheets(x71)
    Bn={norm(k):k for k in B}
    for sn,cells in A.items():
        s71=Bn.get(norm(sn))
        if not s71: continue
        a,b=series(cells),series(B[s71])
        common=set(a)&set(b)
        if not common: continue
        stats['tables']+=1; stats['cmp']+=len(common)
        for k in sorted(common, key=lambda t:(t[1],t[0])):
            va,vb=a[k],b[k]
            if abs(va-vb)>1e-6*max(1,abs(va)):
                res.append((fn,sn,k[0],k[1],vb,va))
with open('results/hanzai_hakusho/c009_revisions_all.tsv','w') as w:
    w.write('file\tsheet\tcolumn\tyear\tv71\tv72\n')
    for r in res: w.write('\t'.join(map(str,r))+'\n')
print(dict(stats),'changed',len(res))
g=collections.defaultdict(list)
for r in res: g[(r[0],r[1])].append(r)
for k,v in sorted(g.items(), key=lambda t:-len(t[1])):
    ys=sorted(set(r[3] for r in v)); cols=sorted(set(r[2] for r in v))
    print(len(v),k,'years',ys[0],'-',ys[-1],'cols',cols[:4], 'ex',v[0][2:])
