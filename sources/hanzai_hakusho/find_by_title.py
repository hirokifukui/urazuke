#!/usr/bin/env python3
"""犯罪白書の版ごとに、表題から Excel のファイル名を探して取得する（版によって番号・ファイル名が違うため）。
使い方: python3 find_by_title.py <版,...> <kind:shiryo|zuhyo> <表題の正規表現> <保存名>
  例:   python3 find_by_title.py 63,64,65 shiryo '刑法犯\\s*認知件数・発生率・検挙件数' keihouhan_ninchi
保存先: data/raw/hanzai_hakusho/<版>/bytitle/<保存名>.xlsx と、同じフォルダの BYTITLE.tsv（版・表題・元ファイル名・SHA256）
目次（mokuji.html / gmokuji.html）は data/raw/hanzai_hakusho/<版>/index/ に保存する（なければ取得）。
"""
import hashlib, html, re, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")
ROOT = Path(__file__).resolve().parents[2]


def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""


def text(b):
    for enc in ("utf-8", "shift_jis", "cp932"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            pass
    return b.decode("utf-8", "replace")


def index(n, page):
    p = ROOT / "data/raw/hanzai_hakusho" / n / "index" / page
    if not p.exists():
        st, b = get(f"https://hakusyo1.moj.go.jp/jp/{n}/nfm/{page}")
        if st != 200:
            return ""
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b)
        time.sleep(0.5)
    return text(p.read_bytes())


def strip(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", s)).split())


def main():
    eds, kind, pat, save = sys.argv[1].split(","), sys.argv[2], re.compile(sys.argv[3]), sys.argv[4]
    for n in eds:
        cands = []
        if kind == "shiryo":
            for href, t in re.findall(r'href="\./(excel/shiryo[^"]+\.xlsx)"[^>]*>(.*?)</a>', index(n, "mokuji.html"), re.S):
                cands.append((href, strip(t)))
        else:
            for anchor, t in re.findall(r'html#h([0-9-]+)"[^>]*>(.*?)</a>', index(n, "gmokuji.html"), re.S):
                cands.append((f"excel/{anchor}.xlsx", strip(t)))
        hits = [(h, t) for h, t in cands if pat.search(t)]
        out = ROOT / "data/raw/hanzai_hakusho" / n / "bytitle"
        if not hits:
            print(n, "NOT FOUND"); continue
        href, title = hits[0]
        st, body = get(f"https://hakusyo1.moj.go.jp/jp/{n}/nfm/{href}")
        time.sleep(0.5)
        ok = st == 200 and body[:2] == b"PK"
        if ok:
            out.mkdir(parents=True, exist_ok=True)
            (out / f"{save}.xlsx").write_bytes(body)
        out.mkdir(parents=True, exist_ok=True)
        with open(out / "BYTITLE.tsv", "a", encoding="utf-8") as fh:
            fh.write("\t".join([save, title, href, str(st), hashlib.sha256(body).hexdigest() if body else "",
                                datetime.now(timezone.utc).isoformat(timespec="seconds")]) + "\n")
        print(n, st, href, title[:60], f"(候補 {len(hits)})")


if __name__ == "__main__":
    main()
