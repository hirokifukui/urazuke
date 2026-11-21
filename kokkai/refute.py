"""Claude の分類を、別会社の GPT に盲検で試させる（2026-11-21）。
食い違いの型（限定が落ちる・範囲のずれ・数字の不一致）で、逐語の引用が元にあったものだけを対象にする。
各候補について「Claude の主張」と「答弁は資料と食い違わない」という対の主張を、書き手を伏せ、順序をばらばらにして渡す。
GPT と Gemini の二つとも、Claude の主張を支持し対の主張を支持しないものだけを「別系統で支持」とする（Gemini は 2026-11-21 から）。python3 kokkai/refute.py <日付>"""
import json, os, random, sys, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import llm, classify_src
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
day = sys.argv[1]; D = os.path.join(ROOT, 'results/kokkai', day)
TARGET = {'言い方が強まる', '限定が落ちる', '範囲のずれ', '数字の不一致', '食い違いなし'}
def prompt(c, claims):
    cl = '\n'.join(f'主張{k}：{t}' for k, t in claims)
    return f"""以下は国会での発言（政府側の答弁、答弁書、または議員の質問。以下「答弁」）の一部と、ある公的資料についての記録・原文の抜粋です。続く二つの主張それぞれについて、答弁と資料の抜粋に書いてあることだけから、
「支持」「不支持」「判定不能」のどれかを判断してください。推測で補わないでください。限定や範囲の食い違いは、結論の強さや当てはまる範囲を変えるもの（効果の有無・程度、対象者の範囲、罪種、指標、年度など）だけを数え、結論に影響しない細目の言い残しは食い違いとしないでください。資料が対象者全体の結果と一部の対象者（罪名・属性などで分けた群）の結果を分けて書いているとき、答弁が全体の結果を全体の結果として述べるだけなら限定は落ちていない。全体の結果を、裏付けのなかった群を含む個々の対象にも当てはまるように述べる場合や、一部の群の結果を全体の結果のように述べる場合は「限定が落ちる」とする。指標（何の再犯を数えたか、など）の違いは、全体と一部の違いではない。資料が一つの指標（例：全ての犯罪の再犯）でだけ効果を示し、別の指標（例：性犯罪の再犯）では示せなかったとき、答弁が指標を言わずに効果を述べれば「限定が落ちる」とする。比べた群の取り方（比較対照群が誰か、除外の条件など）を別の群の名前で言い換えることも、全体と一部の違いではない。言い換えで比べた群が変わって読めるなら「範囲のずれ」とする。発言が、他の人の答弁を「…という御答弁だった」などと言い直しているだけのときは、資料を引いたことにならないので「渡した資料と別の資料」とする（言い直された元の答弁を、それ自体として判定する）。主張の書き手は伏せてあります。
JSON だけを出力：{{"判定": {{"A": "...", "B": "..."}}, "理由": {{"A": "...", "B": "..."}}}}

【答弁】{c['date']} {c['house']} {c['meeting']} {c['speaker']}
{c['passage']}

【資料】
{(c['source']['name'] + chr(10) + c['source']['text']) if c.get('source') else classify_src.block(c['records'])}

【主張】
{cl}
"""
def run(c, k=0):   # k>0：同じ候補のやり直し（主張の順序を変える。confirm.py から）
    j = c['claude']; rid = '・'.join(j.get('record_ids') or []) or (c.get('source') or {}).get('name', '')
    claim = (f"答弁の「{j['speech_quote']}」は、資料（{rid}）の「{j['source_quote']}」と食い違わない（数字・限定・範囲とも資料に沿っている）。" if j['type'] == '食い違いなし'
             else f"答弁の「{j['speech_quote']}」は、資料（{rid}）の「{j['source_quote']}」と比べて「{j['type']}」に当たる：{j.get('explanation', '')}")
    # 対の主張は型ごとに、Claude の主張と両立しない形にする（2026-11-21：「食い違わない」だと数字が正しい場合に両方が支持された）
    null = {'言い方が強まる': f"答弁の「{j['speech_quote']}」の言い方の強さ（示唆か、認められたか、など）は、資料（{rid}）の言い方と同じである。",
            '限定が落ちる': f"答弁の「{j['speech_quote']}」は、資料（{rid}）にある限定や条件を保っており、資料より強い言い方をしていない。",
            '範囲のずれ': f"答弁の「{j['speech_quote']}」が当てはめる対象・範囲は、資料（{rid}）の数字や結論の対象・範囲と同じである。",
            '数字の不一致': f"答弁の「{j['speech_quote']}」の数字は、資料（{rid}）の数字と合っている。",
            '食い違いなし': f"答弁の「{j['speech_quote']}」は、資料（{rid}）と数字・限定・範囲のいずれかで食い違っている。"}[j['type']]
    order = [('claim', claim), ('null', null)]; random.Random(c['speechID'] if not k else f"{c['speechID']}-{k}").shuffle(order)
    lab = {'A': order[0][0], 'B': order[1][0]}
    P = prompt(c, [('A', order[0][1]), ('B', order[1][1])])
    J = {}
    for name, fn in (('gpt', llm.gpt), ('gemini', llm.gemini)):   # 2026-11-21：Gemini を加え、二つとも主張だけを支持したものを採る
        try:
            g = llm.js(fn(P)) or {}
            v = {lab[k]: g.get('判定', {}).get(k) for k in 'AB'}; why = {lab[k]: g.get('理由', {}).get(k) for k in 'AB'}
        except Exception as ex: v, why = {'claim': 'エラー', 'null': 'エラー'}, {'err': type(ex).__name__}
        J[name] = dict(verdict=v, reason=why, ok=(v.get('claim') == '支持' and v.get('null') != '支持'), no=(v.get('claim') == '不支持'))
    v, why = J['gpt']['verdict'], J['gpt']['reason']
    res = '別系統で支持' if all(x['ok'] for x in J.values()) else ('別系統で不支持' if any(x['no'] for x in J.values()) else '判定不能')
    return {**c, 'gpt': dict(verdict=v, reason=why, result=res), 'gemini': J['gemini']}
if __name__ == '__main__':
    IN, OUTF = (sys.argv[2], sys.argv[3]) if len(sys.argv) > 3 else ('classified.jsonl', 'refuted.jsonl')
    C = [json.loads(l) for l in open(os.path.join(D, IN), encoding='utf-8')]
    C = [c for c in C if c['claude'].get('type') in TARGET and c['claude'].get('speech_quote_ok') and c['claude'].get('source_quote_ok')]
    print('対象', len(C), flush=True)
    with cf.ThreadPoolExecutor(4) as ex, open(os.path.join(D, OUTF), 'w', encoding='utf-8') as w:
        for r in ex.map(run, C):
            w.write(json.dumps(r, ensure_ascii=False) + '\n'); w.flush(); print(r['date'], r['speaker'], r['claude']['type'], r['gpt']['result'], flush=True)
