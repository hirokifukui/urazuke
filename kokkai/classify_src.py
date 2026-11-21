"""記録の要旨と原文の引用を、LLM に渡す形に組み立てる（classify.py・refute.py で共用）。"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = {f['id']: f for f in json.load(open(os.path.join(ROOT, 'publish/findings.json'), encoding='utf-8'))}
CIT = {r['rec']: r for r in json.load(open(os.path.join(ROOT, 'publish/citations.json'), encoding='utf-8'))['records']} if os.path.exists(os.path.join(ROOT, 'publish/citations.json')) else {}
def src(rid):
    f = F[rid]
    qs = '\n'.join(f'  - 「{q["文"]}」（{q["ファイル"]} {q["箇所"]}）' for q in f.get('原文の引用', []))
    out = f'■ 記録 {rid}（資料：{f["統計"]}）\n要旨：{f["要旨"]}\n資料の原文：\n{qs}'
    if rid in CIT:   # 引かれ方で「元の資料」としている資料（記録の原文と別のことがある。2026-11-21：これを渡さず、答弁が正しく引いた資料を見落とした）
        c = CIT[rid]; cq = '\n'.join(f'  - 「{q["text"]}」（{q["label"]} {q["where"]}）' for q in c['src_quotes'])
        out += f'\n引かれ方の元の資料：{c["src"]}\nこの資料が言っていること：{c["says"]}\nこの資料の原文：\n{cq}'
    return out
def block(rids): return '\n'.join(src(r) for r in rids)
