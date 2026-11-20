"""R034：R034 は対照 CTRL-T0 の作例が追跡期間と抽出条件を省いており（判定は T4）、採らなかった。作例を直してやり直す。H035 の続き（YK-C1・ST-I2 の基準線）の答えに型を付ける盲検フォルダ（別系統 Codex）。モデル名・条件は伏せ、順序を乱す。対照2つ。"""
import os, json, random, hashlib
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BL = os.path.expanduser('~/mitodoke_blind/R034'); os.makedirs(BL)
import importlib.util
sp = importlib.util.spec_from_file_location('rp2', os.path.join(ROOT, 'checks/llm_probe/run_probe2.py'))
src2 = open(os.path.join(ROOT, 'checks/llm_probe/run_probe2.py')).read(); SRCS = {}
exec(src2[src2.index('SRCS = {'):src2.index('LIM = ')], {}, d := {}); SRCS = d['SRCS']
A = [json.loads(l) for l in open(os.path.join(ROOT, 'results/llm_probe/answers2.jsonl')) if json.loads(l)['answer']]
cases = [(f"{a['model']}|{a['prompt']}|{a['rep']}", a['prompt'][:2], a['answer']) for a in A]
cases += [('CTRL-T0', 'YK', '法務省の概要は、刑事施設及び保護観察所におけるプログラムの処遇効果が示唆されたとした。刑事施設では、薬物依存離脱指導対象者の出所後2年間の再犯率が、平成25年出所の旧実施体制593名で26.6%、標準プログラム改訂後の新実施体制742名で20.9%だった。保護観察所では、受講群と非受講群の属性や特性等が等質となるように抽出した2,812名を最長4年間追跡し、再犯率は非受講群34.6%、受講群30.3%だった。'),
          ('CTRL-T1', 'ST', 'ストーカー規制法違反の検挙は令和７年に1,456件だった。')]
random.Random(20261123).shuffle(cases)
key = {}; L = []
for n, (q, g, t) in enumerate(cases, 1):
    key[f'D{n:03d}'] = q
    L.append(f'### D{n:03d}（資料 {g}）\n{t.strip()}\n')
P = f'''# 課題：文章の型の判定

下に二つの元の資料（資料 YK・資料 ST）の文があります。その後に、どちらかの資料をもとに書かれた文章（D001…、見出しに資料の名前を付けた）が並んでいます。各文章を、その資料の文と比べ、次の型のうち当てはまるものをすべて付けてください。文の比較だけで決め、書いた側の意図や評価は書かないでください。

## 資料 YK
{SRCS['YK']}

## 資料 ST
{SRCS['ST']}

## 型の定義（これ以外は付けない）
- T0 同じ：数値も言い方も元と同じ（言い換えでも、量と強さが同じなら T0）。
- T1 値が違う：数値が元と違う、または元の資料の文にない数値を書く。
- T2 量が置き換わる：別の量・別の比較として書く（旧実施体制と新実施体制の比較を、プログラムを受けた人と受けなかった人の比較として書く、など）。
- T3 言い方が強まる：元より強く書く（「示唆された」を「確認された」「認められた」「効果があった」などとする、など）。
- T4 限定が落ちる：元の資料の文にある但し書き・条件（計上方法の変更の注、比較の範囲、など）を書かずに、結論や比較を書く。文章の中にその但し書きがあれば T4 にしない。
T0 は他の型と同時に付けない。元の資料の文に書かれていないことは判断の材料にしない。判断できないときは「判定不能」とし、理由を書く。

## 文章
''' + '\n'.join(L) + '''
## 出力
REPORT.md に、文章ごとに1行の表で書く。列は「ID｜型（複数可）｜元にない数値（あれば列挙）｜「示唆」を強める（有/無/対象外）｜旧新の比較を受講の効果と書く（有/無/対象外）｜「最多」と書く（有/無/対象外）｜計上方法の変更にふれる（有/無/対象外）｜根拠（1文）」。資料 YK の文章では後ろの二つ、資料 ST の文章では前の二つを「対象外」とする。最後に全体の要約を3行以内で書く。
'''
open(os.path.join(BL, 'PROMPT.md'), 'w').write(P)
rep = os.path.join(ROOT, 'replications/R034_gpt_llmprobe'); os.makedirs(rep, exist_ok=True)
json.dump(key, open(os.path.join(rep, 'KEY.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(rep, 'PROMPT.md'), 'w').write(P)
open(os.path.join(rep, 'FIXED_SHA256.txt'), 'w').write(hashlib.sha256(P.encode()).hexdigest() + '  PROMPT.md\n')
open(os.path.join(rep, 'PROTOCOL.md'), 'w').write(f'# R034 AI の答えの型の判定（別系統：GPT / Codex CLI）— H035\n作成：2026-11-18（実行前に固定）\n答え {len(A)} 件。モデル名・条件は伏せ、順序は乱数（種 20261123）。対照：CTRL-T0・CTRL-T1。両方正答の場合だけ採る。\n')
sh = os.path.expanduser('~/mitodoke_blind/run_R034.sh')
open(sh, 'w').write('#!/bin/sh\ncodex exec --json --skip-git-repo-check -s workspace-write -C ~/mitodoke_blind/R034 -o ~/mitodoke_blind/R034_lastmsg.md - < ~/mitodoke_blind/R034/PROMPT.md > ~/mitodoke_blind/R034_events.jsonl 2> ~/mitodoke_blind/R034_err.log\necho "exit=$? $(date \'+%F %T\')" > ~/mitodoke_blind/R034.done\n')
os.chmod(sh, 0o755)
print(len(cases), {k: v for k, v in key.items() if v.startswith('CTRL')}, len(P))
