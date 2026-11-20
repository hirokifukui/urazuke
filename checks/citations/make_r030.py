"""R030：Perplexity の検索で見つけ、写しで確かめた引用 11件の型を、別系統（Codex）に付けさせる盲検フォルダ（H034、R029 と同じ手順）。
渡すのは元の資料の文・引用の文・掲載時期・型の定義だけ。対照2つ（R029 とは別の作例）を混ぜる。"""
import os, json, random, hashlib
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BL = os.path.expanduser('~/mitodoke_blind/R030'); os.makedirs(BL)
GY_S = '令和４年度中に、全国232か所の児童相談所が児童虐待相談として対応した件数は 219,170 件（速報値）で、過去最多。（2023年公表）／令和４年度中に児童相談所が対応した養護相談のうち児童虐待相談の対応件数は 214,843 件となっている。（確定値、2024年9月公表）'
JH_S = '令和６年の小中高生の自殺者数は529人と、統計のある昭和55年以降、最多の数値となった。（自殺対策白書 令和7年版）'
ST_S = '注）令和５年までは基準年中に受理した相談のうち同年中に実施した行政措置、検挙及び援助（以下「行政措置等」という。）した件数を計上していたところ、令和６年からは、基準年中に受理した相談の有無に関わらず、基準年中に実施した行政措置等の件数は全て計上することに変更した。'
NK_S = '６０歳以上の受刑者のうち，認知症傾向のある受刑者はおよそ１４％（１３．８％）で，全国におよそ１，３００人いると推計（平成28年1月）'
cases = [
 ('P-GY-01', GY_S, '2022年度に全国の児童相談所が対応した児童虐待件数は21万4843件に上り、過去最多となりました。', '2024-09'),
 ('P-GY-02', GY_S, '見出し：22年度の虐待件数4327減の21万4843件に修正', '2024-09'),
 ('P-GY-03', GY_S, '相談対応件数は全国で21万4843件となり、昨年9月に公表した速報値より4000件余り減っているが、過去最多を更新していることや全体の傾向は大きく変わっていない。', '2024-09'),
 ('P-GY-04', GY_S, '全国に２３２カ所ある児相が２０２２年度に相談を受け、指導や措置などの対応をしたのは、前年度より５％増の２１万９１７０件（速報値）だった。', '2023-09'),
 ('P-JH-02', JH_S, '24年の小中高生の自殺者数は529人で、統計のある1980年以降で過去最多。', '2025-10'),
 ('P-JH-04', JH_S, '見出し：小中高生の自殺が過去最多529人「2025年版自殺対策白書」', '2025-10'),
 ('P-ST-04', ST_S, '2025年にストーカー規制法違反での検挙件数は1546件と、過去最多となりました。（記事に数え方の変更の記載はない）', '2026-03'),
 ('P-ST-05', ST_S, 'ストーカー事案の検挙件数は去年3717件で、規制法が施行されて以降、最多となっています。（記事に数え方の変更の記載はない）', '2026-11'),
 ('P-NK-01', NK_S, '見出し：60歳以上の受刑者中「認知症傾向のある人」は約14％【法務省】', '2016-01'),
 ('P-NK-02', NK_S, '法務省の推計（2015年）によると、全国各地の刑務所に服役している60歳以上の受刑者のうち、認知症傾向があるのは1,300人、割合にして14％に上っています。', '2020-01'),
 ('P-NK-03', NK_S, '法務省は、2015年に実施した調査で、全国の60歳以上の受刑者のうち認知症傾向がある人が約1300人いると推計。', '2018-05'),
 ('CTRL-T1', '令和５年の不登校児童生徒数は 346,482 人。', '2023年度の不登校の児童生徒は34万6,842人だった。', '2024-10'),
 ('CTRL-T0', '令和６年の刑法犯の認知件数は 737,679 件。', '2024年の刑法犯の認知件数は73万7679件だった。', '2025-03'),
]
random.Random(20261119).shuffle(cases)
key = {}; L = []
for n, (q, src, cit, d) in enumerate(cases, 1):
    key[f'C{n:02d}'] = q
    L.append(f'### C{n:02d}\n- 引用の掲載時期：{d}\n- 元の資料の文：{src}\n- 引用の文：{cit}\n')
P0 = open(os.path.join(ROOT, 'replications/R029_gpt_types/PROMPT.md')).read()
head = P0[:P0.index('## 組')]
P = head + '## 組\n' + '\n'.join(L) + '''
## 出力
REPORT.md に、組ごとに「型（複数可）」「根拠（どの語・数値の違いか、1〜2文）」を表で書く。最後に全体の要約を3行以内で書く。
'''
open(os.path.join(BL, 'PROMPT.md'), 'w').write(P)
rep = os.path.join(ROOT, 'replications/R030_gpt_types'); os.makedirs(rep, exist_ok=True)
json.dump(key, open(os.path.join(rep, 'KEY.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(rep, 'PROMPT.md'), 'w').write(P)
open(os.path.join(rep, 'FIXED_SHA256.txt'), 'w').write(hashlib.sha256(P.encode()).hexdigest() + '  PROMPT.md\n')
open(os.path.join(rep, 'PROTOCOL.md'), 'w').write('# R030 引用の型の判定（別系統：GPT / Codex CLI）— H034\n作成：2026-11-18（実行前に固定）\n対象：Perplexity の検索で見つけ、写しで引用の文を確かめた 11件。手順・型の定義は R029 と同じ。\n対照：CTRL-T1（値の写し間違い）・CTRL-T0（同じ）。R029 とは別の作例。両方正答の場合だけ採る。\n順序は乱数（種 20261119）。対応は KEY.json。\n')
sh = os.path.expanduser('~/mitodoke_blind/run_R030.sh')
open(sh, 'w').write('#!/bin/sh\ncodex exec --json --skip-git-repo-check -s workspace-write -C ~/mitodoke_blind/R030 -o ~/mitodoke_blind/R030_lastmsg.md - < ~/mitodoke_blind/R030/PROMPT.md > ~/mitodoke_blind/R030_events.jsonl 2> ~/mitodoke_blind/R030_err.log\necho "exit=$? $(date \'+%F %T\')" > ~/mitodoke_blind/R030.done\n')
os.chmod(sh, 0o755)
print(len(cases), {k: v for k, v in key.items() if v.startswith('CTRL')})
