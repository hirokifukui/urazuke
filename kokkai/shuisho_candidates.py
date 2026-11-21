"""質問主意書・答弁書から、記録の資料に触れた箇所を切り出す（2026-11-21）。答弁書（閣議決定）と、質問の側（議員の質問主意書）の両方。
入力：data/raw/kokkai_src/shuisho/。出力：results/kokkai/<日付>/candidates_shuisho.jsonl（classify.py に渡せる形）。python3 kokkai/shuisho_candidates.py <日付>"""
import csv, fnmatch, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import kansuji
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); day = sys.argv[1]; D = os.path.join(ROOT, 'results/kokkai', day); os.makedirs(D, exist_ok=True)
S = os.path.join(ROOT, 'data/raw/kokkai_src/shuisho')
Q = list(csv.DictReader(open(os.path.join(ROOT, 'kokkai/queries.tsv'), encoding='utf-8'), delimiter='\t'))
F = [f['id'] for f in json.load(open(os.path.join(ROOT, 'publish/findings.json'), encoding='utf-8'))]
ERA = {'平成': 1988, '令和': 2018}
def date_of(t):
    m = re.search(r'(平成|令和)([元〇一二三四五六七八九十]+)年([〇一二三四五六七八九十]+)月([〇一二三四五六七八九十]+)日', t)
    if not m: return ''
    y = 1 if m.group(2) == '元' else kansuji._pos(m.group(2))
    return f'{ERA[m.group(1)] + y:04d}-{kansuji._pos(m.group(3)):02d}-{kansuji._pos(m.group(4)):02d}'
n = 0
with open(os.path.join(D, 'candidates_shuisho.jsonl'), 'w', encoding='utf-8') as w:
    for row in csv.reader(open(os.path.join(S, 'index.tsv'), encoding='utf-8'), delimiter='\t'):
        house, ses, num, title, who, qu, au = (row + [''] * 7)[:7]
        for side, url in (('a', au), ('q', qu)):
            p = os.path.join(S, house, ses, f'{int(num):03d}_{side}.txt')
            if not url or not os.path.exists(p): continue
            t = open(p, encoding='utf-8').read()
            qids = [q['qid'] for q in Q if all(k in t for k in q['query'].split())]
            if not qids: continue
            kws = {k for q in Q if q['qid'] in qids for k in q['query'].split()}
            sents = [s for s in re.split(r'(?<=。)', t.replace('\n', '')) if s.strip()]
            idx = [i for i, s in enumerate(sents) if any(k in s for k in kws)]
            keep = sorted({j for i in idx for j in range(max(0, i - 2), min(len(sents), i + 3))})
            recs = sorted({r for q in Q if q['qid'] in qids for pat in q['records'].split(',') for r in F if fnmatch.fnmatch(r, pat.strip())})
            if not recs: continue
            hn = '衆議院' if house == 'shu' else '参議院'
            w.write(json.dumps(dict(speechID=f'{house}-{ses}-{num}-{side}', date=date_of(t) or '', house=hn, meeting=f'質問主意書 第{ses}回国会 第{num}号「{title}」',
                                    speaker='内閣（答弁書）' if side == 'a' else who, position='閣議決定' if side == 'a' else '質問主意書の提出者', side=side,
                                    url=url, qids=qids, records=recs, passage=''.join(sents[j] for j in keep)[:2500]), ensure_ascii=False) + '\n'); n += 1
print('candidates', n)
