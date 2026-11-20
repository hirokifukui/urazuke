#!/bin/bash
# 公開の日の手順のリハーサル（publish/README「公開の日の手順」）。外に出す操作は一つもしない：
# 照会は送らない・GitHub に push しない・Zenodo は認証の確認（GET）だけ・配備しない。
# 使い方：bash publish/rehearse.sh
set -e
cd "$(dirname "$0")/.."
D=$(date +%Y-%m-%d); OUTD=logs/rehearsal/$D; mkdir -p "$OUTD"; LOG="$OUTD/REHEARSAL.md"
T=/tmp/urazuke_rehearsal_$$
set +e
(
set -eo pipefail
echo "# 公開の日の手順のリハーサル（${D}、作業用コミット $(git rev-parse --short HEAD)）"
echo "外に出す操作はしていない（照会の送付・GitHub の push・Zenodo の公開・配備）。"
echo
echo "## 1. 照会"
n=$(ls publish/inquiries/*.md | wc -l | tr -d ' '); k=$(grep -c '^### ' publish/inquiries/*.md | awk -F: '{s+=$2} END{print s}')
echo "- 照会文 $n 通・$k 項目。未記入の欄は「照会日」だけであることを確かめる：$(grep -L '照会日：（送付時に記入）' publish/inquiries/*.md | wc -l | tr -d ' ') 通に欄がない（0 が正しい）。"
echo
echo "## 2. 公開用リポジトリ"
bash publish/make_public_repo.sh "$T/repo" | sed 's/^/- /'
echo
echo "## 3. Zenodo"
tar -czf "$T/urazuke.tar.gz" -C "$T" repo
echo "- 公開用の tar.gz：$(du -h "$T/urazuke.tar.gz" | cut -f1)"
echo "- 予約済みの下書き：$(python3 -c "import json;s=json.load(open('publish/zenodo_state.json'));print(s['doi'],'state='+s['state'],'submitted='+str(s['submitted']))")"
echo "- 認証：$(python3 publish/zenodo.py check 2>&1 | tail -1)"
echo
echo "## 4. 公開版のサイト（配備しない）"
python3 publish/public_build.py | sed 's/^/- /'
echo "- 当日は site/out_public を配備する（.vercel の設定は site/out から写して使う）。"
echo
echo "## 結果"
echo "- すべての段が通った。"
) > "$LOG" 2>&1
rc=$?
if [ $rc -ne 0 ]; then echo "- 途中で止まった（上の最後の行を見る）" >> "$LOG"; cat "$LOG"; rm -rf "$T"; exit 1; fi
rm -rf "$T"; cat "$LOG"
