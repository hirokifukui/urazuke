#!/bin/sh
# 平易版の反証の回を1本ずつ順に走らせ、終わるごとに採点する（2026-11-19、r43）。
# nohup sh publish/plain/run_rounds.sh R049 R050 ... > logs/plain_rounds.log 2>&1 &
cd "$(dirname "$0")/../.." || exit 1
for r in "$@"; do
  echo "== $r start $(date '+%F %T')"
  sh ~/mitodoke_blind/run_$r.sh
  cat ~/mitodoke_blind/$r.done
  python3 publish/plain/score.py "$r"
done
python3 -c "
import json; S=json.load(open('publish/plain/STATUS.json'))
n=len(S); ok=sum(1 for v in S.values() if v['adopted'] and v['verdict']=='支持')
import sys; sys.path.insert(0,'crawl'); import notify; notify.send(f'URAZUKE 平易版の反証：{ok}/{n} 件が支持（$*）')
"
echo "== all done $(date '+%F %T')"
