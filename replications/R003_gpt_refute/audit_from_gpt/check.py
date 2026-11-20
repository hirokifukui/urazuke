from pathlib import Path
import zipfile,xml.etree.ElementTree as E,json
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def sheets(p):
 with zipfile.ZipFile(p) as z:
  ss=[]
  if 'xl/sharedStrings.xml' in z.namelist():
   ss=[''.join(x.itertext()) for x in E.fromstring(z.read('xl/sharedStrings.xml'))]
  rel={x.attrib['Id']:x.attrib['Target'] for x in E.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
  for s in E.fromstring(z.read('xl/workbook.xml')).find('s:sheets',NS):
   t=rel[s.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]; t=t.lstrip('/') if t.startswith('/') else 'xl/'+t
   rows=[]
   for r in E.fromstring(z.read(t)).findall('.//s:sheetData/s:row',NS):
    cells={}
    for c in r:
     v=c.find('s:v',NS); val=v.text if v is not None else ''.join(c.find('s:is',NS).itertext()) if c.find('s:is',NS) is not None else None
     if c.attrib.get('t')=='s' and val is not None: val=ss[int(val)]
     if val is not None: cells[c.attrib['r']]=val
    if cells: rows.append(cells)
   yield s.attrib['name'],rows
if __name__=='__main__':
 data={str(p):dict(sheets(p)) for p in sorted(Path('hakusho').glob('*/*.xlsx'))}
 Path('audit/cells.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
 with open('audit/cells.txt','w') as f:
  for p,ss in data.items():
   for name,rows in ss.items():
    f.write(f'\nFILE {p} SHEET {name}\n')
    for row in rows:f.write(' | '.join(k+'='+v for k,v in row.items())+'\n')
