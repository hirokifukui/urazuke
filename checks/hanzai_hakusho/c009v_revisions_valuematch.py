"""c009v: 版間の遡及改訂を「列の値」で対応させて検出する（見出しにも図表番号にもよらない）。
旧様式（令和2年版以前、和暦の行ラベルだけの印刷用 Excel）と新様式（令和3年版以降、西暦の列）の両方に使える。
各列を {西暦年: 値} の系列にし（lib/yearseries.py）、新しい版の各列について、古い版の全列から、
重なる年が5以上・値の一致率0.8以上の列のうち、一致する年が最も多い列を相手とする。相手と値が違う年を改訂として出す。
使い方: python3 c009v_revisions_valuematch.py <旧版dir> <旧版の最終年> <新版dir> <新版の最終年> <タグ>"""
import sys,os,glob,collections,json
sys.path.insert(0,'.')
from lib.xlsx import read_sheets
from lib.yearseries import series_new,series_old
OLD,OY,NEW,NY,TAG=sys.argv[1],int(sys.argv[2]),sys.argv[3],int(sys.argv[4]),sys.argv[5]
def load(V,last):
    out={}
    for x in sorted(glob.glob(V+'/zuhyo/*.xlsx')+glob.glob(V+'/shiryo/*.xlsx')):
        try: S=read_sheets(x)
        except Exception: continue
        for sn,cells in S.items():
            if '閲覧用' in sn: continue
            d=series_new(cells) or series_old(cells,last)
            for h,ser in d.items():
                if len(ser)>=5: out[(os.path.basename(x),sn,h)]=ser
    return out
def close(a,b): return abs(a-b)<=1e-6*max(1,abs(a))
O=load(OLD,OY); N=load(NEW,NY)
inv=collections.defaultdict(set)
for k,s in O.items():
    for y,v in s.items():
        if abs(v)>=10: inv[(y,round(v,4))].add(k)
st=collections.Counter(); res=[]; pairs=[]
_UV=[0]  # 照合の要約用：対応の取れなかった列の値の数
for nk,ns in N.items():
    cnt=collections.Counter()
    for y,v in ns.items():
        if abs(v)>=10:
            for ok in inv.get((y,round(v,4)),()): cnt[ok]+=1
    best=None
    for ok,c in sorted(cnt.items(),key=lambda t:(-t[1],t[0]))[:10]:  # 同数のときの順を決める（2026-11-17 r26。以前は集合の順に依存）
        common=set(ns)&set(O[ok])
        if len(common)<5: continue
        agree=sum(close(ns[y],O[ok][y]) for y in common)
        if agree/len(common)<0.8: continue
        if best is None or agree>best[1]: best=(ok,agree,len(common))
    if not best: st['unmatched']+=1; _UV[0]+=len(ns); continue
    ok,agree,nc=best; st['matched']+=1; st['cmp']+=nc
    pairs.append((nk,ok,agree,nc))
    for y in sorted(set(ns)&set(O[ok])):
        if not close(ns[y],O[ok][y]): res.append((nk[0],nk[1],nk[2],ok[0],ok[1],ok[2],y,O[ok][y],ns[y]))
os.makedirs('results/hanzai_hakusho',exist_ok=True)
with open(f'results/hanzai_hakusho/c009v_{TAG}.tsv','w') as w:
    w.write(json.dumps(dict(st),ensure_ascii=False)+'\n')
    w.write('new_file\tnew_sheet\tnew_col\told_file\told_sheet\told_col\tyear\told\tnew\n')
    for r in res: w.write('\t'.join(map(str,r))+'\n')
g=collections.defaultdict(list)
for r in res: g[(r[0],r[1])].append(r)
print(TAG,dict(st),'changed',len(res),'tables_with_changes',len(g))
for k,v in sorted(g.items(),key=lambda t:-len(t[1]))[:25]:
    ys=sorted(set(r[6] for r in v)); print(len(v),k,'<-',v[0][3],ys[0],'-',ys[-1],'ex',v[0][2][:30],v[0][6],v[0][7],'->',v[0][8])

# 照合の要約（lib/tally.py）：単位は、値で対応させた列どうしの同じ年の値。値が違えば食い違い（版の改訂を含む）。対応の取れなかった列の値は読み取りの失敗。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('hanzai_hakusho', 'c009v', label=TAG, note='犯罪白書 2版間：値で対応させた列の同じ年の値', script=__file__)
from lib.hanzai_explained import explained as _ex  # 改訂の理由が白書の中に書かれているもの（規則は lib/hanzai_explained.py）
_t.set(compared=st['cmp'], mismatched=len(res), read_failures=_UV[0], explained=sum(1 for r in res if _ex(TAG, r[0], r[1], r[2], r[6]))); print('tally', _t.save())
