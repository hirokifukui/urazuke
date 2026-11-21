"""記録の要旨と原文の引用を、LLM に渡す形に組み立てる（classify.py・refute.py で共用）。"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = {f['id']: f for f in json.load(open(os.path.join(ROOT, 'publish/findings.json'), encoding='utf-8'))}
def src(rid):
    f = F[rid]
    qs = '\n'.join(f'  - 「{q["文"]}」（{q["ファイル"]} {q["箇所"]}）' for q in f.get('原文の引用', []))
    return f'■ 記録 {rid}（資料：{f["統計"]}）\n要旨：{f["要旨"]}\n資料の原文：\n{qs}'
def block(rids): return '\n'.join(src(r) for r in rids)
