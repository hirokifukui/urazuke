"""checks/RUN.tsv の行（tally=yes）と、引数を取らない検査を、1本ずつ順に走らせる（照合の要約の書き出しの移行用）。
使い方: nohup ~/.venvs/urazuke/bin/python checks/generic/run_rows.py <パターン>... > logs/rerun/_x.log 2>&1 &
  パターンが RUN.tsv の command に含まれる行を走らせ、出力を output の列のファイルに書く。
  パターンが checks/ で始まり .py で終わり、RUN.tsv にないときは、引数なしで走らせ、logs/rerun/<検査>.log に書く。"""
import csv, os, sys, subprocess, time
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(R)
PY = os.path.expanduser('~/.venvs/urazuke/bin/python')
rows = list(csv.DictReader(open('checks/RUN.tsv', encoding='utf-8'), delimiter='\t'))
os.makedirs('logs/rerun', exist_ok=True)
for pat in sys.argv[1:]:
    hit = [r for r in rows if pat in r['command'] and r.get('tally', 'yes') == 'yes']
    jobs = [(r['command'], r['output']) for r in hit]
    if not jobs and pat.startswith('checks/') and pat.endswith('.py'):
        jobs = [(pat, 'logs/rerun/' + os.path.basename(pat)[:-3] + '.log')]
    for cmd, out in jobs:
        t = time.time()
        print(time.strftime('%H:%M:%S'), 'start', cmd, flush=True)
        with open(out, 'w') as w:
            rc = subprocess.run([PY] + cmd.split(), stdout=w, stderr=subprocess.STDOUT).returncode
        print(time.strftime('%H:%M:%S'), 'end rc=%d %.0fs' % (rc, time.time() - t), out, flush=True)
print('ALLDONE', flush=True)
