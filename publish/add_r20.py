"""r20 で足した記録・見出し・照会・統計ページ・原文の引用の対象を、各ファイルに差し込む（何度回しても同じ結果になる）。
正本はこのファイルの R20 表。build_findings.py・headlines.tsv・build_inquiries.py・site/build_site.py・checks/quotes/targets.tsv を書き換える。"""
import re, json
C = '機械検証のみ'
# (id, 統計, 照会先, 根拠, 業務との関係, 区分, 格付け, 確実さ, 要旨, 撤回の条件, 再現, 影響, 見出し, 問い, [引用の対象 (label, glob, tokens, mode)])
R20 = json.load(open('publish/r20_records.json'))
STATS20 = json.load(open('publish/r20_stats.json'))
# ---- build_findings.py
p = 'publish/build_findings.py'; s = open(p).read()
s = re.sub(r'\n# ---- r20 BEGIN.*?# ---- r20 END\n', '\n', s, flags=re.S)
blk = ['# ---- r20 BEGIN（publish/add_r20.py が生成。手で編集しない）']
for r in R20:
    blk.append('add(' + ', '.join(f'{k}={v!r}' for k, v in [('id', r['id']), ('統計', r['統計']), ('照会先', r['照会先']), ('根拠', r['根拠']), ('業務との関係', r['業務との関係']), ('区分', r['区分']), ('格付け', r['格付け']), ('確実さ', r['確実さ']), ('確認', r.get('確認', C)), ('要旨', r['要旨']), ('撤回の条件', r['撤回の条件']), ('再現', r['再現'])]) + ')')
blk.append('# ---- r20 END\n')
s = s.replace("os.makedirs('publish/cards', exist_ok=True)", '\n'.join(blk) + "os.makedirs('publish/cards', exist_ok=True)", 1)
open(p, 'w').write(s)
# ---- headlines.tsv
p = 'publish/headlines.tsv'; L = [l for l in open(p) if l.split('\t')[0] not in {r['id'] for r in R20}]
L += [f"{r['id']}\t{r['影響']}\t{r['見出し']}\n" for r in R20]; open(p, 'w').writelines(L)
# ---- build_inquiries.py
p = 'publish/build_inquiries.py'; s = open(p).read()
s = re.sub(r"\n # r20 BEGIN.*? # r20 END\n", '\n', s, flags=re.S)
qs = ''.join(f" {r['id']!r}:{r['問い']!r},\n" for r in R20)
s = s.replace("\n}\nos.makedirs('publish/inquiries'", "\n # r20 BEGIN\n" + qs + " # r20 END\n}\nos.makedirs('publish/inquiries'", 1)
open(p, 'w').write(s)
# ---- site/build_site.py
p = 'site/build_site.py'; s = open(p).read()
s = re.sub(r"\n # r20 BEGIN.*? # r20 END\n", '\n', s, flags=re.S)
st = ''.join(f" ({x['slug']!r},{x['名前']!r},{x['公表元']!r},{x['作業ノート']!r},{x['接頭辞']!r}),\n" for x in STATS20)
s = s.replace(" ('seishin630',", " # r20 BEGIN\n" + st + " # r20 END\n ('seishin630',", 1) if "('seishin630'," in s else s
s = re.sub(r"\nCHK\.update\(\{.*?\}\)  # r20\n", '\n', s, flags=re.S)
chk = {x['slug']: x['CHK'] for x in STATS20 if x.get('CHK')}
s = s.replace("import subprocess as _sp", f"CHK.update({chk!r})  # r20\nimport subprocess as _sp", 1)
open(p, 'w').write(s)
# ---- checks/quotes/targets.tsv
p = 'checks/quotes/targets.tsv'; L = [l for l in open(p) if l.split('\t')[0] not in {r['id'] for r in R20}]
for r in R20:
    for lab, g, tok, mode in r['引用']: L.append(f"{r['id']}\t{lab}\t{g}\t{tok}\t{mode}\n")
open(p, 'w').writelines(L)
print(len(R20), 'records,', len(STATS20), 'stats')

# ---- 犯罪統計・警察白書の統計ページに接頭辞 KH を付け、照合の欄を書き換える
p = 'site/build_site.py'; s = open(p).read()
s = s.replace("('keisatsu','犯罪統計・警察白書','警察庁','results/keisatsu/FINDINGS.md',None)", "('keisatsu','犯罪統計・警察白書','警察庁','results/keisatsu/FINDINGS.md','KH')")
s = s.replace("'keisatsu':'照合済み・記録なし（約13万8千の値：全表の内部整合・版間・警察白書／犯罪白書との突き合わせ）'",
              "'keisatsu':'約13万8千の値（全表の内部整合・版間・警察白書／犯罪白書との突き合わせ）は記録なし。犯罪統計書 第56表の関係の区分（KH-K1、作業ノートは results/stalker/FINDINGS.md）'")
open(p, 'w').write(s)
