import json, os, shutil, hashlib, re
BL = os.path.expanduser('~/mitodoke_blind')
NOTE = {
 'R026': {'HK-A1': 'Q1 支持 → 別系統で支持。言い過ぎの指摘（転記の工程は決まらない）を足した。', 'HK-A5': 'Q3 支持 → 別系統で支持（狭めた主張）。令和4年版の R２ シートには資料2-3 と明記、令和5〜7年版の印刷版本文は資料2-3 を案内、の指摘を足した。',
          'HK-A2': 'Q4 支持 → 別系統で支持。', 'HK-A10': 'Q5 支持 → 別系統で支持。5,926 は整合値である旨を足した。', 'HK-A3': 'Q7 支持 → 別系統で支持。'},
 'R027': {'630-M1': 'Q1 支持 → 別系統で支持。言い過ぎの指摘（他の年の差が「不明」かは確定できない）を足した。',
          'HK-A9': 'Q2 判定不能：犯罪白書の照合は一致したが、「HK-A7 と同じ型」の比較は渡した資料で確かめられない。比較の一文を外し、R028 にかける。',
          'KP-C1': 'Q4 支持 → 別系統で支持（3回目。比較の範囲を4罪名の中に狭めた文）。', 'NK-K1': 'Q5 支持 → 別系統で支持。「各年の本文」を「本文」に直した。',
          'GY-Q1': 'Q6 支持 → 別系統で支持。計上方法の変更の有無は資料からは決まらず照会事項、と確認の状態に書いた。',
          'SH-A1': 'Q8 反証：正誤表の訂正は9か所（223頁の予算額4か所を数えていなかった）。直し、R028 にかける。訂正の記録に残す。'},
}
H = {'R026': 'H031', 'R027': 'H032'}
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
