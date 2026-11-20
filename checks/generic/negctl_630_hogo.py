"""陰性対照（値を1か所変えると、検査が検出することを確かめる）：630調査 c301・c302、保護局 c104。
元のファイルは変えない。一時フォルダに写しを作って走らせる。
使い方: ~/.venvs/urazuke/bin/python checks/generic/negctl_630_hogo.py"""
import os, shutil, subprocess, tempfile, re, openpyxl, json
R = os.getcwd(); PY = os.path.expanduser('~/.venvs/urazuke/bin/python'); PY3 = shutil.which('python3')  # c104 は scipy を使うため、scipy の入った python3 で走らせる
out = []
def mk():
    t = tempfile.mkdtemp(prefix='negctl_')
    for d in ('lib', 'checks'): os.symlink(os.path.join(R, d), os.path.join(t, d))
    os.makedirs(os.path.join(t, 'results/seishin630')); os.makedirs(os.path.join(t, 'results/moj_sexoffender'))
    return t
def run(t, script):
    subprocess.run([PY, script], cwd=t, capture_output=True, text=True, timeout=600)
def nlines(p): return sum(1 for _ in open(p))
# --- 630
t = mk(); src = os.path.join(R, 'data/raw/seishin630'); dst = os.path.join(t, 'data/raw/seishin630'); os.makedirs(dst)
for n in os.listdir(src):
    if n != 'longterm_1998_2025.xlsx': os.symlink(os.path.join(src, n), os.path.join(dst, n))
wb = openpyxl.load_workbook(os.path.join(src, 'longterm_1998_2025.xlsx'))
def bump(sn, name, year, d):
    ws = wb[sn]; yc = [c.column for c in ws[4] if c.value == year or c.value == float(year)][0]
    for r in range(5, 73):
        if ws.cell(r, 1).value == name:
            ws.cell(r, yc).value = ws.cell(r, yc).value + d; return (sn, name, year, d)
ch = [bump('在院患者数', '青森', 2020, 100), bump('F7', '青森', 2020, 7)]
wb.save(os.path.join(dst, 'longterm_1998_2025.xlsx'))
run(t, 'checks/seishin630/c301_longterm_internal.py'); run(t, 'checks/seishin630/c302_longterm_vs_annual.py')
base = {k: nlines(os.path.join(R, f'results/seishin630/{k}.tsv')) for k in ('c301_longterm_internal', 'c302_longterm_vs_annual')}
new = {k: nlines(os.path.join(t, f'results/seishin630/{k}.tsv')) for k in base}
newl = [l for l in open(os.path.join(t, 'results/seishin630/c302_longterm_vs_annual.tsv')) if '青森' in l and '2020' in l]
out.append({'対象': '630 c301・c302', '変更': ch, '検出の行数（元→変更後）': {k: [base[k], new[k]] for k in base}, 'c302 で拾った青森2020の行': len(newl), '判定': 'OK' if all(new[k] > base[k] for k in base) and newl else 'NG'})
shutil.rmtree(t)
# --- 保護局 c104（転記した値を1つ変える）
t = mk(); s = open(os.path.join(R, 'checks/moj_sexoffender/c104_hogo.py')).read()
orig = subprocess.run([PY3, 'checks/moj_sexoffender/c104_hogo.py'], cwd=R, capture_output=True, text=True).stdout
for a, b in [("'仮釈放':(582,251,833)", "'仮釈放':(583,251,833)")]:
    assert a in s; s2 = s.replace(a, b)
    p = os.path.join(t, 'c104_mod.py'); open(p, 'w').write(s2)
    mod = subprocess.run([PY3, p], cwd=R, capture_output=True, text=True).stdout
    diff = [l for l in mod.splitlines() if l not in orig.splitlines()]
    out.append({'対象': '保護局 c104', '変更': f'{a} → {b}', '出力の差（先頭3行）': diff[:3], '判定': 'OK' if any('False' in l for l in diff) else 'NG'})
shutil.rmtree(t)
json.dump(out, open('results/scope/negctl_630_hogo.json', 'w'), ensure_ascii=False, indent=1)
for o in out: print(o)
