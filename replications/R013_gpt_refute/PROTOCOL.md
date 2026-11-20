# R013 反証の試み（別系統：GPT / Codex CLI）— H018
作成：2026-11-17（実行前に固定）
資料：~/mitodoke_blind/R013 に写しを置く（検察統計年報 令和7年 第1表・第2表 Excel、建設工事受注動態統計 令和6年度計分の報道発表ページ・修正情報のページの HTML の写しと記者発表資料 PDF、都道府県決算カード 令和4〜6年度 Excel）。記録・作業ノートは渡さない。sha256 は FIXED_SHA256.txt。
問：Q1〜Q7。対照は Q2（真）と Q5（偽）。本題は Q1（KS-A1）、Q3（KS-I1）、Q4（KJ-L1）、Q6（KJ-I1）、Q7（KC-A1）。対応は SCORING に記す（PROMPT には書かない）。
採点：hypotheses/H018 の基準どおり。
実行：sh ~/mitodoke_blind/run_R013.sh（nohup）。codex exec --json --skip-git-repo-check -s workspace-write -C ~/mitodoke_blind/R013 -o ~/mitodoke_blind/R013_lastmsg.md - < PROMPT.md
