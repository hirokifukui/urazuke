"""r11 で足した記録・見出し・照会・統計ページ・原文の引用の対象を、各ファイルに差し込む（何度回しても同じ結果になる）。
正本はこのファイルの R11 表。build_findings.py・headlines.tsv・build_inquiries.py・site/build_site.py・checks/quotes/targets.tsv を書き換える。"""
import re, json
C = '機械検証のみ'
# (id, 統計, 照会先, 根拠, 業務との関係, 区分, 格付け, 確実さ, 要旨, 撤回の条件, 再現, 影響, 見出し, 問い, [引用の対象 (label, glob, tokens, mode)])
R11 = json.load(open('publish/r11_records.json'))
STATS11 = json.load(open('publish/r11_stats.json'))
# ---- build_findings.py
p = 'publish/build_findings.py'; s = open(p).read()
s = re.sub(r'\n# ---- r11 BEGIN.*?# ---- r11 END\n', '\n', s, flags=re.S)
blk = ['# ---- r11 BEGIN（publish/add_r11.py が生成。手で編集しない）']
for r in R11:
    blk.append('add(' + ', '.join(f'{k}={v!r}' for k, v in [('id', r['id']), ('統計', r['統計']), ('照会先', r['照会先']), ('根拠', r['根拠']), ('業務との関係', r['業務との関係']), ('区分', r['区分']), ('格付け', r['格付け']), ('確実さ', r['確実さ']), ('確認', r.get('確認', C)), ('要旨', r['要旨']), ('撤回の条件', r['撤回の条件']), ('再現', r['再現'])]) + ')')
blk.append('# ---- r11 END\n')
s = s.replace("os.makedirs('publish/cards', exist_ok=True)", '\n'.join(blk) + "os.makedirs('publish/cards', exist_ok=True)", 1)
open(p, 'w').write(s)
# ---- headlines.tsv
p = 'publish/headlines.tsv'; L = [l for l in open(p) if l.split('\t')[0] not in {r['id'] for r in R11}]
L += [f"{r['id']}\t{r['影響']}\t{r['見出し']}\n" for r in R11]; open(p, 'w').writelines(L)
# ---- build_inquiries.py
p = 'publish/build_inquiries.py'; s = open(p).read()
s = re.sub(r"\n # r11 BEGIN.*? # r11 END\n", '\n', s, flags=re.S)
qs = ''.join(f" {r['id']!r}:{r['問い']!r},\n" for r in R11)
s = s.replace("\n}\nos.makedirs('publish/inquiries'", "\n # r11 BEGIN\n" + qs + " # r11 END\n}\nos.makedirs('publish/inquiries'", 1)
open(p, 'w').write(s)
# ---- site/build_site.py
p = 'site/build_site.py'; s = open(p).read()
s = re.sub(r"\nCHK\.update\(\{.*?\}\)  # r11\n", '\n', s, flags=re.S)
chk = {x['slug']: x['CHK'] for x in STATS11 if x.get('CHK')}
s = s.replace("import subprocess as _sp", f"CHK.update({chk!r})  # r11\nimport subprocess as _sp", 1)
open(p, 'w').write(s)
# ---- checks/quotes/targets.tsv
p = 'checks/quotes/targets.tsv'; L = [l for l in open(p) if l.split('\t')[0] not in {r['id'] for r in R11}]
for r in R11:
    for lab, g, tok, mode in r['引用']: L.append(f"{r['id']}\t{lab}\t{g}\t{tok}\t{mode}\n")
open(p, 'w').writelines(L)
print(len(R11), 'records,', len(STATS11), 'stats')
# ---- 訂正の記録（ERR）
p = 'site/build_site.py'; s = open(p).read()
ERR11 = json.load(open('publish/r11_err.json'))
blk = " # r11 ERR BEGIN\n" + ''.join(f" {tuple(e)!r},\n" for e in ERR11) + " # r11 ERR END\n"
if '# r11 ERR BEGIN' in s:
    s = re.sub(r" # r11 ERR BEGIN\n.*? # r11 ERR END\n", lambda m: blk, s, flags=re.S)
else:
    i = s.index('ERR = ['); j = s.index("')]\n", i)
    s = s[:j + 2] + ',\n' + blk + ']\n' + s[j + 4:]
open(p, 'w').write(s)
