# PDF の中で語句を探し、PDF の頁番号と前後の文を出す。使い方: python3 findpage.py file.pdf 語句 [語句...]
import sys, subprocess, re
pdf = sys.argv[1]
n = int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout).group(1))
for p in range(1, n + 1):
    t = subprocess.run(['pdftotext', '-f', str(p), '-l', str(p), pdf, '-'], capture_output=True, text=True).stdout
    flat = re.sub(r'\s+', '', t)
    for q in sys.argv[2:]:
        qq = re.sub(r'\s+', '', q)
        for m in re.finditer(re.escape(qq), flat):
            print(f'p{p}\t{q}\t…{flat[max(0, m.start() - 60):m.end() + 60]}…')
