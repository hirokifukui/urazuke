"""c201: 「地域における自殺の基礎資料」（厚労省）の内部整合（L1）。
対象：A5/A6/B5/B6（都道府県）、A7/A8/B7/B8（市区町村）、B1-4（全国）。年：令和4〜7年。
(a) 都道府県の和（1〜47と不明99）＝全国（率の列を除く全列）
(b) 各行で、項目群の和＝自殺者数（年齢・同居人・職業・場所・手段・時間帯・曜日・未遂歴）。原因・動機は重複計上のため「各値≦自殺者数」のみ
(c) 総数シート＝男シート＋女シート（数の列）
(d) 率から逆算した人口：男＋女＝総数（0.5%以内）、自殺日表と発見日表で同じ
(e) 市区町村の和（政令市の区を除く）＝都道府県（秘匿の有無を記録）
(f) B1（全国・職業別）の総数・男女＝B5 の全国
使い方: ~/.venvs/urazuke/bin/python checks/jisatsu/c201_kiso_internal.py"""
import sys,glob,os,re,collections,json
sys.path.insert(0,'.')
from lib.xls import read_sheets
K='data/raw/jisatsu/kiso'
YEARS={'r04':('r04_kakutei1','r04_kakutei2'),'r05':('r05_jisatsubi_001236396','r05_hakkenbi_001236400'),
       'r06':('r06_jisatsubi_001464821','r06_hakkenbi_001464823'),'r07':('r07_jisatsubi_001680831','r07_hakkenbi_001680832')}
def f(dirn,tag): 
    g=glob.glob(f'{K}/{dirn}/*_{tag}表*.xls'); return g[0] if g else None
GROUPS={'年齢':range(7,16),'同居':range(16,19),'場所':range(28,35),'手段':range(35,42),'時間帯':range(42,55),'曜日':range(55,63),'未遂':range(71,74)}
issues=[]; st=collections.Counter()
def num(v): return isinstance(v,float)
def pref_rows(s):
    rows={}
    for r in range(9,80):
        code=s.get((r,2))
        if num(code): rows[int(code)]=r
    return rows
def check_pref(year,tag,path):
    S=read_sheets(path); names=list(S)
    tot,m,w=[S[n] for n in names[:3]]
    mc=max(c for r,c in tot)
    out={}
    for sn,s in zip(names[:3],(tot,m,w)):
        R=pref_rows(s)
        if 0 not in R: issues.append((year,tag,sn,'no national row')); continue
        for c in [4]+list(range(7,mc+1)):
            nat=s.get((R[0],c))
            if not num(nat): continue
            sm=sum(s.get((r,c),0) for k,r in R.items() if k!=0 and num(s.get((r,c))))
            st['a']+=1
            if abs(sm-nat)>0.5: issues.append((year,tag,sn,'(a) pref sum≠national',s.get((8,c)),nat,sm))
        for k,r in R.items():
            T=s.get((r,4))
            if not num(T): continue
            for g,cols in GROUPS.items():
                vals=[s.get((r,c)) for c in cols]
                if all(num(v) for v in vals):
                    st['b']+=1
                    if abs(sum(vals)-T)>0.5: issues.append((year,tag,sn,f'(b) {g} sum≠total',s.get((r,3)),T,sum(vals)))
            occ=[s.get((r,c)) for c in range(19,28)]
            if all(num(v) for v in occ):
                yu,mu,gak,mus,shu,shitsu,nen,sono,fu=occ; st['b']+=3
                if abs(yu+mu+fu-T)>0.5: issues.append((year,tag,sn,'(b) 有職+無職+不詳≠total',s.get((r,3)),T,yu+mu+fu))
                if abs(gak+mus-mu)>0.5: issues.append((year,tag,sn,'(b) 学生+無職者≠無職',s.get((r,3)),mu,gak+mus))
                if abs(shu+shitsu+nen+sono-mus)>0.5: issues.append((year,tag,sn,'(b) 無職者内訳≠無職者',s.get((r,3)),mus,shu+shitsu+nen+sono))
            for c in range(63,71):
                v=s.get((r,c))
                if num(v):
                    st['b_cause']+=1
                    if v>T+0.5: issues.append((year,tag,sn,'(b) 原因>total',s.get((r,3)),T,v,s.get((8,c))))
        out[sn]=(R,s)
    # (c)
    (Rt,t),(Rm,mm),(Rw,ww)=[out[n] for n in names[:3]]
    for k,r in Rt.items():
        for c in [4]+list(range(7,mc+1)):
            a,b,d=t.get((r,c)),mm.get((Rm.get(k,-1),c)),ww.get((Rw.get(k,-1),c))
            if num(a) and num(b) and num(d):
                st['c']+=1
                if abs(a-b-d)>0.5: issues.append((year,tag,'総数≠男+女',t.get((r,3)),t.get((8,c)),a,b+d))
    # (d) 人口
    pops={}
    for key,(R,s) in zip(('t','m','w'),(out[n] for n in names[:3])):
        for k,r in R.items():
            T,rate=s.get((r,4)),s.get((r,5))
            if num(T) and num(rate) and rate>0: pops[(key,k)]=T/rate*1e5
    for k in Rt:
        if ('t',k) in pops and ('m',k) in pops and ('w',k) in pops:
            st['d']+=1; d=(pops[('m',k)]+pops[('w',k)])/pops[('t',k)]-1
            if abs(d)>0.005: issues.append((year,tag,'(d) 人口 男+女≠総数',t.get((Rt[k],3)),round(pops[('t',k)]),round(pops[('m',k)]+pops[('w',k)]),round(d*100,2)))
    return out,pops
def check_muni(year,tag,path,pref):
    S=read_sheets(path); names=list(S); s=S[names[0]]
    agg=collections.Counter(); supp=collections.Counter()
    for r in range(9,max(r for r,c in s)+1):
        code,name,detail,T=s.get((r,2)),s.get((r,3)),s.get((r,4)),s.get((r,5))
        if not num(code) or name is None: continue  # 政令市の区（詳細）を除く
        p=int(code)//10000  # 6桁の団体コード（検査数字を除く5桁を数値化）の上2桁が都道府県
        if num(T): agg[p]+=T
        else: supp[p]+=1
    R,ps=pref[names[0]] if names[0] in pref else list(pref.values())[0]
    for k in range(1,48):
        if k not in R: continue
        P=ps.get((R[k],4)); st['e']+=1
        if num(P) and abs(P-agg[k])>0.5:
            issues.append((year,tag,'(e) 市区町村和≠都道府県',ps.get((R[k],3)),P,agg[k],'秘匿セル数',supp[k]))
res={}
for y,(a,b) in YEARS.items():
    allpops={}
    for t5,t7,dirn in [('A5','A7',a),('A6','A8',a),('B5','B7',b),('B6','B8',b)]:
        p=f(dirn,t5)
        if not p: issues.append((y,t5,'missing')); continue
        out,pops=check_pref(y,t5,p); allpops[t5]=pops
        q=f(dirn,t7)
        if q: check_muni(y,t7,q,out)
    # 自殺日と発見日で人口が同じか
    for k in range(0,48):
        v=[allpops.get(t,{}).get(('t',k)) for t in ('A5','B5')]
        if all(v): 
            st['d2']+=1
            if abs(v[0]/v[1]-1)>0.001: issues.append((y,'(d) 人口 A5≠B5',k,round(v[0]),round(v[1])))
    # (f)
    p=f(b,'B1-4')
    if p:
        S=read_sheets(p); s=S['表1']; bt=read_sheets(f(b,'B5'))
        nat={sn:[x for (r,c),x in sh.items() if r>=9 and c==4 and num(sh.get((r,2))) and sh.get((r,2))==0.0][0] for sn,sh in bt.items()}
        b1=[s.get((5,5)),s.get((6,5)),s.get((7,5))]
        st['f']+=1
        if [round(x) for x in b1]!=[round(x) for x in list(nat.values())[:3]]: issues.append((y,'(f) B1≠B5全国',b1,list(nat.values())[:3]))
        res[y]={'B1':b1}
os.makedirs('results/jisatsu',exist_ok=True)
with open('results/jisatsu/c201_kiso_internal.tsv','w') as w:
    w.write(json.dumps(dict(st),ensure_ascii=False)+'\n')
    for i in issues: w.write('\t'.join(map(str,i))+'\n')
print(dict(st)); print('issues',len(issues)); print(res)
c=collections.Counter((i[0],i[1],str(i[3])[:20] if len(i)>3 else '') for i in issues)
for k,v in c.most_common(40): print(v,k)

# 照合の要約（lib/tally.py）：(a)〜(f) の式。(b) の「原因＞総数」は、原因・動機を1人につき最大4つまで計上するため照合の対象外
# （数にも食い違いにも入れない）。全国行・表のないものは読み取りの失敗。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('jisatsu', 'c201', note='自殺の統計（地域における自殺の基礎資料）令和6・7年：都道府県の和、内訳の和、男＋女、人口、市区町村の和', script=__file__)
_f = sum(1 for i in issues if any(str(x) in ('missing', 'no national row') for x in i))
_x = sum(1 for i in issues if any('原因>total' in str(x) for x in i))
_t.set(compared=sum(v for k, v in st.items() if k != 'b_cause'), mismatched=len(issues) - _f - _x, read_failures=_f); print('tally', _t.save())
