# H037 を引かれ方に当てる：二つの判定者の型の集合が一致すればその型、違えば「判定が分かれた」。citations.tsv の 型・型の判定 を書き換える。
import csv, json, re
AG = json.load(open('results/judge2/agreement.json'))
P2Q = {'P-GY-01': 'Q-GY-Q1-003', 'P-GY-02': 'Q-GY-Q1-004', 'P-GY-03': 'Q-GY-Q1-005', 'P-GY-04': 'Q-GY-Q1-006', 'P-JH-02': 'Q-JH-A1-003', 'P-JH-04': 'Q-JH-A1-004',
       'P-ST-04': 'Q-ST-I2-005', 'P-ST-05': 'Q-ST-I2-006', 'P-NK-01': 'Q-NK-K1-002', 'P-NK-02': 'Q-NK-K1-003', 'P-NK-03': 'Q-NK-K1-004'}
SRC = {}  # 引用 ID → (回, GPT, Gemini, Gemini の作例が正答か)
for rn, short in (('R029_gpt_types', 'R029'), ('R030_gpt_types', 'R030'), ('R031_gpt_types', 'R031')):
    a = AG[rn]
    for q, v in a['items'].items():
        qid = P2Q.get(q, q)
        if short == 'R030' and qid.startswith('Q-NK'): continue      # R030 の NK は採らず R031 で置き換えた
        if short == 'R029' and qid == 'Q-NK-K1-001': continue         # R031 で置き換えた
        SRC[qid] = (short, v['gpt'], v['gemini'], a['ctrl_ok'])
p = 'results/citations/citations.tsv'; rows = list(csv.reader(open(p), delimiter='\t')); h = rows[0]; ix = {k: i for i, k in enumerate(h)}
J = lambda s: '、'.join(s) if s else '—'
n_split = 0
for r in rows[1:]:
    rn, g, m, ok = SRC[r[0]]
    if not ok:
        r[ix['型']] = J(g); r[ix['型の判定']] = f'{rn}（GPT：{J(g)}。Gemini の回は作例が正答でなく採らない）'; continue
    if set(g) == set(m): r[ix['型']] = J(g); r[ix['型の判定']] = f'{rn}（GPT・Gemini とも {J(g)}）'
    else: r[ix['型']] = '判定が分かれた'; r[ix['型の判定']] = f'{rn}（GPT：{J(g)}／Gemini：{J(m)}）'; n_split += 1
csv.writer(open(p, 'w', newline=''), delimiter='\t', lineterminator='\n').writerows(rows)
print('split', n_split, 'of', len(rows) - 1)
