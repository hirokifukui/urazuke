"""R071（2026-11-21）：R070 で「判定が分かれた」が残った原因への対処（運営者の問い）。
(1) R070 までは 40組を一つの課題文にまとめて渡していたため、一回の判定のぶれが多くの組に同時に及んだ（Gemini の2回目だけが NK-K1 の4件そろって T4）。
    組ごとに別々に渡す（各呼び出しに、対象の組1つと型の明らかな対照2組を、順序を乱して入れる）。対照の2組に正答した呼び出しだけを使う。
(2) 630-D1-001 は、元の資料の文に照合できる値がなく（記録の説明文を渡していた）、引用の文も途中で切れていた。長期データの値（全国の合計、都道府県別の 2024年／1998年、回答率）と、
    引用の段落の全文を渡す。都道府県別の比は長期データの値からの計算と明記する。
各組を各判定者に3回。使える呼び出しが各判定者で2回以上あれば採り、使える全ての呼び出しに共通する型を表示する（なければ「判定が分かれた」）。定義は R067〜R070 と同じ。"""
import json, os, random, re, sys, csv, datetime, concurrent.futures as cf
sys.path.insert(0, 'kokkai'); import llm
OUT = 'replications/R071_perpair'; os.makedirs(OUT, exist_ok=True)
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
C630 = open(f'{OUT}/cite_630.txt').read().strip()   # 神奈川県弁護士会 シンポジウム資料 PDF の該当段落（pdftotext）
items['R029:Q-630-D1-001'] = ("- 引用の掲載時期：2026-02-26\n- 元の資料の文：\n"
  "［1］精神保健福祉資料（630調査）長期データ（longterm_1998_2025.xlsx）シート「在院患者数」合計：1998年 335,847、2024年 250,525（1998〜2025年で 1998年が最多）。\n"
  "［2］同じシートの都道府県の値から計算した 2024年／1998年（指定都市の再掲を除き、低い順）：福島 51.3％、和歌山 53.9％、愛媛 57.1％、徳島 64.7％、岩手 65.1％、島根 65.8％、京都 66.8％、長野 70.0％、東京 70.2％。高い順：宮城 96.8％、山形 96.0％、神奈川 89.5％、奈良 87.6％、群馬 82.9％。\n"
  "［3］630調査の回答率：埼玉 2024年 74.2％（在院患者数 8,635人）、長野 2018年 63.3％、福井 2023年 73.3％。長期データの表には回答率の列も注もない。\n"
  f"- 引用の文：{re.sub(r'\s+', '', C630)}\n\n")
CTRL = {'CTRL-T1': (B['R029']['CTRL-T1'], {'T1'}), 'CTRL-T0': (B['R029']['CTRL-T0'], {'T0'})}
head = open('replications/R067_rejudge/PROMPT.md').read().split('## 組\n', 1)[0]
def call(job):
    u, name, n = job
    ids = [u, 'CTRL-T1', 'CTRL-T0']; random.Random(f'{u}-{name}-{n}').shuffle(ids)
    key = {f'C{i + 1:02d}': x for i, x in enumerate(ids)}
    P = head + '## 組\n' + ''.join(f'### {k}\n{items[x] if x == u else CTRL[x][0]}' for k, x in key.items())
    try: t = (llm.gpt if name == 'gpt' else llm.gemini)(P)
    except Exception as ex: t = f'ERROR {type(ex).__name__}'
    j = llm.js(t) or {}; r = {key[k]: (v or {}).get('型', []) for k, v in j.items() if k in key}
    ok = all(set(r.get(c, [])) == e for c, (_, e) in CTRL.items())
    return dict(pair=u, judge=name, n=n, ok=ok, types=r.get(u, []), raw=t, prompt=P)
jobs = [(u, nm, n) for u in items for nm in ('gpt', 'gemini') for n in range(3)]
res = []
with cf.ThreadPoolExecutor(6) as ex, open(f'{OUT}/calls.jsonl', 'w') as w:
    for x in ex.map(call, jobs):
        res.append(x); w.write(json.dumps(x, ensure_ascii=False) + '\n'); w.flush()
        print(x['pair'], x['judge'], x['n'], x['ok'], x['types'], flush=True)
out = dict(round='R071', date=datetime.date.today().isoformat(), items={}, control_ok=sum(x['ok'] for x in res), calls=len(res))
for u, cids in cmap.items():
    use = {nm: [x['types'] for x in res if x['pair'] == u and x['judge'] == nm and x['ok']] for nm in ('gpt', 'gemini')}
    adopt = all(len(v) >= 2 for v in use.values())
    per = [set(t for t in L if t.startswith('T')) for v in use.values() for L in v]
    com = sorted(set.intersection(*per)) if per and adopt else []
    for c in cids:
        out['items'][c] = dict(pair=u, adopted=adopt, gpt=use['gpt'], gemini=use['gemini'], common=com, unanimous=adopt and len(set(map(frozenset, per))) == 1)
json.dump(out, open('results/citations/R071.json', 'w'), ensure_ascii=False, indent=1)
print('呼び出し', len(res), '対照正答', out['control_ok'], '採れた組', sum(v['adopted'] for v in out['items'].values()), '全回一致', sum(v['unanimous'] for v in out['items'].values()))
