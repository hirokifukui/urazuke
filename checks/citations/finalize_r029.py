# R029 の採点と citations.tsv の確定（H034）
import json, re, csv, hashlib, shutil, os, collections
B = os.path.expanduser('~/mitodoke_blind/R029')
OUT = 'replications/R029_gpt_types'
key = json.load(open(f'{OUT}/KEY.json'))
rep = open(f'{B}/REPORT.md').read()
rows = {}
for m in re.finditer(r'^\| (C\d\d) \| ([^|]+) \| ([^|]+) \|', rep, re.M):
    rows[m.group(1)] = (m.group(2).strip(), m.group(3).strip())
assert len(rows) == 23, len(rows)
c05, c12 = rows['C05'][0], rows['C12'][0]
ok = (c05 == 'T0' and c12 == 'T1')
for f, g in [('REPORT.md', 'REPORT.md'), ('../R029_events.jsonl', 'events.jsonl')]:
    shutil.copy(os.path.join(B, f), os.path.join(OUT, g))
open(f'{OUT}/REPORT_SHA256.txt', 'w').write(hashlib.sha256(open(f'{OUT}/REPORT.md', 'rb').read()).hexdigest() + '  REPORT.md\n')
bytype = {key[c]: rows[c] for c in rows}
sc = ['# R029 採点', '', f'対照：C05（CTRL-T0）→ {c05}、C12（CTRL-T1）→ {c12}。' + ('両方正答。この回を採る。' if ok else '正答でない対照がある。この回は採らない。'), '',
      '判定は一つの別系統だけで、こちら側の型は実行前に固定していない。したがって「判定が分かれた」は、別系統が「判定不能」とした組に限って使う（H034 の「食い違い」は、二つ目の独立した判定を足す回で使う）。', '',
      '| 引用 ID | 型 | 根拠（別系統の文） |', '| --- | --- | --- |']
for q in sorted(bytype):
    if q.startswith('CTRL'): continue
    sc.append(f'| {q} | {bytype[q][0]} | {bytype[q][1]} |')
cnt = collections.Counter()
for q, (t, _) in bytype.items():
    if q.startswith('CTRL'): continue
    for x in re.split(r'[、,]\s*', t): cnt[x] += 1
sc += ['', '型ごとの数（複数該当を含む）：' + '、'.join(f'{k} {v}' for k, v in sorted(cnt.items()))]
open(f'{OUT}/SCORING.md', 'w').write('\n'.join(sc) + '\n')
if not ok: raise SystemExit('controls failed')

# 要旨（引用の文はここに写さない。15字以内の鍵の言い回しだけ）
G = {
 'Q-KP-C1-001': ('性犯罪防止策に一定効果', '見出しで効果を伝え、本文は受講者の再犯率が低かったとする。効果が裏付けられなかった罪名の但し書きはない。'),
 'Q-KP-C1-002': ('0.79倍に抑えられ', 'Cox モデルの再犯可能性 0.79倍を、再犯率の比として書く。同じ記事に罪名による限定はある。'),
 'Q-KP-C1-003': ('効果はある', '別々の群の 38.0％と 27.3％を、受講者の再犯率の低下として書く。'),
 'Q-KP-C1-004': ('再犯リスクが低下', '群別の再犯率と 0.79倍を伝え、裏付けのない罪名も本文に書く。'),
 'Q-KP-C1-005': ('再犯可能性が低い', '保護観察所の分析の群別の割合と倍率を、元と同じ向きで伝える。'),
 'Q-KP-C1-006': ('15.0％と22.5％', '群別の性犯罪再犯の割合を、元と同じ順で示す。'),
 'Q-SO-P1-001': ('11.1ポイント', '群の差と「示唆」をそのまま引く。率が性犯罪に限るかは元の文に書かれていない。'),
 'Q-SO-P1-002': ('15.1％と26.2％', '群別の割合は一致する。引用の「再犯率」が性犯罪に限るかは文からは決まらない。'),
 'Q-YK-C1-001': ('一定の処遇効果', '元の「示唆された」を「認められた」とし、施設・保護観察所という範囲も書かない。'),
 'Q-YK-C1-002': ('一定の処遇効果', '元の「示唆された」を「認められた」とする。'),
 'Q-YK-C1-003': ('一定の処遇効果', '元の「示唆された」を「認められた」とする。'),
 'Q-GY-Q1-001': ('速報値', '速報値を速報値として引く。確定値の公表はこの記事より後。'),
 'Q-GY-Q1-002': ('確定値', '確定値と速報値、その差を元と同じ値で示す。'),
 'Q-JH-A1-001': ('629人', '2024年の小中高生の自殺者数を、元の 529人でなく 629人と書く。'),
 'Q-JH-A1-002': ('538人', '2025年の小中高生の自殺者数を元と同じ値で書く。'),
 'Q-ST-I2-001': ('4年連続で過去最高', '2024年の計上方法の変更をまたいで増加率と最高を書き、変更の注がない。'),
 'Q-ST-I2-002': ('同法施行後、最多', '計上方法の変更をまたいで最多と書き、変更の注がない。'),
 'Q-ST-I2-003': ('前年比24.1%増', '計上方法の変更をまたいで増加率を書き、変更の注がない。'),
 'Q-ST-I2-004': ('1,081件', 'ストーカー規制法違反の検挙数を元と同じ値で書く。'),
 'Q-NK-K1-001': ('約14％', '割合と推計人数を元と同じ丸めで書く。'),
 'Q-630-D1-001': ('', '全国の推移と都道府県の順位を書くが、元の文に照合できる値がない。'),
}
draft = list(csv.DictReader(open('results/citations/citations_draft.tsv'), delimiter='\t'))
fetch = {r['qid']: r for r in csv.DictReader(open('results/citations/FETCH.tsv'), delimiter='\t')}
cols = ['引用ID', '記録ID', '媒体', '種類', '掲載日', '取得日', 'url', '鍵の言い回し', '要旨', '型', '型の判定', 'sha256', 'wayback', '現在の状態', '元の資料']
with open('results/citations/citations.tsv', 'w', newline='') as fh:
    w = csv.writer(fh, delimiter='\t', lineterminator='\n'); w.writerow(cols)
    for r in draft:
        q = r['qid']; f = fetch[q]; t = bytype[q][0]
        kind = '団体の資料' if q == 'Q-630-D1-001' else r['種類']
        wb = f['wayback'] if f['wayback'].startswith('http') else ('なし' if not f['wayback'] else f['wayback'])
        st = '取得できた' if f['status'] == '200' else ('現在は取得できず（Wayback に写しあり）' if wb.startswith('http') else '現在は取得できず（写しなし）')
        judge = '判定が分かれた（別系統が判定不能）' if t == '判定不能' else 'R029 で採った'
        w.writerow([q, r['rec'], r['媒体'], kind, r['掲載日'], f['fetched_utc'][:10], r['url'], G[q][0], G[q][1], t, judge, f['sha256'], wb, st, r['元の資料']])
print('ok', dict(cnt))
