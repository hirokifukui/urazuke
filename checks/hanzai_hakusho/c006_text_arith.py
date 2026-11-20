"""c006: 本文中の「N（前年比M（P％）増/減）」の内部算術チェック。
基準値 = N∓M、P_calc = M/基準値×100 が表記Pと（四捨五入で）一致するか。"""
import re,html,glob,os,sys
D=sys.argv[1] if len(sys.argv)>1 else 'data/raw/hanzai_hakusho/72/honbun'
NUM=r'(\d{1,3}(?:,\d{3})*(?:万(?:\d{1,3}(?:,\d{3})*)?)?|\d+万)'
def val(s):
    s=s.replace(',','')
    if '万' in s:
        a,b=s.split('万'); return int(a)*10000+(int(b) if b else 0)
    return int(s)
UNIT=r'(件|人|日|円|か所|校|施設|団体|組|世帯|台)'
# 文章型: 56万8,104件（前年比4万6,127件（7.5％）減）
P1=re.compile(NUM+UNIT+r'（前年比'+NUM+r'\2（(\d+(?:\.\d+)?)％）(増|減)')
# 表型: 737,679件（＋34,328件、＋4.9％）
P2=re.compile(NUM+UNIT+r'（([＋－+\-])'+NUM+r'\2、[＋－+\-](\d+(?:\.\d+)?)％）')
out=[]
for f in sorted(glob.glob(D+'/*.html')):
    t=open(f,'rb').read().decode('utf-8','replace')
    t=html.unescape(re.sub(r'<[^>]+>','',t)); t=re.sub(r'\s+','',t)
    for m in P1.finditer(t):
        n,u,d,p,s=val(m[1]),m[2],val(m[3]),m[4],m[5]
        base=n-d if s=='増' else n+d
        out.append((os.path.basename(f),m[0],n,d,base,p,s))
    for m in P2.finditer(t):
        n,u,sg,d,p=val(m[1]),m[2],m[3],val(m[4]),m[5]
        s='増' if sg in '＋+' else '減'
        base=n-d if s=='増' else n+d
        out.append((os.path.basename(f),m[0],n,d,base,p,s))
bad=0
rows=[]
for f,txt,n,d,base,p,s in out:
    nd=len(p.split('.')[1]) if '.' in p else 0
    calc=d/base*100 if base>0 else float('nan')
    ok=abs(round(calc,nd)-float(p))<1e-9 or abs(calc-float(p))<=0.5*10**-nd+1e-9
    ctx=txt
    rows.append((f,ok,f'{calc:.3f}',p,ctx))
    if not ok: bad+=1
os.makedirs('results/hanzai_hakusho',exist_ok=True)
with open('results/hanzai_hakusho/c006_text_arith.tsv','w') as w:
    for r in rows: w.write('\t'.join(map(str,r))+'\n')
print('items',len(rows),'NG',bad)
for r in rows:
    if not r[1]: print(r)

# 照合の要約（lib/tally.py）：本文の前年比の記述1件を単位とする。label は版（データのフォルダ名の先頭）。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('hanzai_hakusho', 'c006', label=re.search(r'hanzai_hakusho/(\d+)', D)[1] + ('b' if '090659Z' in D else ''), note='犯罪白書 本文の「N（前年比M（P％））」の内部計算', script=__file__)
for r in rows: (_t.ok if r[1] else _t.ng)()
print('tally', _t.save())
