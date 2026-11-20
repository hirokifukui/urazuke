"""c013 (L1): 全表の全行で、和暦セルと同じ行の西暦セルの対応を確かめる。"""
import sys,os,re,glob,collections
sys.path.insert(0,'.')
from lib.xlsx import read_sheets
BASE={'明治':1867,'大正':1911,'昭和':1925,'平成':1988,'令和':2018}
Z=str.maketrans('０１２３４５６７８９','0123456789')
ERA=re.compile(r'^(明治|大正|昭和|平成|令和)(元|\d{1,2})年$')
YR=re.compile(r'^(\d{4})年$')
out=[]; st=collections.Counter()
for V in sys.argv[1:]:
    tag=os.path.basename(V)
    for x in sorted(glob.glob(V+'/zuhyo/*.xlsx')+glob.glob(V+'/shiryo/*.xlsx')):
        try: S=read_sheets(x)
        except Exception: continue
        for sn,s in S.items():
            byrow=collections.defaultdict(dict)
            for (r,c),v in s.items():
                if isinstance(v,str): byrow[r][c]=v.strip().translate(Z).replace(' ','').replace('　','')
            for r,cells in byrow.items():
                eras=[(c,ERA.match(v)) for c,v in cells.items() if ERA.match(v)]
                yrs=[(c,YR.match(v)) for c,v in cells.items() if YR.match(v)]
                if len(eras)==1 and len(yrs)==1:
                    (ce,m),(cy,my)=eras[0],yrs[0]
                    if cy!=ce+1: continue
                    n=1 if m[2]=='元' else int(m[2]); y=BASE[m[1]]+n
                    st['pairs']+=1
                    if y!=int(my[1]):
                        out.append((tag,os.path.basename(x),sn,r,cells[ce],cells[cy],y))
with open('results/hanzai_hakusho/c013_era_year.tsv','w') as w:
    w.write(str(dict(st))+'\n')
    for o in out: w.write('\t'.join(map(str,o))+'\n')
print(dict(st),'mismatch',len(out))
for o in out: print(o)

# 照合の要約（lib/tally.py）：単位は同じ行の和暦と西暦の組。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('hanzai_hakusho', 'c013', label='5ed', note='犯罪白書 令和3〜7年版：同じ行の和暦と西暦', script=__file__)
_t.set(compared=st['pairs'], mismatched=len(out)); print('tally', _t.save())
