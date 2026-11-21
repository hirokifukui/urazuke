"""国会答弁の引かれ方を、サイトの「引かれ方」に足すデータにする（2026-11-21、運営者の決定：URAZUKE の延長として載せる）。
対象：GPT の盲検で「別系統で支持」になり、かつ引かれ方のページがある記録（publish/citations.json）に結びつくもの。
Claude の説明が不確かさを述べているもの（確認できない・判断できない等）は「判定が分かれた」にする。言い回しは機械で15字以内に切る。
答弁者は役職と日付で示し、個人名は出さない（会議録へのリンクで確かめられる）。出力：publish/kokkai_cites.json。python3 kokkai/export.py <日付>"""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); day = sys.argv[1]; D = os.path.join(ROOT, 'results/kokkai', day)
CIT = {r['rec']: r for r in json.load(open(os.path.join(ROOT, 'publish/citations.json'), encoding='utf-8'))['records']}
TY = {'限定が落ちる': '限定が落ちる', '範囲のずれ': '限定が落ちる', '数字の不一致': '値が違う', '食い違いなし': '同じ'}
NOCITE = re.compile(r'述べず|触れず|述べるだけ|説明するだけ|触れていない|述べていない|挙げるだけ|引いていない')
UNSURE = re.compile(r'確認できな|確認できま|確かめられ|判断できな|特定できな|分からな|わからな|かどうかは|同じ範囲か')
def short(s, n=15): s = re.sub(r'\s+', '', s); return s if len(s) <= n else s[:n]
def phrase(q):
    m = re.search(r'([^、。]{0,7}?)(再犯抑止化?効果|再犯防止効果|抑止の効果|効果|最多)', q)
    if not m: return short(q)
    pre = re.sub(r'^[のがはをにでと]+', '', m.group(1)[-6:])
    return f'{pre}[[{m.group(2)}]]'
def pos(c):   # 役職（会議録の speakerPosition。なければ発言の頭の肩書き）。質問の側は個人名を出さず「質問した議員」
    if c.get('side') == 'q': return '質問した議員' if c.get('position') != '質問主意書の提出者' else '質問主意書の提出者'
    if c.get('position') == '閣議決定': return '答弁書（閣議決定）'
    p = c.get('position') or ''
    if not p: m = re.match(r'○\S+?(政府参考人|国務大臣|副大臣|政務官)', c['passage']); p = m.group(1) if m else ''
    return p
# 追記のみ：前の回に載せたもの（同じ記録・同じ会議録の URL）は残す。回ごとの LLM のぶれで消えないようにする
OUTP = os.path.join(ROOT, 'publish/kokkai_cites.json')
out = json.load(open(OUTP, encoding='utf-8')) if os.path.exists(OUTP) else {}
seen = {(k, c['url']) for k, v in out.items() for c in v}
R = [json.loads(l) for f in ('refuted.jsonl', 'refuted2.jsonl', 'refuted3.jsonl', 'refuted_shuisho.jsonl', 'refuted_q.jsonl') if os.path.exists(os.path.join(D, f)) for l in open(os.path.join(D, f), encoding='utf-8')]
for r in sorted(R, key=lambda r: r['date']):
    if r['gpt']['result'] != '別系統で支持': continue
    j = r['claude']; recs = [x for x in (j.get('record_ids') or []) if x in CIT]
    if not recs: continue
    # 「食い違いなし」は、答弁が資料の数字・結論を実際に引いているものだけ載せる（引いていない答弁を「同じ」と見せない）
    if j['type'] == '食い違いなし' and (NOCITE.search(j.get('explanation', '')) or not re.search(r'[〇一二三四五六七八九十百千万]|効果|認め|示唆|最多|割合|推計', j.get('speech_quote', ''))): continue
    rec = recs[0]; sq = CIT[rec]['src_quotes']
    unsure0 = bool(UNSURE.search(j.get('explanation', '')))
    newt = '判定が分かれた' if unsure0 else TY[j['type']]
    if (rec, r['url']) in seen:
        # 前の回と型が違えば「判定が分かれた」にする（回ごとの LLM のぶれ。どちらかを選ばない。2026-11-21）
        for c in out[rec]:
            if c['url'] == r['url'] and c['types'] != [newt] and c['types'] != ['判定が分かれた']:
                c['judge'] = f"回によって型が分かれた（{c['types'][0]}／{newt}）。どちらも Claude が型を付け GPT が盲検で支持"; c['types'] = ['判定が分かれた']
        continue
    seen.add((rec, r['url']))
    nq = re.sub(r'\s', '', j['source_quote'])
    pair = [i for i, q in enumerate(sq) if any(nq[k:k + 8] in re.sub(r'\s', '', q['text']) for k in range(0, max(1, len(nq) - 7), 2))] or [0]
    unsure = bool(UNSURE.search(j.get('explanation', '')))
    n = len(out.setdefault(rec, [])) + 1
    out[rec].append(dict(id=f'{rec}-K{n:02d}', date=r['date'], kind='国会', media=f"{r['house']} {r['meeting']}（{pos(r)}）", url=r['url'], wayback='', live=True,
                         src_phrase=short(sq[pair[0]]['text']), cite_phrase=phrase(j['speech_quote']), types=['判定が分かれた' if unsure else TY[j['type']]],
                         gist=(re.split(r'(?<=。)', j.get('explanation', ''))[0][:120] or '答弁の数字・言い方は元の資料と同じ。'), judge='国会答弁の照合（Claude が型を付け、GPT が盲検で支持。kokkai/）' if not unsure else 'Claude の説明が不確かさを述べているため判定しない',
                         quote=j['speech_quote'], pair=pair, basis='国会会議録で確認'))
json.dump(out, open(OUTP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print({k: [(c['date'], c['types'][0]) for c in v] for k, v in out.items()})
