"""矯正統計年報：表の上の年次の部分（過去5年の総数の行）で、過去の年がすべて 0 で最新の年だけ値がある列を拾う。
新しく設けた区分の過去の年を「0」と表示している（未集計の記号でなく）場合に当たる。
使い方: python checks/kyosei_ninchi/c4502_zero_past.py [年 ...]（既定 2023 2024 2025）
"""
import sys, glob, re
from pathlib import Path
import openpyxl
ROOT = Path.cwd() if (Path.cwd() / 'data/raw').is_dir() else Path(__file__).resolve().parents[2]
years = [int(a) for a in sys.argv[1:]] or [2023, 2024, 2025]
hits = 0
for y in years:
    for f in sorted(glob.glob(str(ROOT / f'data/raw/kyosei/{y}/*.xlsx'))):
        try:
            rows = [list(r) for r in openpyxl.load_workbook(f, read_only=True, data_only=True).active.iter_rows(values_only=True)]
        except Exception:
            continue
        title = next((str(c) for r in rows[:3] for c in r if isinstance(c, str) and c.strip()), '')
        # 見出しの行：最初に「総数」を含む行
        hi = next((i for i, r in enumerate(rows[:15]) if any(isinstance(c, str) and c.strip() == '総数' for c in r)), None)
        if hi is None:
            continue
        hdr = rows[hi]
        # 年次の部分：「総数」の行で、その前の列に年の印（令和・平成・年・数字・日付）がある行を上から順に
        yr = []
        for r in rows[hi + 1:hi + 40]:
            lab = [c for c in r[:10] if c is not None]
            if any(isinstance(c, str) and c.strip() == '総数' for c in lab) and len(lab) >= 2:
                yr.append(r)
            elif yr and any(isinstance(c, str) and re.search(r'刑法犯|うち|特別法犯', c.strip()) for c in lab) and not any(str(c).strip() == '総数' for c in lab):
                break
        if len(yr) < 3:
            continue
        for j, h in enumerate(hdr):
            if not isinstance(h, str) or not h.strip():
                continue
            col = [r[j] if j < len(r) else None for r in yr]
            if all(isinstance(v, (int, float)) for v in col) and all(v == 0 for v in col[:-1]) and col[-1] > 0:
                hits += 1
                print(f"{y} {Path(f).name} {title[:40]} | 列「{re.sub(r'\s+', '', h)}」 過去 {len(col) - 1} 年が 0、最新 {col[-1]}")
print('該当', hits)
