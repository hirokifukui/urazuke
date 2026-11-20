"""c204: 「X年中における自殺の状況」第3章 補表2-1（年齢階級別自殺者数の推移）の平成28〜令和4年の行を、
基礎資料 B5（発見日・住居地）全国の年齢階級と照合する（L4・L3）。対象の報告：平成28〜令和4年版（第3章）。
基礎資料の「20歳未満」＝補表の「～9歳」＋「10～19歳」。
使い方: ~/.venvs/urazuke/bin/python checks/jisatsu/c204_hohyou_age_series.py"""
import sys,glob,re,collections,json
sys.path.insert(0,'.')
from lib.xls import read_sheets
J='data/raw/jisatsu/joukyou_old'
REPS={'h28':'h28_h28kakutei_4','h29':'h29_h29kakutei-04','h30':'h30_001362228','r01':'r01_001362237','r02':'r02_001362249','r03':'r03_001362254','r04':'r04_001362257'}
KD={'h28':'h28_H28KAKUTEI-CHIIKI02','h29':'h29_H29KAKUTEI-CHIIKI02','h30':'h30_H30KAKUTEI-CHIIKI22','r01':'r01_R1KAKUTEI-CHIIKI02','r02':'r02_R2kakutei-CHIIKI02','r03':'r03_R3kakutei-CHIIKI022','r04':'r04_kakutei2'}
YL={'平成28年':'h28','平成29年':'h29','平成30年':'h30','令和元年':'r01','令和２年':'r02','令和３年':'r03','令和４年':'r04'}
def kiso_nat(y):
    S=read_sheets(glob.glob(f'data/raw/jisatsu/kiso/{KD[y]}/*B5表*')[0]); s=S[list(S)[0]]
    for r in range(4,20):
        if s.get((r,2))==0.0: return [s.get((r,c)) for c in [4]+list(range(7,16))]
K={y:kiso_nat(y) for y in KD}
issues=[]; st=collections.Counter(); seen={}
for rep,fn in REPS.items():
    p=f'{J}/{fn}.txt'
    try: t=open(p,encoding='utf-8').read().split('\n')
    except FileNotFoundError: issues.append((rep,'no text')); continue
    idx=[i for i,l in enumerate(t) if re.search(r'補表\s*２\s*－\s*１|補表2-1',l)]
    if not idx: issues.append((rep,'補表2-1 not found')); continue
    i=idx[-1]
    for l in t[i:i+90]:
        m=re.match(r'^\s*(平成\d+年|令和.年)\s+(.*)$',l)
        if not m or m[1] not in YL: continue
        nums=[float(x.replace(',','')) for x in re.findall(r'[\d,]+',m[2])]
        y=YL[m[1]]; v=nums
        if len(nums)==11: under20=v[0]+v[1]; mid=v[2:9]; fu,tot=v[9],v[10]      # ～9歳,10～19歳,20代..80歳～,不詳,合計
        elif len(nums)==10: under20=v[0]; mid=v[1:8]; fu,tot=v[8],v[9]          # ～19歳 の様式
        else: issues.append((rep,m[1],'列数',len(nums))); continue
        rep_v=[tot,under20]+mid+[fu]
        kv=K[y]; st['cmp']+=1
        if rep_v!=kv: issues.append((rep,m[1],'補表≠基礎資料',rep_v,kv))
        if sum(v[:-1])!=v[-1]: issues.append((rep,m[1],'補表の行の和≠合計',sum(v[:-1]),v[-1]))
        seen.setdefault(m[1],{})[rep]=tuple(v)
# 版間の違い
for yl,d in seen.items():
    vals=set(d.values())
    if len(vals)>1: issues.append(('版間',yl,{k:v for k,v in d.items()}))
with open('results/jisatsu/c204_hohyou_age_series.tsv','w') as w:
    w.write(json.dumps(dict(st),ensure_ascii=False)+'\n')
    for i in issues: w.write('\t'.join(map(str,i))+'\n')
print(dict(st),'issues',len(issues))
for i in issues: print(i)

# 照合の要約（lib/tally.py）：単位は補表2-1 の行（報告×年）と基礎資料。「版間」の違いは平成29年版以前に「～9歳」の列がない様式の違い
# （値は同じ）＝読み取りの失敗。列数の読めない行も読み取りの失敗。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('jisatsu', 'c204', note='「自殺の状況」補表2-1（年齢階級別の推移）と基礎資料', script=__file__)
_ng = sum(1 for i in issues if i[2] in ('補表≠基礎資料', '補表の行の和≠合計'))
_t.set(compared=st['cmp'], mismatched=_ng, read_failures=len(issues) - _ng); print('tally', _t.save())
