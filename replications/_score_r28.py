import json, os, shutil, hashlib, re
BL = os.path.expanduser('~/mitodoke_blind')
NOTE = {'R028': {'SH-A1': 'Q1 支持 → 別系統で支持。言い過ぎの指摘（抽出できる文字の範囲）を足した。', 'HK-A9': 'Q3 支持 → 別系統で支持。'}}
H = {'R028': 'H033'}
for r in NOTE:
    rep = f'replications/{r}_gpt_refute'
    for src, dst in ((f'{BL}/{r}/REPORT.md', 'REPORT.md'), (f'{BL}/{r}_events.jsonl', 'events.jsonl')):
        shutil.copy(src, f'{rep}/{dst}')
    open(f'{rep}/REPORT_SHA256.txt', 'w').write(hashlib.sha256(open(f'{rep}/REPORT.md', 'rb').read()).hexdigest() + '  REPORT.md\n')
    key = json.load(open(f'{rep}/KEY.json')); rp = open(f'{rep}/REPORT.md').read()
    ver = {}
    for q in key:
        sec = re.split(r'^## ', rp, flags=re.M)
        sec = next(x for x in sec if re.match(q + r'(?!\d)', x))
        m = re.search(r'(支持|反証|判定不能)', sec)
        ver[q] = m.group(1) if m else '?'
    done = open(f'{BL}/{r}.done').read().strip()
    ctl = [q for q, i in key.items() if i == 'CTRL']
    ok = all(ver[q] == '反証' for q in ctl)
    L = [f'# {r} 採点（hypotheses/{H[r]} の基準どおり）', f'- 実行：{done}。資料の sha256 は FIXED_SHA256.txt、報告の sha256 は REPORT_SHA256.txt。',
         '- 対照：' + '、'.join(f'{q}（偽）→ {ver[q]}' for q in ctl) + ('。両方とも反証のため、本題の判定を採用する。' if ok else '。両方とも反証ではないため、本題の判定は採らない。'), '']
    if '_' in NOTE[r]: L += ['- ' + NOTE[r]['_'], '']
    L += ['| 問 | 記録 | 判定 | 反映 |', '|---|---|---|---|']
    for q, i in key.items():
        if i == 'CTRL': continue
        L.append(f'| {q} | {i} | {ver[q]} | {NOTE[r].get(i, "反映なし（判定を採らない回）")} |')
    open(f'{rep}/SCORING.md', 'w').write('\n'.join(L) + '\n')
    print(r, ok, ver)
