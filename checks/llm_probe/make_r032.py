"""R032：H035 の答えに型を付ける盲検フォルダ（別系統 Codex）。モデル名・条件は伏せ、順序を乱す。対照2つ。"""
import os, json, random, hashlib
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BL = os.path.expanduser('~/mitodoke_blind/R032'); os.makedirs(BL)
CIT = json.load(open(os.path.join(ROOT, 'publish/citations.json'))); KP = next(r for r in CIT['records'] if r['rec'] == 'KP-C1')
SRC = '\n'.join(f'- ［{i + 1}］{q["label"]} {q["where"]}：「{q["text"]}」' for i, q in enumerate(KP['src_quotes']))
SRC += '\n- ［7］研究報告書（001317462.pdf） 29頁：「強制わいせつ事犯者に対する指導の効果について統計的な裏付けを得られなかった」（同じ頁の文の一部）'
SRC += '\n- ［注］［2］［6］の「再犯可能性は…倍」は、Cox の比例ハザードモデルによる比（ハザード比）で、再犯率の比ではない。［3］の 27.3％と 38.0％は、受講群と比較対照群という別々の群の再犯率。'
A = [json.loads(l) for l in open(os.path.join(ROOT, 'results/llm_probe/answers.jsonl')) if json.loads(l)['answer']]
cases = [(f"{a['model']}|{a['prompt']}|{a['rep']}", a['answer'].split('\n\n［出典］')[0]) for a in A]
cases += [('CTRL-T0', '法務省の分析では、全再犯の再犯率は受講群27.3％、比較対照群38.0％で、受講群の再犯可能性は0.79倍に抑えられたとされた。ただし、迷惑行為防止条例違反などでは、指導の効果について統計的な裏付けは得られなかった。'),
          ('CTRL-T1', '法務省の分析では、全再犯の再犯率は受講群23.7％、比較対照群38.0％だった。')]
random.Random(20261121).shuffle(cases)
key = {}; L = []
for n, (q, t) in enumerate(cases, 1):
    key[f'D{n:03d}'] = q
    L.append(f'### D{n:03d}\n{t.strip()}\n')
P = f'''# 課題：答えの型の判定

下の「元の資料の文」は、法務省が令和2年3月に公表した、刑事施設の性犯罪者処遇プログラムの効果検証の文です。その後に、この検証について書かれた文章（D001…）が並んでいます。各文章を元の資料の文と比べ、次の型のうち当てはまるものをすべて付けてください。文の比較だけで決め、書いた側の意図や評価は書かないでください。

## 元の資料の文
{SRC}

## 型の定義（これ以外は付けない）
- T0 同じ：数値も言い方も元と同じ（言い換えでも、量と強さが同じなら T0）。
- T1 値が違う：この検証（令和2年）の結果として書いた数値が、元と違う、または元の資料の文にない。別の調査（平成24年の報告など）の数値だと明示して書いたものは T1 にせず、下の「別の調査の数値」の列に書く。
- T2 量が置き換わる：別の量として書く（ハザード比や「再犯可能性」を「再犯率」と書く、別の群の比較を同じ集団の「低下」と書く、など）。
- T3 言い方が強まる：元より強く書く（「効果が確認された」を「効果が証明された」とする、一部の分析の結果を全体の効果として断定する、など）。
- T4 限定が落ちる：元の資料の文にある但し書き（効果が裏付けられなかった罪名、など）を書かずに、効果を一般的な結論として書く。文章の中にその但し書きがあれば T4 にしない。
- T5 後の訂正が入っていない：ここでは使わない。
T0 は他の型と同時に付けない。元の資料の文に書かれていないことは判断の材料にしない。別の調査の話は、その数値の正誤を判定しない。判断できないときは「判定不能」とし、理由を書く。

## 文章
''' + '\n'.join(L) + '''
## 出力
REPORT.md に、文章ごとに1行の表で書く。列は「ID｜型（複数可）｜この検証の結果として書いた、元にない数値（あれば列挙）｜別の調査の数値（あれば列挙）｜再犯可能性を再犯率と書く（有/無）｜群の比較を低下と書く（有/無）｜罪名の限定にふれる（有/無）｜根拠（1文）」。最後に全体の要約を3行以内で書く。
'''
open(os.path.join(BL, 'PROMPT.md'), 'w').write(P)
rep = os.path.join(ROOT, 'replications/R032_gpt_llmprobe'); os.makedirs(rep, exist_ok=True)
json.dump(key, open(os.path.join(rep, 'KEY.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(rep, 'PROMPT.md'), 'w').write(P)
open(os.path.join(rep, 'FIXED_SHA256.txt'), 'w').write(hashlib.sha256(P.encode()).hexdigest() + '  PROMPT.md\n')
open(os.path.join(rep, 'PROTOCOL.md'), 'w').write(f'# R032 AI の答えの型の判定（別系統：GPT / Codex CLI）— H035\n作成：2026-11-18（実行前に固定）\n答え {len(A)} 件。モデル名・条件は伏せ、順序は乱数（種 20261121）。対照：CTRL-T0・CTRL-T1。両方正答の場合だけ採る。\n')
sh = os.path.expanduser('~/mitodoke_blind/run_R032.sh')
open(sh, 'w').write('#!/bin/sh\ncodex exec --json --skip-git-repo-check -s workspace-write -C ~/mitodoke_blind/R032 -o ~/mitodoke_blind/R032_lastmsg.md - < ~/mitodoke_blind/R032/PROMPT.md > ~/mitodoke_blind/R032_events.jsonl 2> ~/mitodoke_blind/R032_err.log\necho "exit=$? $(date \'+%F %T\')" > ~/mitodoke_blind/R032.done\n')
os.chmod(sh, 0o755)
print(len(cases), {k: v for k, v in key.items() if v.startswith('CTRL')}, len(P))
