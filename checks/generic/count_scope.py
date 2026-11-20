"""検証の対象にした資料の規模を数える（ファイル数・バイト・数値セル・PDF頁）。個人名を含みうる kyoi は除く。"""
import os, json, re, subprocess, zipfile, io, csv, sys
import openpyxl, xlrd
R='data/raw'; out={'files':0,'bytes':0,'xlsx':0,'xls':0,'csv':0,'pdf':0,'html':0,'numeric_cells':0,'pdf_pages':0,'errors':0,'by_dir':{}}
num=re.compile(r'^-?[\d,]+(\.\d+)?$')
def cnt_xlsx(b):
    wb=openpyxl.load_workbook(io.BytesIO(b),read_only=True,data_only=True); n=0
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            for v in row:
                if isinstance(v,(int,float)) and not isinstance(v,bool): n+=1
    return n
def cnt_xls(b):
    wb=xlrd.open_workbook(file_contents=b); n=0
    for s in wb.sheets():
        for r in range(s.nrows):
            for c in s.row_types(r):
                if c==xlrd.XL_CELL_NUMBER: n+=1
    return n
for d,_,fs in os.walk(R):
    if 'kyoi' in d: continue
    top=d.split('/')[2] if d.count('/')>=2 else d
    for f in fs:
        p=os.path.join(d,f); ext=f.rsplit('.',1)[-1].lower(); b=open(p,'rb').read()
        out['files']+=1; out['bytes']+=len(b); n=0
        try:
            if b[:2]==b'PK' and ext in('xlsx','xls'): n=cnt_xlsx(b); out['xlsx']+=1
            elif ext=='xls': n=cnt_xls(b); out['xls']+=1
            elif ext=='csv':
                t=b.decode('cp932',errors='ignore'); n=sum(1 for row in csv.reader(io.StringIO(t)) for v in row if num.match(v.strip() or 'x')); out['csv']+=1
            elif ext=='pdf':
                o=subprocess.run(['pdfinfo',p],capture_output=True,text=True,errors='ignore').stdout
                m=re.search(r'Pages:\s+(\d+)',o); out['pdf_pages']+=int(m.group(1)) if m else 0; out['pdf']+=1
            elif ext=='html': out['html']+=1
        except Exception: out['errors']+=1
        out['numeric_cells']+=n
        bd=out['by_dir'].setdefault(top,{'files':0,'numeric_cells':0}); bd['files']+=1; bd['numeric_cells']+=n
json.dump(out,open('results/scope/scope.json','w'),ensure_ascii=False,indent=1)
print({k:v for k,v in out.items() if k!='by_dir'})
