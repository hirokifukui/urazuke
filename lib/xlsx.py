"""標準ライブラリだけで .xlsx の値を読む最小限の読み取り器（外部依存なし・再現性のため）。

read_sheets(path) -> {シート名: {(行, 列): 値}}   行・列は 1 始まり。
値は数値なら float、文字列なら str。数式セルはキャッシュされた値を返す。
"""
import re, zipfile
import xml.etree.ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def _col(ref):
    letters = re.match(r"[A-Z]+", ref).group()
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n, int(ref[len(letters):])


def read_sheets(path):
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            # ルビ（rPh）を除いた本文だけを連結する
            parts = [t.text or "" for t in si.findall("m:t", NS)]
            parts += [t.text or "" for r in si.findall("m:r", NS) for t in r.findall("m:t", NS)]
            shared.append("".join(parts))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    target = {r.get("Id"): r.get("Target") for r in rels}
    out = {}
    for s in wb.find("m:sheets", NS):
        rid = s.get("{%s}id" % NS["r"])
        t = target[rid].lstrip("/")
        t = t if t.startswith("xl/") else "xl/" + t
        cells = {}
        for c in ET.fromstring(z.read(t)).iter("{%s}c" % NS["m"]):
            v = c.find("m:v", NS)
            typ = c.get("t")
            if typ == "inlineStr":
                val = "".join(x.text or "" for x in c.iter("{%s}t" % NS["m"]))
            elif v is None:
                continue
            elif typ == "s":
                val = shared[int(v.text)]
            elif typ in ("str", "e"):
                val = v.text
            elif typ == "b":
                val = bool(int(v.text))
            else:
                try:
                    val = float(v.text)
                except ValueError:
                    val = v.text
            col, row = _col(c.get("r"))
            cells[(row, col)] = val
        out[s.get("name")] = cells
    return out


def dump(path, max_rows=40, max_cols=12):
    for name, cells in read_sheets(path).items():
        print(f"## sheet: {name}")
        if not cells:
            continue
        R = min(max(r for r, _ in cells), max_rows)
        C = min(max(c for _, c in cells), max_cols)
        for r in range(1, R + 1):
            row = [cells.get((r, c), "") for c in range(1, C + 1)]
            if any(x != "" for x in row):
                print(r, "|", " | ".join(str(x) for x in row))
