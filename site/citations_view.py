# 「この資料の引かれ方」（引用の追跡 v0.1、H034・R029）。データは publish/citations.json（checks/citations/make_show.py が作る）。
import json, os, re, html
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = 'publish/citations.json'
D = json.load(open(os.path.join(R, SRC)))
BY = {r['rec']: r for r in D['records']}
e = lambda s: html.escape(str(s), quote=True)
TYPES = ['同じ', '値が違う', '量が置き換わる', '言い方が強まる', '限定が落ちる', '訂正が入っていない', '判定が分かれた']
TYPE_EN = {'同じ': 'Same', '値が違う': 'Different value', '量が置き換わる': 'Different quantity', '言い方が強まる': 'Stronger wording',
           '限定が落ちる': 'Qualification dropped', '訂正が入っていない': 'Correction not reflected', '判定が分かれた': 'No verdict'}
TYPE_DEF = {'同じ': '数値も言い方も元と同じ。', '値が違う': '数値が元と違う（写し間違い、速報値と確定値の取り違えを含む）。',
            '量が置き換わる': '別の量として書く（ハザード比を「再犯率」、群の比較を「低下」など）。',
            '言い方が強まる': '元の「示唆」「可能性」などが「確認」「認められた」などになる。結論の強さを変えるものだけを数える。',
            '限定が落ちる': '元の同じ箇所にある但し書き（効果が裏付けられなかった群、数え方の変更など）を書かずに結論を引く。結論が当てはまる範囲（効果の有無・程度、対象者、罪種、指標、年度、数え方）を変えるものだけを数え、細目の言い残しは数えない。',
            '訂正が入っていない': '元の資料が後に直されたのに、直す前の値を引く。', '判定が分かれた': '二つの判定者（GPT と Gemini）に3回ずつ判定させ、全ての回に共通する型がなかった、または判定できないとした（共通する型があるときはそれだけを表示する）。国会の答弁では、型を付けた側（Claude）が資料から確かめられないと述べたもの。人は判定しない。'}
TYPE_DEF_EN = {'同じ': 'Figures and wording are the same as the source.', '値が違う': 'A figure differs from the source (including copying errors and mixing up preliminary and final figures).',
               '量が置き換わる': 'Written as a different quantity (a hazard ratio as a "reoffending rate", a comparison of groups as a "fall", and so on).',
               '言い方が強まる': 'The source’s "suggested" or "possible" becomes "confirmed" or "recognised". Counted only when the strength of the conclusion changes.',
               '限定が落ちる': 'The conclusion is cited without a qualification stated at the same place in the source (groups where no effect was supported, a change in counting, and so on). Counted only when it changes what the conclusion applies to (whether there is an effect and how large, who, which offences, which measure, which year, how things are counted); omitted minor details are not counted.',
               '訂正が入っていない': 'The source was later corrected, but the citation uses the value before correction.', '判定が分かれた': 'Each of the two judges (GPT and Gemini) judged three times, and no type was common to all the runs, or found the texts insufficient for a verdict (when they share a type, only the shared type is shown). For Diet answers: the model assigning the type (Claude) said the texts could not settle it. No person decides.'}
KIND_EN = {'報道': 'News', '公的文書': 'Official document', '論文': 'Paper', '団体の資料': 'Organisation’s material', '国会': 'Diet'}
RKIND = {'途中': ('資料の値・書き方が、引かれるときに変わる', 'The source’s figures or wording change when cited'),
         '資料': ('資料の側が後で変わる、または注がない', 'The source changes later, or lacks a note')}
CSS = """
.cit .src{background:var(--paper);border:1px solid var(--line);border-left:3px solid var(--acc);padding:1rem 1.3rem;margin:1rem 0 1.4rem}.cit .src p{margin:.2rem 0}
ol.tl{list-style:none;margin:0;padding:0 0 0 .2rem;border-left:1px solid var(--line)}ol.tl li{position:relative;padding:.2rem 0 1.1rem 1.4rem;display:grid;grid-template-columns:8.5em 1fr;gap:.2rem 1rem}
ol.tl li:before{content:"";position:absolute;left:-.38rem;top:.62rem;width:.62rem;height:.62rem;border-radius:50%;background:var(--paper);border:1.5px solid var(--sub)}
ol.tl li.ev:before{border-radius:1px;background:var(--acc);border-color:var(--acc)}ol.tl .d{color:var(--sub);font-size:.82rem;padding-top:.15rem;white-space:nowrap}
ol.tl li.ev .b{font-size:.9rem;color:var(--acc)}ol.tl .who{font-size:.8rem;color:var(--sub);margin:0}ol.tl .ph{margin:.15rem 0;font-size:.95rem}
ol.tl .ph .o{color:var(--sub)}ol.tl .ph .ar{color:var(--sub);margin:0 .5rem}ol.tl mark{background:none;border-bottom:2px solid var(--ink);color:inherit;padding:0}
.ty{display:inline-block;font-size:.72rem;padding:0 .5rem;border:1px solid var(--line);border-radius:2px;margin-right:.3rem;color:var(--ink);background:#f6f6f3}
ol.sq{padding-left:0;list-style:none}ol.sq li{margin:.6rem 0;font-size:.92rem}.cq .who{font-size:.82rem;color:var(--sub);margin:0 0 .6rem}.cq .qq{font-size:1.02rem}
ol.tl .g{font-size:.82rem;color:var(--sub);margin:.2rem 0}ol.tl .lk{font-size:.78rem;margin:.1rem 0}
@media(max-width:640px){ol.tl li{grid-template-columns:1fr}}
"""

def mk(s): return re.sub(r'\[\[(.+?)\]\]', r'<mark>\1</mark>', e(s))
def dkey(d):
    if re.fullmatch(r'\d{4}-\d\d-\d\d', d): return d
    if re.fullmatch(r'\d{4}-\d\d', d): return d + '-99'
    if re.fullmatch(r'\d{4}', d): return d + '-99-99'
    return '9999'
def dja(d):
    m = re.fullmatch(r'(\d{4})(?:-(\d\d))?(?:-(\d\d))?', d)
    if not m: return '掲載日不明'
    y, mo, da = m.groups()
    return f'{y}年' + (f'{int(mo)}月' if mo else '') + (f'{int(da)}日' if da else '')
MON = 'January February March April May June July August September October November December'.split()
def den(d):
    m = re.fullmatch(r'(\d{4})(?:-(\d\d))?(?:-(\d\d))?', d)
    if not m: return 'Date unknown'
    y, mo, da = m.groups()
    return (f'{int(da)} ' if da else '') + (f'{MON[int(mo)-1]} ' if mo else '') + y

def _tl(r, en, t, E, link):
    items = [(dkey(v['date']).replace('-99', '-00'), 0, v) for v in r['ev']] + [(dkey(c['date']), 1, c) for c in r['cites']]
    items.sort(key=lambda x: (x[0], x[1])); li = []
    for _, k, v in items:
        dd = den(v['date']) if en else dja(v['date'])
        if k == 0:
            li.append(f'<li class="ev"><span class="d">{dd}</span><div class="b">{E(t(v["text"]))}</div></li>'); continue
        ty = ''.join(f'<span class="ty">{e(TYPE_EN[x] if en else x)}</span>' for x in v['types'])
        li.append(f'<li class="ct"><span class="d">{dd}</span><div><p class="who">{e(KIND_EN[v["kind"]] if en else v["kind"])} · {E(t(v["media"]))} · <a href="{link}#{v["id"]}">{v["id"]}</a></p><p>{ty}</p></div></li>')
    return f'<ol class="tl">{"".join(li)}</ol>'

def _fns(lang, T):
    en = lang == 'en'; t = (lambda s: T(s)) if en else (lambda s: s)
    E = (lambda s: re.sub(r'`([^`]+)`', r'<code>\1</code>', e(s))) if en else e
    return en, t, E

def summary(r, en):
    c = counts(r)
    return '、'.join(f'{k} {c[k]}' for k in TYPES if c[k]) if not en else ', '.join(f'{TYPE_EN[k]} {c[k]}' for k in TYPES if c[k])

def block(rid, lang='ja', T=None):
    """記録のページに置く短い案内（詳しくは citations/<記録>.html）。"""
    r = BY.get(rid)
    if not r: return ''
    en, t, E = _fns(lang, T)
    if en:
        return (f'<section class="cit"><h2>How this source is cited</h2><div class="src"><p class="kick">{e(RKIND[r["kind"]][1])}</p>'
                f'<p>{len(r["cites"])} citations found in news, official documents, papers and Diet answers ({summary(r, True)}).</p>'
                f'<p><a href="../citations/{rid}.html">Each citation side by side with the source text</a></p></div></section>')
    return (f'<section class="cit"><h2>この資料の引かれ方</h2><div class="src"><p class="kick">{e(RKIND[r["kind"]][0])}</p>'
            f'<p>報道・公的文書・論文・国会の答弁で見つけた引用 {len(r["cites"])}件（{summary(r, False)}）。</p>'
            f'<p><a href="../citations/{rid}.html">引用ごとに、元の資料の原文と並べて見る</a></p></div></section>')

def detail(rid, lang='ja', T=None):
    r = BY[rid]; en, t, E = _fns(lang, T)
    sq = r['src_quotes']
    def srcq(n): q = sq[n]; return f'<span class="muted">［{n + 1}］{E(t(q["label"]))}　{E(t(q["where"]))}</span><br><span lang="ja">「{e(q["text"])}」</span>'
    cards = []
    for c in sorted(r['cites'], key=lambda c: dkey(c['date'])):
        dd = den(c['date']) if en else dja(c['date'])
        ty = ''.join(f'<span class="ty">{e(TYPE_EN[x] if en else x)}</span>' for x in c['types'])
        basis = {'国会会議録で確認': 'checked against the Diet record (NDL)', '保存した写しで確認': 'checked against the saved copy', 'Wayback の写しで確認': 'checked against the Wayback copy', '原文未確認（検索の表示で得た文。写しなし）': 'not checked against the original (text as shown in search results; no copy)'}[c['basis']] if en else c['basis']
        lk = f'<a href="{e(c["url"])}">{"Original page" if en else "元のページ"}</a>' + ('' if c['live'] else (' <span class="muted">(not retrievable now)</span>' if en else '<span class="muted">（現在は取得できない）</span>'))
        lk += f'　<a href="{e(c["wayback"])}">{"Archived copy" if en else "保存された写し"}</a>' if c['wayback'] else ''
        L = ('Citation', 'Source text', 'Difference', 'Type') if en else ('引用', '元の資料の原文', '違い', '型')
        cards.append(f'<div class="card cq" id="{c["id"]}"><p class="who">{dd} · {e(KIND_EN[c["kind"]] if en else c["kind"])} · {E(t(c["media"]))} · {c["id"]}</p>'
                     f'<dl><dt>{L[0]}</dt><dd><span lang="ja" class="qq">「{e(c["quote"])}」</span><br><span class="muted">{e(basis)}</span></dd>'
                     f'<dt>{L[1]}</dt><dd>{"<br>".join(srcq(n) for n in c["pair"])}</dd>'
                     f'<dt>{L[2]}</dt><dd>{E(t(c["gist"]))}</dd><dt>{L[3]}</dt><dd>{ty}<br><span class="muted">{E(t(c.get("judge", "")))}</span></dd><dt></dt><dd class="lk">{lk}</dd></dl></div>')
    sl = ''.join(f'<li>{srcq(n)}</li>' for n in range(len(sq)))
    if en:
        return (f'<p class="muted"><a href="../citations.html">How sources are cited</a> / record <a href="../records/{rid}.html">{rid}</a></p>'
                f'<h1>How this source is cited</h1><p class="head">{E(t(r["src"]))}</p><p class="kick">{e(RKIND[r["kind"]][1])}</p><p class="concl">{E(t(r["says"]))}</p>'
                f'<h2>Source text</h2><p class="muted">Quoted from the source document, with the PDF page. Numbers in brackets are referred to below.</p><ol class="sq">{sl}</ol>'
                f'<h2>Timeline</h2><p class="muted">■ events on the source side (publication, final figures, changes in counting); ○ citations.</p>{_tl(r, en, t, E, "")}'
                f'<h2>Citations</h2><p class="muted">{len(r["cites"])} citations: {summary(r, True)}. The citation is quoted in the original Japanese, one passage per article: up to about 30 characters for news, up to one sentence for official documents and papers. Compared key phrases are limited to 15 characters.</p>{"".join(cards)}'
                + ai_block(rid, 'en', T) + f'<h2>How the citation types were assigned</h2><p class="muted">Two independent AIs (GPT / Codex and Gemini) were each shown only the source text, the citation text and the definitions of the types, in shuffled order, without the record ID, the outlet or the URL. Two dummy pairs with obvious types were mixed in; round {D["round"]} was adopted because both were answered correctly. No evaluation of the citing side is made, and no correction is requested. Definitions: <a href="../citations.html">How sources are cited</a>.</p>')
    return (f'<p class="muted"><a href="../citations.html">引かれ方</a> ／ 記録 <a href="../records/{rid}.html">{rid}</a></p>'
            f'<h1>この資料の引かれ方</h1><p class="head">{e(r["src"])}</p><p class="kick">{e(RKIND[r["kind"]][0])}</p><p class="concl">{e(r["says"])}</p>'
            f'<h2>元の資料の原文</h2><p class="muted">元の資料からの引用（頁は PDF の頁）。［ ］の番号は下の引用で使う。</p><ol class="sq">{sl}</ol>'
            f'<h2>時系列</h2><p class="muted">■ 資料の側の出来事（公表・確定値・数え方の変更）、○ 引用。</p>{_tl(r, en, t, E, "")}'
            f'<h2>引用</h2><p class="muted">{len(r["cites"])}件：{summary(r, False)}。引用は一つの記事から一か所で、報道は30字程度まで、公的文書・論文は一文まで。言い回しの比較（元と引用の語の違い）は15字以内。</p>{"".join(cards)}'
            + ai_block(rid, 'ja') + f'<h2>引用の型の付け方</h2><p class="muted">元の文・引用の文・型の定義だけを、記録 ID・媒体名・URL を伏せ、順序を乱して、二つの別系統の AI（GPT / Codex と Gemini）に渡した。型の明らかな作例を2つ混ぜ、両方正答だった回（{D["round"]}）を採った。引いた側の評価はせず、訂正の依頼もしない。型の定義は<a href="../citations.html">引かれ方</a>。</p>')

def counts(r):
    c = {k: 0 for k in TYPES}
    for x in r['cites']:
        for t in x['types']: c[t] += 1
    return c

def index_body(lang='ja', T=None):
    en = lang == 'en'; t = (lambda s: T(s)) if en else (lambda s: s)
    tot = {k: 0 for k in TYPES}; n = 0; rows = []
    for r in D['records']:
        c = counts(r); n += len(r['cites'])
        for k in TYPES: tot[k] += c[k]
        yrs = sorted({x['date'][:4] for x in r['cites'] if re.match(r'\d{4}', x['date'])})
        span = (f'{yrs[0]}–{yrs[-1]}' if len(yrs) > 1 else (yrs[0] if yrs else '—'))
        rows.append(f'<tr><td><a href="citations/{r["rec"]}.html">{r["rec"]}</a></td><td>{e(t(r["src"]))}</td><td>{len(r["cites"])}</td>' + ''.join(f'<td>{c[k] or ""}</td>' for k in TYPES) + f'<td class="muted">{span}</td></tr>')
    # 点検 #60（2026-11-20）：元と違う形で引かれた引用の実数と、複数の型を持つ引用の数を注に書く
    _all = [x for r in D['records'] for x in r['cites']]
    _diff = [x for x in _all if x['types'] and not set(x['types']) & {'同じ', '判定が分かれた'}]
    _multi = sum(1 for x in _diff if len(x['types']) > 1)
    th = ''.join(f'<th>{e(TYPE_EN[k] if en else k)}</th>' for k in TYPES)
    dl = ''.join(f'<tr><td>{e(TYPE_EN[k] if en else k)}</td><td>{e(TYPE_DEF_EN[k] if en else TYPE_DEF[k])}</td><td>{tot[k]}</td></tr>' for k in TYPES)
    if en:
        return (f'<h1>How sources are cited</h1><p class="lead">For the source documents of the records, we searched how their figures and conclusions are cited in news, official documents, papers and answers in the Diet, and compared each citation with the source text. Diet answers are collected from the Diet record (National Diet Library); Claude assigns a type and only those supported by GPT in a blinded test are shown (speakers are identified by post and date, with a link to the record; the procedure is in kokkai/ in the public repository). New citations are searched for every week as part of the weekly crawl. Checks to make before citing: <a href="checklist.html">Before citing a statistic</a>.</p>'
                f'<div class="nums big"><div><b>{len(D["records"])}</b><span>records with citations found</span></div><div><b>{n}</b><span>citations</span></div><div><b>{tot["同じ"]}</b><span>of which the same as the source</span></div></div>'
                f'<h2>By record</h2><table><tr><th>Record</th><th>Source</th><th>Citations</th>{th}<th>Years</th></tr>{"".join(rows)}</table><p class="muted">A citation can have more than one type. Citations that differ from the source (where the two judgments agreed) number {len(_diff)}. {f'{_multi} of them have two or more types, so the column totals are larger.' if _multi else 'At present no citation has two or more types, so the column totals match.'}</p>'
                f'<h2>Types</h2><table><tr><th>Type</th><th>Definition</th><th>Count</th></tr>{dl}</table>'
                f'<h2>Method and limits</h2><ul><li>Search terms were fixed for each record before searching (hypothesis H034). Of the 56 records, 43 were searched; 13 have no figure that is cited and were not searched.</li>'
                f'<li>The search is not exhaustive. The counts show citations found, not the share of all citations. On 18 November 2026 we also searched with the Perplexity API. Perplexity’s answer text is not published; only citations whose text was checked against a saved copy of the original page were added. Pages disallowed by robots.txt were not retrieved. In the weekly check of 20 November 2026, queries for records SH-C1, ST-D1, SK-C1 and ST-C1 were added and searched in the same way (R066).</li>'
                f'<li>Types were assigned separately by two independent AIs (GPT / Codex and Gemini) shown only the source text, the citation text and the definitions (H037). Only types on which both agreed are shown; where they disagreed, the citation is marked “No verdict” and both judgments are given. Two dummy pairs with obvious types were mixed in; the rounds ({D["round"]}) were adopted because both were answered correctly. Where the AI could not decide, the result is shown as “No verdict”; no person decides. For NK-K1, the source text first given omitted the survey period and the definition of “tendency towards dementia”; the pairs were judged again with them included (R031), and that round replaces the earlier judgments.</li>'
                f'<li>Each cited page was saved with a SHA-256 hash and checked for an archived copy. Pages that can no longer be retrieved are marked.</li>'
                f'<li>We do not assess the intentions of the citing side or evaluate media outlets, and we do not ask them for corrections. Compared key phrases are limited to 15 characters; each citation quotes one passage per article (about 30 characters for news, one sentence for official documents and papers).</li></ul>')
    return (f'<h1>引かれ方</h1><p class="lead">記録のある資料について、その数字・結論が報道・公的文書・論文・国会の答弁でどう引かれているかを探し、引用の文を元の文と比べました。国会の答弁は国会会議録（国立国会図書館）から集め、Claude が型を付け、GPT がそれを盲検で試して支持したものだけを載せます（答弁者は役職と日付で示し、会議録へのリンクを付けます。手順は公開リポジトリの kokkai/）。新しい引用は、週1回の巡回で毎週検索して足します。引く前の確かめ方は<a href="checklist.html">引く前に確かめること</a>にあります。</p>'
            f'<div class="nums big"><div><b>{len(D["records"])}</b><span>引用が見つかった記録</span></div><div><b>{n}</b><span>引用</span></div><div><b>{tot["同じ"]}</b><span>そのうち元と同じ</span></div></div>'
            f'<h2>記録ごと</h2><table><tr><th>記録</th><th>元の資料</th><th>引用</th>{th}<th>年</th></tr>{"".join(rows)}</table><p class="muted">一つの引用が複数の型を持つことがある。元の文と違う形で引かれた引用（二つの判定が一致した分）は実数で {len(_diff)} 件。{f'うち {_multi} 件が2つ以上の型に当たるため、列の和はこれより多い。' if _multi else 'いまは2つ以上の型に当たる引用はなく、列の和と一致する。'}</p>'
            f'<h2>型</h2><table><tr><th>型</th><th>定義</th><th>数</th></tr>{dl}</table>'
            f'<h2>方法と限り</h2><ul><li>検索語は、探す前に記録ごとに固定した（H034）。56件のうち 43件を探し、引用される値のない 13件は探していない。</li>'
            f'<li>検索は網羅ではない。数は見つけた引用の数で、引用全体の中の割合ではない。2026-11-18 に、Perplexity の API でも探した。Perplexity の答えの文は載せず、出てきた URL の元のページを取得して、引用の文を写しで確かめたものだけを足した。robots.txt で拒否されるページは取得していない。2026-11-20 の週1回の巡回で、記録 SH-C1・ST-D1・SK-C1・ST-C1 の問いを足して同じ方法で探した（R066）。</li>'
            f'<li>型は、元の文・引用の文・定義だけを渡して、二つの別系統の AI（GPT / Codex と Gemini）がそれぞれ付けた（H037）。二つの型が一致したものだけを載せ、一致しなかったものは「判定が分かれた」として両方の判定を書く。型の明らかな作例を2つ混ぜ、両方正答だった回（{D["round"]}）を採った。判定できなかったものは「判定が分かれた」とし、人は判定しない。NK-K1 は、元の資料の文に調査時期と「認知症傾向」の定義を含めずに渡していたため、含めてやり直した（R031）。その回の判定で R029・R030 の判定を置き換えた。</li>'
            f'<li>引いたページは sha256 を付けて保存し、保存された写し（Wayback）の有無を記した。いま取得できないページはその旨を書いた。</li>'
            f'<li>引いた側の意図を推測せず、媒体の評価をしない。訂正の依頼もしない。言い回しの比較は15字以内、引用の文は一つの記事から一か所（報道は30字程度、公的文書・論文は一文まで）に限る。</li></ul>')

def guide_box(lang='ja'):
    # 点検 #29・#39（2026-11-20）：例に引かれ方の表の判定（型・判定が分かれた）と版の名を付け、元の文を一か所（処遇効果が示唆された）に揃える。2022年版は元の文が違うため別に書く
    r = BY['YK-C1']; cs = sorted([c for c in r['cites'] if c['kind'] == '公的文書'], key=lambda c: c['date'])
    p0 = sorted({c['src_phrase'] for c in cs}, key=lambda x: -sum(1 for c in cs if c['src_phrase'] == x))[0]
    main = [c for c in cs if c['src_phrase'] == p0]; other = [c for c in cs if c['src_phrase'] != p0]
    import ast
    def tys(c, en):
        t = ast.literal_eval(c['types']) if isinstance(c['types'], str) else c['types']
        return '、'.join((TYPE_EN.get(x, x) if en else x) for x in t) if not en else ', '.join(TYPE_EN.get(x, x) for x in t)
    if lang == 'en':
        rows = ''.join(f'<li>{den(c["date"])} · <span lang="ja">{e(c["media"])}「{mk(c["cite_phrase"])}」</span> — judgment: {e(tys(c, True))}</li>' for c in main)
        oth = ''.join(f'<li>{den(c["date"])} · <span lang="ja">{e(c["media"])}</span> cites a different sentence of the source (<span lang="ja">「{mk(c["src_phrase"])}」</span>) — judgment: {e(tys(c, True))}</li>' for c in other)
        return (f'<h2>How figures travel</h2><div class="box"><p class="kick">Stronger wording, within government documents</p>'
                f'<p>The October 2022 summary of the effectiveness study of programmes for drug offenders says <span lang="ja">「{mk(p0)}」</span> (suggested). {len(main)} editions of the White Paper on Recidivism Prevention cite it as follows. The judgment is the type given in <a href="citations.html">How sources are cited</a>: shown only where two independent AIs agreed, otherwise “No verdict”.</p><ul>{rows}</ul>'
                + (f'<p class="muted">Also:</p><ul>{oth}</ul>' if oth else '') +
                f'<p class="muted">(“recognised”. Record <a href="records/YK-C1.html">YK-C1</a>. Other examples: <a href="citations.html">How sources are cited</a>.)</p></div>')
    rows = ''.join(f'<li>{dja(c["date"])}　{e(c["media"])}「{mk(c["cite_phrase"])}」（判定：{e(tys(c, False))}）</li>' for c in main)
    oth = ''.join(f'<li>{dja(c["date"])}　{e(c["media"])}は元の別の文（「{mk(c["src_phrase"])}」）を引く（判定：{e(tys(c, False))}）</li>' for c in other)
    return (f'<h2>数字の伝わり方</h2><div class="box"><p class="kick">公的文書の中で言い方が強まる</p>'
            f'<p>薬物事犯者に対するプログラムの効果検証の概要（令和4年10月）は「{mk(p0)}」と書く。再犯防止推進白書の {len(main)} つの版は、これを次のように引く。判定は<a href="citations.html">引かれ方</a>の型で、二つの AI の判定が一致したものだけ型を書き、一致しなかったものは「判定が分かれた」とする。</p><ul>{rows}</ul>'
            + (f'<p class="muted">このほか：</p><ul>{oth}</ul>' if oth else '') +
            f'<p class="muted">（記録 <a href="records/YK-C1.html">YK-C1</a>。ほかの例は<a href="citations.html">引かれ方</a>。）</p></div>')

# ---- AI に聞いたとき（H036）
LA_P = os.path.join(R, 'publish/llm_answers.json')
LA = json.load(open(LA_P)) if os.path.exists(LA_P) else {'runs': {}}
COLS = ['同じ', '値が違う', '量が置き換わる', '言い方が強まる', '限定が落ちる', '判定が分かれた']
COND_EN = {'検索なし': 'Without search', '検索あり': 'With search (Perplexity)', '原文を渡す': 'Given the source text'}
import sys as _sys
_sys.path.insert(0, os.path.join(R, 'checks/llm_probe'))
try:
    import h036_spec as _H
except Exception:
    _H = None
def ai_block(rec, lang='ja', T=None):
    runs = [(d, r) for d, r in sorted(LA['runs'].items()) if rec in r['records']]
    if not runs or _H is None: return ''
    en, t, E = _fns(lang, T)
    d, run = runs[-1]; x = run['records'][rec]
    out = []
    for cond in ('検索なし', '検索あり', '原文を渡す'):
        rows = [r for r in x['table'] if r['cond'] == cond]
        if not rows: continue
        th = ''.join(f'<th>{e(TYPE_EN[c] if en else c)}</th>' for c in COLS)
        tr = ''.join(f'<tr><td>{e(r["model"])}</td><td>{r["n"]}</td>' + ''.join(f'<td>{r[c] or ""}</td>' for c in COLS) + f'<td>{r["元にない数値"] or ""}</td></tr>' for r in rows)
        ex = x['examples'].get(cond)
        exh = ''
        if ex:
            ty = ''.join(f'<span class="ty">{e(TYPE_EN[k] if en else k)}</span>' for k in (ex['types'] or ['判定が分かれた']))
            exh = (f'<p class="muted">{"Example (one answer picked at random)" if en else "例（乱数で選んだ一件）"}：{e(ex["model"])} · {ex["prompt"]}</p>'
                   f'<p class="ph"><span lang="ja">「{e(ex["excerpt"])}…」</span></p><p>{ty}</p>')
        name = COND_EN[cond] if en else cond
        nn = 'Figures not in the source' if en else '元にない数値'
        out.append(f'<h3>{e(name)}</h3><table><tr><th>{"Model" if en else "モデル"}</th><th>{"Answers" if en else "答え"}</th>{th}<th>{nn}</th></tr>{tr}</table>{exh}')
    qs = ''.join(f'<li lang="ja">{e(q)}</li>' for q in _H.A[rec])
    bs = '、'.join(_H.B.values())
    if en:
        intro = (f'<p class="muted">On {den(d)} we asked the main AI models about this source, {run["reps"]} times per question, with “answer in 300 characters or less”. The types were assigned separately by two independent AIs (GPT / Codex and Gemini) without being shown the model names or conditions (round {x["round"]}; both judged the two dummy answers correctly). The table counts a type only when both assigned it. The two agreed on {x.get("agree")}% of the answers; answers on which they disagreed, or both found no verdict, are counted under “No verdict”. One answer can carry more than one type, so the columns do not add up to the number of answers. '
                 f'This records the answers only; it does not show how the models were trained. The answers were collected by Claude (Anthropic), and Claude models are among those compared. Model versions are as of that date; the same questions are asked again every three months and changes are added below.</p>'
                 f'<p class="muted">Questions without / with search (in Japanese):</p><ul>{qs}</ul><p class="muted">Given the source text: a three-sentence summary for general readers, and a news headline with a lead paragraph.</p>')
        return f'<h2>When asked, AI models answer</h2>{intro}{"".join(out)}<h3>Changes since the previous round</h3><p class="muted">First round ({den(d)}).</p>'
    intro = (f'<p class="muted">{dja(d)}に、主な AI にこの資料のことを尋ねた（各問い{run["reps"]}回、「300字以内」）。型は、モデル名と条件を伏せて、二つの別系統の AI（GPT / Codex と Gemini）がそれぞれ付けた（{x["round"]}、どちらも作例2つは正答）。表の型は、二つがともに付けたものだけを数える。二つの型が一致した答えは {x.get("agree")}％で、一致しなかった答えと、ともに判定できないとした答えは「判定が分かれた」に数える。一つの答えに型が複数付くことがあり、表の列の和は答えの数と合わない。'
             f'答えの記録で、学習の影響は扱わない。答えを集めたのは Claude（Anthropic）で、比べるモデルに Claude を含む。モデルの版はその日のもの。同じ問いで3か月に1回やり直し、変化を下に追記する。</p>'
             f'<p class="muted">検索なし・検索ありの問い：</p><ul>{qs}</ul><p class="muted">原文を渡すとき：{e(bs)}（原文は上の「元の資料の原文」と同じ内容）。</p>')
    return f'<h2>AI に聞いたとき</h2>{intro}{"".join(out)}<h3>前の回からの変化</h3><p class="muted">初回（{dja(d)}）。</p>'
