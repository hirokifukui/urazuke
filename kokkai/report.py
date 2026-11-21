"""国会の「引かれ方」の回の報告（results/kokkai/<日付>/REPORT.md）。python3 kokkai/report.py <日付>"""
import collections, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); day = sys.argv[1]; D = os.path.join(ROOT, 'results/kokkai', day)
C = [json.loads(l) for l in open(os.path.join(D, 'classified.jsonl'), encoding='utf-8')]
R = [json.loads(l) for f in ('refuted.jsonl', 'refuted2.jsonl', 'refuted3.jsonl', 'refuted_shuisho.jsonl', 'refuted_q.jsonl') if os.path.exists(os.path.join(D, f)) for l in open(os.path.join(D, f), encoding='utf-8')]
C2 = [json.loads(l) for l in open(os.path.join(D, 'classified2.jsonl'), encoding='utf-8')] if os.path.exists(os.path.join(D, 'classified2.jsonl')) else []
NC = [json.loads(l) for l in open(os.path.join(D, 'negctl.jsonl'), encoding='utf-8')] if os.path.exists(os.path.join(D, 'negctl.jsonl')) else []
t = collections.Counter(c['claude'].get('type') for c in C)
okq = sum(1 for c in C if c['claude'].get('speech_quote_ok') and c['claude'].get('source_quote_ok'))
L = [f'# 国会答弁の引かれ方（{day}）', '', f'- 候補（政府側の発言）：{len(C)}。逐語の引用が両方とも元にあった：{okq}。',
     '- Claude の分類：' + '、'.join(f'{k} {v}' for k, v in t.most_common()),
     '- 版の原文で照らし直した（死亡事例検証・虐待相談件数）：' + str(len(C2)) + '件。' + '、'.join(f'{k} {v}' for k, v in collections.Counter(c['claude'].get('type') for c in C2).most_common()),
     f"- 陰性対照（三つの判定者がそろって食い違いなしとした答弁に、偽の「限定が落ちる」を付けた）：{len(NC)}件中 {sum(r['gpt']['result'] == '別系統で支持' for r in NC)}件を GPT と Gemini がそろって支持",
     '- GPT の盲検（食い違いの型・引用が元にあったもの）：' + '、'.join(f'{k} {v}' for k, v in collections.Counter(r['gpt']['result'] for r in R).most_common()), '']
S = [r for r in R if r['gpt']['result'] == '別系統で支持']
L += ['## 別系統で支持されたもの（記録の候補）', '']
for r in sorted(S, key=lambda r: r['date']):
    j = r['claude']
    L += [f"### {r['date']} {r['house']} {r['meeting']} — {r['speaker']}（{j['type']}、{'記録 ' + '・'.join(j['record_ids']) if j.get('record_ids') else (r.get('source') or {}).get('name', '')}）", f"- 答弁：「{j['speech_quote']}」", f"- 資料：「{j['source_quote']}」",
          f"- Claude：{j.get('explanation','')}", f"- GPT：{(r['gpt']['reason'] or {}).get('claim','')}", f"- 会議録：{r['url']}", '']
open(os.path.join(D, 'REPORT.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L[:6]))
