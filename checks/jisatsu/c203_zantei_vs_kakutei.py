"""c203（L3）: 自殺統計の暫定値（1月公表）と確定値（3月公表）の差。
同じ形の表（性別・年齢階級別×職業／原因・動機／詳細、発見日）をセルごとに比べる。
使い方: ~/.venvs/urazuke/bin/python checks/jisatsu/c203_zantei_vs_kakutei.py"""
import sys,glob,collections,json
sys.path.insert(0,'.')
from lib.xlsx import read_sheets
PAIRS=[('r02','zantei/r02_000739744.xlsx','r02_R2kakutei-CHIIKI02'),('r03','zantei/r03_000892994.xlsx','r03_R3kakutei-CHIIKI022'),('r04','zantei/r04_001051370.xlsx','R4FILE'),('r05','zantei/r05_zantei_001197854.xlsx','r05_hakkenbi_001236400'),('r06','zantei/r06_zantei_001386267.xlsx','r06_hakkenbi_001464823'),('r07','zantei/r07_zantei_001644135.xlsx','r07_hakkenbi_001680832')]
out=[]; summ={}
for y,zf,kd in PAIRS:
    Z=read_sheets('data/raw/jisatsu/'+zf)
    K=read_sheets('data/raw/jisatsu/joukyou_old/r04_001213915.xlsx' if kd=='R4FILE' else glob.glob(f'data/raw/jisatsu/kiso/{kd}/【*.xlsx')[0])
    st=collections.Counter(); neg=[]
    for i,sn in enumerate(Z):
        z,k=Z[sn],K[list(K)[i]] if i<len(K) else {}
        for key,v in z.items():
            w=k.get(key)
            if isinstance(v,float) and isinstance(w,float) and key[0]>=8:
                st['cells']+=1
                if w!=v: st['changed']+=1
                if w<v: st['decreased']+=1; neg.append((sn,key,v,w,z.get((7,key[1]))))
    first=lambda S:[v for (r,c),v in sorted(S[list(S)[0]].items()) if r in (8,9) and isinstance(v,float) and c>=5][0]
    t8=first(Z),first(K)
    summ[y]={'total_zantei':t8[0],'total_kakutei':t8[1],'diff':t8[1]-t8[0],**st}
    out+= [(y,)+n for n in neg]
with open('results/jisatsu/c203_zantei_vs_kakutei.tsv','w') as w:
    w.write(json.dumps(summ,ensure_ascii=False)+'\n')
    for o in out: w.write('\t'.join(map(str,o))+'\n')
print(json.dumps(summ,ensure_ascii=False,indent=0)); print('decreased cells (sample):',out[:10])

# 照合の要約（lib/tally.py）：単位は同じ形の表のセル。暫定値と確定値の違いは、暫定値であることが資料に明記されている＝説明あり。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('jisatsu', 'c203', note='自殺の統計：暫定値（1月）と確定値（3月）の同じ表のセル', script=__file__)
_c = sum(v['cells'] for v in summ.values()); _m = sum(v.get('changed', 0) for v in summ.values())
_t.set(compared=_c, mismatched=_m, explained=_m); print('tally', _t.save())
