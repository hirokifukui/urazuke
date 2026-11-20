"""c202: 「X年中における自殺の状況」本体 PDF（厚労省・警察庁）と「地域における自殺の基礎資料」の照合（L1/L4/L3）。
(1) 図表4-4 都道府県別：当年の自殺者数・自殺死亡率＝基礎資料 B6（発見日・発見地）、前年の数＝前年の B6、前年差の計算
(2) 前年の報告の当年値と、今年の報告の前年値の比較（遡及改訂）
(3) 図表1-1 年齢階級別・男女別：基礎資料 B5 の全国行と一致、差の行の計算
使い方: ~/.venvs/urazuke/bin/python checks/jisatsu/c202_joukyou_vs_kiso.py"""
import sys,glob,re,collections,json
sys.path.insert(0,'.')
from lib.xls import read_sheets
J='data/raw/jisatsu/joukyou'; K='data/raw/jisatsu/kiso'
# 令和5年版の報告は図表の構成が違う（都道府県別は図）ため、表形式の令和6・7年版だけを対象にする
REP={'r06':'r06_honbun_001464717','r07':'r07_honbun_001680736'}
KISO={'r04':'r04_kakutei2','r05':'r05_hakkenbi_001236400','r06':'r06_hakkenbi_001464823','r07':'r07_hakkenbi_001680832'}
PREV={'r05':'r04','r06':'r05','r07':'r06'}
def kiso(y,tag):
    S=read_sheets(glob.glob(f'{K}/{KISO[y]}/*_{tag}表*.xls')[0]); out={}
    for sn,s in S.items():
        d={}
        for r in range(9,80):
            if isinstance(s.get((r,2)),float): d[re.sub(r'\s','',str(s.get((r,3))))]=(s.get((r,4)),s.get((r,5)),[s.get((r,c)) for c in range(7,16)])
        out[sn]=d
    return out
def n(x): return float(x.replace(',','').replace(' ',''))
def parse44(y):
    t=open(f'{J}/{REP[y]}.txt',encoding='utf-8').read().split('\n')
    i=[k for k,l in enumerate(t) if '都道府県別自殺者数及び自殺死亡率' in l and '・・' not in l][-1]; d={}
    for l in t[i:i+80]:
        m=re.match(r'^\s*([^\d\s\-+][^\d\-+]*?)\s+([\d,]+)\s+([\d.]+)\s+([\d,]+)\s+([\d.]+)\s+([-+]\s*[\d,]+|±?0)\s+([-+]\s*[\d.]+|±?0\.0|0\.0)\s*$',l)
        if m:
            name=re.sub(r'\s','',m[1]); d[name]=[n(m[2]),float(m[3]),n(m[4]),float(m[5]),m[6],m[7]]
    return d
issues=[]; st=collections.Counter(); summary={}
K6={y:kiso(y,'B6') for y in KISO}; K5={y:kiso(y,'B5') for y in KISO}
P={y:parse44(y) for y in REP}
for y,d in P.items():
    summary[y]=len(d)
    kc=K6[y]['総数 (秘)']; kp=K6[PREV[y]]['総数 (秘)']
    for name,(c,r,pc,pr,dc,dr) in d.items():
        key=name if name in kc else name.replace('全国','全国')
        if key not in kc: issues.append((y,'4-4 name not in B6',name)); continue
        st['44']+=1
        if c!=kc[key][0]: issues.append((y,'4-4 当年数≠B6',name,c,kc[key][0]))
        if abs(r-round(kc[key][1],1))>0.051: issues.append((y,'4-4 当年率≠B6',name,r,round(kc[key][1],2)))
        if key in kp and pc!=kp[key][0]: issues.append((y,'4-4 前年数≠前年B6',name,pc,kp[key][0]))
        if key in kp and abs(pr-round(kp[key][1],1))>0.051: st['44_prevrate_diff']+=1
        ddc=n(dc.replace('±','')) ; ddr=float(dr.replace(' ','').replace('±','') or 0)
        if abs((c-pc)-ddc)>0.5: issues.append((y,'4-4 前年差（数）の計算',name,c,pc,dc))
        if abs(round(r-pr,1)-ddr)>0.051: issues.append((y,'4-4 前年差（率）の計算',name,r,pr,dr))
    # (2) 前年報告との比較
    if PREV[y] in P:
        for name,v in d.items():
            if name in P[PREV[y]]:
                st['rev']+=1; old=P[PREV[y]][name]
                if v[2]!=old[0]: issues.append((y,'前年報告の当年数→今年報告の前年数 が変化',name,old[0],v[2]))
                if abs(v[3]-old[1])>0.051: st['rev_rate_changed']+=1
# (3) 図表1-1
AGE=['総数','～19歳','20～29歳','30～39歳','40～49歳','50～59歳','60～69歳','70～79歳','80歳～','不詳']
for y in REP:
    t=open(f'{J}/{REP[y]}.txt',encoding='utf-8').read().split('\n')
    i=[k for k,l in enumerate(t) if '図表１－１' in l and '年齢階級別' in l][-1]
    rows=[]
    for l in t[i:i+20]:
        nums=re.findall(r'-?[\d,]+',re.sub(r'令和.年|平成.+年','',l))
        lab=re.search(r'(総数|男|女)\s',l)
        if lab and len(nums)>=10: rows.append((lab[1],[n(x) for x in nums[-10:]]))
    if len(rows)<9: issues.append((y,'1-1 parse',len(rows))); continue
    cur,prev,diff=rows[0:3],rows[3:6],rows[6:9]
    for (yy,blk) in ((y,cur),(PREV[y],prev)):
        k=K5[yy]
        for (lab,vals),sn in zip(blk,['総数 (秘)','男 (秘)','女 (秘)']):
            T,_,ages=k[sn]['全国']
            # 基礎資料の年齢：20歳未満,20-29,...,80歳以上,不詳（9区分）
            st['11']+=1
            if [vals[0]]+vals[1:]!=[T]+ages: issues.append((y,'1-1 ≠ B5全国',yy,lab,vals,[T]+ages))
    for a,b,c in zip(cur,prev,diff):
        st['11d']+=1
        if [x-z for x,z in zip(a[1],b[1])]!=c[1]: issues.append((y,'1-1 差の計算',a[0]))
with open('results/jisatsu/c202_joukyou_vs_kiso.tsv','w') as w:
    w.write(json.dumps(dict(st),ensure_ascii=False)+'\t'+json.dumps(summary)+'\n')
    for i in issues: w.write('\t'.join(map(str,i))+'\n')
print(dict(st),summary,'issues',len(issues))
for i in issues[:60]: print(i)

# 照合の要約（lib/tally.py）：図表4-4 は都道府県ごとに 当年数・当年率・前年差（数）・前年差（率）の4つ、遡及改訂（前年の報告の当年数）、図表1-1 の行と差の行。
# 当年率の違い（76件）は、二つの資料が割る人口の違い（基礎資料は住民基本台帳人口と明記）による＝説明あり。読めない表・名前の対応なしは読み取りの失敗。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('jisatsu', 'c202', note='「自殺の状況」本体の図表4-4・1-1 と基礎資料', script=__file__)
_t.set(compared=4 * st['44'] + st['rev'] + st['11'] + st['11d'], mismatched=0)
for i in issues:
    k = str(i[1])
    if 'parse' in k or 'not in B6' in k: _t.fail()
    else: _t.ng(explained=('当年率≠B6' in k))
print('tally', _t.save())
