"""c304: 2017年（h29）の従来ベース集計「Ⅲ.2.(5)総数」と長期時系列の照合。c302 はシート名の違いで 2017年を読み飛ばしていた。
h29 の表には指定都市の行がない（都道府県のみ）。比較は都道府県×疾患分類12区分＋合計。"""
import sys,glob,re,collections
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
f=sorted(glob.glob('data/raw/seishin630/h29/h29_other_totalization_630/*.xlsx'))[0]
s=read_sheets(f)['Ⅲ.2.(5)総数']
hdr={re.sub(r'\s','',v):c for (r,c),v in s.items() if r==4 and isinstance(v,str)}
totc=[c for h,c in hdr.items() if h.startswith('合')]
st=collections.Counter(); iss=[]
for r in range(6,80):
    p=s.get((r,1))
    if not isinstance(p,str) or len(p)>8: continue
    name=norm(re.sub(r'[\s　]','',p))
    for h,sn in CATS+[('TOTAL','在院患者数')]:
        c=(totc[0] if totc else None) if h=='TOTAL' else hdr.get(h)
        if c is None: st['列なし:'+h]+=1; continue
        a=s.get((r,c)); b=lt(sn,name,2017)
        if not isinstance(a,float) or b is None: st['値なし']+=1; continue
        st['cmp']+=1
        if abs(a-b)>0.5: iss.append((name,sn,a,b))
print(dict(st),'不一致',len(iss))
for i in iss[:30]: print(i)

# 照合の要約（lib/tally.py）：単位は（都道府県・区分）のセル。値・列のないものは読み取りの失敗。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('seishin630', 'c304', note='630調査 2017年の従来ベース集計と長期データ', script=__file__)
_t.set(compared=st['cmp'], mismatched=len(iss), read_failures=sum(v for k, v in st.items() if k != 'cmp')); print('tally', _t.save())
