"""照らし直しで支持された「記録のない資料」の候補を、報告書の広い範囲で照らし直す（2026-11-21）。
答弁の数と語（漢字2字以上）を含む行の前後30行を、全体版の原文から最大6万字まで抜き出して渡す。出力：classified3.jsonl（refute.py に渡せる形）。
python3 kokkai/fullcheck.py <日付>"""
import glob, json, os, re, sys, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import llm, kansuji, series_check as SC
D = SC.D
def wide(text, nums, words, cap=60000, w=20):
    """語（答弁の言い回しを資料の書き方に寄せたもの）と数の両方を含む行を先に、次に語だけ、最後に数だけの行。各行の前後 w 行。上限で切られて大事な行が落ちないように順に詰める。"""
    L = text.splitlines(); forms = kansuji.forms(nums)
    def score(l): return (2 if any(f in l for f in forms) else 0) + sum(x in l for x in words)
    hits = sorted([i for i, l in enumerate(L) if score(L[i]) >= 2], key=lambda i: -score(L[i]))
    keep, size = set(), 0
    for i in hits:
        add = [k for k in range(max(0, i - w), min(len(L), i + w)) if k not in keep]
        size += sum(len(L[k]) + 1 for k in add)
        if size > cap: break
        keep |= set(add)
    return '\n'.join(L[k] for k in sorted(keep))
def run(r):
    n = int(re.search(r'第(\d+)次', r['source']['name']).group(1))
    t = SC.shibo_text(n)
    words = sorted({x for x in re.findall(r'[一-龥０-９]{2,}', kansuji.terms(r['claude']['speech_quote'])) if x not in ('報告', '資料', '答弁')})[:12]
    s = dict(name=r['source']['name'], text=wide(t, kansuji.numbers(r['passage']), words), nums=r['source']['nums'])
    p = SC.prompt(r, s).replace('（抜粋は、答弁に出てくる数を含む行とその前後を機械で切り出したもの。', '（抜粋は、答弁に出てくる数や語を含む行の前後30行を報告書の全体から機械で切り出したもの。')
    def once():
        try: j = llm.js(llm.claude(p, max_tokens=2500)) or {}
        except Exception as ex: j = {'type': 'エラー', 'explanation': type(ex).__name__}
        j['speech_quote_ok'] = bool(j.get('speech_quote')) and SC.norm(j['speech_quote']) in SC.norm(r['passage'])
        j['source_quote_ok'] = bool(j.get('source_quote')) and SC.norm(j['source_quote']) in SC.norm(s['text'])
        j['record_ids'] = []
        return j
    j = SC.vote(once)
    return {**{k: v for k, v in r.items() if k not in ('gpt',)}, 'source': s, 'claude': j}
if __name__ == '__main__':
    R = [json.loads(l) for l in open(os.path.join(D, 'refuted2.jsonl'), encoding='utf-8') if json.loads(l)['gpt']['result'] == '別系統で支持']
    with cf.ThreadPoolExecutor(3) as ex, open(os.path.join(D, 'classified3.jsonl'), 'w', encoding='utf-8') as w:
        for x in ex.map(run, R):
            w.write(json.dumps(x, ensure_ascii=False) + '\n'); print(x['date'], x['source']['name'][-7:], len(x['source']['text']), x['claude'].get('type'), x['claude'].get('speech_quote_ok'), x['claude'].get('source_quote_ok'), '|', x['claude'].get('explanation', '')[:200], flush=True)
