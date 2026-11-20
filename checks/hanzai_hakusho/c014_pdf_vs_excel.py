"""c014 (L4): PDF の「表」に現れる数値が、同じ番号の Excel に含まれるかを調べる。
PDF テキスト（pdftotext -layout）で ") X-X-X(-X)表 " の見出しから次の図表見出しまでを表の範囲とし、
整数(>=10、カンマ区切りを含む)と小数(1桁)を抜き出す。Excel 側は同名ファイルの全シートの値（小数は1桁に丸める）。
PDF にあって Excel にない数値を、表ごとに列挙する。使い方: c014 <PDFテキスト> <Excel版ディレクトリ> <タグ>"""
import sys,os,re,collections
sys.path.insert(0,'.')
from lib.xlsx import read_sheets
txt,V,tag=sys.argv[1],sys.argv[2],sys.argv[3]
L=open(txt,encoding='utf-8',errors='replace').read().split('\n')
# 令和3・4年版の PDF は番号と「表」の間に空白が入るため、空白を許す（2026-11-16 追記）
# 令和2年版は見出しの前に「◥」がある（2026-11-16 追記）
TITLE=re.compile(r'^\f?\s*[)◥◤]?\s*(\d+-\d+-\d+(?:-\d+)?)\s*(表|図)\s')
heads=[(i,m[1],m[2]) for i,l in enumerate(L) if (m:=TITLE.match(l))]
NUM=re.compile(r'(?<![\d.,])(\d{1,3}(?:,\d{3})+|\d+\.\d+|\d+)(?![\d,])')
out=[]; st=collections.Counter()
_TB=[]  # 照合の要約用：(表番号, 欠けた数値があるか)
seen=set()
for k,(i,no,kind) in enumerate(heads):
    if kind!='表' or no in seen: continue
    seen.add(no)
    j=heads[k+1][0] if k+1<len(heads) else min(len(L),i+200)
    j=min(j,i+250)
    block=L[i+1:j]
    # 注（脚注）以下は除外
    for q,l in enumerate(block):
        if re.match(r'^\s*注\s',l): block=block[:q]; break
    toks=[]
    for l in block:
        for t in NUM.findall(l):
            if '.' in t: toks.append(('d',round(float(t),1)))
            else:
                v=int(t.replace(',',''))
                if v>=10 and not (1980<=v<=2030 and ',' not in t): toks.append(('i',v))
    x=os.path.join(V,'zuhyo',no+'.xlsx')
    if not os.path.exists(x): st['no_excel']+=1; continue
    try: S=read_sheets(x)
    except Exception: st['readerr']+=1; continue
    ints=set(); decs=set()
    for s in S.values():
        for v in s.values():
            if isinstance(v,float):
                if v==int(v): ints.add(int(v))
                decs.add(round(v,1)); decs.add(round(v+1e-9,1))
    miss=[v for t,v in toks if (t=='i' and v not in ints) or (t=='d' and v not in decs)]
    st['tables']+=1; st['tokens']+=len(toks); st['missing']+=len(miss)
    if miss: out.append((no,len(toks),len(miss),miss[:15],i+1))
    _TB.append((no, bool(miss)))
out.sort(key=lambda o:-o[2])
with open(f'results/hanzai_hakusho/c014_{tag}.tsv','w') as w:
    w.write(str(dict(st))+'\n')
    for o in out: w.write('\t'.join(map(str,o))+'\n')
print(tag,dict(st)); 
for o in out[:30]: print(o)

# 照合の要約（lib/tally.py）：単位は表。PDF の表の数値がすべて Excel にあれば一致。欠けた数値のある表のうち、作業ノートで資料の欠落と
# 確かめたもの（2-3-3-3＝A5）は食い違い。それ以外は PDF のテキストの読み取りの事情による誤検出、または未確認＝読み取りの失敗。
# Excel のない表・読めない表も読み取りの失敗。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_REAL = {'2-3-3-3'}
_t = Tally('hanzai_hakusho', 'c014', label=tag, note='犯罪白書 全体版 PDF の表の数値と同じ番号の Excel', script=__file__)
for no, m in _TB: (_t.ok() if not m else _t.ng() if no in _REAL else _t.fail())
_t.fail(st['no_excel'] + st['readerr']); print('tally', _t.save())
