#!/bin/sh
# 走らせ直した出力を、走らせ直す前の写し（/tmp/urz_before/results）と比べる。tally の行は除く。
# 使い方: sh checks/generic/compare_rerun.sh results/hanzai_hakusho [results/cross ...]
cd "$(dirname "$0")/../.." || exit 1
B=${URZ_BEFORE:-/tmp/urz_before}
for d in "$@"; do
  sub=${d#results/}
  find "$d" -type f ! -path '*/tally/*' -newer "$B/$sub" 2>/dev/null | sort | while read -r f; do
    o="$B/${f#results/}"
    if [ ! -f "$o" ]; then echo "NEW  $f"; continue; fi
    if grep -v '^tally ' "$f" | cmp -s - "$o"; then :; else
      echo "DIFF $f"; grep -v '^tally ' "$f" | diff "$o" - | head -${DL:-6}
    fi
  done
done
for f in $(ls "$@" 2>/dev/null | sed 's#^#x#' >/dev/null); do :; done
for d in "$@"; do for t in "$d"/tally/*.json; do [ -f "$t" ] && python3 -c "import json;d=json.load(open('$t'));print('TALLY',d['check'],d['label'] or '-',d['compared'],d['mismatched'],d['read_failures'],d['explained'])"; done; done
