"""R031：R031 で元の資料の文に調査時期を示していなかった NK-K1 の組を、調査時期と定義を足してやり直す。Perplexity の検索で見つけ、写しで確かめた引用 11件の型を、別系統（Codex）に付けさせる盲検フォルダ（H034、R029・R030 と同じ手順）。
渡すのは元の資料の文・引用の文・掲載時期・型の定義だけ。対照2つ（R029 とは別の作例）を混ぜる。"""
import os, json, random, hashlib
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BL = os.path.expanduser('~/mitodoke_blind/R031'); os.makedirs(BL)
GY_S = '令和４年度中に、全国232か所の児童相談所が児童虐待相談として対応した件数は 219,170 件（速報値）で、過去最多。（2023年公表）／令和４年度中に児童相談所が対応した養護相談のうち児童虐待相談の対応件数は 214,843 件となっている。（確定値、2024年9月公表）'
JH_S = '令和６年の小中高生の自殺者数は529人と、統計のある昭和55年以降、最多の数値となった。（自殺対策白書 令和7年版）'
ST_S = '注）令和５年までは基準年中に受理した相談のうち同年中に実施した行政措置、検挙及び援助（以下「行政措置等」という。）した件数を計上していたところ、令和６年からは、基準年中に受理した相談の有無に関わらず、基準年中に実施した行政措置等の件数は全て計上することに変更した。'
NK_S = '■調査対象者 平成２６年末時点で６０歳以上の受刑者のうち，層別無作為抽出法により選定した４５１人　■調査時期 平成２７年１月２０日～２月２３日　■定義 本調査における「認知症傾向のある受刑者」とは，ＨＤＳ－Ｒの得点が２０点以下であった者を指し，医師による診断の有無…による区別は行っていない。／６０歳以上の受刑者のうち，認知症傾向のある受刑者はおよそ１４％（１３．８％）で，全国におよそ１，３００人いると推計（法務省矯正局、平成28年1月公表）'
cases = [
 ('P-NK-01', NK_S, '見出し：60歳以上の受刑者中「認知症傾向のある人」は約14％【法務省】', '2016-01'),
 ('P-NK-02', NK_S, '法務省の推計（2015年）によると、全国各地の刑務所に服役している60歳以上の受刑者のうち、認知症傾向があるのは1,300人、割合にして14％に上っています。', '2020-01'),
 ('P-NK-03', NK_S, '法務省は、2015年に実施した調査で、全国の60歳以上の受刑者のうち認知症傾向がある人が約1300人いると推計。', '2018-05'),
 ('Q-NK-K1-001', NK_S, '法務省が実施した特別調査によると、60歳以上の受刑者のうち認知症傾向が認められた者は約14%（2015年6月時点）を占め、全国の刑務所では約1300人（同）に上ると推計されている。', '2018-02'),
 ('CTRL-T1', '令和５年の小中高生の自殺者数は 513 人。', '2023年の小中高生の自殺者は531人だった。', '2024-03'),
 ('CTRL-T0', '令和５年度の児童虐待相談の対応件数は 225,509 件。', '2023年度の児童虐待相談の対応件数は22万5509件だった。', '2024-10'),
]
random.Random(20261120).shuffle(cases)
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
rep = os.path.join(ROOT, 'replications/R031_gpt_types'); os.makedirs(rep, exist_ok=True)
json.dump(key, open(os.path.join(rep, 'KEY.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(rep, 'PROMPT.md'), 'w').write(P)
open(os.path.join(rep, 'FIXED_SHA256.txt'), 'w').write(hashlib.sha256(P.encode()).hexdigest() + '  PROMPT.md\n')
open(os.path.join(rep, 'PROTOCOL.md'), 'w').write('# R031 引用の型の判定（別系統：GPT / Codex CLI）— H034\n作成：2026-11-18（実行前に固定）\n対象：NK-K1 の引用 4件（R030 で元の資料の文に調査時期を示していなかったため）。手順・型の定義は R029 と同じ。\n対照：CTRL-T1（値の写し間違い）・CTRL-T0（同じ）。R029 とは別の作例。両方正答の場合だけ採る。\n順序は乱数（種 20261120）。対応は KEY.json。\n')
sh = os.path.expanduser('~/mitodoke_blind/run_R031.sh')
open(sh, 'w').write('#!/bin/sh\ncodex exec --json --skip-git-repo-check -s workspace-write -C ~/mitodoke_blind/R031 -o ~/mitodoke_blind/R031_lastmsg.md - < ~/mitodoke_blind/R031/PROMPT.md > ~/mitodoke_blind/R031_events.jsonl 2> ~/mitodoke_blind/R031_err.log\necho "exit=$? $(date \'+%F %T\')" > ~/mitodoke_blind/R031.done\n')
os.chmod(sh, 0o755)
print(len(cases), {k: v for k, v in key.items() if v.startswith('CTRL')})
