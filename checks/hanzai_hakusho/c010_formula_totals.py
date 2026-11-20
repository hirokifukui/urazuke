"""c010: 全表の L1 検査（版を引数に取る）。
(a) 式の列：見出しに「X/Y」があり、X・Y が同じ行の「（X）」列として特定できる列を再計算（％なら×100）。
(b) 計の列：見出しが「<接頭>_計」「<接頭>_総数」などで、同じ接頭の兄弟列があるとき、兄弟の和と比べる。
    2行見出し（上段にグループ名）の「計」「総数」も同様に扱う。
結果: results/hanzai_hakusho/c010_<版>.tsv"""
import sys,os,re,glob,collections
sys.path.insert(0,'.')
from lib.xlsx import read_sheets
V=sys.argv[1]; tag=os.path.basename(V.rstrip('/'))
Z=str.maketrans('ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ／','ABCDEFGHIJKLMNOPQRSTUVWXYZ/')
def hdr_row(s):
    # 年次列 or 罪名列などのデータが始まる直前の、文字列が最も多い行（上から15行）
    best=None;bn=0
    for r in range(1,16):
        n=sum(1 for c in range(1,120) if isinstance(s.get((r,c)),str))
        if n>bn: best,bn=r,n
    return best
out=[]; stats=collections.Counter()
for x in sorted(glob.glob(V+'/zuhyo/*.xlsx')+glob.glob(V+'/shiryo/*.xlsx')):
    try: S=read_sheets(x)
    except Exception as e: stats['readerr']+=1; continue
    fn=os.path.basename(x)
    for sn,s in S.items():
        if '閲覧用' in sn: continue
        hr=hdr_row(s)
        if not hr: continue
        mc=max(c for (r,c) in s)
        H={c:str(s.get((hr,c))).translate(Z) for c in range(1,mc+1) if s.get((hr,c)) is not None}
        G={c:(str(s.get((hr-1,c))) if isinstance(s.get((hr-1,c)),str) else '') for c in H}
        rows=[r for r in range(hr+1,hr+400) if any(isinstance(s.get((r,c)),float) for c in H)]
        # (a) 式の列
        tagcol={}
        for c,h in H.items():
            for m in re.finditer(r'[（(]([A-Z])[）)]',h): tagcol.setdefault(m[1],c)
        for c,h in H.items():
            m=re.search(r'([A-Z](?:\+[A-Z])*)/([A-Z](?:\+[A-Z])*)',h.replace('（','(').replace('）',')'))
            if not m: continue
            num=m[1].split('+'); den=m[2].split('+')
            if not all(k in tagcol for k in num+den): stats['formula_unresolved']+=1; continue
            pct=100 if ('％' in h or '%' in h or '率' in h) else 1
            stats['formula_cols']+=1
            for r in rows:
                v=s.get((r,c)); a=[s.get((r,tagcol[k])) for k in num]; b=[s.get((r,tagcol[k])) for k in den]
                if not (isinstance(v,float) and all(isinstance(t,float) for t in a+b)) or sum(b)==0: continue
                calc=pct*sum(a)/sum(b); stats['formula_cells']+=1
                if abs(calc-v)>max(0.051,1e-6*abs(v)):
                    out.append(('formula',fn,sn,r,h,str(s.get((r,2)))+'|'+str(s.get((r,3))),v,round(calc,4)))
        # (b) 計の列
        groups=collections.defaultdict(list)
        for c,h in H.items():
            if '_' in h: groups[h.rsplit('_',1)[0]].append(c)
            elif G[c]: groups['G:'+G[c]].append(c)
        for g,cols in groups.items():
            labs={c:(H[c].rsplit('_',1)[1] if '_' in H[c] else H[c]) for c in cols}
            tot=[c for c in cols if re.fullmatch(r'(計|総数|合計)(（[A-Z]）)?',labs[c])]
            if len(tot)!=1 or len(cols)<3: continue
            t=tot[0]; parts=[c for c in cols if c!=t and not re.search(r'率|比|％|%|平均|うち|再掲',labs[c])]
            if len(parts)<2: continue
            stats['total_groups']+=1
            for r in rows:
                T=s.get((r,t)); ps=[s.get((r,c)) for c in parts]
                nums=[p for p in ps if isinstance(p,float)]
                if not isinstance(T,float) or len(nums)<2: continue
                stats['total_cells']+=1
                if abs(sum(nums)-T)>0.5 and not any(isinstance(p,str) and p not in('…','-','－') for p in ps):
                    out.append(('total',fn,sn,r,g,str(s.get((r,2)))+'|'+str(s.get((r,3))),T,sum(nums)))
os.makedirs('results/hanzai_hakusho',exist_ok=True)
with open(f'results/hanzai_hakusho/c010_{tag}.tsv','w') as w:
    w.write('kind\tfile\tsheet\trow\tcolumn\trowkey\tstated\tcalc\n')
    for o in out: w.write('\t'.join(map(str,o))+'\n')
with open(f'results/hanzai_hakusho/c010_{tag}.summary','w') as w:
    w.write(str(dict(stats))+'\n')
    cnt=collections.Counter((o[0],o[1],o[2],o[4]) for o in out)
    for k,v in cnt.most_common(): w.write(f'{v}\t{k}\n')
print('done',tag)

# 照合の要約（lib/tally.py）：単位は再計算したセル（比率の列・計の列）。引っかかったセルのうち、作業ノートで資料の誤りと確かめた表
# （A4：2-2-3-2 の残存行〔令和3〜5年版〕、A6 と 2004年の勾留請求率：2-2-3-1、A1：5-4-4表③〔令和5・6年版〕）は食い違い。
# それ以外の引っかかりは見出しの構造による誤検出（作業ノート）＝読み取りの失敗。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_REAL = {'68': {'2-2-3-2.xlsx', '2-2-3-1.xlsx'}, '69': {'2-2-3-2.xlsx', '2-2-3-1.xlsx'}, '70': {'2-2-3-2.xlsx', '2-2-3-1.xlsx', '5-4-4.xlsx'}, '71': {'5-4-4.xlsx'}}
_t = Tally('hanzai_hakusho', 'c010', label=tag, note='犯罪白書 全表：比率の列の再計算と、計と内訳の和', script=__file__)
_ng = sum(1 for o in out if o[1] in _REAL.get(tag[:2], ())); _fl = len(out) - _ng
_t.set(compared=stats['formula_cells'] + stats['total_cells'] - _fl, mismatched=_ng, read_failures=_fl); print('tally', _t.save())
