"""r12 で足した記録・見出し・照会・統計ページ・原文の引用の対象を、各ファイルに差し込む（何度回しても同じ結果になる）。
正本はこのファイルの R12 表。build_findings.py・headlines.tsv・build_inquiries.py・site/build_site.py・checks/quotes/targets.tsv を書き換える。"""
import re, json
C = '機械検証のみ'
# (id, 統計, 照会先, 根拠, 業務との関係, 区分, 格付け, 確実さ, 要旨, 撤回の条件, 再現, 影響, 見出し, 問い, [引用の対象 (label, glob, tokens, mode)])
R12 = json.load(open('publish/r12_records.json'))
STATS12 = json.load(open('publish/r12_stats.json'))
# ---- build_findings.py
p = 'publish/build_findings.py'; s = open(p).read()
s = re.sub(r'\n# ---- r12 BEGIN.*?# ---- r12 END\n', '\n', s, flags=re.S)
blk = ['# ---- r12 BEGIN（publish/add_r12.py が生成。手で編集しない）']
for r in R12:
    blk.append('add(' + ', '.join(f'{k}={v!r}' for k, v in [('id', r['id']), ('統計', r['統計']), ('照会先', r['照会先']), ('根拠', r['根拠']), ('業務との関係', r['業務との関係']), ('区分', r['区分']), ('格付け', r['格付け']), ('確実さ', r['確実さ']), ('確認', r.get('確認', C)), ('要旨', r['要旨']), ('撤回の条件', r['撤回の条件']), ('再現', r['再現'])]) + ')')
blk.append('# ---- r12 END\n')
s = s.replace("os.makedirs('publish/cards', exist_ok=True)", '\n'.join(blk) + "os.makedirs('publish/cards', exist_ok=True)", 1)
open(p, 'w').write(s)
# ---- headlines.tsv
p = 'publish/headlines.tsv'; L = [l for l in open(p) if l.split('\t')[0] not in {r['id'] for r in R12}]
L += [f"{r['id']}\t{r['影響']}\t{r['見出し']}\n" for r in R12]; open(p, 'w').writelines(L)
# ---- build_inquiries.py
p = 'publish/build_inquiries.py'; s = open(p).read()
s = re.sub(r"\n # r12 BEGIN.*? # r12 END\n", '\n', s, flags=re.S)
qs = ''.join(f" {r['id']!r}:{r['問い']!r},\n" for r in R12)
s = s.replace("\n}\nos.makedirs('publish/inquiries'", "\n # r12 BEGIN\n" + qs + " # r12 END\n}\nos.makedirs('publish/inquiries'", 1)
open(p, 'w').write(s)
# ---- site/build_site.py
p = 'site/build_site.py'; s = open(p).read()
s = re.sub(r"\nCHK\.update\(\{.*?\}\)  # r12\n", '\n', s, flags=re.S)
chk = {x['slug']: x['CHK'] for x in STATS12 if x.get('CHK')}
s = s.replace("import subprocess as _sp", f"CHK.update({chk!r})  # r12\nimport subprocess as _sp", 1)
open(p, 'w').write(s)
# ---- checks/quotes/targets.tsv
p = 'checks/quotes/targets.tsv'; L = [l for l in open(p) if l.split('\t')[0] not in {r['id'] for r in R12}]
for r in R12:
    for lab, g, tok, mode in r['引用']: L.append(f"{r['id']}\t{lab}\t{g}\t{tok}\t{mode}\n")
open(p, 'w').writelines(L)
print(len(R12), 'records,', len(STATS12), 'stats')
# ---- 訂正の記録（ERR）
p = 'site/build_site.py'; s = open(p).read()
ERR12 = json.load(open('publish/r12_err.json'))
blk = " # r12 ERR BEGIN\n" + ''.join(f" {tuple(e)!r},\n" for e in ERR12) + " # r12 ERR END\n"
if '# r12 ERR BEGIN' in s:
    s = re.sub(r" # r12 ERR BEGIN\n.*? # r12 ERR END\n", lambda m: blk, s, flags=re.S)
else:
    assert ' # r11 ERR END\n]' in s
    s = s.replace(' # r11 ERR END\n]', ' # r11 ERR END\n' + blk + ']', 1)
open(p, 'w').write(s)
