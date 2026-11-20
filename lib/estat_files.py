"""estat_files.py <datalist URL> [タイトルの正規表現]
e-Stat の「ファイル」一覧（layout=datalist）を全ページ読み、
statInfId<TAB>表番号<TAB>表題<TAB>調査年月<TAB>公開日<TAB>形式(カンマ区切り：0=Excel,1=CSV,2=PDF…) を出す。"""
import sys, re, urllib.request, html, subprocess
base = sys.argv[1]; pat = re.compile(sys.argv[2]) if len(sys.argv) > 2 else None
seen = set()
for page in range(1, 60):
    u = re.sub(r'page=\d+', f'page={page}', base)
    t = subprocess.run(['curl', '-sL', '--max-time', '60', u], capture_output=True, text=True).stdout
    arts = re.split(r'<article class="stat-dataset_list-item">', t)[1:]
    new = 0
    for a in arts:
        m = re.search(r'data-value="(\d{12})"[^>]*>\s*(.*?)\s*</a>', a, re.S)
        if not m: continue
        sid, title = m[1], re.sub(r'\s+', ' ', html.unescape(m[2])).strip()
        if sid in seen: continue
        seen.add(sid); new += 1
        no = re.search(r'表番号&nbsp;</span><span>(.*?)</span>', a)
        ym = re.search(r'調査年月&nbsp;&nbsp;</span>\s*(.*?)</div>', a, re.S)
        pd = re.search(r'公開（更新）日&nbsp;&nbsp;</span>\s*(.*?)\s*</div>', a, re.S)
        kinds = sorted(set(re.findall(rf'statInfId={sid}&fileKind=(\d)', a)))
        if pat and not pat.search(title): continue
        print('\t'.join([sid, no[1] if no else '', title, (ym[1].strip() if ym else ''), (pd[1].strip() if pd else ''), ','.join(kinds)]), flush=True)
    if new == 0: break
