"""国会の発言の候補を Claude で分類する（2026-11-21）。答弁が記録の資料をどう引いたかを、決めた型のどれかに当てる。
逐語の引用（答弁から一つ、資料から一つ）を必ず出させ、機械でその文字列が元にあるかを確かめる（無ければ「引用が元にない」で落とす）。
python3 kokkai/classify.py <日付> [件数の上限]"""
import json, os, re, sys, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import llm
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
day = sys.argv[1]; LIM = int(sys.argv[2]) if len(sys.argv) > 2 else 10**9; D = os.path.join(ROOT, 'results/kokkai', day)
F = {f['id']: f for f in json.load(open(os.path.join(ROOT, 'publish/findings.json'), encoding='utf-8'))}
TYPES = ['限定が落ちる', '範囲のずれ', '数字の不一致', '出典が示されていない', '食い違いなし', '渡した資料と別の資料', '判定不能']
import classify_src
src = classify_src.src
def prompt(c):
    return f"""あなたは日本の公的資料の引用を点検する係です。以下は国会での発言（政府側の答弁、閣議決定された答弁書、または議員の質問）の一部と、URAZUKE が記録した資料の原文です。
発言（以下「答弁」と呼ぶ）が、渡した資料（の内容）を引いているかを判断し、引いているなら、資料の原文と比べて次の型のどれに当たるかを一つ選んでください。
型：
- 限定が落ちる：資料にある限定（「示唆」「一部」「有意差なし」「〜に限る」など）が答弁で落ち、言い方が強くなっている
- 範囲のずれ：資料の数字や結論の範囲（対象・罪種・年度・指標）と、答弁が当てはめる範囲が違う
- 数字の不一致：答弁の数字が資料の数字と合わない
- 出典が示されていない：答弁が数字や結論を述べるが、どの資料か特定できない
- 食い違いなし：答弁は資料と食い違わない
- 渡した資料と別の資料：答弁が引いているのは、渡した資料とは別の資料（別の年度の報告書など）
- 判定不能：渡された情報では判断できない
決まり：推測で補わない。「限定が落ちる」「範囲のずれ」は、結論の強さや当てはまる範囲を変えるものに限る（効果の有無・程度、対象者の範囲、罪種、指標、年度など）。施設名の例外や細かな条件の言い残しなど、結論に影響しない細目は「食い違いなし」とする。答弁の文と資料の原文に書いてあることだけで判断する。答弁からの引用（speech_quote）と資料からの引用（source_quote）は、下の文からそのまま写す（一字も変えない。60字以内）。型が「食い違いなし」以外なら、何がどう違うかを explanation に2文以内で書く。
JSON だけを出力：{{"record_ids": [...], "type": "...", "speech_quote": "...", "source_quote": "...", "explanation": "..."}}

【答弁】{c['date']} {c['house']} {c['meeting']} {c['speaker']}（{c['position']}）
{c['passage']}

【資料（URAZUKE の記録と原文）】
{chr(10).join(src(r) for r in c['records'])}
"""
norm = lambda s: re.sub(r'\s+', '', s or '')
def run(c):
    try:
        t = llm.claude(prompt(c)); j = llm.js(t) or {}
    except Exception as ex: j = {'type': 'エラー', 'explanation': type(ex).__name__}
    srcs = norm(' '.join(q['文'] for r in c['records'] for q in F[r].get('原文の引用', [])) + ' '.join(q['text'] for r in c['records'] if r in classify_src.CIT for q in classify_src.CIT[r]['src_quotes']))
    j['speech_quote_ok'] = bool(j.get('speech_quote')) and norm(j['speech_quote']) in norm(c['passage'])
    j['source_quote_ok'] = bool(j.get('source_quote')) and norm(j['source_quote']) in srcs
    return {**c, 'claude': j}
IN, OUT = (sys.argv[3], sys.argv[4]) if len(sys.argv) > 4 else ('candidates.jsonl', 'classified.jsonl')
C = [json.loads(l) for l in open(os.path.join(D, IN), encoding='utf-8')][:LIM]
with cf.ThreadPoolExecutor(4) as ex, open(os.path.join(D, OUT), 'w', encoding='utf-8') as w:
    for r in ex.map(run, C):
        w.write(json.dumps(r, ensure_ascii=False) + '\n'); w.flush()
        print(r['date'], r['speaker'], r['claude'].get('type'), r['claude'].get('record_ids'), r['claude'].get('speech_quote_ok'), r['claude'].get('source_quote_ok'), flush=True)
