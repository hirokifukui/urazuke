"""e-Stat のファイル一覧（年次）から、表番号・表題・statInfId を集める。
使い方: python3 list_tables.py <toukei> <tstat> <year>   例: 00250005 000001012930 2024（矯正統計）
        00250003 000001012929 2024（検察統計）。Excel は file-download?statInfId=<id>&fileKind=4
"""
import re,html,sys,urllib.request,time
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
toukei,tstat,year=sys.argv[1],sys.argv[2],sys.argv[3]
rows=[];page=1
while True:
    u=f"https://www.e-stat.go.jp/stat-search/files?page={page}&layout=datalist&cycle=7&toukei={toukei}&tstat={tstat}&tclass1val=0&year={year}0&month=0&result_back=1"
    s=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":UA}),timeout=40).read().decode()
    items=re.findall(r'<article class="stat-dataset_list-item.*?</article>',s,re.S)
    got=0
    for blk in items:
        m=re.search(r'表番号\s*</span>\s*<span[^>]*>\s*([^<]+)',blk)
        txt=re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",blk))).strip()
        mm=re.search(r'表番号 (\S+) (.*?) 調査年月',txt)
        ids=re.findall(r'statInfId=(\d+)&(?:amp;)?fileKind=(\d)',blk)
        if mm:
            rows.append((mm.group(1),mm.group(2),ids)); got+=1
    if got==0: break
    page+=1; time.sleep(0.5)
    if page>30: break
for r in rows: print(r[0],"|",r[1],"|",",".join(f"{a}:{b}" for a,b in r[2]))
print("TOTAL",len(rows),file=sys.stderr)
