"""c303: 平成27・28年度の630調査（旧様式 h27_630.xlsx・h28_630.xlsx）Ⅲ.2.(5)総数 と長期データ（2015・2016年）の照合（L4）。
旧様式の都道府県の行は指定都市を含まない（指定都市は別の行で、全部の和が合計）。長期データの都道府県は指定都市を含む。
そこで「道府県の行＋その中の指定都市の行」を長期データの都道府県と比べ、指定都市の行は長期データの指定都市と比べる。
使い方: ~/.venvs/urazuke/bin/python checks/seishin630/c303_old_vs_longterm.py"""
import sys,re,collections,json
sys.path.insert(0,'.')
from lib.xlsx import read_sheets
L=read_sheets('data/raw/seishin630/longterm_1998_2025.xlsx')
YCOL={int(v):c for (r,c),v in L['在院患者数'].items() if r==4 and isinstance(v,float)}
def lt(sn,name,y):
    s=L[sn]
    for r in range(5,73):
        if s.get((r,1))==name: return s.get((r,YCOL[y]))
CITY_PREF={'札幌市':'北海道','仙台市':'宮城','さいたま市':'埼玉','千葉市':'千葉','横浜市':'神奈川','川崎市':'神奈川','相模原市':'神奈川','新潟市':'新潟','静岡市':'静岡','浜松市':'静岡','名古屋市':'愛知','京都市':'京都','大阪市':'大阪','堺市':'大阪','神戸市':'兵庫','岡山市':'岡山','広島市':'広島','北九州市':'福岡','福岡市':'福岡','熊本市':'熊本'}
COLS={'F0':2,'F1':6,'F2':10,'F3':11,'F4':12,'F5':13,'F6':14,'F7':15,'F8':16,'F9':17,'てんかん':18,'その他の疾患分類':19,'在院患者数':20}
issues=[]; st=collections.Counter()
for y,e in [(2015,'h27'),(2016,'h28')]:
    s=read_sheets(f'data/raw/seishin630/{e}/{e}_630/{e}_630.xlsx')['Ⅲ.2.(5)総数']
    rows={}
    for r in range(6,73):
        n=s.get((r,1))
        if isinstance(n,str): rows[re.sub(r'\s','',n)]=r
    for sn,c in COLS.items():
        vals={n:s.get((r,c)) for n,r in rows.items()}
        # 合計＝全行の和
        tot=vals.get('合計'); sm=sum(v for n,v in vals.items() if n!='合計' and isinstance(v,float))
        st['sum']+=1
        if tot is not None and abs(tot-sm)>0.5: issues.append((y,sn,'旧様式 行の和≠合計',tot,sm))
        incl=dict(vals)
        for city,pref in CITY_PREF.items():
            if city in vals and pref in incl and isinstance(vals[city],float): incl[pref]=incl[pref]+vals[city]
        for n,v in incl.items():
            if n=='合計' or not isinstance(v,float): continue
            b=lt(sn,n,y)
            if b is None: continue
            st['cmp']+=1
            if abs(v-b)>0.5: issues.append((y,sn,n,'旧様式（指定都市を足した値）',v,'長期',b))
with open('results/seishin630/c303_old_vs_longterm.tsv','w') as w:
    w.write(json.dumps(dict(st),ensure_ascii=False)+'\n')
    for i in issues: w.write('\t'.join(map(str,i))+'\n')
print(dict(st),'issues',len(issues))
for i in issues[:40]: print(i)

# 照合の要約（lib/tally.py）：単位は旧様式の行の和＝合計の式と、旧様式と長期データのセル。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('seishin630', 'c303', note='630調査 旧様式（2015・2016年）と長期データ', script=__file__)
_t.set(compared=st['sum'] + st['cmp'], mismatched=len(issues)); print('tally', _t.save())
