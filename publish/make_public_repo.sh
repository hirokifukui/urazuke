#!/bin/bash
# 公開用のリポジトリを、履歴を持たない新しいリポジトリとして作る（push はしない）。
# 理由：作業用リポジトリの過去のコミットには、公開を控えたファイル（publish/WITHHELD.tsv）が含まれる。
# 作業用リポジトリの履歴は書き換えない。公開用には PUBLIC_FILES.tsv のファイルだけを、一つのコミットで入れる。
# 使い方：publish/make_public_repo.sh <出力先のフォルダ（空、または存在しない）>
set -e
SRC=$(cd "$(dirname "$0")/.." && pwd)
DST=${1:?出力先を指定}
if [ -e "$DST" ] && [ -n "$(ls -A "$DST")" ]; then echo "出力先が空ではない: $DST"; exit 1; fi
mkdir -p "$DST"
tail -n +2 "$SRC/publish/PUBLIC_FILES.tsv" | cut -f1 > /tmp/urazuke_pubfiles.txt
rsync -a --files-from=/tmp/urazuke_pubfiles.txt "$SRC/" "$DST/"
cp "$SRC/publish/PUBLIC_FILES.tsv" "$DST/publish/PUBLIC_FILES.tsv"
# 中身の確認：WITHHELD と EXCLUDE の対象が入っていないこと、sha256 が一覧と一致すること
cd "$DST"
for f in $(tail -n +3 "$SRC/publish/WITHHELD.tsv" | cut -f1); do if [ -e "$f" ]; then echo "公開を控えたファイルが入っている: $f"; exit 1; fi; done
if [ -d data ]; then echo "data/ が入っている"; exit 1; fi
tail -n +2 publish/PUBLIC_FILES.tsv | awk -F'\t' '{print $3"  "$1}' | shasum -a 256 -c --quiet
git init -q && git add -A && git -c user.name=URAZUKE -c user.email=contact@urazuke.org commit -q -m "URAZUKE public release (from $(git -C "$SRC" rev-parse --short HEAD))"
git tag "release-$(date +%Y%m%d)-$(git -C "$SRC" rev-parse --short HEAD)"
echo "作成: ${DST}（$(git ls-files | wc -l) ファイル、コミット $(git rev-parse --short HEAD)）。push はしていない。"
