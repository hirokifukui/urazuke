"""公開してよいファイルの一覧（publish/PUBLIC_FILES.tsv、sha256 つき）と、除外の一覧を作る。
方針：原データ（data/raw）は再配布せず、取得元 URL と sha256（各 MANIFEST.tsv）を公開する。
個人名を含みうる資料（教育委員会の処分ごとの発表）は、ファイルも URL も公開しない。"""
import os, hashlib, re, csv
ROOT = '.'
INCLUDE_DIRS = ['lib', 'checks', 'sources', 'results', 'hypotheses', 'replications', 'publish', 'translate']
INCLUDE_FILES = ['README.md', 'METHODS.md', 'PROCESS.md', 'TERMS.md', 'LICENSE', 'requirements.txt', 'site/build_site.py', 'site/citations_view.py', 'site/checklist_view.py', 'CITATION.cff', '.zenodo.json', 'publish/zenodo.py', 'site/crawl.json']
EXCLUDE = [r'^data/', r'/ANALYTICS\.md$', r'^crawl/analytics\.py$', r'^publish/send_mail\.py$', r'^publish/inquiry_contacts\.tsv$', r'^publish/letters/', r'zenodo_state\.json$',  r'(^|/)kyoi/', r'list_monka_kyoi\.tsv$', r'c605_kouhyou_shozai\.tsv$', r'FINDINGS_kyosei_wip\.md$', r'^hypotheses/H001_', r'^replications/R00[12]_', r'^translate/missing\.json$', r'citations_draft\.tsv$', r'^results/citations/perplexity/', r'^results/llm_probe/(?!h036/)', r'^replications/R03[234]_gpt_llmprobe/', r'^replications/R03[01]_gpt_types/(PROMPT\.md|events\.jsonl)$', r'^replications/R029_gpt_types/(PROMPT\.md|events\.jsonl)$', r'__pycache__', r'\.DS_Store$', r'\.bak', r'/\.']
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
pub, exc = [], []
for d in INCLUDE_DIRS:
    for dp, dn, fn in os.walk(d):
        for f in fn:
            p = os.path.join(dp, f)
            (exc if any(re.search(x, p) for x in EXCLUDE) else pub).append(p)
pub += [f for f in INCLUDE_FILES if os.path.exists(f)]
# 原データは MANIFEST だけ公開（個人名資料の行を除く）
for dp, dn, fn in os.walk('data/raw'):
    for f in fn:
        if f == 'MANIFEST.tsv':
            src = os.path.join(dp, f); dst = 'publish/source_manifests/' + src.replace('data/raw/', '').replace('/', '__')
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(src, errors='replace') as r, open(dst, 'w') as w:
                for line in r:
                    if 'kyoi/' in line: continue
                    w.write(line)
            if dst not in pub: pub.append(dst)
with open('publish/PUBLIC_FILES.tsv', 'w') as w:
    w.write('path\tbytes\tsha256\n')
    for p in sorted(set(pub)):
        if p.endswith('PUBLIC_FILES.tsv'): continue
        w.write(f'{p}\t{os.path.getsize(p)}\t{sha(p)}\n')
with open('publish/EXCLUDED_FILES.tsv', 'w') as w:
    w.write('path\t理由\n')
    for p in sorted(exc): w.write(f'{p}\t個人名を含みうる資料、またはキャッシュ\n')
    w.write('data/raw/**\t原データは再配布しない（取得元 URL と sha256 を source_manifests/ で公開）\n')
print('public', len(set(pub)), 'excluded', len(exc))
