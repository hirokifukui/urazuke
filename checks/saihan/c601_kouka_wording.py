# 再犯防止推進白書（平成30年版〜令和7年版の全体版 PDF）から、効果検証の結果を述べる文を抜き出す（記録 YK-C1 の型の総点検、H038）。
import os, re, glob, subprocess, json
OUT = 'results/saihan/kouka_wording'; os.makedirs(OUT, exist_ok=True)
PAT = re.compile(r'(効果検証|処遇効果|再犯抑止効果|指導効果|受講効果|効果が(認め|確認|示唆|見られ|み られ|あ)|示唆され|有意)')
rows = []
for f in sorted(glob.glob('data/raw/saihan/*/zentai_*.pdf')):
    ed = f.split('/')[3]
    n = int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', f], capture_output=True, text=True).stdout).group(1))
    txt = subprocess.run(['pdftotext', '-layout', f, '-'], capture_output=True, text=True).stdout
    pages = txt.split('\f')
    for p, t in enumerate(pages, 1):
        flat = re.sub(r'\s+', '', t)
        for s in re.split(r'(?<=。)', flat):
            if PAT.search(s) and ('効果' in s) and len(s) < 400:
                rows.append(dict(edition=ed, file=os.path.basename(f), page=p, text=s))
json.dump(rows, open(f'{OUT}/sentences.json', 'w'), ensure_ascii=False, indent=1)
print(len(rows))
