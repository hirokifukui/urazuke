"""旧形式 .xls を lib/xlsx.py と同じ形 {シート名: {(行, 列): 値}} で読む（xlrd、~/.venvs/urazuke）。"""
import xlrd
def read_sheets(path):
    b=xlrd.open_workbook(path,on_demand=True); out={}
    for sh in b.sheets():
        d={}
        for r in range(sh.nrows):
            for c in range(sh.ncols):
                cell=sh.cell(r,c)
                if cell.ctype in (xlrd.XL_CELL_EMPTY,xlrd.XL_CELL_BLANK): continue
                v=cell.value
                if cell.ctype==xlrd.XL_CELL_NUMBER: v=float(v)
                elif isinstance(v,str): v=v.strip()
                if v=='' : continue
                d[(r+1,c+1)]=v
        out[sh.name]=d
    return out
