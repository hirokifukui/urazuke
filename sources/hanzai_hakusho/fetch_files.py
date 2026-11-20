#!/usr/bin/env python3
"""犯罪白書の特定の Excel だけを、複数の版から取得する（版をまたいだ比較用）。
使い方: python3 fetch_files.py <版番号,...> <相対パス,...>
  例:   python3 fetch_files.py 63,64,65 excel/shiryo1-1.xlsx,excel/5-1-1.xlsx
保存先: data/raw/hanzai_hakusho/<版>/{shiryo|zuhyo}/<ファイル名>、取得記録は同じフォルダの MANIFEST_partial.tsv に追記。
既にあるファイルは取り直さない。
"""
import hashlib, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")
ROOT = Path(__file__).resolve().parents[2]
eds, files = sys.argv[1].split(","), sys.argv[2].split(",")
for n in eds:
    out = ROOT / "data" / "raw" / "hanzai_hakusho" / n
    for rel in files:
        name = Path(rel).name
        sub = "shiryo" if name.startswith("shiryo") else "zuhyo"
        path = out / sub / name
        if path.exists():
            continue
        url = f"https://hakusyo1.moj.go.jp/jp/{n}/nfm/{rel}"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
                status, body = r.status, r.read()
        except urllib.error.HTTPError as e:
            status, body = e.code, b""
        if status == 200 and body[:2] == b"PK":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
        out.mkdir(parents=True, exist_ok=True)
        with open(out / "MANIFEST_partial.tsv", "a", encoding="utf-8") as fh:
            fh.write("\t".join([url, str(path.relative_to(ROOT)) if path.exists() else "", str(len(body)),
                                hashlib.sha256(body).hexdigest() if body else "", str(status),
                                datetime.now(timezone.utc).isoformat(timespec="seconds")]) + "\n")
        print(n, name, status, len(body))
        time.sleep(0.5)
