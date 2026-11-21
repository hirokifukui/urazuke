#!/bin/bash
# 国会答弁の引かれ方の週1回の回（2026-11-21）。crawl/weekly_llm.sh から、Claude Code の段の前に呼ぶ（その段の build に反映される）。
# 会議録：取得→切り出し（答弁と質問）→Claude の分類→版の原文での照らし直し→広い範囲での照らし直し→GPT の盲検。
# 質問主意書・答弁書：最近の回次を取り直し→切り出し→分類→盲検。最後に陰性対照・報告・サイト用のデータ（追記のみ）。
cd "$(dirname "$0")/.." || exit 1
D=$(date +%F); O="results/kokkai/$D"; mkdir -p "$O"
step() { "$@" >> "$O/weekly.log" 2>&1 || { echo "失敗: $*" >> "$O/weekly.log"; FAIL="$FAIL $2"; }; }
FAIL=""
step python3 kokkai/fetch.py
step python3 kokkai/candidates.py "$D"
step python3 kokkai/classify.py "$D"
step python3 kokkai/series_check.py "$D"
step python3 kokkai/refute.py "$D"
step python3 kokkai/refute.py "$D" classified2.jsonl refuted2.jsonl
step python3 kokkai/fullcheck.py "$D"
step python3 kokkai/refute.py "$D" classified3.jsonl refuted3.jsonl
step python3 kokkai/fetch_shuisho.py 219
step python3 kokkai/shuisho_candidates.py "$D"
step python3 kokkai/classify.py "$D" 100000 candidates_shuisho.jsonl classified_shuisho.jsonl
step python3 kokkai/refute.py "$D" classified_shuisho.jsonl refuted_shuisho.jsonl
step python3 kokkai/negctl.py "$D"
step python3 kokkai/report.py "$D"
# step python3 kokkai/export.py "$D"   # 2026-11-21 止めた：回ごとの判定のぶれと陰性対照（20件中7件を誤って支持）のため、安定させるまでサイトへの自動の追加をしない
[ -n "$FAIL" ] && python3 crawl/notify.py "⚠️ URAZUKE 国会答弁の回 $D：失敗した段 $FAIL（$O/weekly.log）"
exit 0
