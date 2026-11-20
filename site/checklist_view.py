"""引く前の確かめ方（1ページ、日英）。2026-11-18、アイデア6。
各項目の例は「別系統で支持」の記録に限る（build_site.py で assert）。"""
from html import escape as e

# (見出し, 確かめること, 例の記録ID, 引かれ方の型)
ITEMS = [
 ('正誤表と訂正のお知らせ', '引く版に正誤表・訂正のお知らせが出ていないかを見る。訂正は、ダウンロードできる表や全体版 PDF・Web 版に入っていないことがある。', ['HK-A7', 'SH-A1', 'SH-A2'], '訂正が入っていない'),
 ('版による違い', '同じ年の同じ数を、別の年の版でも見る。版によって値が違い、説明のないことがある。どの版の値かを書く。', ['MK-I1', 'SH-B1'], '値が違う'),
 ('数える範囲の変更', '表の注を読む。法改正や数え方の変更で数える範囲が変わると、「最多」「増加」は範囲の違う数どうしの比較になる。', ['ST-D1', 'ST-I2'], '限定が落ちる'),
 ('概要と本文', '1枚の概要・白書の要約だけで引かない。報告書の本文と表で、同じ結論が同じ強さで書かれているかを見る。', ['BV-P1', 'SH-C1'], '言い方が強まる'),
 ('何の割合か', '再犯率なら、全ての犯罪か罪種別か、何年以内か、誰を分母にしたかを書く。別の量（ハザード比、群の比較）を「再犯率」「低下」と言い換えない。', ['SH-C1', 'NK-K1'], '量が置き換わる'),
 ('比べ方と但し書き', '何と何を比べた差かを確かめる。報告書の同じ箇所にある但し書き（差が有意でなかった群、精度の限界、統制していない条件）を落とさない。有意でないことは効果がないことを示さない。', ['YK-C1', 'KP-C1'], '限定が落ちる'),
 ('出典の書き方', '資料名・版・頁（表番号やセル）・取得日を書く。Web の資料は差し替わることがある。写しを手元に残す。', [], ''),
]
ITEMS_EN = [
 ('Errata and correction notices', 'Check whether errata or a correction notice has been issued for the edition you cite. Corrections are not always reflected in the downloadable tables, the full PDF or the web edition.'),
 ('Differences between editions', 'Look up the same figure for the same year in other editions. Values can differ between editions without a note. State which edition the value comes from.'),
 ('Changes in what is counted', 'Read the notes to the table. When a legal amendment or a change in counting widens or narrows what is counted, a "record high" or an "increase" compares counts with different scopes.'),
 ('Summary and report body', 'Do not cite from a one-page summary or a white paper summary alone. Check that the report body and tables state the same conclusion with the same strength.'),
 ('What the rate is a rate of', 'For a reoffending rate, state whether it covers all offences or one type, the follow-up period and the denominator. Do not restate a different quantity (a hazard ratio, a comparison of groups) as a "reoffending rate" or a "fall".'),
 ('Comparisons and qualifications', 'Check which groups the difference is between. Keep the qualifications stated at the same place in the report (groups without a significant difference, limits on precision, conditions not controlled). A non-significant result does not show that there is no effect.'),
 ('How to give the source', 'Give the title, edition, page (table number or cell) and the date you obtained it. Documents on the web can be replaced. Keep a copy.'),
]


def ids():
    return sorted({i for _, _, xs, _ in ITEMS for i in xs})


def body(lang, FBY, title_of, type_label=None):
    en = lang == 'en'
    rows = []
    for n, (h, w, xs, ty) in enumerate(ITEMS):
        if en: h, w = ITEMS_EN[n]
        ex = '、'.join(f'<a href="records/{i}.html">{i}</a>' for i in xs) if not en else ', '.join(f'<a href="records/{i}.html">{i}</a>' for i in xs)
        tl = (type_label(ty) if (en and ty and type_label) else ty)
        meta = ''
        if xs: meta = (f'Examples: {ex}' if en else f'例：{ex}')
        if ty: meta += (f' · Citation type: {e(tl)}' if en else f'・引かれ方の型：{e(tl)}')
        rows.append(f'<li><p><b>{e(h)}</b><br>{e(w)}</p>' + (f'<p class="muted">{meta}</p>' if meta else '') + '</li>')
    lst = '<ol class="checklist">' + ''.join(rows) + '</ol>'
    if en:
        return (f'<h1>Before citing a statistic</h1><p class="lead">Seven checks drawn from the records and from how their sources are cited. Each example is a record supported by an independent model.</p>{lst}'
                '<p class="muted">The citation types are defined on <a href="citations.html">How sources are cited</a>. To cite URAZUKE itself, see <a href="guide.html">In brief</a>.</p>')
    return (f'<h1>引く前に確かめること</h1><p class="lead">記録と、その資料の引かれ方から作った7項目です。例はどれも、別系統で支持された記録です。</p>{lst}'
            '<p class="muted">引かれ方の型の定義は<a href="citations.html">引かれ方</a>にあります。URAZUKE を引くときは<a href="guide.html">はじめての方へ</a>を見てください。</p>')


CSS = '.checklist li{margin:0 0 1em}.checklist p{margin:.2em 0}'
