"""c1103: 自殺対策白書 参考資料2（Excel）で、数字が文字列として入っているセル（例 '172'）を数える（L4：機械判読の不備）。令和6・7・8年版。
使い方: ~/.venvs/urazuke/bin/python checks/jisatsu_hakusho/c1103_text_numbers.py"""
import re, json, openpyxl, collections
D = 'data/raw/jisatsu_hakusho'
E = {'r2024': f'{D}/r2024/sanko2_001332662.xlsx', 'r2025': f'{D}/r2025/sanko2_001593171.xlsx', 'r2026': f'{D}/r2026/sanko2_001760475.xlsx'}
out = {}
for e, p in E.items():
    wb = openpyxl.load_workbook(p); hits = []; n = 0
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, (int, float)): n += 1
                elif isinstance(c.value, str) and re.fullmatch(r'\s*-?[\d,]+(\.\d+)?\s*', c.value):
                    hits.append((ws.title, c.coordinate, c.value, ws.cell(c.row, 1).value))
    out[e] = {'numeric_cells': n, 'text_numbers': hits}
    print(e, 'numeric', n, 'text-numbers', len(hits), collections.Counter(h[0] for h in hits).most_common(5), hits[:6])
json.dump(out, open('results/jisatsu_hakusho/c1103_text_numbers.json', 'w'), ensure_ascii=False, indent=1, default=str)
