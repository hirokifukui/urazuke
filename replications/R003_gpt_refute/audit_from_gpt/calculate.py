import json,re
from pathlib import Path
D=json.load(open('audit/cells.json'))
def sheet(ed,f,pat):
 return next((s,{int(re.search(r'\d+',next(iter(r))).group()):r for r in rs}) for s,rs in D[f'hakusho/{ed}/{f}.xlsx'].items() if pat in s)
def val(rows,n,col):return rows[n].get(f'{col}{n}')
print('P03 row sums',582+251,319+46,901+297,'column sums',582+319,251+46,833+365)
print('P04 rates',[(x,(x+3565)/(92511+122)*100) for x in [83315,83815]])
print('P05',1/1.485,15.1/26.2)
print('P07',226/297*100,319/901*100,46/297*100)
print('P12',1264+1531+1390,3838+410,(3838+410)-(1264+1531+1390))
# residuals, compare all seven columns to r03 official 2020 body
_,base=sheet('r03','2-2-3-2','R２）※機械')
for ed in ['r03','r04','r05','r06','r07']:
 for s,rs0 in D[f'hakusho/{ed}/2-2-3-2.xlsx'].items():
  if ed in ['r03','r04','r05'] and '機械' not in s:continue
  rs={int(re.search(r'\d+',next(iter(r))).group()):r for r in rs0}
  extra=[n for n in range(68,105) if n in rs]
  mism=[]
  for n in extra:
   for c,b in zip(['F','G','H','I','J','K','L'],['D','E','F','G','H','I','J']):
    a=val(rs,n,c);v=val(base,n-61,b)
    if a!=v:mism.append((f'{c}{n}',a,f'{b}{n-61}',v))
  print('P06',ed,s,'extra rows',len(extra),'mismatches',mism[:12], 'count',len(mism))
# cancellation all old years, sum actual annual cells
_,a=sheet('r06','5-4-4','①');_,b=sheet('r06','5-4-4','③');_,c=sheet('r07','5-4-4','③')
print('P08 all 28 equal',all(val(a,n,'AN')==val(b,n,'AN') for n in range(7,35)))
for n in range(7,35):
 nums=[int(v) for k,v in b[n].items() if re.fullmatch('[A-Z]+',re.sub('[0-9]','',k)) and re.sub('[0-9]','',k) not in ['B','C','D','AN','AO'] and v.isdigit()]
 print('P08',1982+n,'r06 AN'+str(n),val(b,n,'AN'),'sum',sum(nums),'r07 AO'+str(n),val(c,n,'AO'))
# all 2002-2014 comparison table
print('P10 year,r03 total,r04 total,r04 age total,r05 age total,r04 boys/girls,r05 boys/girls')
_,a=sheet('r03','1-1-1-1','機械');_,b=sheet('r04','1-1-1-1','機械');_,c=sheet('r04','1-1-1-5','①（S61');_,d=sheet('r05','1-1-1-5','①（S61');_,e=sheet('r04','3-1-1-4','機械');_,f=sheet('r05','3-1-1-4','機械')
for y in range(2002,2015):
 n=y-1939;m=y-1979;k=y-1959
 print(y,val(a,n,'P'),val(b,n,'L'),val(c,m,'D'),val(d,m,'D'),(val(e,k,'D'),val(e,k,'F')),(val(f,k,'D'),val(f,k,'F')))
# quantity sums; do not count subcategories K/M twice
for ed in ['r04','r05','r06','r07']:
 _,r=sheet(ed,'4-2-2-2','①')
 for n in [12,13,14]:
  if n in r and 'E'+str(n) in r[n]:print('P09',ed,n,[val(r,n,c) for c in ['E','G','I','O']],sum(int(val(r,n,c)) for c in ['E','G','I','O']))
# Verify all cells in the relevant inner-breakdown rows stayed unchanged r03->r04.
for file,pattern in [('1-1-1-5','①（S61'),('1-1-1-5','②※機械'),('1-1-1-5','③※機械'),('3-1-1-4','機械')]:
 _,old=sheet('r03',file,pattern);_,new=sheet('r04',file,pattern)
 selected=[n for n,r in old.items() if any(v.startswith(str(y)+'年') for y in range(2002,2015) for v in r.values())]
 print('P10 r03->r04 unchanged',file,pattern,len(selected),all(old[n]==new[n] for n in selected))
