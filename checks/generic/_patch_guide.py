p = 'site/build_site.py'
s = open(p).read()
JA = r'''# ---- はじめての方へ（1ページで意味が伝わる案内）
FBY = {f['id']: f for f in F}
GUIDE_EX = [('MK-I1', '版によって数が違い、説明がない', '同じ年の同じ数が、刊行の年によって違う。どの版を引くかで値が変わる。'),
            ('HK-A7', '訂正が公開中のファイルに入っていない', '正誤表で訂正を告知した後も、ダウンロードできる表は訂正前の値のまま。'),
            ('BV-P1', '概要が報告書の結果より強く書かれている', '1枚の概要と報告書の本文で、効果の書き方が違う。'),
            ('YK-C1', '比べ方によって読み方が変わる', '同じデータでも、どの群を比べるかで効果の有無の読み方が変わる。')]
assert all(STATE(FBY[i]) == 'sup' for i, _, _ in GUIDE_EX), 'はじめての方への例は別系統で支持された記録に限る'
_gx = ''.join(f'<div class="box"><p class="kick">{e(t)}</p><h3><a href="records/{i}.html">{e(FBY[i]["見出し"])}</a></h3><p class="muted">{e(w)}（{i}・{LV[FBY[i]["影響"]][0]}・{ST_JA["sup"]}）</p></div>' for i, t, w in GUIDE_EX)
page('guide.html', 'はじめての方へ', f"""<h1>はじめての方へ</h1>
<p class="lead">URAZUKE は、日本の犯罪・司法・精神医療・福祉の公的統計を、コードで照合し、食い違いを記録する場所です。</p>
<ul><li>国の統計の数字を、同じ資料の別の表、別の年の版、別の資料と突き合わせます。</li>
<li>合わないところを「記録」として残し、根拠（ファイル・頁・セル）と計算のスクリプトを公開します。</li>
<li>照合と記録は AI（Claude）が行い、別の会社の AI（GPT）が、結論を伏せた手順で反証を試みます。</li></ul>
<div class="nums lead"><div><b>{NSTAT_IN}</b><span>検証した統計（重点領域）</span></div><div><b>{NC:,}</b><span>照合した数値の組</span></div><div><b>{NM:,}</b><span>そのうち一致</span></div><div><b>{len(INSCOPE)}</b><span>記録（うち別系統で支持 {d2}）</span></div></div>
<p class="muted">ほとんどの数字は合っています。合っていたことも、記録と同じ手順で残しています（<a href="index.html">トップ</a>の「確かめたこと」）。</p>
<h2>見つかるものの例</h2><div class="grid3">{_gx}</div>
<h2>記録の読み方</h2>
<table><tr><th>項目</th><th>意味</th></tr>
<tr><td>影響</td><td>大：報告書の結論・政策の指標・全国の総数に関わる。中：版・資料・表の間で値が食い違う。小：副次的なファイルだけの不備。</td></tr>
<tr><td>確実さ</td><td>確定：資料の上で確かめられた事実。推定：資料から導いたが確定できない部分。要照会：担当部署に尋ねないと分からない部分。</td></tr>
<tr><td>確認の状態</td><td>{ST_JA['sup']}：別の会社の AI が、反証の手順で同じ結論に達した。{ST_JA['pre']}・{ST_JA['rew']}：その手順をまだ終えていない。{ST_JA['fin']}：手順を尽くしても判定できなかった（理由を記録に書く）。</td></tr></table>
<h2>URAZUKE がしないこと</h2>
<ul><li>作成者の意図や事情を推測しません。記録するのは、資料の上の事実だけです。</li>
<li>統計や政策の良し悪しを評価しません。</li>
<li>人が記録の内容を判断して取捨しません。手順は<a href="process.html">進め方</a>に固定し、変えたときは<a href="method.html">方法</a>に記します。</li></ul>
<h2>引用・取材の方へ</h2>
<ul><li>引用するときは、記録の ID（例：MK-I1）、ページの URL、見た日付を添えてください。記録は訂正されることがあり、訂正はすべて<a href="errors.html">訂正の記録</a>に残します。</li>
<li>担当部署への照会と回答は、<a href="inquiries.html">照会</a>に全文を載せます（いまは照会の前です）。</li>
<li>計算は <a href="https://github.com/hirokifukui/urazuke">GitHub</a> のスクリプトで、同じ資料から誰でもやり直せます。</li>
<li>問い合わせ：<a href="mailto:contact@urazuke.org">contact@urazuke.org</a></li></ul>""")
'''
EN = r'''# In brief (one-page guide)
_gx_en = ''.join(f'<div class="box"><p class="kick">{t}</p><h3><a href="records/{i}.html">{inline(ftr(FBY[i], "見出し"))}</a></h3><p class="muted">{w} ({i} · {LV_EN[FBY[i]["影響"]][0]} · {ST_EN["sup"]})</p></div>' for i, t, w in [
    ('MK-I1', 'The same figure differs between editions, without a note', 'The same figure for the same year differs by the year of publication. The value depends on which edition is cited.'),
    ('HK-A7', 'A published correction is not in the downloadable file', 'After a correction notice, the downloadable table still holds the value before correction.'),
    ('BV-P1', 'A summary states the result more strongly than the report', 'The one-page summary and the report body describe the effect differently.'),
    ('YK-C1', 'The reading changes with the comparison', 'With the same data, whether an effect appears depends on which groups are compared.')])
page_en('guide.html', 'In brief', f"""<h1>In brief</h1>
<p class="lead">URAZUKE checks Japan’s official statistics on crime, justice, psychiatric care and welfare with code, and records the discrepancies it finds.</p>
<ul><li>Figures in government statistics are compared with other tables in the same publication, with other editions, and with other sources.</li>
<li>Where they do not agree, a “record” is kept, with its basis (file, page, cell) and the scripts used for the calculation.</li>
<li>The checking and recording are done by an AI (Claude); an AI from another company (GPT) then tries to refute each record without being shown the conclusion.</li></ul>
<div class="nums lead"><div><b>{NSTAT_IN}</b><span>statistics verified (focus areas)</span></div><div><b>{NC:,}</b><span>pairs of figures compared</span></div><div><b>{NM:,}</b><span>of which agree</span></div><div><b>{len(INSCOPE)}</b><span>records ({d2} supported by an independent model)</span></div></div>
<p class="muted">Most figures agree. What agreed is kept by the same procedure as the records (“What was checked” on the <a href="index.html">home page</a>).</p>
<h2>Examples of what is found</h2><div class="grid3">{_gx_en}</div>
<h2>How to read a record</h2>
<table><tr><th>Item</th><th>Meaning</th></tr>
<tr><td>Impact</td><td>High: affects a report’s conclusion, a policy indicator or a national total. Medium: values disagree between editions, sources or tables. Low: a defect only in a secondary file.</td></tr>
<tr><td>Certainty</td><td>Confirmed: a fact checked against the source. Inferred: derived from the source but not confirmable. Inquiry needed: can only be settled by asking the responsible office.</td></tr>
<tr><td>Verification status</td><td>{ST_EN['sup']}: an AI from another company reached the same conclusion in a refutation check. {ST_EN['pre']} / {ST_EN['rew']}: that check is not yet complete. {ST_EN['fin']}: the check could not reach a verdict after the full procedure (the reason is written in the record).</td></tr></table>
<h2>What URAZUKE does not do</h2>
<ul><li>It does not guess at the intentions or circumstances of those who produced a statistic. Records state only facts found in the sources.</li>
<li>It does not judge whether a statistic or a policy is good or bad.</li>
<li>No person selects or drops records by their content. The procedure is fixed in <a href="process.html">Process</a>, and changes are noted in <a href="method.html">Methods</a>.</li></ul>
<h2>For citation and press enquiries</h2>
<ul><li>When citing, please give the record ID (for example MK-I1), the page URL and the date you viewed it. Records can be corrected; every correction is kept in <a href="errors.html">Corrections</a>.</li>
<li>Inquiries to the responsible offices and their replies are published in full under <a href="inquiries.html">Inquiries</a> (no inquiries have been sent yet).</li>
<li>Anyone can redo the calculations from the same sources with the scripts on <a href="https://github.com/hirokifukui/urazuke">GitHub</a>.</li>
<li>Contact: <a href="mailto:contact@urazuke.org">contact@urazuke.org</a></li></ul>""")
'''
a = '# ---- 記録一覧'
assert s.count(a) == 1 and 'guide.html' not in s
s = s.replace(a, JA + a)
i = s.index("page_en('index.html'"); j = s.index('# 記録の一覧', i)
j = s.rindex('\n', 0, j) + 1
s = s[:j] + EN + s[j:]
s = s.replace("NAV = [('records/', '記録'),", "NAV = [('guide.html', 'はじめに'), ('records/', '記録'),", 1)
s = s.replace("NAV_EN = [('records/', 'Records'),", "NAV_EN = [('guide.html', 'In brief'), ('records/', 'Records'),", 1)
s = s.replace('<p class="note">スクリプト、取得した資料の一覧', '<p class="note"><a href="guide.html">はじめての方へ（1ページの案内）</a></p>\n<p class="note">スクリプト、取得した資料の一覧', 1)
open(p, 'w').write(s)
print('ok')
