"""Claude の分類を、別会社の GPT に盲検で試させる（2026-11-21）。
食い違いの型（限定が落ちる・範囲のずれ・数字の不一致）で、逐語の引用が元にあったものだけを対象にする。
各候補について「Claude の主張」と「答弁は資料と食い違わない」という対の主張を、書き手を伏せ、順序をばらばらにして渡す。
GPT が Claude の主張を支持し、対の主張を支持しないものだけを「別系統で支持」とする。python3 kokkai/refute.py <日付>"""
import json, os, random, sys, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import llm, classify_src
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
day = sys.argv[1]; D = os.path.join(ROOT, 'results/kokkai', day)
TARGET = {'限定が落ちる', '範囲のずれ', '数字の不一致', '食い違いなし'}
def prompt(c, claims):
    cl = '\n'.join(f'主張{k}：{t}' for k, t in claims)
    return f"""以下は国会での発言（政府側の答弁、答弁書、または議員の質問。以下「答弁」）の一部と、ある公的資料についての記録・原文の抜粋です。続く二つの主張それぞれについて、答弁と資料の抜粋に書いてあることだけから、
「支持」「不支持」「判定不能」のどれかを判断してください。推測で補わないでください。限定や範囲の食い違いは、結論の強さや当てはまる範囲を変えるもの（効果の有無・程度、対象者の範囲、罪種、指標、年度など）だけを数え、結論に影響しない細目の言い残しは食い違いとしないでください。主張の書き手は伏せてあります。
JSON だけを出力：{{"判定": {{"A": "...", "B": "..."}}, "理由": {{"A": "...", "B": "..."}}}}

【答弁】{c['date']} {c['house']} {c['meeting']} {c['speaker']}
{c['passage']}

【資料】
{(c['source']['name'] + chr(10) + c['source']['text']) if c.get('source') else classify_src.block(c['records'])}

【主張】
{cl}
"""
def run(c):
    j = c['claude']; rid = '・'.join(j.get('record_ids') or []) or (c.get('source') or {}).get('name', '')
    claim = (f"答弁の「{j['speech_quote']}」は、資料（{rid}）の「{j['source_quote']}」と食い違わない（数字・限定・範囲とも資料に沿っている）。" if j['type'] == '食い違いなし'
             else f"答弁の「{j['speech_quote']}」は、資料（{rid}）の「{j['source_quote']}」と比べて「{j['type']}」に当たる：{j.get('explanation', '')}")
    # 対の主張は型ごとに、Claude の主張と両立しない形にする（2026-11-21：「食い違わない」だと数字が正しい場合に両方が支持された）
    null = {'限定が落ちる': f"答弁の「{j['speech_quote']}」は、資料（{rid}）にある限定や条件を保っており、資料より強い言い方をしていない。",
            '範囲のずれ': f"答弁の「{j['speech_quote']}」が当てはめる対象・範囲は、資料（{rid}）の数字や結論の対象・範囲と同じである。",
            '数字の不一致': f"答弁の「{j['speech_quote']}」の数字は、資料（{rid}）の数字と合っている。",
            '食い違いなし': f"答弁の「{j['speech_quote']}」は、資料（{rid}）と数字・限定・範囲のいずれかで食い違っている。"}[j['type']]
    order = [('claim', claim), ('null', null)]; random.Random(c['speechID']).shuffle(order)
    lab = {'A': order[0][0], 'B': order[1][0]}
    try:
        g = llm.js(llm.gpt(prompt(c, [('A', order[0][1]), ('B', order[1][1])]))) or {}
        v = {lab[k]: g.get('判定', {}).get(k) for k in 'AB'}; why = {lab[k]: g.get('理由', {}).get(k) for k in 'AB'}
    except Exception as ex: v, why = {'claim': 'エラー', 'null': 'エラー'}, {'err': type(ex).__name__}
    res = '別系統で支持' if (v.get('claim') == '支持' and v.get('null') != '支持') else ('別系統で不支持' if v.get('claim') == '不支持' else '判定不能')
    return {**c, 'gpt': dict(verdict=v, reason=why, result=res)}
if __name__ == '__main__':
    IN, OUTF = (sys.argv[2], sys.argv[3]) if len(sys.argv) > 3 else ('classified.jsonl', 'refuted.jsonl')
    C = [json.loads(l) for l in open(os.path.join(D, IN), encoding='utf-8')]
    C = [c for c in C if c['claude'].get('type') in TARGET and c['claude'].get('speech_quote_ok') and c['claude'].get('source_quote_ok')]
    print('対象', len(C), flush=True)
    with cf.ThreadPoolExecutor(4) as ex, open(os.path.join(D, OUTF), 'w', encoding='utf-8') as w:
        for r in ex.map(run, C):
            w.write(json.dumps(r, ensure_ascii=False) + '\n'); w.flush(); print(r['date'], r['speaker'], r['claude']['type'], r['gpt']['result'], flush=True)
