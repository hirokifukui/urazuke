#!/bin/bash
# 取得の順番待ち。queue.tsv（一覧TSV<TAB>保存先）を上から1件ずつ fetch_list.py にかける。
# 途中で queue.tsv に行を足してよい。済んだ行は queue.done に記録。30分なにも無ければ終わる。
# 同時に走らせるのは1本だけ（pgrep -f run_queue.sh で確かめる）。
cd "$(dirname "$0")/../.." || exit 1
Q=sources/generic/queue.tsv; D=sources/generic/queue.done; touch $Q $D
PY=~/.venvs/urazuke/bin/python; idle=0
while [ $idle -lt 180 ]; do
  line=$(grep -v '^#' $Q | grep -vxFf $D | head -1)
  if [ -z "$line" ]; then sleep 10; idle=$((idle+1)); continue; fi
  idle=0; lst=$(echo "$line" | cut -f1); out=$(echo "$line" | cut -f2)
  echo "$(date -u +%FT%TZ) start $lst -> $out" >> logs/run_queue.log
  $PY -I sources/generic/fetch_list.py "$lst" "$out" >> logs/run_queue.log 2>&1
  echo "$(date -u +%FT%TZ) end $lst rc=$?" >> logs/run_queue.log
  echo "$line" >> $D
done
echo "$(date -u +%FT%TZ) idle exit" >> logs/run_queue.log
