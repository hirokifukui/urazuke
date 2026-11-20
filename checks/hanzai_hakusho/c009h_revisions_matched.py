"""c009h: 2版間の遡及改訂を、ファイル名ではなく中身で表を対応させて検出する。
理由：図表番号は版ごとに振り直されるため、同じファイル名が同じ表とは限らない（68→69 で確認）。
方法：各シートの時系列 {(列見出し, 西暦年): 値} を作る（c009 の series と同じ）。閲覧用シートは除く。
新版の各シートについて、旧版の全シートから共通キーが20以上で、値の一致率が最も高いものを相手とする。
一致率が0.7以上の対だけを比べ、値の違うセルを改訂として出す。
使い方: python3 c009h_revisions_matched.py <旧版dir> <新版dir> <タグ>"""
import sys,os,re,glob,collections
sys.path.insert(0,'.')
from lib.xlsx import read_sheets
# series を再利用するため、関数だけを読み込む
src=open(os.path.join(os.path.dirname(__file__),'c009_revisions_all.py'),encoding='utf-8').read()
ns={'re':re,'collections':collections}; exec(src[src.find('YR='):src.find('res=[]')],ns)
series=ns['series']
OLD,NEW,TAG=sys.argv[1],sys.argv[2],sys.argv[3]
TT={}
def title_of(cells):
    ts=[x for (r,c),x in sorted(cells.items()) if r<=5 and isinstance(x,str)]
    ts=[re.sub(r'[\s\u3000①-⑳]|※.*|図|表','',t) for t in ts if not re.search(r'\d{4}年|[平令昭][成和]|\(|（',t)]
    return '|'.join(t for t in ts if t)
def load(V):
    out={}
    for x in sorted(glob.glob(V+'/zuhyo/*.xlsx')+glob.glob(V+'/shiryo/*.xlsx')):
        try: S=read_sheets(x)
        except Exception: continue
        for sn,cells in S.items():
            if '閲覧用' in sn: continue
            s=series(cells)
            if len(s)>=20:
                out[(os.path.basename(x),sn)]=s; TT[(V,os.path.basename(x),sn)]=title_of(cells)
    return out
def close(a,b): return abs(a-b)<=1e-6*max(1,abs(a))
O=load(OLD); N=load(NEW)
inv=collections.defaultdict(set)
for k,s in O.items():
    for key in s: inv[key].add(k)
res=[]; st=collections.Counter(); pairs=[]
_UV=[0]  # 照合の要約用：対応の取れなかったシートの値の数
for nk,ns_ in N.items():
    cnt=collections.Counter()
    for key in ns_:
        for ok in inv.get(key,()): cnt[ok]+=1
    best=None; why='no_candidate'
    for ok,c in sorted(cnt.items(),key=lambda t:(-t[1],t[0]))[:15]:  # 同数のときの順を決める（2026-11-17 r26。以前は集合の順に依存し、走らせるたびに相手が変わることがあった）
        if c<20: why='lt20'; break
        common=set(ns_)&set(O[ok]); agree=sum(close(ns_[k],O[ok][k]) for k in common)/len(common)
        if agree<0.7: why='low_agree'; continue
        if best is None or (len(common),agree)>(best[2],best[1]): best=(ok,agree,len(common))
    # 相手の選び方：一致率0.7以上の候補のうち、共通キーが最も多いもの（同じ版の部分表を相手にしないため）
    if not best: st['unmatched_'+why]+=1; _UV[0]+=len(ns_); continue
    ok,agree,nc=best
    tn,to=TT[(NEW,)+nk],TT[(OLD,)+ok]
    if tn and to and not any(a in b or b in a for a in to.split('|') for b in tn.split('|')):
        st['title_mismatch']+=1; _UV[0]+=len(ns_); pairs.append((nk,ok,round(agree,4),nc,'TITLE_MISMATCH',to,tn)); continue
    st['matched']+=1; st['cmp']+=nc
    pairs.append((nk,ok,round(agree,4),nc))
    for k in sorted(set(ns_)&set(O[ok]),key=lambda t:(t[1],t[0])):
        if not close(ns_[k],O[ok][k]): res.append((nk[0],nk[1],ok[0],ok[1],k[0],k[1],O[ok][k],ns_[k]))
os.makedirs('results/hanzai_hakusho',exist_ok=True)
with open(f'results/hanzai_hakusho/c009h_{TAG}.tsv','w') as w:
    w.write('new_file\tnew_sheet\told_file\told_sheet\tcolumn\tyear\told\tnew\n')
    for r in res: w.write('\t'.join(map(str,r))+'\n')
with open(f'results/hanzai_hakusho/c009h_{TAG}_pairs.tsv','w') as w:
    for p in pairs: w.write('\t'.join(map(str,p))+'\n')
print(dict(st),'changed',len(res),'renumbered',sum(1 for p in pairs if p[0][0]!=p[1][0]))
g=collections.defaultdict(list)
for r in res: g[(r[0],r[1])].append(r)
for k,v in sorted(g.items(), key=lambda t:-len(t[1]))[:40]:
    ys=sorted(set(r[5] for r in v)); cols=sorted(set(r[4] for r in v))
    print(len(v),k,'<-',v[0][2],'years',ys[0],'-',ys[-1],'cols',cols[:3],'ex',v[0][4:])

# 照合の要約（lib/tally.py）：単位は、対応の取れた表どうしの同じ（列・年）の値。値が違えば食い違い（版の改訂を含む。誤りとは限らない）。
# 対応の取れなかった表（候補なし・共通キー20未満・一致率0.7未満・表題の不一致）の値は読み取りの失敗。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('hanzai_hakusho', 'c009h', label=TAG, note='犯罪白書 2版間：中身で対応させた表の同じ年の値', script=__file__)
from lib.hanzai_explained import explained as _ex  # 改訂の理由が白書の中に書かれているもの（規則は lib/hanzai_explained.py）
_t.set(compared=st['cmp'], mismatched=len(res), read_failures=_UV[0], explained=sum(1 for r in res if _ex(TAG, r[0], r[1], r[4], r[5]))); print('tally', _t.save())
