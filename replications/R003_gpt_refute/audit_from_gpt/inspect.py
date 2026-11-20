import json,re
D=json.load(open('audit/cells.json'))
def get(ed,file,pattern):
 return [(s,rs) for s,rs in D[f'hakusho/{ed}/{file}.xlsx'].items() if pattern in s]
for ed in ['r04','r05','r06','r07']:
 for s,rs in get(ed,'4-2-2-2','①'):
  print(ed,s)
  for r in rs:
   if any(re.match('202[123]年',v) for v in r.values()):print(r)
for ed in ['r06','r07']:
 for pat in ['①','③']:
  for s,rs in get(ed,'5-4-4',pat):
   print(ed,s)
   for r in rs:
    n=int(re.search(r'\d+',next(iter(r))).group())
    if n<=8 or any(re.match('(2016|2017)年',v) for v in r.values()): print({k:v for k,v in r.items() if re.match('(B|C|D|AM|AN|AO|AP)\\d',k)} if n>6 else r)
for ed in ['r03','r04','r05']:
 for f,pat in [('1-1-1-1','機械'),('1-1-1-5','①（S61'),('1-1-1-5','②※機械'),('1-1-1-5','③※機械'),('3-1-1-4','機械')]:
  for s,rs in get(ed,f,pat):
   print(ed,s)
   for r in rs:
    if any(v.startswith('2002年') or v.startswith('2014年') for v in r.values()) or any('総数' in v or '14～' in v or '男子' in v for v in r.values()):print(r)
