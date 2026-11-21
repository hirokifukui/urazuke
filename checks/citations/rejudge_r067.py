"""R067（2026-11-21、運営者の決定）：引かれ方の型を、定義を改めて全件やり直す。
改めた点：T3・T4 は「結論の強さや当てはまる範囲を変えるもの」だけを数える（重要性の条件）。分かれたものだけをやり直すと結果を見て基準を変えることになるため、国会以外の引用を全件やり直す。
組は記録 ID・媒体名・URL を伏せ、順序を乱し、型の明らかな対照2組を混ぜて、GPT と Gemini に別々に渡す。両方が対照に正答した場合だけ採る。
出力：replications/R067_rejudge/（PROMPT.md・KEY.json・REPORT_gpt.json・REPORT_gemini.json）と results/citations/R067.json。"""
import json, os, random, re, sys, hashlib, datetime
sys.path.insert(0, 'kokkai'); import llm
OUT = 'replications/R067_rejudge'; os.makedirs(OUT, exist_ok=True)
C = json.load(open('publish/citations.json', encoding='utf-8'))['records']
pairs = []
for r in C:
    for c in r['cites']:
        if c.get('kind') == '国会': continue
        src = '\n'.join(f"［{n + 1}］{r['src_quotes'][n]['label']} {r['src_quotes'][n]['where']}：「{r['src_quotes'][n]['text']}」" for n in c['pair'] if n < len(r['src_quotes']))
        pairs.append(dict(id=c['id'], src=src, cite=c['quote']))
CTRL = [dict(id='CTRL-T1', src='令和４年度の児童虐待相談の対応件数（確定値）は 214,843 件。', cite='2022年度の児童虐待相談の対応件数（確定値）は21万4483件だった。', expect={'T1'}),
        dict(id='CTRL-T0', src='令和５年の小中高生の自殺者数は 513 人。', cite='2023年の小中高生の自殺者数は513人だった。', expect={'T0'})]
allp = pairs + CTRL; random.Random(67).shuffle(allp)
key = {f'C{i + 1:02d}': p['id'] for i, p in enumerate(allp)}
DEF = """## 型の定義（これ以外は付けない）
- T0 同じ：数値も言い方も元と同じ（言い換えでも、量と強さが同じなら T0）。
- T1 値が違う：数値が元と違う（写し間違い、速報値と確定値の取り違えを含む）。
- T2 量が置き換わる：別の量として書く（ハザード比や「再犯可能性」を「再犯率」と書く、別の群の比較を同じ集団の「低下」と書く、など）。
- T3 言い方が強まる：元の「示唆」「有意傾向」「可能性」が「確認」「効果があった」「認められた」などになる。
- T4 限定が落ちる：元の資料の文にある但し書き・条件（効果が裏付けられなかった群、数え方の変更、など）を書かずに結論や比較を引く。引用の文の中にその但し書きがあれば T4 にしない。
- T5 後の訂正が入っていない：元の資料が後に直された（正誤表・確定値）のに、引用の掲載時期にはすでに直っていた値を、直す前の値のまま引く。

T3・T4 は、結論の強さや当てはまる範囲（効果の有無・程度、対象者、罪種、指標、年度、数え方）を変えるものだけに付ける。結論の強さや範囲を変えない細目の言い残しは、T3・T4 にしない。
T0 は他の型と同時に付けない。元の資料の文に書かれていないことは判断の材料にしない。判断できないときは「判定不能」とし、理由を書く。"""
P = ("# 課題：引用の型の判定\n\n公的な資料の文（元の資料の文）と、それを引いた文（引用の文）の組が下にあります。各組について、次の型のうち当てはまるものをすべて付けてください。文の比較だけで決め、引いた側の意図や評価は書かないでください。\n\n"
     + DEF + "\n\n## 出力\nJSON だけを出力：{\"C01\": {\"型\": [\"T4\"], \"理由\": \"…\"}, \"C02\": {…}, …}（判断できないときは \"型\": [\"判定不能\"]）\n\n## 組\n"
     + ''.join(f"### {k}\n- 元の資料の文：\n{p['src']}\n- 引用の文：{p['cite']}\n\n" for k, p in zip(key, allp)))
open(f'{OUT}/PROMPT.md', 'w').write(P); json.dump(key, open(f'{OUT}/KEY.json', 'w'), ensure_ascii=False, indent=1)
res = {}
for name, fn in (('gpt', llm.gpt), ('gemini', llm.gemini)):
    t = fn(P); open(f'{OUT}/REPORT_{name}.txt', 'w').write(t)
    j = llm.js(t) or {}; res[name] = {key[k]: v.get('型', []) for k, v in j.items() if k in key}
    json.dump(res[name], open(f'{OUT}/REPORT_{name}.json', 'w'), ensure_ascii=False, indent=1)
ctrl_ok = {n: all(set(res[n].get(c['id'], [])) == c['expect'] for c in CTRL) for n in res}
out = dict(round='R067', date=datetime.date.today().isoformat(), prompt_sha256=hashlib.sha256(P.encode()).hexdigest(), control_ok=ctrl_ok, items={})
for p in pairs:
    g, m = res['gpt'].get(p['id'], []), res['gemini'].get(p['id'], [])
    com = sorted(set(x for x in g if x.startswith('T')) & set(x for x in m if x.startswith('T')))
    out['items'][p['id']] = dict(gpt=g, gemini=m, common=com)
json.dump(out, open('results/citations/R067.json', 'w'), ensure_ascii=False, indent=1)
print('対照', ctrl_ok, '件数', len(pairs), '共通の型あり', sum(1 for v in out['items'].values() if v['common']))
