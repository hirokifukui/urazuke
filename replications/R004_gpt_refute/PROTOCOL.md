# R004 反証の試み（別系統）— GPT / Codex CLI
作成：2026-11-16 21:20 JST（実行前に固定）

目的：照会に回す候補4件（H002〜H005）を、作成者と別系統のモデル（OpenAI、Codex CLI）に反証させる。METHODS「発見を確定する条件」6。R004 は当初「630の F7 の反証」だったが、Dr. Fukui の確認（2026-11-16）で、照会候補の反証を1回にまとめた。

## 設計
- 対象ごとに独立の作業フォルダ（~/mitodoke_blind/R004/S1〜S4）と独立のセッション。各フォルダには原本の写しだけを置く。FINDINGS、仮説ファイル、Claude の説明、検査スクリプトは置かない。他の対象の資料も置かない。
- 各セッションの主張は3つ：本題1つと対照2つ（真1・偽1）。対照は作成者が答えを確かめ済み。どれが対照かは指示文に書かず、順序は本題を2番目か3番目に置いた。
- 判定の規則（支持／反証／判定不能）は指示文で先に固定。確認を促す言い回しは使わない（R003 と同じ）。

| セッション | 本題 | 真の対照（正答：支持） | 偽の対照（正答：反証） |
|---|---|---|---|
| S1 630 | Q2（H002） | Q1 札幌市 2019 F7 299・F8 42 | Q3 さいたま市 2022 長期 F7＝年度別 F8（実際は 長期9＝年度別F7 9、F8 4） |
| S2 文科 | Q3（H003） | Q2 平成27年度合計 6,320 は差し替えで不変 | Q1 横浜市の総計が差し替えで変わった（実際は割合だけ） |
| S3 ストーカー | Q2（H004） | Q3 2021 男性2,442＋女性17,286＝19,728 | Q1 2023 抵触しない動機 883 が内訳と不一致（実際は 114＋24＋202＋543＝883） |
| S4 児童虐待 | Q3（H005） | Q2 2021 検挙総数 2,174 | Q1 2022 殺人（既遂）が令和6・7年版で異なる（実際は両版 23） |

## 実行
- `codex exec --json --skip-git-repo-check -s workspace-write -C <フォルダ> -o <lastmsg> - < PROMPT.md`、4セッションを順に1本の nohup で。イベントは ~/mitodoke_blind/R004_<S>_events.jsonl。

## 採点（事前に固定）
- 各セッションで対照2つの正答を先に見る。1つでも外したセッションは、本題の判定を使わない（再実行は新しい番号で）。8つの対照のうち3つ以上を外したら R004 全体を使わない。
- 本題が「反証」：示された箇所を Claude 側で再確認し、FINDINGS を訂正するか、反証の誤りを記録する。
- 「判定不能」：理由を記録し、確実さを1段下げる。
- 「支持」：確認の状態を「二重検証済み（別系統）」にする。
- 「別の説明」「言い過ぎ」の指摘は、仮説ファイルの反証の条件に照らして扱い、FINDINGS の文言に反映する。

## 固定したファイル（sha256）
77280aea9ad9c882a04c6912f7d5b7e2fb0cef9e27384a3d933c9fea40eda50d  hypotheses/H002_630_F7_is_F8.md
c2019270e5a19922e9b581964fbcd0c7fdf959d4491d0060019d9775f7b3c4fa  hypotheses/H003_monka_H26_total.md
79bfa60421afa3b776664f00d027cce7f9000befcfde911a2f81b6393694e712  hypotheses/H004_stalker_motive_2022.md
64f2f795e1698e878d53e3c195802802f1cd63e4d948a4439e91af103923a47b  hypotheses/H005_CA_murder_swap.md
ab51bb1d28d3e94f657cdcb573020248e13ac6cd088e797552376dca59d573a4  replications/R004_gpt_refute/PROMPT_S1_630.md
94c4edd99a5daaf1938991be4bcf473d2808ab4b656e6f4a149ab63641d7c02b  replications/R004_gpt_refute/PROMPT_S2_monka.md
26ab120500190ea7121a5bb1d4c4cf3ccc207a90ab84c00f2560b4fded82a650  replications/R004_gpt_refute/PROMPT_S3_stalker.md
bcb9c9c6d9893e082bf31cb90fe0b26def78bba8e407f7670be573ecc5281554  replications/R004_gpt_refute/PROMPT_S4_ca.md
