#!/usr/bin/env python3
"""犯罪白書（法務総合研究所）の公開 Excel を取得し、取得記録（MANIFEST.tsv）を残す。

使い方:  python3 fetch.py 72          # 72 = 令和7年版（hakusyo1.moj.go.jp/jp/<番号>/nfm/）
         python3 fetch.py 72 --fill   # 既存フォルダの欠けている分だけ取得し、MANIFEST に追記
取得物:  data/raw/hanzai_hakusho/<番号>/
           index/   mokuji.html（資料編の目次）, gmokuji.html（図表目次）
           shiryo/  資料編の Excel（shiryoX-Y.xlsx）
           zuhyo/   図表ごとのバックデータ Excel（例 1-1-1-1.xlsx）
           honbun/  本文の HTML（図表目次から参照されるページ）
           MANIFEST.tsv  URL・保存先・バイト数・SHA256・HTTP 状態・取得時刻（UTC）
同じ番号で再実行すると、既存ファイルは上書きせず、新しい取得日時のフォルダに保存する。
"""
import hashlib, re, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://hakusyo1.moj.go.jp/jp/{n}/nfm/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")
ROOT = Path(__file__).resolve().parents[2]
DELAY = 0.5  # 先方サーバへの配慮（秒）


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""


def main():
    n = sys.argv[1] if len(sys.argv) > 1 else "72"
    fill = "--fill" in sys.argv
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "data" / "raw" / "hanzai_hakusho" / n
    done = set()
    if out.exists() and fill:
        man = out / "MANIFEST.tsv"
        for line in man.read_text(encoding="utf-8").splitlines()[1:]:
            done.add(line.split("\t")[0])
    elif out.exists():
        out = out.with_name(f"{n}_{stamp}")
    base = BASE.format(n=n)
    rows = []

    def save(rel_url, sub, force=False):
        url = base + rel_url
        if url in done and not force:
            return None, b""
        status, body = get(url)
        path = out / sub / Path(rel_url).name
        if status == 200 and body:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
        rows.append([url, str(path.relative_to(ROOT)) if status == 200 else "",
                     str(len(body)), hashlib.sha256(body).hexdigest() if body else "",
                     str(status), datetime.now(timezone.utc).isoformat(timespec="seconds")])
        time.sleep(DELAY)
        return status, body

    if fill:  # 目次は保存済みのものを使う（取り直さない）
        mokuji = (out / "index" / "mokuji.html").read_bytes()
        gmokuji = (out / "index" / "gmokuji.html").read_bytes()
    else:
        _, mokuji = save("mokuji.html", "index")
        _, gmokuji = save("gmokuji.html", "index")
    shiryo = sorted(set(re.findall(rb'href="\./excel/(shiryo[0-9-]+\.xlsx)"', mokuji)))
    charts = sorted(set(re.findall(rb'html#h([0-9]+(?:-[0-9]+){2,3})"', gmokuji)))
    for f in shiryo:
        save("excel/" + f.decode(), "shiryo")
    for c in charts:
        save(f"excel/{c.decode()}.xlsx", "zuhyo")
    pages = sorted(set(re.findall(rb'href="(n[0-9]+_[0-9_]+\.html)#', gmokuji)))
    for pg in pages:
        save(pg.decode(), "honbun")

    mode = "a" if fill else "w"
    with open(out / "MANIFEST.tsv", mode, encoding="utf-8") as fh:
        if not fill:
            fh.write("url\tpath\tbytes\tsha256\thttp_status\tfetched_at_utc\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
    ok = sum(1 for r in rows if r[4] == "200")
    print(f"edition {n}: {ok}/{len(rows)} files saved to {out.relative_to(ROOT)} "
          f"(shiryo {len(shiryo)}, charts {len(charts)})")
    for r in rows:
        if r[4] != "200":
            print("  failed:", r[4], r[0])


if __name__ == "__main__":
    main()
