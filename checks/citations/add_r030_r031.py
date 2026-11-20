# R030・R031 の結果を取り込む：採点、写しの付け替え、citations.tsv への追加、NK-K1-001 の型の置き換え。
import os, re, csv, json, shutil, hashlib, collections
B = os.path.expanduser('~/mitodoke_blind')
def score(rn):
    out = f'replications/{rn}_gpt_types'; key = json.load(open(f'{out}/KEY.json')); rep = open(f'{B}/{rn}/REPORT.md').read()
    rows = {m.group(1): (m.group(2).strip(), m.group(3).strip()) for m in re.finditer(r'^\| (C\d\d) \| ([^|]+) \| ([^|]+) \|', rep, re.M)}
    by = {key[c]: rows[c] for c in rows}
    ok = by['CTRL-T0'][0] == 'T0' and by['CTRL-T1'][0] == 'T1'
    shutil.copy(f'{B}/{rn}/REPORT.md', f'{out}/REPORT.md'); shutil.copy(f'{B}/{rn}_events.jsonl', f'{out}/events.jsonl')
    open(f'{out}/REPORT_SHA256.txt', 'w').write(hashlib.sha256(open(f'{out}/REPORT.md', 'rb').read()).hexdigest() + '  REPORT.md\n')
    sc = [f'# {rn} 採点', '', f'対照：CTRL-T0 → {by["CTRL-T0"][0]}、CTRL-T1 → {by["CTRL-T1"][0]}。' + ('両方正答。この回を採る。' if ok else '正答でない対照がある。採らない。'), '', '| 組 | 型 | 根拠（別系統の文） |', '| --- | --- | --- |']
    sc += [f'| {q} | {t} | {g} |' for q, (t, g) in sorted(by.items()) if not q.startswith('CTRL')]
    open(f'{out}/SCORING.md', 'w').write('\n'.join(sc) + '\n'); assert ok, rn
    return by
r30, r31 = score('R030'), score('R031')
open('replications/R030_gpt_types/SCORING.md', 'a').write('\nP-NK-01〜03 は採らない：元の資料の文に調査時期と定義を示していなかったため、R031 でやり直した。\n')
open('replications/R031_gpt_types/SCORING.md', 'a').write('\nQ-NK-K1-001 は R029 の判定（T0）をこの回の判定で置き換える。R029 では元の資料の文に定義（HDS-R 20点以下、医師の診断によらない）を含めていなかった。「2015年6月時点」の部分は別系統が判定不能とした。\n')
def T(s): return '、'.join(re.findall(r'T\d', s))
NEW = [  # (新 ID, 候補 ID, 記録, 媒体, 掲載日, url, 鍵, 要旨, 型, 判定)
 ('Q-GY-Q1-003', 'P-GY-01', 'GY-Q1', '日本テレビ（日テレNEWS）', '2024-09-24', 'https://news.ntv.co.jp/category/society/a10aad1acaca4833801ce6ea32f55391', '21万4843件', '児童虐待相談の対応件数（確定値）を「児童虐待件数」として書く。値は確定値と同じ。', T(r30['P-GY-01'][0]), 'R030 で採った'),
 ('Q-GY-Q1-004', 'P-GY-02', 'GY-Q1', '福祉新聞', '2024-09-29', 'https://fukushishimbun.com/series07/37138', '4327減', '見出しで、確定値と速報値からの差を元と同じ値で書く。対象を「虐待件数」と書く（元は児童虐待相談の対応件数）。', T(r30['P-GY-02'][0]), 'R030 で採った'),
 ('Q-GY-Q1-005', 'P-GY-03', 'GY-Q1', '教育新聞', '2024-09-24', 'https://www.kyobun.co.jp/article/2024092405', '4000件余り減', '確定値と、速報値より約4,000件少ないことを書く。', T(r30['P-GY-03'][0]), 'R030 で採った'),
 ('Q-GY-Q1-006', 'P-GY-04', 'GY-Q1', '福祉新聞', '2023-09-19', 'https://fukushishimbun.com/topics/31075', '（速報値）', '速報値を速報値として引く。確定値の公表はこの記事より後。', T(r30['P-GY-04'][0]), 'R030 で採った'),
 ('Q-JH-A1-003', 'P-JH-02', 'JH-A1', '教育新聞', '2025-10-24', 'https://www.kyobun.co.jp/article/2025102405', '529人', '2024年の小中高生の自殺者数を、比較の範囲（1980年以降）とともに元と同じ値で書く。', T(r30['P-JH-02'][0]), 'R030 で採った'),
 ('Q-JH-A1-004', 'P-JH-04', 'JH-A1', '先端教育オンライン', '2025-10-29', 'https://www.sentankyo.jp/articles/200a089a-2419-4ec7-b0d0-90b77c259c35', '過去最多529人', '見出しで 529人を「過去最多」と書き、元にある比較の範囲（統計のある1980年以降）を書かない。', T(r30['P-JH-04'][0]), 'R030 で採った'),
 ('Q-ST-I2-005', 'P-ST-04', 'ST-I2', '日本テレビ（日テレNEWS）', '2026-03-19', 'https://news.ntv.co.jp/category/society/624a38986ea54fcc97d848f66893edee', '過去最多', '計上方法の変更をまたいで「過去最多」と書き、変更の注がない。', T(r30['P-ST-04'][0]), 'R030 で採った'),
 ('Q-ST-I2-006', 'P-ST-05', 'ST-I2', 'テレビ朝日', '2026-11-18', 'https://news.tv-asahi.co.jp/news_politics/articles/000548663.html', '施行されて以降、最多', '計上方法の変更をまたいで「施行以降、最多」と書き、変更の注がない。', T(r30['P-ST-05'][0]), 'R030 で採った'),
 ('Q-NK-K1-002', 'P-NK-01', 'NK-K1', '認知症ねっと', '2016-01-28', 'https://info.ninchisho.net/archives/7328', '約14％', '見出しで約14％と書き、元にある「認知症傾向」の定義（HDS-R 20点以下で、医師の診断によらない）を書かない。', T(r31['P-NK-01'][0]), 'R031 で採った'),
 ('Q-NK-K1-003', 'P-NK-02', 'NK-K1', 'みんジョブ', '2020-01-24', 'https://minjob.com/news/kaigogaku/no474/', '14％に上っています', '「およそ」を落として 1,300人・14％と書き、定義も書かない。', T(r31['P-NK-02'][0]), 'R031 で採った'),
 ('Q-NK-K1-004', 'P-NK-03', 'NK-K1', 'nippon.com', '2018-05-17', 'https://www.nippon.com/ja/features/h00195/', '約1300人', '推計人数を元と同じ丸めで書き、定義を書かない。', T(r31['P-NK-03'][0]), 'R031 で採った'),
]
cand = {r['cid']: r for r in csv.DictReader(open('results/citations/CANDIDATES_R030.tsv'), delimiter='\t')}
p = 'results/citations/citations.tsv'; rows = list(csv.reader(open(p), delimiter='\t')); h = rows[0]; ix = {k: i for i, k in enumerate(h)}
have = {r[0] for r in rows[1:]}
SRC = {'GY-Q1': 'こども家庭庁 速報値／福祉行政報告例 令和4年度', 'JH-A1': '自殺対策白書 令和7年版', 'ST-I2': '警察庁 令和7年におけるストーカー事案…への対応状況', 'NK-K1': '法務省矯正局 平成28年1月（001170401.pdf）'}
for nid, cid, rec, media, date, url, keyp, gist, ty, jd in NEW:
    c = cand[cid]; ext = c['file'].rsplit('.', 1)[1]
    shutil.copy(f'data/raw/citations/{c["file"]}', f'data/raw/citations/{nid}.{ext}')
    row = [''] * len(h)
    vals = {'引用ID': nid, '記録ID': rec, '媒体': media, '種類': '報道', '掲載日': date, '取得日': c['fetched_utc'][:10], 'url': url, '鍵の言い回し': keyp, '要旨': gist, '型': ty, '型の判定': jd, 'sha256': c['sha256'], 'wayback': 'なし', '現在の状態': '取得できた', '元の資料': SRC[rec]}
    for k, v in vals.items(): row[ix[k]] = v
    if nid in have: rows = [row if r[0] == nid else r for r in rows]
    else: rows.append(row)
for r in rows[1:]:
    if r[0] == 'Q-NK-K1-001':
        r[ix['型']] = T(r31['Q-NK-K1-001'][0]); r[ix['型の判定']] = 'R031 で採った（R029 の判定を置き換え）'
        r[ix['要旨']] = '割合と推計人数を元と同じ丸めで書き、元にある「認知症傾向」の定義を書かない。「2015年6月時点」は、元の調査時期（2015年1〜2月）からは確かめられない（別系統も判定不能とした）。'
csv.writer(open(p, 'w', newline=''), delimiter='\t', lineterminator='\n').writerows(rows)
print(collections.Counter(r[ix['型']] for r in rows[1:]), len(rows) - 1)
