#!/bin/sh
# 陰性対照用：本物の pdftotext の出力の1か所を NEGCTL_OLD → NEGCTL_NEW に置き換える（NEGCTL_FILE を含むパスのときだけ）
REAL=$(PATH=$(echo "$PATH" | sed 's#/tmp/urazuke_negctl_bin:##') command -v pdftotext)
case "$*" in
  *"$NEGCTL_FILE"*) "$REAL" "$@" | NEGCTL_OLD="$NEGCTL_OLD" NEGCTL_NEW="$NEGCTL_NEW" python3 -c 'import os,sys; t=sys.stdin.read(); o=os.environ["NEGCTL_OLD"]; sys.stdout.write(t.replace(o, os.environ["NEGCTL_NEW"], 1))' ;;
  *) exec "$REAL" "$@" ;;
esac
