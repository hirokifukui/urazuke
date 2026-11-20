"""表から「列ごとの年次系列」{列見出し: {西暦年: 値}} を取り出す（新旧どちらの様式にも使う）。
新様式：西暦の列（'2019年'）がある。旧様式（令和2年版以前の印刷用 Excel）：和暦の行ラベル（'昭和21年'、'22'、'元年' など）だけ。
旧様式は、行ラベルが連続した年であることを確かめたうえで、最後の行を last_year（その版のデータの最終年）として後ろから西暦を割り当てる。
ラベルの数字の並び（1ずつ増える、元号の切替わりで 30以上→元）と矛盾する表は使わない。"""
import re,unicodedata
YR=re.compile(r'^(\d{4})年$')
ERA=re.compile(r'^\s*(昭和|平成|令和)?\s*(\d{1,2}|元)\s*年?\s*$')
def _num(v): return isinstance(v,float)
def headers(cells,first_data_row,cols):
    out={}
    hrows=range(max(1,first_data_row-8),first_data_row)
    for c in cols:
        parts=[]
        for r in hrows:
            v=cells.get((r,c))
            if not isinstance(v,str):
                # 結合セル：左に最も近い見出しを使う（同じ行）
                for cc in range(c-1,max(0,c-12),-1):
                    w=cells.get((r,cc))
                    if isinstance(w,str): v=w; break
                    if _num(w): break
            if isinstance(v,str):
                v=re.sub(r'\s','',v)
                if v and v not in parts: parts.append(v)
        out[c]='/'.join(parts)
    return out
def series_new(cells):
    from collections import Counter
    yc=Counter(c for (r,c),v in cells.items() if isinstance(v,str) and YR.match(v.strip()))
    if not yc: return {}
    col,n=yc.most_common(1)[0]
    if n<3: return {}
    rows=sorted(r for (r,c),v in cells.items() if c==col and isinstance(v,str) and YR.match(v.strip()))
    cols=sorted({c for (r,c),v in cells.items() if r in rows and c>col and _num(v)})
    H=headers(cells,rows[0],cols); out={}
    for c in cols:
        d={int(YR.match(cells[(r,col)].strip())[1]):cells[(r,c)] for r in rows if _num(cells.get((r,c)))}
        if len(d)>=3: out[H[c]+f'@{c}']=d
    return out
def series_old(cells,last_year):
    from collections import Counter
    cand=Counter()
    for (r,c),v in cells.items():
        if isinstance(v,str) and ERA.match(unicodedata.normalize('NFKC',v)) and len(v.strip())<=8: cand[c]+=1
        elif _num(v) and float(v).is_integer() and 1<=v<=64 and c<=3: cand[c]+=0.5
    if not cand: return {}
    col,n=cand.most_common(1)[0]
    if n<5: return {}
    rows=[]
    for r in sorted({r for (r,c) in cells if c==col}):
        v=cells.get((r,col))
        if isinstance(v,str):
            v=unicodedata.normalize('NFKC',v); m=ERA.match(v)
            if m: rows.append((r,1 if m[2]=='元' else int(m[2]),m[1]))
        elif _num(v) and float(v).is_integer() and 1<=v<=64: rows.append((r,int(v),None))
    if len(rows)<5: return {}
    # 最後の連続ブロックだけを使う（行番号が飛ぶところで切る）
    blk=[rows[-1]]
    for x in reversed(rows[:-1]):
        if blk[-1][0]-x[0]>3: break
        blk.append(x)
    blk=list(reversed(blk))
    # ラベルの並びが1年ずつかを確かめる（元号の切替わりを許す）
    for a,b in zip(blk,blk[1:]):
        if not (b[1]==a[1]+1 or (b[1]==1 and a[1]>=30)): return {}   # 元号の切替わり（昭和63→平成元、平成30/31→令和元）
    years={r:last_year-(len(blk)-1-i) for i,(r,_,_) in enumerate(blk)}
    cols=sorted({c for (r,c),v in cells.items() if r in years and c>col and _num(v)})
    H=headers(cells,blk[0][0],cols); out={}
    for c in cols:
        d={years[r]:cells[(r,c)] for r in years if _num(cells.get((r,c)))}
        if len(d)>=3: out[H[c]+f'@{c}']=d
    return out
