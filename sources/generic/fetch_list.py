#!/usr/bin/env python3
"""URL の一覧（TSV: URL<TAB>保存先の相対パス）を取得し、MANIFEST.tsv を残す。
使い方: python3 fetch_list.py <一覧.tsv> <保存先ディレクトリ>
既にあるファイルは取り直さない（上書きしない）。"""
import sys,os,hashlib,time,urllib.request,urllib.error
from datetime import datetime,timezone
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
lst,out=sys.argv[1],sys.argv[2]; os.makedirs(out,exist_ok=True)
man=os.path.join(out,'MANIFEST.tsv'); new=not os.path.exists(man)
with open(man,'a') as M:
    if new: M.write('url\tpath\tbytes\tsha256\tstatus\tlast_modified\tfetched_utc\n')
    for line in open(lst):
        line=line.strip()
        if not line or line.startswith('#'): continue
        url,rel=line.split('\t'); dst=os.path.join(out,rel)
        if os.path.exists(dst): continue
        os.makedirs(os.path.dirname(dst),exist_ok=True)
        for attempt in range(4):   # 429（回数制限）のときは待って取り直す（30・90・180秒）
            try:
                with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':('curl/8.7.1' if 'web.archive.org' in url else UA)}),timeout=120) as r:
                    b=r.read(); st=r.status; lm=r.headers.get('Last-Modified','')
            except urllib.error.HTTPError as e: b=b''; st=e.code; lm=''
            except Exception as e: b=b''; st='ERR:'+type(e).__name__; lm=''
            if st!=429: break
            time.sleep([30,90,180,0][attempt])
        if b: open(dst,'wb').write(b)
        M.write(f"{url}\t{rel}\t{len(b)}\t{hashlib.sha256(b).hexdigest() if b else ''}\t{st}\t{lm}\t{datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"); M.flush()
        time.sleep(float(os.environ.get('FETCH_SLEEP','0.5')))
