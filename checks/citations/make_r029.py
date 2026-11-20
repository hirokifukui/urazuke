"""R029：引用の型の判定を別系統（Codex）に独立に付けさせる盲検フォルダを作る（H034）。
記録 ID・媒体名は渡さない。渡すのは、元の文・引用の文・型の定義だけ。対照2つ（型が明らかな作例）を混ぜる。"""
import csv, os, json, random, hashlib
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BL = os.path.expanduser('~/mitodoke_blind/R029'); os.makedirs(BL)
rows = list(csv.DictReader(open(os.path.join(ROOT, 'results/citations/citations_draft.tsv')), delimiter='\t'))
cases = [(r['qid'], r['元の文（元の資料）'], r['引用の文'], r['掲載日']) for r in rows]
cases += [('CTRL-T1', '確定値 214,843件（2024年9月公表）。', '確定値は21万4,483件だった（2024年9月公表）。', '2024-09'),
          ('CTRL-T0', 'ストーカー規制法違反検挙 1,081件（令和5年）。', '2023年のストーカー規制法違反の検挙は1081件だった。', '2024-03')]
random.Random(20261118).shuffle(cases)
key = {}; L = []
for n, (q, src, cit, d) in enumerate(cases, 1):
    key[f'C{n:02d}'] = q
    L.append(f'### C{n:02d}\n- 引用の掲載時期：{d}\n- 元の資料の文：{src}\n- 引用の文：{cit}\n')
P = '''# 課題：引用の型の判定

公的な資料の文（元の資料の文）と、それを引いた文（引用の文）の組が下にあります。各組について、次の型のうち当てはまるものをすべて付けてください。文の比較だけで決め、引いた側の意図や評価は書かないでください。

## 型の定義（これ以外は付けない）
- T0 同じ：数値も言い方も元と同じ（言い換えでも、量と強さが同じなら T0）。
- T1 値が違う：数値が元と違う（写し間違い、速報値と確定値の取り違えを含む）。
- T2 量が置き換わる：別の量として書く（ハザード比や「再犯可能性」を「再犯率」と書く、別の群の比較を同じ集団の「低下」と書く、など）。
- T3 言い方が強まる：元の「示唆」「有意傾向」「可能性」が「確認」「効果があった」「認められた」などになる。
- T4 限定が落ちる：元の資料の文にある但し書き・条件（効果が裏付けられなかった群、数え方の変更、など）を書かずに結論や比較を引く。引用の文の中にその但し書きがあれば T4 にしない。
- T5 後の訂正が入っていない：元の資料が後に直された（正誤表・確定値）のに、引用の掲載時期にはすでに直っていた値を、直す前の値のまま引く。

T0 は他の型と同時に付けない。元の資料の文に書かれていないことは判断の材料にしない。判断できないときは「判定不能」とし、理由を書く。

## 組
''' + '\n'.join(L) + '''
## 出力
REPORT.md に、組ごとに「型（複数可）」「根拠（どの語・数値の違いか、1〜2文）」を表で書く。最後に全体の要約を3行以内で書く。
'''
open(os.path.join(BL, 'PROMPT.md'), 'w').write(P)
rep = os.path.join(ROOT, 'replications/R029_gpt_types'); os.makedirs(rep, exist_ok=True)
json.dump(key, open(os.path.join(rep, 'KEY.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(rep, 'PROMPT.md'), 'w').write(P)
open(os.path.join(rep, 'FIXED_SHA256.txt'), 'w').write(hashlib.sha256(P.encode()).hexdigest() + '  PROMPT.md\n')
open(os.path.join(rep, 'PROTOCOL.md'), 'w').write('# R029 引用の型の判定（別系統：GPT / Codex CLI）— H034\n作成：2026-11-18（実行前に固定）\n渡したもの：元の文・引用の文・掲載時期・型の定義だけ（記録 ID・媒体名・URL は渡さない）。\n対照：CTRL-T1（値の写し間違いの作例）・CTRL-T0（同じの作例）。両方正答の場合だけ採る。\n組の順序は乱数（種 20261118）で並べ替えた。対応は KEY.json。\n')
sh = os.path.expanduser('~/mitodoke_blind/run_R029.sh')
open(sh, 'w').write('#!/bin/sh\ncodex exec --json --skip-git-repo-check -s workspace-write -C ~/mitodoke_blind/R029 -o ~/mitodoke_blind/R029_lastmsg.md - < ~/mitodoke_blind/R029/PROMPT.md > ~/mitodoke_blind/R029_events.jsonl 2> ~/mitodoke_blind/R029_err.log\necho "exit=$? $(date \'+%F %T\')" > ~/mitodoke_blind/R029.done\n')
os.chmod(sh, 0o755)
print(len(cases), 'cases', {k: v for k, v in key.items() if v.startswith('CTRL')})
