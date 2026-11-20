#!/bin/sh
# 3回目以降：支持でない記録を反証の報告で書き直し、かけ直す。sh publish/plain/round2.sh <最初の回の番号>
cd "$(dirname "$0")/../.." || exit 1
python3 -u publish/plain/revise.py
IDS=$(python3 -c "import json;S=json.load(open('publish/plain/STATUS.json'));print(' '.join(sorted(i for i,v in S.items() if not (v['adopted'] and v['verdict']=='支持'))))")
python3 publish/plain/make_rounds.py replan $1 $IDS
RS=$(python3 -c "import json;print(' '.join(json.load(open('publish/plain/ROUNDS.json'))))")
python3 publish/plain/make_rounds.py build $RS
sh publish/plain/run_rounds.sh $RS
