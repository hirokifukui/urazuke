"""c201b: 「地域における自殺の基礎資料」の内部整合（L1）を平成28〜令和7年の10年分に広げた版。
c201 と同じ検査 (a)〜(f) を、見出しから列を割り出して行う（平成28〜令和3年は職業の列の構成が違うため）。
使い方: ~/.venvs/urazuke/bin/python checks/jisatsu/c201b_kiso_internal_10y.py"""
import sys,glob,re,collections,json
sys.path.insert(0,'.')
from lib.xls import read_sheets
K='data/raw/jisatsu/kiso'
Y={'h28':('h28_H28KAKUTEI-CHIIKI01','h28_H28KAKUTEI-CHIIKI02'),'h29':('h29_H29KAKUTEI-CHIIKI01','h29_H29KAKUTEI-CHIIKI02'),
   'h30':('h30_H30KAKUTEI-CHIIKI11','h30_H30KAKUTEI-CHIIKI22'),'r01':('r01_R1KAKUTEI-CHIIKI01','r01_R1KAKUTEI-CHIIKI02'),
   'r02':('r02_R2kakutei-CHIIKI01','r02_R2kakutei-CHIIKI02'),'r03':('r03_R3kakutei-CHIIKI01','r03_R3kakutei-CHIIKI022'),
   'r04':('r04_kakutei1','r04_kakutei2'),'r05':('r05_jisatsubi_001236396','r05_hakkenbi_001236400'),
   'r06':('r06_jisatsubi_001464821','r06_hakkenbi_001464823'),'r07':('r07_jisatsubi_001680831','r07_hakkenbi_001680832')}
def f(d,t):
    g=glob.glob(f'{K}/{d}/*_{t}表*.xls'); return g[0] if g else None
def num(v): return isinstance(v,float)
def norm(x): return re.sub(r'\s','',x) if isinstance(x,str) else x
def layout(s):
    lab={}; grp={}
    for r in range(1,9):
        for c in range(1,90):
            v=norm(s.get((r,c)))
            if not isinstance(v,str): continue
            if v in ('自殺者数','都道府県コード','自殺死亡率'): lab[v]=c
            for g in ('年齢','同居人の有無','職業','場所別','手段別','自殺の時間帯別','自殺の曜日別','原因・動機別','自殺未遂歴の有無'):
                if v.startswith(g): grp.setdefault(g,c)
            lab.setdefault(('L',c),[]).append(v)
    starts=sorted(grp.items(),key=lambda x:x[1]); G={}
    for i,(g,c) in enumerate(starts):
        end=starts[i+1][1]-1 if i+1<len(starts) else c+2
        G[g]=list(range(c,end+1))
    labels={c:v for k,v in lab.items() if isinstance(k,tuple) for c in [k[1]]}
    return lab,G,labels
issues=[]; st=collections.Counter()
def rows_of(s,codecol):
    R={}
    for r in range(4,90):
        v=s.get((r,codecol))
        if num(v): R[int(v)]=r
    return R
def check_pref(y,tag,path):
    S=read_sheets(path); names=list(S)[:3]; out={}
    for sn in names:
        s=S[sn]; lab,G,labels=layout(s); T=lab['自殺者数']; R=rows_of(s,lab['都道府県コード'])
        numcols=[T]+[c for g,cs in G.items() for c in cs]
        for c in numcols:
            nat=s.get((R.get(0,-1),c))
            if not num(nat): continue
            sm=sum(s.get((r,c)) for k,r in R.items() if k!=0 and num(s.get((r,c)))); st['a']+=1
            if abs(sm-nat)>0.5: issues.append((y,tag,sn,'(a)',c,nat,sm))
        occ=G.get('職業',[])
        def find(*names):
            for c in occ:
                if any(n in ''.join(labels.get(c,[])) for n in names): return c
        top=[c for c in occ if any(x in ''.join(labels.get(c,[])) for x in ('有職','自営業','被雇用'))]
        cmu=find('無職'); cfu=[c for c in occ if '不詳' in ''.join(labels.get(c,[]))]
        cgak=find('学生'); cmus=[c for c in occ if ''.join(labels.get(c,[]))=='無職者']
        sub=[c for c in occ if any(x in ''.join(labels.get(c,[])) for x in ('主婦','失業者','年金','その他の無職者'))]
        for k,r in R.items():
            TT=s.get((r,T))
            if not num(TT): continue
            for g,cs in G.items():
                if g in ('職業','原因・動機別'): continue
                v=[s.get((r,c)) for c in cs]
                if v and all(num(x) for x in v):
                    st['b']+=1
                    if abs(sum(v)-TT)>0.5: issues.append((y,tag,sn,'(b) '+g,s.get((r,3)),TT,sum(v)))
            try:
                tops=[s.get((r,c)) for c in top]+[s.get((r,cmu)),s.get((r,cfu[0]))]
                if all(num(x) for x in tops):
                    st['b']+=1
                    if abs(sum(tops)-TT)>0.5: issues.append((y,tag,sn,'(b) 職業 第1層',s.get((r,3)),TT,sum(tops)))
                a,b,m=s.get((r,cgak)),s.get((r,cmus[0])),s.get((r,cmu))
                if all(num(x) for x in (a,b,m)):
                    st['b']+=1
                    if abs(a+b-m)>0.5: issues.append((y,tag,sn,'(b) 学生+無職者≠無職',s.get((r,3)),m,a+b))
                ss=[s.get((r,c)) for c in sub]
                if all(num(x) for x in ss) and num(b):
                    st['b']+=1
                    if abs(sum(ss)-b)>0.5: issues.append((y,tag,sn,'(b) 無職者内訳',s.get((r,3)),b,sum(ss)))
            except Exception as e: issues.append((y,tag,sn,'職業の列が読めない',str(e)[:40])); break
        out[sn]=(s,lab,G,R)
    t,m,w=[out[n] for n in names]
    for k,r in t[3].items():
        for c in [t[1]['自殺者数']]+[c for cs in t[2].values() for c in cs]:
            a=t[0].get((r,c)); b=m[0].get((m[3].get(k,-1),c)); d=w[0].get((w[3].get(k,-1),c))
            if num(a) and num(b) and num(d):
                st['c']+=1
                if abs(a-b-d)>0.5: issues.append((y,tag,'(c) 総数≠男+女',k,c,a,b+d))
    pops={}
    for key,(s,lab,G,R) in zip('tmw',(t,m,w)):
        for k,r in R.items():
            T,rate=s.get((r,lab['自殺者数'])),s.get((r,lab['自殺死亡率']))
            if num(T) and num(rate) and rate>0: pops[(key,k)]=T/rate*1e5
    for k in t[3]:
        if all((x,k) in pops for x in 'tmw'):
            st['d']+=1; d=(pops[('m',k)]+pops[('w',k)])/pops[('t',k)]-1
            if abs(d)>0.005: issues.append((y,tag,'(d) 人口 男+女≠総数',k,round(d*100,2)))
    return t
def check_muni(y,tag,path,t):
    S=read_sheets(path); s=S[list(S)[0]]
    hr=[r for r in range(1,12) if any(norm(s.get((r,c)))=='市区町村コード' for c in range(1,6))]
    if not hr: issues.append((y,tag,'(e) 見出しなし')); return
    hr=hr[0]; cols={norm(s.get((hr,c))):c for c in range(1,10) if isinstance(s.get((hr,c)),str)}
    cc,cn,ct=cols['市区町村コード'],cols.get('市区町村名'),cols['自殺者数']
    agg=collections.Counter()
    for r in range(hr+1,max(r for r,c in s)+1):
        code,name,T=s.get((r,cc)),s.get((r,cn)),s.get((r,ct))
        if not num(code) or name is None: continue
        if num(T): agg[int(code)//10000]+=T
    ts,lab,G,R=t
    for k in range(1,48):
        P=ts.get((R.get(k,-1),lab['自殺者数'])); st['e']+=1
        if num(P) and abs(P-agg[k])>0.5: issues.append((y,tag,'(e) 市区町村和≠都道府県',k,P,agg[k]))
nat={}
for y,(a,b) in Y.items():
    for t5,t7,d in [('A5','A7',a),('A6','A8',a),('B5','B7',b),('B6','B8',b)]:
        p=f(d,t5)
        if not p: issues.append((y,t5,'missing')); continue
        try: t=check_pref(y,t5,p)
        except Exception as e: issues.append((y,t5,'error',str(e)[:80])); continue
        if t5=='B5': nat[y]=t[0].get((t[3][0],t[1]['自殺者数']))
        q=f(d,t7)
        if q:
            try: check_muni(y,t7,q,t)
            except Exception as e: issues.append((y,t7,'error',str(e)[:80]))
with open('results/jisatsu/c201b_kiso_internal_10y.tsv','w') as w:
    w.write(json.dumps(dict(st),ensure_ascii=False)+'\t'+json.dumps(nat)+'\n')
    for i in issues: w.write('\t'.join(map(str,i))+'\n')
print(dict(st)); print(nat); print('issues',len(issues))
c=collections.Counter((i[0],i[1],str(i[3])[:24] if len(i)>3 else i[2]) for i in issues)
for k,v in c.most_common(40): print(v,k)

# 照合の要約（lib/tally.py）：(a)〜(e) の比較した組。missing・error・見出しなしは読み取りの失敗。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('jisatsu', 'c201b', note='自殺の統計（地域における自殺の基礎資料）10年分：都道府県・市区町村の内訳の和と総数', script=__file__)
_f = sum(1 for i in issues if i[2] in ('missing', 'error') or '見出しなし' in str(i[2]))
_t.set(compared=sum(st.values()), mismatched=len(issues) - _f, read_failures=_f); print('tally', _t.save())
