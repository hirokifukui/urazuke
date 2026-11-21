#!/bin/bash
# 国会答弁の引かれ方の週1回の回（2026-11-21）。crawl/weekly_llm.sh から、Claude Code の段の前に呼ぶ（その段の build に反映される）。
# 取得→切り出し→Claude の分類→版の原文での照らし直し→GPT の盲検→陰性対照→報告→サイト用のデータ（追記のみ）。
cd "$(dirname "$0")/.." || exit 1
D=$(date +%F); O="results/kokkai/$D"; mkdir -p "$O"
python3 kokkai/fetch.py > "$O/fetch.log" 2>&1 && python3 kokkai/candidates.py "$D" > "$O/candidates.log" 2>&1 \
 && python3 kokkai/classify.py "$D" > "$O/classify.log" 2>&1 && python3 kokkai/series_check.py "$D" > "$O/series.log" 2>&1 \
 && python3 kokkai/refute.py "$D" > "$O/refute.log" 2>&1 && python3 kokkai/refute.py "$D" classified2.jsonl refuted2.jsonl > "$O/refute2.log" 2>&1 \
 && python3 kokkai/negctl.py "$D" > "$O/negctl.log" 2>&1 && python3 kokkai/report.py "$D" > "$O/report.log" 2>&1 \
 && python3 kokkai/export.py "$D" > "$O/export.log" 2>&1
RC=$?
[ $RC -ne 0 ] && python3 crawl/notify.py "⚠️ URAZUKE 国会答弁の回 $D：途中で止まった（終了コード $RC、$O）"
exit 0
