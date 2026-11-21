"""国会の発言から、記録の資料に触れた箇所を切り出し、関係する記録と組にする（2026-11-21）。
入力：results/kokkai/<日付>/speeches.jsonl、kokkai/queries.tsv、publish/findings.json。出力：candidates.jsonl。政府側の発言だけ（質問の側は次の段で）。"""
import csv, json, os, re, sys, fnmatch
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
day = sys.argv[1]; D = os.path.join(ROOT, 'results/kokkai', day)
Q = {q['qid']: q for q in csv.DictReader(open(os.path.join(ROOT, 'kokkai/queries.tsv'), encoding='utf-8'), delimiter='\t')}
F = {f['id']: f for f in json.load(open(os.path.join(ROOT, 'publish/findings.json'), encoding='utf-8'))}
GOV = ('政府参考人', '国務大臣', '副大臣', '大臣政務官', '政務官', '内閣総理大臣')
def recs(qids):
    out = []
    for q in qids:
        for pat in Q[q]['records'].split(','):
            out += [i for i in F if fnmatch.fnmatch(i, pat.strip())]
    return sorted(set(out))
n = 0
with open(os.path.join(D, 'candidates.jsonl'), 'w', encoding='utf-8') as w:
    for l in open(os.path.join(D, 'speeches.jsonl'), encoding='utf-8'):
        r = json.loads(l); head = r['speech'][:30]
        if not any(g in head for g in GOV): continue
        S = [s for s in re.split(r'(?<=。)', r['speech']) if s.strip()]
        kws = {k for q in r['_q'] for k in Q[q]['query'].split()}
        idx = [i for i, s in enumerate(S) if sum(k in s for k in kws) >= 1 and re.search(r'[〇一二三四五六七八九十]|効果|認め|示唆|確認', s)]
        if not idx: continue
        keep = sorted({j for i in idx for j in range(max(0, i - 2), min(len(S), i + 3))})
        passage = ''.join(S[j] for j in keep)[:2500]
        R = recs(r['_q'])
        if not R: continue
        w.write(json.dumps(dict(speechID=r['speechID'], date=r['date'], house=r['nameOfHouse'], meeting=r['nameOfMeeting'], speaker=r['speaker'], position=r.get('speakerPosition', ''),
                                url=r['speechURL'], qids=r['_q'], records=R, passage=passage), ensure_ascii=False) + '\n'); n += 1
print('candidates', n)
