"""c301: 精神保健福祉資料「長期時系列」longterm_1998_2025.xlsx（NCNP）の内部整合（L1）と大きな変動。
行：5〜51 都道府県、52〜71 指定都市（再掲）、72 合計。列：1998〜2025年。
(a) 都道府県の和＝合計（全シート・全年）
(b) 内訳の和＝在院患者数（入院形態、疾患分類〔大分類〕、在院期間、年齢）、中分類＝大分類（F0, F1）、★の区分＝もとの区分の和、看護職員＝看護師＋准看護師
(c) 指定都市 ≦ その都道府県
(d) 前年比 25%以上の変動（値500以上）。誤りではなく、照会・確認の候補として列挙
使い方: ~/.venvs/urazuke/bin/python checks/seishin630/c301_longterm_internal.py"""
import sys,collections,json
sys.path.insert(0,'.')
from lib.xlsx import read_sheets
S=read_sheets('data/raw/seishin630/longterm_1998_2025.xlsx')
YCOL={int(v):c for (r,c),v in S['在院患者数'].items() if r==4 and isinstance(v,float)}
def grid(sn):
    s=S[sn]; g={}
    for r in range(5,73):
        name=s.get((r,1))
        for y,c in YCOL.items():
            v=s.get((r,c))
            if isinstance(v,float): g[(name,y)]=v
    names=[s.get((r,1)) for r in range(5,73)]
    return g,names
G={}; NAMES=None
for sn in S:
    if sn=='目次': continue
    G[sn],nm=grid(sn); NAMES=NAMES or nm
PREFS=NAMES[:47]; CITIES=NAMES[47:67]; TOTAL=NAMES[67]
issues=[]; st=collections.Counter()
# (a)
for sn,g in G.items():
    for y in YCOL:
        tot=g.get((TOTAL,y)); vals=[g.get((p,y)) for p in PREFS]
        if tot is None or any(v is None for v in vals): continue
        st['a']+=1
        if abs(sum(vals)-tot)>0.5: issues.append(('(a) 都道府県の和≠合計',sn,y,tot,sum(vals)))
# (b)
RULES=[('在院患者数',['措置','医療保護','任意','その他の入院形態'],'入院形態'),
       ('在院患者数',['F0','F1','F2','F3','F4','F5','F6','F7','F8','F9','てんかん','その他の疾患分類'],'疾患分類'),
       ('F0',['F00','F01','F02-09'],'F0内訳'),('F1',['F10','覚せい剤','アルコール覚せい剤以外'],'F1内訳'),
       ('在院患者数',['1ヶ月未満','1～3ヶ月','3～6ヶ月','6～12ヶ月','1～5年','5～10年','10～20年','20年以上'],'在院期間'),
       ('★3ヶ月未満',['1ヶ月未満','1～3ヶ月'],'★3ヶ月未満'),('★3～12ヶ月',['3～6ヶ月','6～12ヶ月'],'★3～12ヶ月'),('★5年以上',['5～10年','10～20年','20年以上'],'★5年以上'),
       ('在院患者数',['20歳未満','20～40歳','40～65歳','65～75歳','75歳以上'],'年齢'),
       ('★20～65歳',['20～40歳','40～65歳'],'★20～65歳'),('★65歳以上',['65～75歳','75歳以上'],'★65歳以上'),
       ('看護職員',['看護職員（看護師）','看護職員（准看護師）'],'看護職員')]
for tgt,parts,lab in RULES:
    for (name,y),T in G[tgt].items():
        vals=[G[p].get((name,y)) for p in parts]
        if any(v is None for v in vals): continue
        st['b']+=1
        if abs(sum(vals)-T)>0.5: issues.append(('(b) '+lab,name,y,T,sum(vals),round(sum(vals)-T)))
# ★F0,F2以外
for (name,y),T in G['在院患者数'].items():
    a,b,c=G['F0'].get((name,y)),G['F2'].get((name,y)),G['★F0,F2以外の疾患'].get((name,y))
    if None in (a,b,c): continue
    st['b']+=1
    if abs(T-a-b-c)>0.5: issues.append(('(b) ★F0,F2以外',name,y,c,T-a-b))
# (c) 指定都市と道府県
CITY_PREF={'札幌市':'北海道','仙台市':'宮城','さいたま市':'埼玉','千葉市':'千葉','横浜市':'神奈川','川崎市':'神奈川','相模原市':'神奈川','新潟市':'新潟','静岡市':'静岡','浜松市':'静岡','名古屋市':'愛知','京都市':'京都','大阪市':'大阪','堺市':'大阪','神戸市':'兵庫','岡山市':'岡山','広島市':'広島','北九州市':'福岡','福岡市':'福岡','熊本市':'熊本'}
for sn,g in G.items():
    for y in YCOL:
        agg=collections.Counter()
        for c in CITIES:
            v=g.get((c,y))
            if v is not None and c in CITY_PREF: agg[CITY_PREF[c]]+=v
        for p,v in agg.items():
            P=g.get((p,y))
            if P is None: continue
            st['c']+=1
            if v>P+0.5: issues.append(('(c) 指定都市の和>道府県',sn,p,y,P,v))
# (d)
jumps=[]
for sn in ['在院患者数','精神病床数','精神科病院数','措置','医療保護','任意']:
    g=G[sn]
    for name in NAMES:
        for y in sorted(YCOL)[1:]:
            a,b=g.get((name,y-1)),g.get((name,y))
            if a and b and max(a,b)>=500 and abs(b/a-1)>=0.25:
                jumps.append((sn,name,y-1,a,y,b,round((b/a-1)*100,1)))
with open('results/seishin630/c301_longterm_internal.tsv','w') as w:
    w.write(json.dumps(dict(st),ensure_ascii=False)+'\n')
    for i in issues: w.write('\t'.join(map(str,i))+'\n')
    w.write('## (d) 大きな変動\n')
    for j in jumps: w.write('\t'.join(map(str,j))+'\n')
print(dict(st),'issues',len(issues),'jumps',len(jumps))
c=collections.Counter(i[0]+' '+str(i[1]) for i in issues)
for k,v in c.most_common(30): print(v,k)
for i in issues[:25]: print(i)
print('--- jumps'); 
for j in jumps[:40]: print(j)

# 照合の要約（lib/tally.py）：単位は (a)(b)(c) の式。(b) の不一致の大半は、長期データに「不明」の区分がないこと（2017年以降）と、
# 指定都市の F7 に F8 の値が入っていること（630-A1）による内訳の和の不足で、資料どうしの食い違い（説明なし）。(d) の大きな変動は照合ではない。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('seishin630', 'c301', note='630調査 長期データ：都道府県の和と合計、区分の和、指定都市の和≦道府県', script=__file__)
_t.set(compared=st['a'] + st['b'] + st['c'], mismatched=len(issues)); print('tally', _t.save())
