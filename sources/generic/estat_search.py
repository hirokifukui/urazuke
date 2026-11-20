#!/usr/bin/env python3
"""e-Stat のファイル検索結果（layout=dataset）を TSV に。URL 探索用。
使い方: python3 estat_search.py <toukei> <query> [pages]
出力: statInfId<TAB>fileKinds<TAB>表題・調査年など（項目を | で連結）"""
import sys,re,html,urllib.request,urllib.parse
UA="Mozilla/5.0"
toukei,q=sys.argv[1],sys.argv[2]; pages=int(sys.argv[3]) if len(sys.argv)>3 else 3
for p in range(1,pages+1):
    u=f"https://www.e-stat.go.jp/stat-search/files?page={p}&layout=dataset&toukei={toukei}&query={urllib.parse.quote(q)}&metadata=1&data=1"
    t=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA}),timeout=60).read().decode('utf-8')
    items=re.split(r'class="stat-resource_list-item',t)[1:]
    if not items: break
    for b in items:
        ids=sorted(set(re.findall(r'statInfId=(\d+)&(?:amp;)?fileKind=(\d)',b)))
        det=[re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',x))).strip() for x in re.findall(r'class="stat-resource_list-detail-item(?:-text)?"[^>]*>(.*?)</(?:li|span>\s*</a)>',b,re.S)]
        if ids: print(f"{ids[0][0]}\t{','.join(k for _,k in ids)}\t{' | '.join(d for d in det if d)}")
