"""R074（2026-11-22）：記録 HR-Q1（法総研 研究部報告55の 84.6％）の引用 6件を、R073 と同じ定義・手順（組ごと、GPT・Gemini 各5回の過半、対照2組、根拠つき）で判定する。
以下は R073 の説明。
R073（2026-11-21、実行前に固定）：「判定が分かれた」は原因を AI の外に特定するまで解消する（運営者の決定）。R072 で残った2組を調べると、どちらも引いた文の前後を渡していなかった（GY-Q1-004 は見出しだけで、本文は「児童虐待相談の対応件数」と書く。SO-P1-002 は注の後半だけで、同じ注の前半が「性犯罪の再犯率は」と書く）。
定義に、何を一つの引用として読むかを足す：見出しは本文と合わせて読む。引いた文は、同じ段落・同じ注の前後と合わせて読む。定義が変わるので全件をやり直す。
出力に「根拠」（判定が拠った定義の文）を足し、割れたときに定義の穴か材料の不足かを見分けられるようにする。R072b の材料の足し（ST-I2-003・GY-Q1-003）も入れる。手順（組ごと、5回×2者の過半）は R072 と同じ。
以下は R072 の説明。
R072（2026-11-21、実行前に固定）：R071 の結果から二つを改める。
(a) 定義に基準点の一文を足す：比べる相手は元の資料の文の言い方。元の資料の文が自分の数字より強く言っている場合、それを引いた側は型に数えない（資料の側の論点として別に記録する）。
(b) 組ごとに別々に渡すと呼び出しは互いに独立になり、境目の組では1回の外れが出やすい（R071：全回一致 28/49）。6回全一致の規則は、独立な呼び出しでは外れ1回で決まってしまう。
    各判定者に5回ずつ渡し、対照に正答した呼び出しの過半で付いた型を、その判定者の型とする（過半が判定不能なら判定不能）。二つの判定者の型が同じならそれを、違えば共通する型を、共通がなければ「判定が分かれた」とする。
(c) それでも「判定が分かれた」になる組は、元の資料の文が一つに読めない書き方になっている候補として results/citations/R074_split.json に出す（意図は問わない）。
以下は R071 の説明。
R071（2026-11-21）：R070 で「判定が分かれた」が残った原因への対処（運営者の問い）。
(1) R070 までは 40組を一つの課題文にまとめて渡していたため、一回の判定のぶれが多くの組に同時に及んだ（Gemini の2回目だけが NK-K1 の4件そろって T4）。
    組ごとに別々に渡す（各呼び出しに、対象の組1つと型の明らかな対照2組を、順序を乱して入れる）。対照の2組に正答した呼び出しだけを使う。
(2) 630-D1-001 は、元の資料の文に照合できる値がなく（記録の説明文を渡していた）、引用の文も途中で切れていた。長期データの値（全国の合計、都道府県別の 2024年／1998年、回答率）と、
    引用の段落の全文を渡す。都道府県別の比は長期データの値からの計算と明記する。
各組を各判定者に3回。使える呼び出しが各判定者で2回以上あれば採り、使える全ての呼び出しに共通する型を表示する（なければ「判定が分かれた」）。定義は R067〜R070 と同じ。"""
import json, os, random, re, sys, csv, datetime, concurrent.futures as cf
sys.path.insert(0, 'kokkai'); import llm
OUT = 'replications/R074_hrq1'; os.makedirs(OUT, exist_ok=True)
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
_g = open(f'replications/R073_context/GY-Q1-004_body.txt').read().replace('\n', ' ')
_x = items['R030:P-GY-02']; _i = _x.index('- 引用の文：'); _j = _x.index('\n', _i)
items['R030:P-GY-02'] = _x[:_i] + '- 引用の文：' + _g + _x[_j:]
_s = re.sub(r'\s+', '', open(f'replications/R073_context/SO-P1-002_footnote83.txt').read())
_x = items['R029:Q-SO-P1-002']; _i = _x.index('- 引用の文：'); _j = _x.index('\n', _i)
items['R029:Q-SO-P1-002'] = _x[:_i] + '- 引用の文：（注83の全文）' + _s + _x[_j:]
assert '207,660' in items['R030:P-GY-01'] and '1,341件' in items['R029:Q-ST-I2-003'] and '児童虐待相談の対応件数を修正' in items['R030:P-GY-02'] and '性犯罪の再犯率は' in items['R029:Q-SO-P1-002']
SRC74 = '［1］研究部報告55 4-5-10図の本文（PDF 61頁）：「性犯罪前科２回以上の者について，調査対象事件中の性犯罪と同一の類型の性犯罪前科（以下この節において「同型性犯罪前科」という。）の有無別構成比を類型別に見ると，4‑5‑10図のとおりである。同型性犯罪前科のある者の割合は，調査対象事件中の性犯罪により強制わいせつ（その他）型と類型化された者で，44.0％と最も低く，次いで，単独強姦型で63.2％，小児わいせつ型で84.6％の順であった。」4-5-10図「性犯罪前科 2 回以上の者 同型性犯罪前科の有無別構成比（類型別）」：小児わいせつ型（13）同型性犯罪前科あり 84.6・なし 15.4。図の注：性犯罪前科２回以上の者に限る。\n［2］同 4-4-3図「再犯調査対象者 再犯率（性犯罪者類型別）」（PDF 37頁）：図の注「調査対象事件の裁判確定から 5 年経過時点における再犯の有無を示す」。小児わいせつ型（136）性犯罪再犯（刑法犯）あり 6.6・性犯罪再犯（条例違反）あり 2.9・その他再犯あり 6.6・再犯なし 83.8。'
NEW74 = {'R074:Q-HR-Q1-001': ('2023-06', '質問主意書の一の段落：再犯防止で着目すべきは、性犯罪行為の「病気や障害」としての側面に着目したアプローチである。依存症等の専門家によると、盗撮は「性依存症」、子どもへの性的関心は「小児性愛障害」との診断が付くケースがあるとのことである。病因だけに再犯率が異常に高く、子どもへの性犯罪前科二回以上の者の再犯率は八十四・六％に上るとの調査結果もある。病理的な原因に着目すると、再発防止の鍵として、専門治療や療法という対応策が前面に出てくる。 もちろん、病気や障害としての側面に着目しすぎることで、本人の行為責任を隠蔽することは避けなければならないが、現在は再犯対策を策定するに当たり、性犯罪行為の「病気や障害としての側面」からのアプローチが手薄すぎるのではないか。この視点について政府の認識を示されたい。'), 'R074:Q-HR-Q1-002': ('2021-01', '本文：まず問題を整理しておきたいと思います。性暴力の被害は、実は「面識のある人」から受けることが多く（6～7割程度）、通り魔的な犯行はごくわずか（1割程度）だということが分かっています。加害者は、教師・医師・スポーツコーチなどの優位な立場、「対等ではない関係性」を悪用しているのです。 また、小児性わいせつは、再犯率と常習性が非常に高いことが分かっています。再犯率はなんと84.6％にも上り、他の性犯罪と比較して突出して高い数値となっています。'), 'R074:Q-HR-Q1-003': ('2019-07', '本文：日本国内に目を向けてみると、法務省が公表した「平成27年版犯罪白書」によると、13歳未満の子どもに対する強制わいせつ事件は、1年間で953件発生しており、実に1日に2件以上起きている計算だという。また、一度子どもに手を出した犯罪者の再犯率は、84.6％と極めて高いことも分かった。'), 'R074:Q-HR-Q1-004': ('2018-07', '小見出し：再犯率84.6％ ／ 同じ小見出しの下の本文（抜粋）：それを裏付けるように、法務省の法務総合研究所の調査によると、裁判確定から5年経過時点での再犯の有無を示す再犯率は、低年齢の子供を狙った小児わいせつ型の再犯調査対象者で「性犯罪再犯あり」が9･5％、「その他再犯あり」は6･6％だった。ただ、性犯罪前科が2回以上ある人を類型別でみると、小児わいせつ型は84･6％に上り、痴漢を除く強制わいせつ型（44･0％）や単独強姦型（63･2％）と比べても同一類型の小児わいせつ型性犯罪を繰り返す傾向がうかがえた。'), 'R074:Q-HR-Q1-005': ('2018-12', '掲載時の文（媒体の訂正の注記にある修正前の文）：「法務総合研究所の調査によれば、性犯罪前科が2回以上ある小児わいせつ型の人の再犯率は84.6％にも上る」。同じ段落の前の文：「被害者をケアするのはもちろんですが、同時に加害者の犯行を防ぐことにも取り組まないといけない。とくに小児性犯罪の再犯率は、他の性犯罪の刑法犯と比較すると上位に位置します。こうしたデータだけでなく、実際に私が勤めるクリニックを受診する小児性犯罪者の人たちは繰り返し加害を行ってしまう人が多いのが現実です。これから出てしまうかもしれない被害者を減らすためには、一人の加害者の性加害を止めることが必要なんです」'), 'R074:Q-HR-Q1-006': ('2023-07', '議事録の段落：次に、それとは別に84.6％といった数字が取り上げられることがあるところ、それはど のような数字かということにつきまして、前回口頭で御説明いたしましたけれども、こち らの図で言いますと左半分で御紹介しているところでございます。これは小児わいせつ型 の性犯罪で有罪確定した者のうち、それ以前に２回以上の性犯罪前科を有している者を 調 査対象全体の中から取り上げまして、これは13人でございましたけれども、それらの者に 1 ついて見た場合、その前科も同じく小児わいせつ型であった者が 11人で84.6％、それ以外 の性犯罪の類型だった者が２人だったという数字でございます。こちらは 先ほど説明した 再犯率ということではございませんけれども、小児わいせつ型の性犯罪に及んだ者の中に 、 複数回の刑事処分を受けているにもかかわらず、同じく小児 わいせつ型の性犯罪を繰り返 す者が一定数存在するということが認められるかと思われます。')}
items = {u: f'- 引用の掲載時期：{d}\n- 元の資料の文：\n{SRC74}\n- 引用の文：{c}\n\n' for u, (d, c) in NEW74.items()}
cmap = {u: [u.split(':')[1]] for u in NEW74}
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
    ids = [u, 'CTRL-T1', 'CTRL-T0']; random.Random(f'R074-{u}-{name}-{n}').shuffle(ids)
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
out = dict(round='R074', date=datetime.date.today().isoformat(), items={}, control_ok=sum(x['ok'] for x in res), calls=len(res))
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
json.dump(out, open('results/citations/R074.json', 'w'), ensure_ascii=False, indent=1)
json.dump(amb, open('results/citations/R074_split.json', 'w'), ensure_ascii=False, indent=1)
print('呼び出し', len(res), '対照正答', out['control_ok'], '判定が分かれた', len(amb))
