# R008 反証の試み（別系統：GPT / Codex CLI）— H008
作成：2026-11-17（実行前に固定）
資料：~/mitodoke_blind/R008 に写しを置く（自殺対策白書 令和6〜8年版 参考資料2 Excel、司法統計年報（刑事編）令和5年更新版・令和6年更新版・令和7年 Excel と令和7年 PDF、衛生行政報告例 第2表-1 CSV 2023〜2025年度と2023年度の正誤情報）。記録・作業ノートは渡さない。
問：Q1〜Q6。対照は Q3（真）と Q5（偽）。本題は Q1・Q2（JH-A1）、Q4（SJ-A1）、Q6（ES-I1）。対応は SCORING に記す（PROMPT には書かない）。
採点：hypotheses/H008 の基準どおり。
実行：sh ~/mitodoke_blind/run_R008.sh（nohup）。codex exec --json --skip-git-repo-check -s workspace-write -C ~/mitodoke_blind/R008 -o ~/mitodoke_blind/R008_lastmsg.md - < PROMPT.md
