"""c302: 長期時系列（longterm_1998_2025.xlsx）と各年度の従来ベース集計（h29〜r7、2017〜2025年）の照合（L4）と、回答率。
(1) 在院患者数（疾患分類別）Ⅲ.2.(5)：各都道府県・指定都市の F0〜F9・てんかん・その他・合計 を長期時系列と比べる。
(2) 1.1 回答率：回答した病院数／配布数。回答率と、長期時系列の大きな変動（c301 (d)）を並べる。
使い方: ~/.venvs/urazuke/bin/python checks/seishin630/c302_longterm_vs_annual.py"""
import sys,glob,re,collections,json
sys.path.insert(0,'.')
from lib.xlsx import read_sheets
L=read_sheets('data/raw/seishin630/longterm_1998_2025.xlsx')
YCOL={int(v):c for (r,c),v in L['在院患者数'].items() if r==4 and isinstance(v,float)}
def lt(sn,name,y):
    s=L[sn]
    for r in range(5,73):
        if s.get((r,1))==name: return s.get((r,YCOL[y]))
def norm(p): return re.sub(r'[県府都]$','',p) if p not in ('東京都','京都府','北海道') else {'東京都':'東京','京都府':'京都','北海道':'北海道'}[p]
CATS=[('Ｆ０','F0'),('Ｆ１','F1'),('Ｆ２','F2'),('Ｆ３','F3'),('Ｆ４','F4'),('Ｆ５','F5'),('Ｆ６','F6'),('Ｆ７','F7'),('Ｆ８','F8'),('Ｆ９','F9'),('てんかん','てんかん'),('その他','その他の疾患分類')]
issues=[]; st=collections.Counter(); resp={}
ED={2017:'h29',2018:'h30',**{2018+k:f'r{k}' for k in range(1,8)}}
for y,e in ED.items():
    f=sorted(glob.glob(f'data/raw/seishin630/{e}/{e}_other_totalization_630/*.xlsx'))[0]
    S=read_sheets(f)
    if 'Ⅲ.2.(5)' not in S: issues.append((y,'Ⅲ.2.(5) なし',list(S)[:8])); continue
    s=S['Ⅲ.2.(5)']
    hdr={}
    for c in range(1,40):
        v=s.get((4,c))
        if isinstance(v,str): hdr[re.sub(r'\s','',v)]=c
    totc=[c for h,c in hdr.items() if h.startswith('合計') or h.startswith('合')][0]
    for r in range(6,90):
        p=s.get((r,1))
        if not isinstance(p,str) or len(p)>8: continue
        name=norm(p)
        for h,sn in CATS+[('TOTAL','在院患者数')]:
            c=totc if h=='TOTAL' else hdr.get(h)
            if c is None: continue
            a=s.get((r,c)); b=lt(sn,name,y)
            if not isinstance(a,float) or b is None: continue
            st['cmp']+=1
            if abs(a-b)>0.5: issues.append((y,name,sn,'年度別',a,'長期',b))
    t=S['1.1']; resp[y]={}
    for r in range(5,80):
        p=t.get((r,2)); A=t.get((r,3)); B=t.get((r,4))
        if isinstance(p,str) and isinstance(A,float) and isinstance(B,float) and B>0: resp[y][norm(p)]=(A,B,round(A/B,3))
with open('results/seishin630/c302_longterm_vs_annual.tsv','w') as w:
    w.write(json.dumps(dict(st),ensure_ascii=False)+'\n')
    for i in issues: w.write('\t'.join(map(str,i))+'\n')
    w.write('## 回答率（回答病院数, 配布数, 率）\n')
    for y,d in resp.items():
        for p,v in d.items(): w.write(f'{y}\t{p}\t{v[0]}\t{v[1]}\t{v[2]}\n')
print(dict(st),'issues',len(issues))
for i in issues[:40]: print(i)
for y,d in resp.items():
    low=sorted([(v[2],p) for p,v in d.items() if v[2]<0.9])
    nat=d.get('合計') or d.get('全国')
    print(y,'national',nat,'low(<0.9):',low[:12])

# 照合の要約（lib/tally.py）：単位は（年・都道府県/指定都市・区分）のセル。不一致は F7 の60セル（630-A1）。シートのない年は読み取りの失敗。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('seishin630', 'c302', note='630調査 年度別の表（Ⅲ.2.(5)）と長期データ', script=__file__)
_f = sum(1 for i in issues if len(i) > 1 and str(i[1]).endswith('なし'))
_t.set(compared=st['cmp'], mismatched=len(issues) - _f, read_failures=_f); print('tally', _t.save())
