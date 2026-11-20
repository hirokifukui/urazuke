"""R046（H038）：再犯防止推進白書が効果検証の結果を述べる文と、元の資料の文を比べる。判定は GPT（Codex）と Gemini（H037）。
対になる組は、白書の各版で同じ文のもの（白書の文 × 元の資料）を一つの組にまとめる。"""
import os, sys, json, random, hashlib
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'checks/llm_probe')); import h036_spec as S
S2012 = '\n'.join([
 '［1］刑事施設における性犯罪者処遇プログラム受講者の再犯等に関する分析 研究報告書（平成24年12月、000105286.pdf） 8頁 表5：再犯の分類別推定再犯率　全ての犯罪　受講群 21.9%　非受講群 29.6%／性犯罪　受講群 12.8%　非受講群 15.4%',
 '［2］同 10頁：「受講の有無は５％水準で有意となり，受講群は非受講群と比べて瞬間再犯確率が０．８０倍になることが示された。」「プログラムの効果が確認された。」（全対象者の「全ての再犯」についての分析）',
 '［3］同 11頁：「受講の有無の変数は有意でなく，プログラムの効果を確認するまでには至らなかった。」（全対象者の「性犯罪再犯」についての分析）',
 '［4］同 4頁：「本分析結果の精度については，一定の限界がある。」'])
PAIRS = {
 'W-KP': (S.SRC['KP-C1'], '同指導については、2019年度に効果検証の結果を公表しており、プログラム受講群の方が、非受講群よりも再犯率が10.7ポイント低いことが示され、一定の再犯抑止効果が認められた。'),
 'W-SO': (S.SRC['SO-P1'], '2019年度に実施した効果検証の結果においては、プログラム受講群の方が非受講群よりも性犯罪の再犯率が11.1ポイント低く、一定の再犯抑止効果が示唆された。'),
 'W-YK': (S.SRC['YK-C1'], '2018年（平成30年）に薬物事犯により保護観察に付された成人保護観察対象者の保護観察開始後4年以内の薬物事犯の再犯率を、同プログラム受講群と非受講群別に調査したところ、同プログラム受講群の再犯率は30.3％であり、非受講群のそれ（34.6％）より統計的に有意に低く、同プログラムの受講による一定の再犯防止効果が示唆された。'),
 'W-2012': (S2012, '2012年度（平成24年度）に実施した効果検証の結果では、プログラム受講群の方が、非受講群よりも再犯率が7.7ポイント低いことが示され、一定の再犯抑止効果が認められている。'),
 'CTRL-T0': ('令和５年の小中高生の自殺者数は 513 人。', '2023年の小中高生の自殺者数は513人だった。'),
 'CTRL-T1': ('令和４年度の児童虐待相談の対応件数（確定値）は 214,843 件。', '2022年度の児童虐待相談の対応件数（確定値）は21万4483件だった。'),
}
cases = list(PAIRS.items()); random.Random(20261124).shuffle(cases)
key = {}; L = []
for n, (q, (src, cit)) in enumerate(cases, 1):
    key[f'C{n:02d}'] = q
    L.append(f'### C{n:02d}\n- 元の資料の文：\n{src}\n- 引用の文：{cit}\n')
P0 = open(os.path.join(ROOT, 'replications/R029_gpt_types/PROMPT.md')).read()
P = P0[:P0.index('## 組')] + '## 組\n' + '\n'.join(L) + '\n## 出力\nREPORT.md に、組ごとに「型（複数可）」「根拠（どの語・数値の違いか、1〜2文）」を表で書く。最後に全体の要約を3行以内で書く。\n'
BL = os.path.expanduser('~/mitodoke_blind/R046'); os.makedirs(BL)
open(os.path.join(BL, 'PROMPT.md'), 'w').write(P)
rep = os.path.join(ROOT, 'replications/R046_gpt_hakusho'); os.makedirs(rep, exist_ok=True)
json.dump(key, open(os.path.join(rep, 'KEY.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(rep, 'PROMPT.md'), 'w').write(P)
open(os.path.join(rep, 'FIXED_SHA256.txt'), 'w').write(hashlib.sha256(P.encode()).hexdigest() + '  PROMPT.md\n')
open(os.path.join(rep, 'PROTOCOL.md'), 'w').write('# R046 再犯防止推進白書の効果検証の文（H038）\n実行前に固定。白書の文 4組（各版で同じ文をまとめた）。対照 CTRL-T0・CTRL-T1。GPT（Codex）と Gemini（H037）で判定し、両方の作例が正答の場合だけ採る。\n')
sh = os.path.expanduser('~/mitodoke_blind/run_R046.sh')
open(sh, 'w').write('#!/bin/sh\ncodex exec --json --skip-git-repo-check -s workspace-write -C ~/mitodoke_blind/R046 -o ~/mitodoke_blind/R046_lastmsg.md - < ~/mitodoke_blind/R046/PROMPT.md > ~/mitodoke_blind/R046_events.jsonl 2> ~/mitodoke_blind/R046_err.log\necho "exit=$? $(date \'+%F %T\')" > ~/mitodoke_blind/R046.done\n')
os.chmod(sh, 0o755); print(key)
