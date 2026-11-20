# H038 の結果（R046・R047、GPT と Gemini）を引かれ方に足す。白書の各版の同じ文を、版ごとの公的文書の引用として足す。
import csv, json, os, re, shutil, hashlib, sys
sys.path.insert(0, 'checks/judge2')
ED = {'R02': ('001362421', 2020), 'R03': ('001365515', 2021), 'R04': ('001389118', 2022), 'R05': ('001407646', 2023), 'R06': ('001433241', 2024), 'R07': ('001451882', 2025)}
PG_KP = {'R02': 114, 'R03': 164, 'R04': 150, 'R05': 126, 'R06': 132, 'R07': 104}
def parse(path):
    rows = {}
    for ln in open(path).read().splitlines():
        c = [x.strip() for x in ln.strip().strip('|').split('|')]
        if len(c) >= 2 and re.fullmatch(r'C\d{2}', c[0]): rows[c[0]] = sorted(set(re.findall(r'T\d|判定不能', c[1])))
    return rows
def judged(rn, q):
    d = f'replications/{rn}'; key = json.load(open(f'{d}/KEY.json')); inv = {v: k for k, v in key.items()}
    g, m = parse(f'{d}/REPORT.md'), parse(f'{d}/REPORT_gemini.md')
    for c in ('CTRL-T0', 'CTRL-T1'):
        assert g[inv['CTRL-T0']] == ['T0'] and m[inv['CTRL-T0']] == ['T0'] and 'T1' in g[inv['CTRL-T1']] and 'T1' in m[inv['CTRL-T1']], rn
    a, b = g[inv[q]], m[inv[q]]
    J = lambda s: '、'.join(s)
    return (J(a), f'{rn.split("_")[0]}（GPT・Gemini とも {J(a)}）') if a == b else ('判定が分かれた', f'{rn.split("_")[0]}（GPT：{J(a)}／Gemini：{J(b)}）')
# 判定の写しを replications に置く（Codex の報告）
for rn in ('R046_gpt_hakusho', 'R047_gpt_hakusho'):
    n = rn.split('_')[0]; b = os.path.expanduser('~/mitodoke_blind')
    shutil.copy(f'{b}/{n}/REPORT.md', f'replications/{rn}/REPORT.md'); shutil.copy(f'{b}/{n}_events.jsonl', f'replications/{rn}/events.jsonl')
    open(f'replications/{rn}/REPORT_SHA256.txt', 'w').write(hashlib.sha256(open(f'replications/{rn}/REPORT.md', 'rb').read()).hexdigest() + '  REPORT.md\n')
KP = judged('R046_gpt_hakusho', 'W-KP'); SO = judged('R046_gpt_hakusho', 'W-SO'); YK = judged('R047_gpt_hakusho', 'W-YK'); W12 = judged('R046_gpt_hakusho', 'W-2012')
print('KP', KP, 'SO', SO, 'YK', YK, '2012', W12)
NEW = []
for i, e in enumerate(['R02', 'R03', 'R04', 'R05', 'R06', 'R07'], 7):
    NEW.append((f'Q-KP-C1-{i:03d}', 'KP-C1', e, PG_KP[e], KP, '一定の再犯抑止効果が認められた',
                '全再犯の群の差（38.0％と27.3％の差、10.7ポイント）を引き、元にある罪名構成の差の注と、効果が裏付けられなかった罪名（迷惑行為防止条例違反・強制わいせつ）を書かない。'))
for i, e in enumerate(['R02', 'R04', 'R05', 'R06', 'R07'], 3):
    NEW.append((f'Q-SO-P1-{i:03d}', 'SO-P1', e, PG_KP[e], SO, '一定の再犯抑止効果が示唆された',
                '性犯罪の再犯率の差（11.1ポイント）と「示唆」を元と同じに書く。比較の時点（観測期間最終日）を書かない点を限定が落ちるとみるかで、二つの判定者の判定が分かれた。'))
NEW.append(('Q-YK-C1-004', 'YK-C1', 'R04', 25, YK, '一定の再犯防止効果が示唆された',
            '保護観察所の受講群と非受講群の差と「示唆」を元と同じに書き、元にある抽出の条件、女性では有意差が認められなかったこと、効果量が小さいことを書かない。'))
p = 'results/citations/citations.tsv'; rows = list(csv.reader(open(p), delimiter='\t')); h = rows[0]; ix = {k: i for i, k in enumerate(h)}
have = {r[0]: n for n, r in enumerate(rows)}
QUO = {}
for qid, rec, e, pg, (ty, jd), keyp, gist in NEW:
    fid, yr = ED[e]; src = f'data/raw/saihan/{e}/zentai_{fid}.pdf'
    dst = f'data/raw/citations/{qid}.pdf'
    if not os.path.exists(dst): os.system(f'cp -c "{src}" "{dst}"')
    row = [''] * len(h)
    vals = {'引用ID': qid, '記録ID': rec, '媒体': f'再犯防止推進白書 令和{int(e[1:])}年版（全体版 {pg}頁）', '種類': '公的文書', '掲載日': str(yr), '取得日': '2026-11-18',
            'url': f'https://www.moj.go.jp/content/{fid}.pdf', '鍵の言い回し': keyp, '要旨': gist, '型': ty, '型の判定': jd,
            'sha256': hashlib.sha256(open(src, 'rb').read()).hexdigest(), 'wayback': 'なし', '現在の状態': '取得できた', '元の資料': {'KP-C1': '法務省矯正局 令和2年3月 分析結果', 'SO-P1': '法務省保護局 令和2年3月 概要・分析', 'YK-C1': '法務省保護局 令和4年10月 概要・報告書'}[rec]}
    for k, v in vals.items(): row[ix[k]] = v
    if qid in have: rows[have[qid]] = row
    else: rows.append(row)
csv.writer(open(p, 'w', newline=''), delimiter='\t', lineterminator='\n').writerows(rows)
json.dump({'W-2012': W12}, open('results/saihan/kouka_wording/R046_W2012.json', 'w'), ensure_ascii=False)
print(len(rows) - 1, 'citations')
