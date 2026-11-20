import glob, io, re, sys, openpyxl, xlrd
pat = re.compile(sys.argv[2])
for f in sorted(glob.glob(sys.argv[1])):
    b = open(f,'rb').read()
    try:
        if b[:2]==b'PK':
            wb = openpyxl.load_workbook(io.BytesIO(b), data_only=True); sheets = [(ws.title, [list(r) for r in ws.iter_rows(values_only=True)]) for ws in wb.worksheets]
        else:
            wb = xlrd.open_workbook(file_contents=b); sheets = [(s.name, [s.row_values(i) for i in range(s.nrows)]) for s in wb.sheets()]
    except Exception as e:
        print(f, 'ERR', e); continue
    for name, R in sheets:
        for r in R:
            line = ' | '.join(str(c) for c in r if c not in (None, ''))
            if pat.search(line): print(f.split('/')[-1], name, '::', line[:260])
