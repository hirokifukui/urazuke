"""judge_pairs.py — 引用の型を付ける（毎週の巡回でも使う。2026-11-22、R073・R074 の手順を固定したもの）。
使い方：python3 checks/citations/judge_pairs.py <回の名前 例 R076> <組の JSON>
組の JSON：{"Q-XX-Y1-001": {"date": "2025-03", "src": "元の資料の文（頁・表を添える。引用が拠る範囲をすべて）", "cite": "引用の文（見出しなら本文も、文なら同じ段落・同じ注の前後も）"}, ...}
手順（R073 と同じ。変えるときは METHODS に書き、全件をやり直す）：
- 定義は R067 の課題文に、基準点の一文（元の資料の文の言い方と比べる）と、引用の単位の一文（見出しは本文と、文は段落・注の前後と合わせて読む）を足したもの。出力に「根拠」を含める。
- 組ごとに別々に渡す。各呼び出しに、対象の組1つと型の明らかな対照2組（CTRL-T1・CTRL-T0）を、順序を乱して入れる。対照の2組に正答した呼び出しだけを使う。
- GPT と Gemini に各5回。判定者ごとに、使える呼び出しの過半で付いた型をその判定者の型とする（使える呼び出しが3回未満なら判定が分かれた）。
- 二つの判定者の型が同じならそれを、違えば共通する型を、共通がなければ「判定が分かれた」。
- 「判定が分かれた」は <回>_split.json に出す。原因を AI の外に特定するまで解消する（材料の不足 → 定義の穴 → 文が一つに読めない、の順に調べる）。
出力：results/citations/<回>.json、results/citations/<回>_split.json、replications/<回>_pairs/calls.jsonl（公開から除く）。
citations.tsv の「型の判定」欄の書き方：<回>（<how>：GPT <型>／Gemini <型>。組ごとに各5回の過半）。apply オプションで書き込む：
python3 checks/citations/judge_pairs.py --apply <回>"""
import json, os, random, re, sys, datetime, concurrent.futures as cf
sys.path.insert(0, 'kokkai'); import llm
def blocks(d):
    P = open(f'replications/{d}/PROMPT.md').read(); K = json.load(open(f'replications/{d}/KEY.json'))
    b = re.split(r'(?m)^### (C\d+)\n', P.split('## 組\n', 1)[1])[1:]
    return {K[b[i]]: b[i + 1].split('\n## ')[0].strip() + '\n\n' for i in range(0, len(b), 2)}
def build_head():
    head = open('replications/R067_rejudge/PROMPT.md').read().split('## 組\n', 1)[0]
    A = 'T0 は他の型と同時に付けない。'; assert A in head
    head = head.replace(A, '比べる相手は元の資料の文の言い方とする。元の資料の文が、自分の示す数字より強く言っている場合（群の比較を「抑えられた」と書く、など）、それを同じ強さで引いた側は型に数えない。\n' + A)
    head = head.replace(A, '引用は、見出しなら本文と合わせて、文なら同じ段落・同じ注の前後と合わせて読む。その範囲で名前や限定が示されていれば、見出しや一文で縮めていても落ちたとはしない。\n' + A)
    Bq = 'JSON だけを出力：{"C01": {"型": ["T4"], "理由": "…"}'; assert Bq in head
    return head.replace(Bq, 'JSON だけを出力：{"C01": {"型": ["T4"], "理由": "…", "根拠": "判定が拠った定義の文（そのまま写す）"}')
def maj(L):
    if not L: return None
    n = len(L); ts = [set(t for t in x if t.startswith('T')) for x in L]
    if sum(1 for x in L if not any(t.startswith('T') for t in x)) * 2 > n: return frozenset(['判定不能'])
    allt = set().union(*ts)
    return frozenset(t for t in allt if sum(t in x for x in ts) * 2 > n)
def run(rnd, pairs):
    OUT = f'replications/{rnd}_pairs'; os.makedirs(OUT, exist_ok=True)
    B29 = blocks('R029_gpt_types')
    CTRL = {'CTRL-T1': (B29['CTRL-T1'], {'T1'}), 'CTRL-T0': (B29['CTRL-T0'], {'T0'})}
    head = build_head()
    items = {u: f"- 引用の掲載時期：{v['date']}\n- 元の資料の文：\n{v['src']}\n- 引用の文：{v['cite']}\n\n" for u, v in pairs.items()}
    open(f'{OUT}/PROMPT_HEAD.md', 'w').write(head)
    def call(job):
        u, name, n = job
        ids = [u, 'CTRL-T1', 'CTRL-T0']; random.Random(f'{rnd}-{u}-{name}-{n}').shuffle(ids)
        key = {f'C{i + 1:02d}': x for i, x in enumerate(ids)}
        P = head + '## 組\n' + ''.join(f'### {k}\n{items[x] if x == u else CTRL[x][0]}' for k, x in key.items())
        try: t = (llm.gpt if name == 'gpt' else llm.gemini)(P)
        except Exception as ex: t = f'ERROR {type(ex).__name__}'
        j = llm.js(t) or {}; r = {key[k]: (v or {}).get('型', []) for k, v in j.items() if k in key}
        basis = (j.get([k for k, x in key.items() if x == u][0]) or {}).get('根拠', '')
        ok = all(set(r.get(c, [])) == e for c, (_, e) in CTRL.items())
        return dict(pair=u, judge=name, n=n, ok=ok, types=r.get(u, []), basis=basis, raw=t, prompt=P)
    jobs = [(u, nm, n) for u in items for nm in ('gpt', 'gemini') for n in range(5)]
    res = []
    with cf.ThreadPoolExecutor(6) as ex, open(f'{OUT}/calls.jsonl', 'w') as w:
        for x in ex.map(call, jobs):
            res.append(x); w.write(json.dumps(x, ensure_ascii=False) + '\n'); w.flush()
            print(x['pair'], x['judge'], x['n'], x['ok'], x['types'], flush=True)
    out = dict(round=rnd, date=datetime.date.today().isoformat(), items={}, control_ok=sum(x['ok'] for x in res), calls=len(res)); amb = []
    for u in items:
        use = {nm: [x['types'] for x in res if x['pair'] == u and x['judge'] == nm and x['ok']] for nm in ('gpt', 'gemini')}
        m = {nm: maj(v) for nm, v in use.items()}
        if None in m.values() or any(len(v) < 3 for v in use.values()): final, how = ['判定が分かれた'], '対照に正答した呼び出しが足りない'
        elif m['gpt'] == m['gemini'] and m['gpt']: final, how = sorted(m['gpt']), '二つの判定者の過半の型が同じ'
        elif (m['gpt'] & m['gemini']) - {'判定不能'}: final, how = sorted((m['gpt'] & m['gemini']) - {'判定不能'}), '二つの判定者の過半の型に共通する型'
        else: final, how = ['判定が分かれた'], '共通する型がない'
        if final == ['判定が分かれた']: amb.append(dict(pair=u, gpt=sorted(m['gpt'] or []), gemini=sorted(m['gemini'] or []), basis=[x['basis'] for x in res if x['pair'] == u and x['ok']]))
        out['items'][u] = dict(pair=f'{rnd}:{u}', gpt=use['gpt'], gemini=use['gemini'], gpt_major=sorted(m['gpt'] or []), gemini_major=sorted(m['gemini'] or []), final=final, how=how)
    json.dump(out, open(f'results/citations/{rnd}.json', 'w'), ensure_ascii=False, indent=1)
    json.dump(amb, open(f'results/citations/{rnd}_split.json', 'w'), ensure_ascii=False, indent=1)
    print('呼び出し', len(res), '対照正答', out['control_ok'], '判定が分かれた', len(amb))
def apply(rnd):
    d = json.load(open(f'results/citations/{rnd}.json'))['items']; p = 'results/citations/citations.tsv'
    L = open(p, encoding='utf-8').read().split('\n'); n = 0
    for i, l in enumerate(L):
        c = l.split('\t')
        if c and c[0] in d:
            r = d[c[0]]; c[9] = '、'.join(r['final'])
            c[10] = f"{rnd}（{r['how']}：GPT {'、'.join(r['gpt_major'])}／Gemini {'、'.join(r['gemini_major'])}。組ごとに各5回の過半）"
            L[i] = '\t'.join(c); n += 1
    open(p, 'w', encoding='utf-8').write('\n'.join(L)); print('書き込んだ', n)
if __name__ == '__main__':
    if sys.argv[1] == '--apply': apply(sys.argv[2])
    else: run(sys.argv[1], json.load(open(sys.argv[2], encoding='utf-8')))
