#!/bin/sh
# 2回目：反証の5件を書き直し、支持でない記録すべてを、資料のフォルダ全体を渡して反証にかけ直す（2026-11-19、r43）
cd "$(dirname "$0")/../.." || exit 1
python3 -u publish/plain/revise.py 630-M1 HK-A4 NK-K1 SJ-A1 YK-D1
IDS=$(python3 -c "import json;S=json.load(open('publish/plain/STATUS.json'));print(' '.join(sorted(i for i,v in S.items() if not (v['adopted'] and v['verdict']=='支持'))))")
python3 publish/plain/make_rounds.py replan 57 $IDS
RS=$(python3 -c "import json;print(' '.join(json.load(open('publish/plain/ROUNDS.json'))))")
python3 publish/plain/make_rounds.py build $RS
sh publish/plain/run_rounds.sh $RS
