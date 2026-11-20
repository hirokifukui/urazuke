#!/bin/bash
# 公開用リポジトリ（hirokifukui/urazuke、公開）を、作業用（hirokifukui/urazuke-work、非公開）の PUBLIC_FILES.tsv に合わせて更新する（2026-11-20〜）。
# 公開用には PUBLIC_FILES.tsv のファイルだけを入れる。WITHHELD の対象と data/ が入っていないこと、sha256 が一覧と一致することを確かめてから push する。
set -eo pipefail
SRC=$(cd "$(dirname "$0")/.." && pwd); W=$HOME/.cache/urazuke_public
if [ ! -d "$W/.git" ]; then mkdir -p "$(dirname "$W")"; git clone -q https://github.com/hirokifukui/urazuke.git "$W"; fi
cd "$W"; git pull -q --ff-only
tail -n +2 "$SRC/publish/PUBLIC_FILES.tsv" | cut -f1 > /tmp/urazuke_pubfiles.txt
git -c core.quotepath=off ls-files | grep -vxF -f /tmp/urazuke_pubfiles.txt | grep -vx 'publish/PUBLIC_FILES.tsv' | while read -r f; do git rm -q -- "$f"; done || true
rsync -a --files-from=/tmp/urazuke_pubfiles.txt "$SRC/" "$W/"; cp "$SRC/publish/PUBLIC_FILES.tsv" "$W/publish/PUBLIC_FILES.tsv"
for f in $(tail -n +3 "$SRC/publish/WITHHELD.tsv" | cut -f1); do [ -e "$f" ] && { echo "公開を控えたファイルが入っている: $f"; exit 1; }; done
[ -d data ] && { echo "data/ が入っている"; exit 1; }
tail -n +2 publish/PUBLIC_FILES.tsv | awk -F'\t' '{print $3"  "$1}' | shasum -a 256 -c --quiet
git add -A
if git diff --cached --quiet; then echo "公開用リポジトリ：変更なし"; exit 0; fi
git -c user.name=URAZUKE -c user.email=contact@urazuke.org commit -q -m "URAZUKE update (from $(git -C "$SRC" rev-parse --short HEAD))"
git push -q origin main; echo "公開用リポジトリを更新：$(git rev-parse --short HEAD)"
