# R015 反証の試み（別系統：GPT / Codex CLI）— H021
作成：2026-11-17（実行前に固定。H021 は 914e444 でコミット）
資料：~/mitodoke_blind/R015 に写しを置く（矯正統計年報 2025年の全表と 2020〜2024年の第88・93表、犯罪白書 令和4〜7年版 PDF、令和6年版の Web 版本文 HTML と訂正のお知らせ、再犯防止推進白書 令和4・6・7年版 PDF）。記録・作業ノートは渡さない。sha256 は FIXED_SHA256.txt（PROMPT）。
問：Q1〜Q7。対照は Q3（偽：第37表に認知症の区分がある）と Q6（偽：Web 版本文が訂正後の値）。本題は Q1（HK-A9）、Q2・Q4・Q5・Q7（NK-K1）。
採点：hypotheses/H021 の基準どおり。
実行：sh ~/mitodoke_blind/run_R015.sh（nohup）。codex exec --json --skip-git-repo-check -s workspace-write -C ~/mitodoke_blind/R015 -o ~/mitodoke_blind/R015_lastmsg.md - < PROMPT.md
