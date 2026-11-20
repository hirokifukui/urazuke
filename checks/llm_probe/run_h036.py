# H036：8記録について AI の答えを集める（検索なし A、検索あり A'、原文を渡す B）。モデルごとに並行。途中から再開できる。
# 使い方：python3 checks/llm_probe/run_h036.py 2026-11-18   （回の日付。結果は results/llm_probe/h036/<日付>/answers.jsonl）
import os, sys, json, datetime, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h036_spec as S
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run_probe.py')).read()
ns = {}; exec(src[:src.index('MODELS = [')], ns)  # キーの読み込みと ask() だけを使う
ask = ns['ask']
RUN = sys.argv[1]; D = f'results/llm_probe/h036/{RUN}'; os.makedirs(D, exist_ok=True); OUT = f'{D}/answers.jsonl'
P = S.prompts(); json.dump(P, open(f'{D}/PROMPTS.json', 'w'), ensure_ascii=False, indent=1)
done = {(j['model'], j['key'], j['rep']) for j in map(json.loads, open(OUT)) if j['answer']} if os.path.exists(OUT) else set()
lock = threading.Lock()
def worker(model, keys):
    for k in keys:
        for r in range(1, S.REPS + 1):
            if (model, k, r) in done: continue
            try: a = ask(model, P[k]); err = ''
            except Exception as ex: a = ''; err = f'{type(ex).__name__}: {str(ex)[:150]}'
            rec = dict(run=RUN, model=model, key=k, rep=r, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'), answer=a, error=err)
            with lock:
                open(OUT, 'a').write(json.dumps(rec, ensure_ascii=False) + '\n')
                print(model, k, r, len(a), err[:50], flush=True)
NW = {'grok-4.7': 6, 'o3': 3, 'claude-opus-5-5': 3, 'claude-sonnet-4-5-20250929': 3, 'gpt-6.2-sol': 3, 'gemini-3.8-flash': 3}
T = []
for m in S.MODELS:
    ks = list(P); n = NW.get(m, 2)
    T += [threading.Thread(target=worker, args=(m, ks[i::n])) for i in range(n)]
T.append(threading.Thread(target=worker, args=(S.SEARCH_MODEL, [k for k in P if '|A' in k])))
for t in T: t.start()
for t in T: t.join()
print('done')
