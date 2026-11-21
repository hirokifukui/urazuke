"""R073b（2026-11-21）：R073 で「判定が分かれた」になった3組の「根拠」と理由を見ると、どれも渡した材料の不足だった（JH-A1-004・NK-K1-002 は見出しだけを渡し、Gemini が「見出しは本文と合わせて読む」に拠って判定不能。KP-C1-005 は「比較対照群」が誰かを渡していなかった）。記事の本文と、報告書の対象の定義の文を足し、この3組だけを R073 と同じ手順でやり直す。
以下は R073 の説明。
R073（2026-11-21、実行前に固定）：「判定が分かれた」は原因を AI の外に特定するまで解消する（運営者の決定）。R072 で残った2組を調べると、どちらも引いた文の前後を渡していなかった（GY-Q1-004 は見出しだけで、本文は「児童虐待相談の対応件数」と書く。SO-P1-002 は注の後半だけで、同じ注の前半が「性犯罪の再犯率は」と書く）。
定義に、何を一つの引用として読むかを足す：見出しは本文と合わせて読む。引いた文は、同じ段落・同じ注の前後と合わせて読む。定義が変わるので全件をやり直す。
出力に「根拠」（判定が拠った定義の文）を足し、割れたときに定義の穴か材料の不足かを見分けられるようにする。R072b の材料の足し（ST-I2-003・GY-Q1-003）も入れる。手順（組ごと、5回×2者の過半）は R072 と同じ。
以下は R072 の説明。
R072（2026-11-21、実行前に固定）：R071 の結果から二つを改める。
(a) 定義に基準点の一文を足す：比べる相手は元の資料の文の言い方。元の資料の文が自分の数字より強く言っている場合、それを引いた側は型に数えない（資料の側の論点として別に記録する）。
(b) 組ごとに別々に渡すと呼び出しは互いに独立になり、境目の組では1回の外れが出やすい（R071：全回一致 28/49）。6回全一致の規則は、独立な呼び出しでは外れ1回で決まってしまう。
    各判定者に5回ずつ渡し、対照に正答した呼び出しの過半で付いた型を、その判定者の型とする（過半が判定不能なら判定不能）。二つの判定者の型が同じならそれを、違えば共通する型を、共通がなければ「判定が分かれた」とする。
(c) それでも「判定が分かれた」になる組は、元の資料の文が一つに読めない書き方になっている候補として results/citations/R073b_split.json に出す（意図は問わない）。
以下は R071 の説明。
R071（2026-11-21）：R070 で「判定が分かれた」が残った原因への対処（運営者の問い）。
(1) R070 までは 40組を一つの課題文にまとめて渡していたため、一回の判定のぶれが多くの組に同時に及んだ（Gemini の2回目だけが NK-K1 の4件そろって T4）。
    組ごとに別々に渡す（各呼び出しに、対象の組1つと型の明らかな対照2組を、順序を乱して入れる）。対照の2組に正答した呼び出しだけを使う。
(2) 630-D1-001 は、元の資料の文に照合できる値がなく（記録の説明文を渡していた）、引用の文も途中で切れていた。長期データの値（全国の合計、都道府県別の 2024年／1998年、回答率）と、
    引用の段落の全文を渡す。都道府県別の比は長期データの値からの計算と明記する。
各組を各判定者に3回。使える呼び出しが各判定者で2回以上あれば採り、使える全ての呼び出しに共通する型を表示する（なければ「判定が分かれた」）。定義は R067〜R070 と同じ。"""
import json, os, random, re, sys, csv, datetime, concurrent.futures as cf
sys.path.insert(0, 'kokkai'); import llm
OUT = 'replications/R073b_bodies'; os.makedirs(OUT, exist_ok=True)
DIR = {'R029': 'R029_gpt_types', 'R030': 'R030_gpt_types', 'R031': 'R031_gpt_types', 'R046': 'R046_gpt_hakusho', 'R047': 'R047_gpt_hakusho', 'R066': 'R066_gpt_types'}
def blocks(d):
    P = open(f'replications/{d}/PROMPT.md').read(); K = json.load(open(f'replications/{d}/KEY.json'))
    b = re.split(r'(?m)^### (C\d+)\n', P.split('## 組\n', 1)[1])[1:]
    return {K[b[i]]: b[i + 1].split('\n## ')[0].strip() + '\n\n' for i in range(0, len(b), 2)}
B = {r: blocks(d) for r, d in DIR.items()}
M = {}
for line in open('checks/citations/add_r030_r031.py'):
    m = re.match(r"\s*\('(Q-[^']+)', '(P-[^']+)'", line)
    if m: M[m.group(1)] = m.group(2)
M.update({f'Q-KP-C1-{n:03d}': 'W-KP' for n in range(7, 13)}); M.update({f'Q-SO-P1-{n:03d}': 'W-SO' for n in range(3, 8)})
M.update({'Q-YK-C1-004': 'W-YK', 'Q-ST-D1-001': 'P2-ST-02', 'Q-SK-C1-001': 'P2-SK-01', 'Q-SH-C1-001': 'P2-SH-01', 'Q-GY-Q1-007': 'P2-GY-02', 'Q-JH-A1-005': 'P2-JH-01'})
T = list(csv.DictReader(open('results/citations/citations.tsv'), delimiter='\t'))
items, cmap = {}, {}
for t in T:
    rnd = re.match(r'R0\d\d', t['型の判定']).group(0); rnd = rnd if rnd in DIR else None
    # R070 で上書きされた判定欄から元の回を引けないので、R070 の KEY から組の名前を取る
for t in T:
    pass
R070 = json.load(open('results/citations/R070.json'))['items']
for cid, v in R070.items():
    rnd, k = v['pair'].split(':', 1)
    items[v['pair']] = B[rnd][k]; cmap.setdefault(v['pair'], []).append(cid)
C630 = open('replications/R071_perpair/cite_630.txt').read().strip()   # 神奈川県弁護士会 シンポジウム資料 PDF の該当段落（pdftotext）
items['R029:Q-630-D1-001'] = ("- 引用の掲載時期：2026-02-26\n- 元の資料の文：\n"
  "［1］精神保健福祉資料（630調査）長期データ（longterm_1998_2025.xlsx）シート「在院患者数」合計：1998年 335,847、2024年 250,525（1998〜2025年で 1998年が最多）。\n"
  "［2］同じシートの都道府県の値から計算した 2024年／1998年（指定都市の再掲を除き、低い順）：福島 51.3％、和歌山 53.9％、愛媛 57.1％、徳島 64.7％、岩手 65.1％、島根 65.8％、京都 66.8％、長野 70.0％、東京 70.2％。高い順：宮城 96.8％、山形 96.0％、神奈川 89.5％、奈良 87.6％、群馬 82.9％。\n"
  "［3］630調査の回答率：埼玉 2024年 74.2％（在院患者数 8,635人）、長野 2018年 63.3％、福井 2023年 73.3％。長期データの表には回答率の列も注もない。\n"
  f"- 引用の文：{re.sub(r'\s+', '', C630)}\n\n")
items['R029:Q-ST-I2-003'] = items['R029:Q-ST-I2-003'].replace("- 元の資料の文：", "- 元の資料の文：［1］令和6年版・令和7年版の表（警察庁）：ストーカー規制法違反の検挙 令和5年 1,081件、令和6年 1,341件。［2］", 1)
items['R030:P-GY-01'] = items['R030:P-GY-01'].replace("（確定値、2024年9月公表）", "（確定値、2024年9月公表）／福祉行政報告例（確定値）の児童虐待相談の対応件数：平成26年度 88,931、27年度 103,286、28年度 122,575、29年度 133,778、30年度 159,838、令和元年度 193,780、2年度 205,044、3年度 207,660、4年度 214,843（毎年度増加）。", 1)
_g = open('replications/R073_context/GY-Q1-004_body.txt').read().replace('\n', ' ')
_x = items['R030:P-GY-02']; _i = _x.index('- 引用の文：'); _j = _x.index('\n', _i)
items['R030:P-GY-02'] = _x[:_i] + '- 引用の文：' + _g + _x[_j:]
_s = re.sub(r'\s+', '', open('replications/R073_context/SO-P1-002_footnote83.txt').read())
_x = items['R029:Q-SO-P1-002']; _i = _x.index('- 引用の文：'); _j = _x.index('\n', _i)
items['R029:Q-SO-P1-002'] = _x[:_i] + '- 引用の文：（注83の全文）' + _s + _x[_j:]
assert '207,660' in items['R030:P-GY-01'] and '1,341件' in items['R029:Q-ST-I2-003'] and '児童虐待相談の対応件数を修正' in items['R030:P-GY-02'] and '性犯罪の再犯率は' in items['R029:Q-SO-P1-002']
for _u, _f in (('R030:P-JH-04', 'JH-A1-004_body.txt'), ('R031:P-NK-01', 'NK-K1-002_body.txt')):
    _x = items[_u]; _i = _x.index('- 引用の文：'); _j = _x.index('\n', _i)
    items[_u] = _x[:_i] + '- 引用の文：' + open(f'replications/R073_context/{_f}').read() + _x[_j:]
items['R029:Q-KP-C1-005'] = items['R029:Q-KP-C1-005'].replace('- 元の資料の文：', '- 元の資料の文：［対象の定義（分析結果について 001317461.pdf 1頁）］指導を受講することが必要とされた者 1,980 名。うち，受講群は 1,444 名，比較対照群は 324 名。なお，両群の同質性確保のため，同指導を受講していないが，比較対照群としては不適当な者 212 名を除外している。［数値］', 1)
assert '統計のある1980' in items['R030:P-JH-04'] and 'HDS-R' in items['R031:P-NK-01'] and '212 名' in items['R029:Q-KP-C1-005']
_keep = ('R030:P-JH-04', 'R031:P-NK-01', 'R029:Q-KP-C1-005')
cmap = {u: v for u, v in cmap.items() if u in _keep}
items = {u: items[u] for u in _keep}
CTRL = {'CTRL-T1': (B['R029']['CTRL-T1'], {'T1'}), 'CTRL-T0': (B['R029']['CTRL-T0'], {'T0'})}
head = open('replications/R067_rejudge/PROMPT.md').read().split('## 組\n', 1)[0]
A = 'T0 は他の型と同時に付けない。'
assert A in head
head = head.replace(A, '比べる相手は元の資料の文の言い方とする。元の資料の文が、自分の示す数字より強く言っている場合（群の比較を「抑えられた」と書く、など）、それを同じ強さで引いた側は型に数えない。\n' + A)
head = head.replace(A, '引用は、見出しなら本文と合わせて、文なら同じ段落・同じ注の前後と合わせて読む。その範囲で名前や限定が示されていれば、見出しや一文で縮めていても落ちたとはしない。\n' + A)
B = 'JSON だけを出力：{"C01": {"型": ["T4"], "理由": "…"}'
assert B in head
head = head.replace(B, 'JSON だけを出力：{"C01": {"型": ["T4"], "理由": "…", "根拠": "判定が拠った定義の文（そのまま写す）"}')
def call(job):
    u, name, n = job
    ids = [u, 'CTRL-T1', 'CTRL-T0']; random.Random(f'R073b-{u}-{name}-{n}').shuffle(ids)
    key = {f'C{i + 1:02d}': x for i, x in enumerate(ids)}
    P = head + '## 組\n' + ''.join(f'### {k}\n{items[x] if x == u else CTRL[x][0]}' for k, x in key.items())
    try: t = (llm.gpt if name == 'gpt' else llm.gemini)(P)
    except Exception as ex: t = f'ERROR {type(ex).__name__}'
    j = llm.js(t) or {}; r = {key[k]: (v or {}).get('型', []) for k, v in j.items() if k in key}; basis = (j.get([k for k, x in key.items() if x == u][0]) or {}).get('根拠', '')
    ok = all(set(r.get(c, [])) == e for c, (_, e) in CTRL.items())
    return dict(pair=u, judge=name, n=n, ok=ok, types=r.get(u, []), basis=basis, raw=t, prompt=P)
jobs = [(u, nm, n) for u in items for nm in ('gpt', 'gemini') for n in range(5)]
res = []
with cf.ThreadPoolExecutor(6) as ex, open(f'{OUT}/calls.jsonl', 'w') as w:
    for x in ex.map(call, jobs):
        res.append(x); w.write(json.dumps(x, ensure_ascii=False) + '\n'); w.flush()
        print(x['pair'], x['judge'], x['n'], x['ok'], x['types'], flush=True)
out = dict(round='R073b', date=datetime.date.today().isoformat(), items={}, control_ok=sum(x['ok'] for x in res), calls=len(res))
def maj(L):   # 対照に正答した呼び出しの過半で付いた型
    if not L: return None
    n = len(L); ts = [set(t for t in x if t.startswith('T')) for x in L]
    if sum(1 for x in L if not any(t.startswith('T') for t in x)) * 2 > n: return frozenset(['判定不能'])
    allt = set().union(*ts)
    return frozenset(t for t in allt if sum(t in x for x in ts) * 2 > n)
amb = []
for u, cids in cmap.items():
    use = {nm: [x['types'] for x in res if x['pair'] == u and x['judge'] == nm and x['ok']] for nm in ('gpt', 'gemini')}
    m = {nm: maj(v) for nm, v in use.items()}
    if None in m.values() or any(len(v) < 3 for v in use.values()): final, how = ['判定が分かれた'], '対照に正答した呼び出しが足りない'
    elif m['gpt'] == m['gemini'] and m['gpt']: final, how = sorted(m['gpt']), '二つの判定者の過半の型が同じ'
    elif (m['gpt'] & m['gemini']) - {'判定不能'}: final, how = sorted((m['gpt'] & m['gemini']) - {'判定不能'}), '二つの判定者の過半の型に共通する型'
    else: final, how = ['判定が分かれた'], '共通する型がない'
    if final == ['判定が分かれた']: amb.append(dict(pair=u, cites=cids, gpt=sorted(m['gpt'] or []), gemini=sorted(m['gemini'] or [])))
    for c in cids:
        out['items'][c] = dict(pair=u, gpt=use['gpt'], gemini=use['gemini'], gpt_major=sorted(m['gpt'] or []), gemini_major=sorted(m['gemini'] or []), final=final, how=how)
json.dump(out, open('results/citations/R073b.json', 'w'), ensure_ascii=False, indent=1)
json.dump(amb, open('results/citations/R073b_split.json', 'w'), ensure_ascii=False, indent=1)
print('呼び出し', len(res), '対照正答', out['control_ok'], '判定が分かれた', len(amb))
