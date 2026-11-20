"""平易版の反証の回を採点する（2026-11-19、r43）。
python3 publish/plain/score.py R049 ...
~/mitodoke_blind/<R>/REPORT.md から問ごとの判定を読み、replications/<R>_gpt_refute/ に REPORT.md・SCORING.md を置く。
対照（偽）が2件とも「反証」のときだけ本題の判定を採る。結果は publish/plain/STATUS.json に書く（id → 回・問・判定・採否）。"""
import json, os, re, sys, shutil, hashlib
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(ROOT)
BL = os.path.expanduser('~/mitodoke_blind'); ST = 'publish/plain/STATUS.json'
V = ('支持', '反証', '判定不能')


def verdicts(t, n):
    """問ごとに、その問の見出しから次の問までの中で最初に出る判定の語を取る"""
    out = {}
    pos = [(int(m.group(1)), m.start()) for m in re.finditer(r'(?m)^(?:#+\s*|\*\*|\|?\s*)\**Q(\d+)\b', t)]
    seen = {}
    for q, p in pos: seen.setdefault(q, p)
    qs = sorted(seen.items(), key=lambda x: x[1])
    for k, (q, p) in enumerate(qs):
        end = qs[k + 1][1] if k + 1 < len(qs) else len(t); seg = t[p:end]
        m = re.search(r'判定[^\n]{0,20}?(支持|反証|判定不能)', seg) or re.search(r'(支持|反証|判定不能)', seg)
        if m: out[f'Q{q}'] = m.group(1)
    return out


def score(r):
    rep = os.path.join(ROOT, 'replications', r + '_gpt_refute'); key = json.load(open(os.path.join(rep, 'KEY.json')))
    src = os.path.join(BL, r, 'REPORT.md'); assert os.path.exists(src), src + ' がない'
    shutil.copy(src, os.path.join(rep, 'REPORT.md'))
    open(os.path.join(rep, 'REPORT_SHA256.txt'), 'w').write(hashlib.sha256(open(src, 'rb').read()).hexdigest() + '  REPORT.md\n')
    for x in ('_events.jsonl', '.done'):
        p = os.path.join(BL, r + x)
        if os.path.exists(p): shutil.copy(p, os.path.join(rep, 'events.jsonl' if x == '_events.jsonl' else 'DONE.txt'))
    t = open(src).read(); v = verdicts(t, len(key))
    ctl = [q for q, i in key.items() if i == 'CTRL']
    ok = all(v.get(q) == '反証' for q in ctl)
    done = open(os.path.join(BL, r + '.done')).read().strip() if os.path.exists(os.path.join(BL, r + '.done')) else ''
    L = [f'# {r} 採点（記録の平易版。publish/plain/score.py が REPORT.md から機械的に読んだ）', f'- 実行：{done}。資料の sha256 は FIXED_SHA256.txt、報告の sha256 は REPORT_SHA256.txt。',
         '- 対照：' + '。'.join(f'{q}（偽）→ {v.get(q, "読めない")}（{"正答" if v.get(q) == "反証" else "誤答"}）' for q in ctl) + '。' + ('両方正答のため、本題の判定を採用する。' if ok else '対照に誤答があるため、この回は採らない。'), '',
         '| 問 | 記録 | 判定 | 反映 |', '|---|---|---|---|']
    S = json.load(open(ST)) if os.path.exists(ST) else {}
    for q, i in key.items():
        if i == 'CTRL': continue
        L.append(f'| {q} | {i} | {v.get(q, "読めない")} | 記録の平易版（publish/plain/drafts/{i}.json） |')
        S[i] = dict(round=r, q=q, verdict=v.get(q, ''), adopted=ok)
    open(os.path.join(rep, 'SCORING.md'), 'w').write('\n'.join(L) + '\n')
    json.dump(S, open(ST, 'w'), ensure_ascii=False, indent=1)
    print(r, 'controls ok' if ok else 'CONTROLS FAILED', {q: v.get(q) for q in key})


if __name__ == '__main__':
    for r in sys.argv[1:]: score(r)
