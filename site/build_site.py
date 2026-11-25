"""URAZUKE サイト（草案・非公開）を静的 HTML で作る。データは publish/ と results/ から読む。出力は site/out/。"""
import json, os, re, shutil, html, glob
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R, 'site', 'out')
SENT = json.load(open(os.path.join(R, 'publish/inquiry_sent.json'))) if os.path.exists(os.path.join(R, 'publish/inquiry_sent.json')) else {'date': '—', 'deadline': '—'}
_vl = os.path.join(OUT, '.vercel', 'project.json'); _keep = open(_vl).read() if os.path.exists(_vl) else None
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)
if _keep: os.makedirs(os.path.dirname(_vl)); open(_vl, 'w').write(_keep)
F = json.load(open(os.path.join(R, 'publish/findings.json')))
e = html.escape
def inline(s):
    s = e(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2">\1</a>', s)
    return s
def md(t):
    out, lst, tbl = [], 0, []
    lines = t.split('\n')
    def flush_tbl():
        nonlocal tbl
        if not tbl: return
        rows = [r for r in tbl if not re.match(r'^\|\s*-', r)]
        h = '<table>'
        for i, r in enumerate(rows):
            cells = [c.strip() for c in r.strip().strip('|').split('|')]
            tag = 'th' if i == 0 else 'td'
            h += '<tr>' + ''.join(f'<{tag}>{inline(c)}</{tag}>' for c in cells) + '</tr>'
        out.append(h + '</table>'); tbl = []
    for ln in lines:
        if ln.startswith('|'): tbl.append(ln); continue
        flush_tbl()
        m = re.match(r'^(#{1,4})\s+(.*)', ln)
        if m:
            while lst: out.append('</ul>'); lst -= 1
            n = len(m.group(1)) + 1; out.append(f'<h{n}>{inline(m.group(2))}</h{n}>'); continue
        m = re.match(r'^(\s*)[-*]\s+(.*)', ln) or re.match(r'^(\s*)\d+\.\s+(.*)', ln)
        if m:
            depth = len(m.group(1)) // 2 + 1
            while lst < depth: out.append('<ul>'); lst += 1
            while lst > depth: out.append('</ul>'); lst -= 1
            out.append(f'<li>{inline(m.group(2))}</li>'); continue
        while lst: out.append('</ul>'); lst -= 1
        if ln.strip() in ('---', ''): continue
        out.append(f'<p>{inline(ln)}</p>')
    flush_tbl()
    while lst: out.append('</ul>'); lst -= 1
    return '\n'.join(out)
CSS = """
:root{--ink:#1f2328;--sub:#5d646b;--line:#d9dde1;--bg:#fbfbf9;--acc:#2f4f6f;--paper:#fff}
*{box-sizing:border-box}html{font-size:16px}body{margin:0;background:var(--bg);color:var(--ink);font-family:"Hiragino Sans","Noto Sans JP",system-ui,sans-serif;line-height:1.85;letter-spacing:.02em}
a{color:var(--acc);text-decoration:none;border-bottom:1px solid rgba(47,79,111,.25)}a:hover{border-color:var(--acc)}
.draft{background:#3a3a3a;color:#f5f5f0;text-align:center;font-size:.8rem;padding:.35rem;letter-spacing:.08em}
header.site{max-width:1040px;margin:0 auto;padding:2.2rem 1.5rem 1rem;display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:1rem}
.logo{font-family:"Hiragino Mincho ProN","Noto Serif JP",serif;font-size:1.5rem;letter-spacing:.35em;color:var(--ink);border:0;display:inline-flex;align-items:center;gap:.7rem}.logo .mark{width:1.55rem;height:1.55rem;flex:none}
nav a{margin-left:1.4rem;font-size:.9rem;color:var(--sub);border:0}nav a:hover{color:var(--ink)}
main{max-width:1040px;margin:0 auto;padding:1rem 1.5rem 5rem}
h1,h2,h3{font-family:"Hiragino Mincho ProN","Noto Serif JP",serif;font-weight:600;letter-spacing:.06em}
h1{font-size:1.7rem;margin:2.2rem 0 1.2rem}h2{font-size:1.25rem;margin:2.6rem 0 .8rem;padding-bottom:.4rem;border-bottom:1px solid var(--line)}h3{font-size:1.05rem;margin:1.8rem 0 .5rem}h4,h5{font-size:.95rem;margin:1.4rem 0 .4rem}
.hero{padding:4.5rem 0 3rem;border-bottom:1px solid var(--line)}
.hero p.lead{font-family:"Hiragino Mincho ProN","Noto Serif JP",serif;font-size:1.55rem;line-height:1.9;margin:0 0 1.2rem;max-width:34em}
.hero p.idea{font-family:"Hiragino Mincho ProN","Noto Serif JP",serif;font-size:1.05rem;line-height:1.95;max-width:40em;margin:0 0 1.4rem;padding-left:1rem;border-left:2px solid var(--line)}.hero p.note{color:var(--sub);font-size:.92rem;margin:0 0 .6rem}
.nums{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:0;margin:2.2rem 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.nums div{padding:1.2rem 1rem}.nums.lead b{font-size:2.5rem}.nums.big b{font-size:1.5rem}h2.sub{font-size:1rem;color:var(--sub);border:0;margin:2rem 0 .2rem}.nums b{display:block;font-family:"Hiragino Mincho ProN",serif;font-size:1.9rem;font-weight:500}.nums span{color:var(--sub);font-size:.82rem}
table{border-collapse:collapse;width:100%;font-size:.88rem;margin:1rem 0;background:var(--paper)}td:first-child,#t td:last-child,#t th:last-child{white-space:nowrap}th,td{border-bottom:1px solid var(--line);padding:.55rem .6rem;text-align:left;vertical-align:top}th{color:var(--sub);font-weight:500;font-size:.8rem;background:#f4f5f3}
.tag{display:inline-block;font-size:.75rem;padding:.05rem .55rem;border:1px solid currentColor;border-radius:2px;white-space:nowrap}
.lv3{color:#7a2e1f;font-weight:600;white-space:nowrap}.lv2{color:#8a6d2f;font-weight:600;white-space:nowrap}.lv1{color:#7d858c;white-space:nowrap}.k-誤り{color:#6b3b2a}.k-不整合{color:#5b4a1f}.k-欠落{color:#3d5a3a}.k-説明のない改訂{color:#2f4f6f}.k-設計上の問題{color:#4b3f66}.k-照会事項{color:#555}.k-引かれ方{color:#6a4a2a}
.card{background:var(--paper);border:1px solid var(--line);padding:1.6rem 1.8rem;margin:1.2rem 0}
.card dl{display:grid;grid-template-columns:11em 1fr;gap:.55rem 1.2rem;margin:0}.card dt{color:var(--sub);font-size:.85rem}.card dd{margin:0}
.head{font-family:"Hiragino Mincho ProN",serif;font-size:1.35rem;margin:.5rem 0 0}.qt{margin:0 0 .6rem;font-size:.85rem;line-height:1.6;word-break:break-all}.concl{font-family:"Hiragino Mincho ProN","Noto Serif JP",serif;font-size:1.2rem;line-height:1.9;border-left:3px solid var(--acc);padding:.2rem 0 .2rem 1.2rem;margin:1.5rem 0}
.filters{display:flex;gap:.6rem;flex-wrap:wrap;margin:1rem 0}.filters select,.filters input{font:inherit;font-size:.85rem;padding:.35rem .5rem;border:1px solid var(--line);background:#fff}
.muted{color:var(--sub);font-size:.88rem}.grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1.2rem;margin:1.5rem 0}
.box{background:var(--paper);border:1px solid var(--line);padding:1.2rem 1.4rem}.box h3{margin-top:0}
.prose{max-width:46em}.prose p,.prose li{font-size:.95rem}.prose table{font-size:.82rem}
footer{border-top:1px solid var(--line);color:var(--sub);font-size:.8rem;padding:2rem 1.5rem;text-align:center}
code{font-family:ui-monospace,Menlo,monospace;font-size:.85em;background:#f0f1ee;padding:.05rem .3rem}
.tierh{border:0;margin:2.4rem 0 .4rem}.tiers{display:grid;grid-template-columns:1.25fr 1fr .8fr;gap:1.2rem;margin:1rem 0 .6rem}
.tier{background:var(--paper);border:1px solid var(--line);border-top:4px solid var(--ink);padding:1.2rem 1.3rem}
.tier.t3{border-top-color:#7a2e1f}.tier.t2{border-top-color:#8a6d2f}.tier.t1{border-top-color:#9aa1a7}
.kick{font-size:.75rem;letter-spacing:.2em;font-weight:600}.t3 .kick{color:#7a2e1f}.t2 .kick{color:#8a6d2f}.t1 .kick{color:#7d858c}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:1.2rem;margin:1.5rem 0}@media(max-width:640px){.grid2{grid-template-columns:1fr}}.box .kick{color:var(--sub);letter-spacing:.05em;margin:0 0 .4rem}
.big{font-family:"Hiragino Mincho ProN",serif;line-height:1;margin:.5rem 0 .2rem}.big b{font-weight:500}.big span{font-size:.9rem;margin-left:.3rem;color:var(--sub)}
.t3 .big b{font-size:3.6rem;color:#7a2e1f}.t2 .big b{font-size:2.8rem}.t1 .big b{font-size:2.2rem;color:#5d646b}
.tier h3{margin:.4rem 0 .2rem;font-size:1.1rem}.t3 h3{font-size:1.25rem}
.tsub{color:var(--sub);font-size:.8rem;margin:0 0 .8rem;line-height:1.6}.tier ul{list-style:none;margin:0;padding:0}
.tier li{border-top:1px solid var(--line);padding:.6rem 0;font-size:.88rem;line-height:1.6}.tier li a{border:0;color:var(--ink);display:block}.tier li a:hover{color:var(--acc)}
.t3 li{font-size:.95rem}.stages{display:flex;align-items:stretch;gap:.4rem;margin:2.4rem 0 .6rem;flex-wrap:wrap}.stg{flex:1 1 0;min-width:120px;background:var(--paper);border:1px solid var(--line);border-top:3px solid var(--acc);padding:.8rem .9rem;display:flex;flex-direction:column}.cbranch{display:flex;align-items:flex-start;gap:.3rem;margin:.1rem 0 .3rem 30%}.cba{font-size:1.6rem;line-height:1;color:var(--sub);padding-top:.4rem}.stg.cb{flex:0 1 460px;border-top-color:var(--sub)}.cbex{margin-left:calc(30% + 1.9rem)}@media(max-width:700px){.cbranch{margin-left:0}.cbex{margin-left:0}}.stg.s0{flex:1.6 1 0;border-top-color:var(--ink)}.stg.s9{flex:1.4 1 0;border-top-color:#3d5a3a}.stg .sl{font-size:.75rem;letter-spacing:.08em;color:var(--sub)}.stg b{font-family:"Hiragino Mincho ProN",serif;font-size:2rem;font-weight:500;line-height:1.3}.stg .su{font-size:.75rem;color:var(--sub);line-height:1.5}.stg .sd{font-size:.8rem;color:var(--sub);margin-top:.2rem}.stg .sd b{font-size:1.4rem;margin-right:.3rem;color:var(--ink)}.sa{align-self:center;color:var(--sub);font-size:1.4rem}table.rt tr.rsep td{background:#f4f5f3;color:var(--sub);font-size:.78rem;letter-spacing:.06em}@media(max-width:860px){.sa{display:none}.stg{min-width:45%}}.vbox h3{margin:0}.vbox .muted{margin:.2rem 0}.vnum{font-family:"Hiragino Mincho ProN",serif;margin:.9rem 0 .2rem;color:var(--sub);font-size:.9rem}.vnum b{font-size:2.2rem;font-weight:500;color:var(--ink);margin-right:.2rem}.vres{margin:.1rem 0 .7rem;font-weight:600;color:var(--ink)}.tier li.tsep{font-size:.72rem;color:var(--sub);letter-spacing:.08em;border-top:1px dashed var(--line);padding-top:.9rem}.tier li.pend a{color:var(--sub)}.tid{display:block;font-size:.72rem;color:var(--sub);letter-spacing:.05em}.tmeta{display:block;font-size:.72rem;color:var(--sub)}
@media(max-width:860px){.tiers{grid-template-columns:1fr}}
.crawl{border-bottom:1px solid var(--line);background:#f3f4f1}.cin{max-width:1040px;margin:0 auto;padding:.55rem 1.5rem;display:flex;flex-wrap:wrap;align-items:baseline;gap:.35rem .7rem;font-size:.8rem;color:var(--sub)}
.crawl b{font-weight:600;color:var(--ink);font-feature-settings:"palt"}.cl{letter-spacing:.08em}.sep{width:1px;height:.8rem;background:var(--line);margin:0 .3rem;align-self:center}
.dot{width:.5rem;height:.5rem;border-radius:50%;background:#3d6b4f;align-self:center;box-shadow:0 0 0 0 rgba(61,107,79,.5);animation:pl 2.4s infinite}
.dot.off{background:#9aa1a7;animation:none}@keyframes pl{0%{box-shadow:0 0 0 0 rgba(61,107,79,.45)}70%{box-shadow:0 0 0 .45rem rgba(61,107,79,0)}100%{box-shadow:0 0 0 0 rgba(61,107,79,0)}}
table.crn{width:100%;border-collapse:collapse;margin:1rem 0 .6rem;text-align:center}table.crn th{font-size:.75rem;font-weight:400;color:var(--sub);padding:.2rem .3rem}table.crn td{font-size:1.5rem;font-weight:700;padding:.1rem .3rem;border-top:1px solid var(--line)}table.crn td:last-child{font-size:1rem}.crflow{font-size:.9rem;margin:.4rem 0 .8rem}.crscope{font-size:.9rem;padding-left:1.1rem;margin:.4rem 0}.crscope li{margin:.25rem 0}@media(max-width:600px){table.crn th{font-size:.65rem}table.crn td{font-size:1.1rem}table.crn td:last-child{font-size:.75rem}}.cn{margin-left:auto;font-size:.75rem}@media(max-width:860px){.cn{margin-left:0;width:100%}}
@media(max-width:640px){.card dl{grid-template-columns:1fr}nav a{margin:0 1rem 0 0}.hero p.lead{font-size:1.25rem}}
"""
# スマートフォン（幅640px以下）：主な表はカード型の縦並び（各セルに項目名）、それ以外の表は表だけを横にスクロール（r26）
CSS += """
@media(max-width:640px){
header.site{padding:1.2rem 1rem .6rem;gap:.5rem}nav{display:flex;flex-wrap:wrap;gap:.1rem 1rem}nav a{margin:0;white-space:nowrap}.filters select,.filters input{max-width:100%;min-width:0}main{padding:.6rem 1rem 4rem}.cin{padding:.5rem 1rem}
h1{font-size:1.4rem;margin:1.4rem 0 .8rem}h2{font-size:1.1rem;margin:2rem 0 .6rem}
.nums.lead b{font-size:1.8rem}.nums b{font-size:1.5rem}
.stages{gap:.35rem}.stg{min-width:0;flex:1 1 28%;padding:.5rem .6rem}.stg.s0,.stg.s9{flex:1 1 100%}.stg b{font-size:1.45rem}.stg .sl{font-size:.68rem;line-height:1.4}
td:first-child{white-space:normal}td code,th code,.prose code{overflow-wrap:anywhere;word-break:break-all}.prose p,.prose li,.card dd,.qt{overflow-wrap:anywhere}
table:not(.stack){display:block;overflow-x:auto;-webkit-overflow-scrolling:touch}
table.stack,table.stack tbody{display:block;background:none}table.stack tr.hd{display:none}
table.stack tr{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.35rem .8rem;background:var(--paper);border:1px solid var(--line);margin:0 0 .6rem;padding:.6rem .7rem}
table.stack td{display:block;border:0;padding:0;white-space:normal;min-width:0}
table.stack td[data-label]::before{content:attr(data-label);display:block;color:var(--sub);font-size:.68rem;line-height:1.4}
table.stack td.t1{grid-column:1/-1;font-weight:600}table.stack td.t1::before,table.stack td[data-label=""]::before{display:none}
table.stack td.wide{grid-column:1/-1}
table.stack tr.rsep{border:0;background:none;padding:.8rem 0 .2rem;margin:0}table.stack tr.rsep td{display:block;background:none;padding:0;font-weight:600;color:var(--ink)}
}
"""
import citations_view as CV
import checklist_view as CK
CSS += """
.vis{padding:4.2rem 0 2.4rem}
.vis .vlead{font-family:"Hiragino Mincho ProN","Noto Serif JP",serif;font-size:1.7rem;line-height:1.8;margin:0 0 1.4rem;letter-spacing:.06em}
.vis .videa{font-size:1rem;color:var(--sub);max-width:38em;margin:0}
h2.vh{border:0;margin:2.4rem 0 1rem;font-size:1.05rem;color:var(--sub);letter-spacing:.3em}
ol.flow{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(6,1fr);gap:0}
ol.flow li{position:relative;background:var(--paper);border:1px solid var(--line);border-top:3px solid var(--acc);padding:1rem .8rem 1.1rem;margin-right:1.1rem;display:flex;flex-direction:column;gap:.35rem}
ol.flow li:last-child{margin-right:0}
ol.flow li:not(:last-child)::after{content:"";position:absolute;right:-1.05rem;top:50%;width:.9rem;height:.9rem;margin-top:-.45rem;background:var(--acc);clip-path:polygon(0 15%,60% 15%,60% 0,100% 50%,60% 100%,60% 85%,0 85%)}
ol.flow .fn{font-size:.75rem;color:var(--sub);letter-spacing:.1em}
ol.flow b{font-family:"Hiragino Mincho ProN","Noto Serif JP",serif;font-size:1.15rem;letter-spacing:.08em}
ol.flow li span:last-child{font-size:.82rem;color:var(--sub);line-height:1.6}
p.loop{margin:.9rem 0 0;font-size:.9rem;color:var(--sub)}p.loop b{color:var(--acc);font-weight:600}
.why{margin:2.6rem 0 0;padding:1.3rem 1.5rem;border-left:3px solid var(--acc);background:var(--paper)}
.why b{font-family:"Hiragino Mincho ProN","Noto Serif JP",serif;letter-spacing:.08em}.why p{margin:.4rem 0 0;max-width:40em}
.nums.top{margin:2.6rem 0 0}
.entry{margin-top:2.2rem}
.entry .ebox{margin-bottom:0}
a.ebox{display:flex;flex-direction:column;gap:.3rem;background:var(--paper);border:1px solid var(--line);padding:1.3rem 1.4rem;color:var(--ink)}
a.ebox:hover{border-color:var(--acc)}a.ebox b{font-family:"Hiragino Mincho ProN","Noto Serif JP",serif;font-size:1.1rem;color:var(--acc)}a.ebox span{font-size:.88rem;color:var(--sub)}
p.foot{margin-top:2.4rem;font-size:.88rem;color:var(--sub)}
.crawl b.wk{font-weight:600;color:var(--acc)}.crawl a.cmore{margin-left:1rem;font-size:.82rem}
.allx{display:inline-block;margin-top:.15rem;font-size:.72rem;color:#2e6b4a;border:1px solid #9cc5ae;padding:0 .4rem;letter-spacing:.04em}
@media(max-width:820px){ol.flow{grid-template-columns:1fr 1fr 1fr;row-gap:1.1rem}ol.flow li:nth-child(3){margin-right:0}ol.flow li:nth-child(3)::after{display:none}}
@media(max-width:520px){ol.flow{grid-template-columns:1fr;row-gap:1.3rem}ol.flow li{margin-right:0}ol.flow li:not(:last-child)::after{display:block;right:auto;left:50%;top:auto;bottom:-1.15rem;margin:0 0 0 -.45rem;transform:rotate(90deg)}.vis .vlead{font-size:1.3rem}}
"""
# ---- r38：記録の3つの型（区分から機械的に決める）と、各ページの入口の数行・目次
TYPE3 = [('A', '数字が合わない', 'Numbers that do not agree', '同じになるはずの数字が、表どうし・版どうしで合わない。転記のずれや、正誤表の反映漏れを含む。', 'Figures that should be the same differ between tables or editions, including transcription slips and corrections not carried into the files.', ('誤り', '不整合')),
         ('B', '版で変わる・載っていない', 'Changed between editions, or not published', '説明なしに過去の値が変わった、数え方が変わった、判断に必要な数字が載っていない。', 'Past values changed without explanation, the way of counting changed, or figures needed to judge are not published.', ('説明のない改訂', '欠落')),
         ('C', '分析や書き方の論点', 'Questions of analysis or wording', '効果の書き方、群の比べ方、概要と本文の違いなど。数字の誤りではなく、読み方に関わる。', 'How effects are described, how groups are compared, differences between a summary and the report. Not numerical errors, but matters of interpretation.', ('設計上の問題', '照会事項', '引かれ方'))]
def type3(f):
    k = f['区分'].split('（')[0]
    return next(t for t in TYPE3 if k in t[5])
def type_rows(rowfun, fs, en=False, ncol=8):
    out = []
    for t in TYPE3:
        g = [f for f in fs if type3(f)[0] == t[0]]
        if not g: continue
        out.append(f'<tr class="rsep t3"><td colspan="{ncol}"><b>{t[2] if en else t[1]}</b>　{len(g)}{"" if en else " 件"}<br><span class="muted">{t[4] if en else t[3]}</span></td></tr>')
        out.extend(rowfun(f) for f in g)
    return ''.join(out)
LEAD = {
 'overview.html': 'AI が照合した数字の結果です。大半は一致しています。食い違ったもののうち、理由が資料に書かれていないものを調べ、手順の条件を満たしたものが記録になります。まず上の帯で進み具合を、下の表で統計ごとの数を見てください。',
 'records/index.html': '見つかった食い違いと論点の一覧です。3つの型に分けて並べています。「数字が合わない」「版で変わる・載っていない」「分析や書き方の論点」。気になる型から、見出しを選んで読んでください。各記録のページに、根拠の原文と、確かめ方があります。',
  'citations.html': '記録した数字が、報道や論文でどう引かれているかの記録です。元の文と同じ形で引かれたか、言い方が変わったかを分けています。',
 'inquiries.html': '担当の役所に送る質問の文です。答えが一つに決まる問いにしています。返事が来たら、そのまま載せます。',
 'method.html': '検証の手順の詳しい説明です。何を照合するか、いつ「確定」とするか、AI がどう反証するか、人が何を決めるかを書いています。下の目次から、必要なところへ進んでください。',
 'process.html': '運営の決まりです。記録の区分、照会の手順、利益相反、訂正の仕方を書いています。下の目次から、必要なところへ進んでください。',
 'errors.html': 'URAZUKE の側の誤りと、その訂正の記録です。公開前に反証で直したものも含めて、すべて残しています。',
 'data.html': '取得した資料の数え方と、どこから取ったかの一覧です。同じ資料を手に入れれば、同じ計算をやり直せます。',
}
LEAD_EN = {
 'overview.html': 'Results of the numbers compared by AI. Most agree. Mismatches whose reason is not written in the sources are examined, and those that meet the conditions of the procedure become records. See the band above for progress and the table below for each statistic.',
 'records/index.html': 'A list of the mismatches and questions found, in three types: numbers that do not agree; changed between editions or not published; questions of analysis or wording. Start with the type that interests you. Each record page gives the source text and how to check it.',
  'citations.html': 'How the recorded figures are cited in news reports and papers: whether in the same form as the source or in changed wording.',
 'inquiries.html': 'The questions to be sent to the responsible offices, each with a single definite answer. Replies are published as they are.',
 'method.html': 'A detailed description of the verification procedure: what is compared, when a finding is established, how AI tries to refute it, and what people decide. Use the contents below.',
 'process.html': 'The rules of operation: record categories, inquiry procedure, conflicts of interest and corrections. Use the contents below.',
 'errors.html': 'Errors on URAZUKE’s side and their corrections, including those fixed by refutation before publication.',
 'data.html': 'How the fetched sources are counted, and where they come from. With the same versions of the sources, anyone can redo the same calculations.',
}
TOC = {'method.html', 'process.html'}
def add_lead(path, body, en=False):
    L = (LEAD_EN if en else LEAD).get(path)
    if not L: return body
    tag_end = '</h1>' if '</h1>' in body else ('</h2>' if path in TOC and '</h2>' in body else None)
    if not tag_end: return body
    i = body.index(tag_end) + len(tag_end); head, rest = body[:i], body[i:]
    toc = ''
    if path in TOC:
        hs = []; seen_h2 = [False]
        def _id(m):
            lv, attrs, txt = m.group(1), m.group(2), m.group(3)
            if lv == '2': seen_h2[0] = True
            elif seen_h2[0]: return m.group(0)
            n = len(hs) + 1; hid = re.search(r'id="([^"]+)"', attrs); hid = hid.group(1) if hid else f's{n}'
            hs.append((hid, re.sub('<[^>]+>', '', txt)))
            return f'<h{lv} id="{hid}">{txt}</h{lv}>'
        rest = re.sub(r'<h([23])([^>]*)>(.*?)</h\1>', _id, rest)
        toc = '<nav class="toc"><b>' + ('Contents' if en else '目次') + '</b><ol>' + ''.join(f'<li><a href="#{h}">{t}</a></li>' for h, t in hs) + '</ol></nav>'
    return head + f'<p class="plain">{L}</p>' + toc + rest
CSS += """
p.plain{font-size:1rem;line-height:1.9;max-width:40em;margin:.2rem 0 1.6rem;padding:.9rem 1.1rem;background:var(--paper);border-left:3px solid var(--acc)}
nav.toc{margin:0 0 2rem;padding:.8rem 1.1rem;border:1px solid var(--line);background:var(--paper);font-size:.92rem}nav.toc ol{margin:.3rem 0 0;padding-left:1.4rem;columns:2;column-gap:2rem}nav.toc a{border:0}
tr.rsep.t3 td{background:#f1f3f5;padding:.8rem .7rem;font-size:.95rem}tr.rsep.t3 b{font-family:"Hiragino Mincho ProN","Noto Serif JP",serif;letter-spacing:.06em}
p.type3{margin:.4rem 0 -.6rem;font-size:.85rem;color:var(--acc);letter-spacing:.06em}
@media(max-width:640px){nav.toc ol{columns:1}}
"""
# ---- r43：記録の平易版（publish/plain）。別系統の反証で支持され、対照が正答した回のものだけ載せる
_PST = json.load(open(os.path.join(R, 'publish/plain/STATUS.json'))) if os.path.exists(os.path.join(R, 'publish/plain/STATUS.json')) else {}
def plain(f):
    st = _PST.get(f['id'])
    if not st or not st.get('adopted') or st.get('verdict') != '支持': return None
    p = os.path.join(R, 'publish/plain/drafts', f['id'] + '.json')
    return json.load(open(p)) if os.path.exists(p) else None
def HEAD(f):
    d = plain(f); return d['見出し'] if d else f['見出し']
def plain_block(f, d, en=False):
    tr = (lambda x: inline(T(x, SRC_F, f['id']))) if en else e
    H = ('What is written', 'The figures side by side', 'Where misreading can occur', 'Direction of the difference', 'What this record does not show', 'What we are asking the responsible office', 'Refutation check') if en else \
        ('書かれていること', '数字を並べると', '読み違えが起きうるところ', '違いの向き', 'この記録からは言えないこと', '担当部署に尋ねていること', '反証')
    t = d['表']
    tab = '<table class="ptab"><tr>' + ''.join(f'<th>{tr(h)}</th>' for h in t['head']) + '</tr>' + ''.join('<tr>' + ''.join(f'<td>{tr(c)}</td>' for c in r) + '</tr>' for r in t['rows']) + '</table>'
    st = _PST[f['id']]
    return (f'<div class="plainrec"><h3>{H[0]}</h3><p>{tr(d["書かれていること"])}</p><h3>{H[1]}</h3>{tab}'
            f'<h3>{H[2]}</h3><ul>' + ''.join(f'<li>{tr(x)}</li>' for x in d['読み違え']) + f'<li><b>{H[3]}</b>：{tr(d["向き"])}</li></ul>'
            f'<h3>{H[4]}</h3><ul>' + ''.join(f'<li>{tr(x)}</li>' for x in d['言えないこと']) + '</ul>'
            f'<h3>{H[5]}</h3><p>{tr(d["照会"])}</p>'
            f'<p class="muted">{H[6]}：{st["round"]} {st["q"]}（' + ('supported' if en else '支持') + '）</p></div>')
CSS += """
.plainrec{margin:1.2rem 0 2rem}.plainrec h3{margin:1.6rem 0 .4rem;font-size:1rem;color:var(--acc)}.plainrec p,.plainrec li{max-width:44em}
table.ptab{margin:.4rem 0 .6rem;font-size:.95rem}table.ptab th{background:#f1f3f5}
h3.yoshi{margin-top:2rem;font-size:.95rem;color:var(--sub)}
"""
open(os.path.join(OUT, 'style.css'), 'w').write(CSS + CV.CSS + CK.CSS)
def _mobile(doc):
    """主な表（作業ノートの外の、見出しの行がある表）に、各セルの項目名（data-label）と class="stack" を付ける。作業ノートの表は横スクロールのまま。"""
    k = doc.find('<div class="prose">')
    head, tail = (doc, '') if k < 0 else (doc[:k], doc[k:])
    def one(m):
        t = m.group(0)
        hdr = re.search(r'<tr>((?:\s*<th[^>]*>.*?</th>)+)\s*</tr>', t, re.S)
        if not hdr: return t
        labs = [re.sub(r'<[^>]+>', '', x).strip() for x in re.findall(r'<th[^>]*>(.*?)</th>', hdr.group(1), re.S)]
        t = t.replace(hdr.group(0), '<tr class="hd">' + hdr.group(0)[4:], 1)
        def row(rm):
            r = rm.group(0)
            if '<th' in r or 'colspan' in r: return r
            i = [0]
            cells = re.findall(r'<td[^>]*>(.*?)</td>', r, re.S)
            def cell(cm):
                k = i[0]; lab = labs[k] if k < len(labs) else ''; i[0] += 1
                txt = re.sub(r'<[^>]+>', '', cells[k]) if k < len(cells) else ''
                cls = ' class="t1"' if k == 0 else (' class="wide"' if len(txt) > 12 else '')
                return f'<td data-label="{e(lab)}"{cls}' + cm.group(1)
            r = re.sub(r'<td(\s|>)', cell, r)
            return re.sub(r'class="([^"]*)" class="([^"]*)"', r'class="\1 \2"', r)  # 元の class とまとめる
        t = re.sub(r'<tr[^>]*>.*?</tr>', row, t, flags=re.S)
        o = re.match(r'<table[^>]*>', t).group(0)
        o2 = o.replace('class="', 'class="stack ', 1) if 'class="' in o else o.replace('<table', '<table class="stack"', 1)
        return o2 + t[len(o):]
    return re.sub(r'<table[^>]*>.*?</table>', one, head, flags=re.S) + tail
# ロゴ（案A：裏打ち）。正は site/assets/make_assets.sh が作る SVG・PNG
for _a in ('mark.svg', 'favicon.svg', 'favicon-16.png', 'favicon-32.png', 'apple-touch-icon.png', 'og.png', 'og-en.png'):
    shutil.copy(os.path.join(R, 'site/assets', _a), os.path.join(OUT, _a))
MARK = '<svg class="mark" viewBox="0 0 32 32" aria-hidden="true"><rect x="11" y="9" width="17" height="21" fill="#2f4f6f"/><rect x="5" y="3" width="17" height="21" fill="#fbfbf9" stroke="#1f2328" stroke-width="2.4"/></svg>'
SITE_URL = 'https://urazuke.org/'
def canon(path):
    return SITE_URL + (path[:-len('index.html')] if path.endswith('index.html') else path)
def head_extra(root, og_img, path, title, desc, lang):
    return (f'<link rel="canonical" href="{canon(path)}"><meta name="description" content="{e(desc)}">'
            f'<link rel="icon" href="{root}favicon.svg" type="image/svg+xml"><link rel="icon" href="{root}favicon-32.png" sizes="32x32" type="image/png">'
            f'<link rel="apple-touch-icon" href="{root}apple-touch-icon.png"><meta property="og:site_name" content="URAZUKE">'
            f'<meta property="og:title" content="{e(title)} — URAZUKE"><meta property="og:description" content="{e(desc)}"><meta property="og:type" content="website">'
            f'<meta property="og:url" content="{canon(path)}"><meta property="og:image" content="{SITE_URL}{og_img}"><meta property="og:locale" content="{lang}"><meta name="twitter:card" content="summary_large_image">')
import datetime as _dt
CR = json.load(open(os.path.join(R, 'site/crawl.json')))
_WD = '月火水木金土日'
def jd(s):
    d = _dt.date.fromisoformat(s); return f'{d.year}年{d.month}月{d.day}日（{_WD[d.weekday()]}）'
_last = CR['runs'][-1]
# 毎週の自動巡回の数（2026-11-25、しくみのページの表と上部の帯。数はすべて site/crawl.json・publish/findings.json・crawl/ の控えから機械で出す）
def _cnt_tsv(path, col=None, val=None):
    import csv as _c
    try: rows = list(_c.DictReader(open(os.path.join(R, path), encoding='utf-8'), delimiter='\t'))
    except FileNotFoundError: return 0
    return sum(1 for r in rows if col is None or r.get(col) == val)
try: _NREC = len(json.load(open(os.path.join(R, 'publish/findings.json'))))
except Exception: _NREC = None
CRN = dict(sources=_last['sources'], changed=_last.get('changed'), new=(max(0, _NREC - _last['records']) if _NREC is not None and _last.get('records') is not None else None),
           hold=_cnt_tsv('crawl/hold.tsv', 'status', '保留'), entry=_cnt_tsv('crawl/watch_pages.tsv'))
try: CRN['council_docs'] = len(json.load(open(os.path.join(R, 'crawl/councils_state.json')))['known'])
except Exception: CRN['council_docs'] = None
def _n(x): return '—' if x is None else f'{x:,}'
CRAWL = (f'''<div class="crawl"><div class="cin"><span class="dot"></span><span class="cl"><b class="wk">毎週の自動巡回</b>　{'最終' if _last['kind'] == '週1回の巡回' else '最終の取得'}</span><b>{jd(_last['date'])}</b><span class="sep"></span><span class="cl">変わった資料</span><b>{_n(CRN['changed'])}</b><span class="sep"></span><span class="cl">次回</span><b>{jd(CR['next'])}</b><a class="cmore" href="@PRE@about.html#crawl">しくみ</a></div></div>''' if CR.get('active') else f'''<div class="crawl"><div class="cin"><span class="dot off"></span><span class="cl">資料の取得日</span><b>{jd(_last['date'])}</b><span class="sep"></span><span class="cl">定期巡回（{CR['interval_days']}日ごと）</span><b>準備中</b><span class="cn">取得元 {_last['sources']:,} 件を取り直し、変化を LLM が検証して記録する仕組みを準備しています</span></div></div>''')
NAV = [('records/', '記録'), ('overview.html', '統計'), ('citations.html', '引かれ方'), ('inquiries.html', '照会'), ('about.html', 'しくみ')]
def page(path, title, body, depth=None):
    body = add_lead(path, body)
    d = path.count('/'); pre = '../' * d
    nav = ''.join(f'<a href="{pre}{h}">{t}</a>' for h, t in NAV) + f'<a href="{pre}en/{path}" hreflang="en" lang="en">English</a>'
    doc = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><link rel="alternate" hreflang="en" href="{pre}en/{path}">{head_extra(pre, "og.png", path, title, "日本の犯罪・司法・精神医療・福祉に関する公開データを、再現できる方法で検証し、記録する。", "ja_JP")}<title>{e(title)} — URAZUKE（草案）</title><link rel="stylesheet" href="{pre}style.css"><script>window.va = window.va || function () {{ (window.vaq = window.vaq || []).push(arguments); }};</script><script defer src="/_vercel/insights/script.js"></script></head><body>
<div class="draft">草案・非公開　顧問弁護士の確認前です。内容は確定していません。</div>
{CRAWL.replace('@PRE@', pre)}
<header class="site"><a class="logo" href="{pre}index.html">{MARK}URAZUKE</a><nav>{nav}</nav></header>
<main>{body}</main>
<footer>URAZUKE — 日本の犯罪・司法・精神医療・福祉の公開データを検証し、記録する。<br><a href="{pre}errors.html">訂正の記録</a>　<a href="{pre}terms.html">利用規約とプライバシー</a><br>異論・追加資料・誤りの指摘：<a href="mailto:contact@urazuke.org">contact@urazuke.org</a></footer></body></html>"""
    doc = _mobile(doc)
    p = os.path.join(OUT, path); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w').write(doc)
def kcls(k): return 'k-' + k.split('（')[0]
def tag(k): return f'<span class="tag {kcls(k)}">{e(k.split("（")[0])}</span>'
def short(s, n=70): return s if len(s) <= n else s[:n] + '…'
VER = json.load(open(os.path.join(R, 'results/scope/verified.json')))  # checks/generic/count_verified.py の出力
CHK = {'keisatsu': '記録は犯罪統計書 第56表の関係の区分（KH-K1）'}  # r26：照合の数は各統計のページの照合の表に出す
CHK.update({'kyoin-chokai': '推移の表の版間（当初の版を含む、式 3,686、不一致は説明のある改訂だけ）、状況の表の内訳（式 19、不一致 0）、資料の表題の版間（MK-L1）、令和4年度の公表の取組状況の中身の集計（作業ノート）、免許失効データベースの登録件数（MK-L2）', 'koumuin-chokai': '性犯罪の区分の有無（KM-K1）'})  # r18
CHK.update({})  # r19
CHK.update({})  # r20
import subprocess as _sp, unicodedata as _ud
import sys as _sys0; _sys0.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'publish')); from inquiry_dest import fname as _fname
def qslug(s): return 'q-' + re.sub(r'[\s_（）()]+', '', _ud.normalize('NFC', s))
COMMIT = _sp.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=R, capture_output=True, text=True).stdout.strip()
STATS = [
 ('hanzai-hakusho','犯罪白書','法務省 法務総合研究所','results/hanzai_hakusho/FINDINGS.md','HK'),
 ('keisatsu','犯罪統計・警察白書','警察庁','results/keisatsu/FINDINGS.md','KH'),
 ('stalker','ストーカー・DV・児童虐待事件','警察庁','results/stalker/FINDINGS.md','ST'),
 ('saihan','再犯防止推進白書','法務省','results/saihan/FINDINGS.md','SH'),
 ('moj-sexoffender','保護局 性犯罪者処遇プログラム効果検証','法務省 保護局','results/moj_sexoffender/FINDINGS.md','SO'),
 ('monka','教職員の懲戒処分（人事行政状況調査）','文部科学省','results/monka/FINDINGS.md','MK'),
 ('gyakutai','児童虐待相談対応件数','こども家庭庁（旧 厚生労働省）','results/gyakutai/FINDINGS.md','GY'),
 ('jisatsu','自殺統計','警察庁・厚生労働省','results/jisatsu/FINDINGS.md',None),
 # r08 BEGIN
 ('jisatsu-hakusho','自殺対策白書','厚生労働省','results/jisatsu_hakusho/FINDINGS.md','JH'),
 ('futoko','児童生徒の問題行動・不登校等調査','文部科学省','results/futoko/FINDINGS.md',None),
 ('shiho','司法統計年報（刑事編）','最高裁判所','results/shiho/FINDINGS.md','SJ'),
 ('eisei','衛生行政報告例（精神保健福祉）','厚生労働省','results/eisei/FINDINGS.md','ES'),
 ('jinko-dotai','人口動態統計（確定数）','厚生労働省','results/jinko_dotai/FINDINGS.md',None),
 ('kokusei','国勢調査','総務省','results/kokusei/FINDINGS.md',None),
 ('juki-idou','住民基本台帳人口移動報告','総務省','results/juki_idou/FINDINGS.md',None),
 ('kanja','患者調査','厚生労働省','results/kanja/FINDINGS.md',None),
 ('iryosd','医療施設（動態）調査','厚生労働省','results/iryosd/FINDINGS.md',None),
 ('shogai-hakusho','障害者白書','内閣府','results/shogai_hakusho/FINDINGS.md',None),
 ('danjo-hakusho','男女共同参画白書','内閣府','results/danjo_hakusho/FINDINGS.md',None),
 ('kodomo-hakusho','こども白書（旧 子供・若者白書）','こども家庭庁','results/kodomo_hakusho/FINDINGS.md',None),
 ('maikin','毎月勤労統計調査','厚生労働省','results/maikin/FINDINGS.md',None),
 ('roudouryoku','労働力調査','総務省','results/roudouryoku/FINDINGS.md',None),
 ('cpi','消費者物価指数','総務省','results/cpi/FINDINGS.md',None),
 ('kessan','決算検査報告','会計検査院','results/kessan/FINDINGS.md',None),
 # r08 END
 # r09 BEGIN
 ('kyosei','矯正統計年報','法務省','results/kyosei/FINDINGS.md','KY'),
 ('hogo','保護統計年報','法務省','results/hogo/FINDINGS.md',None),
 ('kensatsu','検察統計年報','法務省','results/kensatsu/FINDINGS.md','KS'),
 ('iryokansatsu','医療観察法の統計','厚生労働省・法務省','results/iryokansatsu/FINDINGS.md',None),
 ('koutsuu','交通事故統計','警察庁','results/koutsuu/FINDINGS.md',None),
 ('seiho','生活保護 被保護者調査','厚生労働省','results/seiho/FINDINGS.md',None),
 ('monka-kihon','学校基本調査・体罰の懲戒処分等の推移','文部科学省','results/monka_kihon/FINDINGS.md',None),
 ('jinko-suikei','人口推計','総務省','results/jinko_suikei/FINDINGS.md',None),
 ('chinkin','賃金構造基本統計調査','厚生労働省','results/chinkin/FINDINGS.md',None),
 ('karoshi','過労死等の労災補償状況','厚生労働省','results/karoshi/FINDINGS.md',None),
 ('kensetsu-juchu','建設工事受注動態統計','国土交通省','results/kensetsu_juchu/FINDINGS.md','KJ'),
 ('sna','国民経済計算（年次推計）','内閣府','results/sna/FINDINGS.md',None),
 ('kessan-card','地方財政状況調査（都道府県決算カード）','総務省','results/kessan_card/FINDINGS.md','KC'),
 # r09 END
 # r10 BEGIN
 ('shibo-jirei','こども虐待による死亡事例等の検証結果（死亡事例検証報告）','こども家庭庁','results/shibo_jirei/FINDINGS.md','SD'),
 ('shogai-gyakutai','障害者虐待対応状況調査','厚生労働省','results/shogai_gyakutai/FINDINGS.md',None),
 ('kyosei-so','矯正局 性犯罪者処遇プログラム効果検証','法務省 矯正局','results/moj_sexoffender/FINDINGS_kyosei.md','KP'),
 # r10 END
 # r13 BEGIN
 ('yakubutsu','薬物事犯者のプログラム効果検証（矯正局・保護局）','法務省 矯正局・保護局','results/moj_yakubutsu/FINDINGS.md','YK'),
 ('boryoku','暴力防止プログラム効果検証（保護局）','法務省 保護局','results/moj_yakubutsu/FINDINGS.md','BV'),
 # r13 END
 # r14 BEGIN
 ('shokugyo','職業訓練・刑務作業の効果検証（矯正局）','法務省 矯正局','results/moj_kensho2/FINDINGS.md','SK'),
 ('sib','少年院出院者の学習支援（SIB）事業総括','法務省・日本総合研究所','results/moj_kensho2/FINDINGS.md','SB'),
 # r14 END
 # r16 BEGIN
 # r16 END
 # r15 BEGIN
 ('kyosei-ninchi','刑事施設の認知症の把握','法務省 矯正局（矯正統計年報・白書）','results/kyosei_ninchi/FINDINGS.md','NK'),
 # r15 END
 # r17 BEGIN
 # r17 END
 # r18 BEGIN
 ('kyoin-chokai','公立学校教職員の人事行政状況調査（懲戒処分・性犯罪等）','文部科学省','results/kyoin_chokai/FINDINGS.md','MK'),
 ('koumuin-chokai','公務員の懲戒処分・犯罪の統計（人事院・総務省・警察庁・犯罪白書）','人事院・総務省・警察庁・法務省','results/kyoin_chokai/FINDINGS.md','KM'),
 # r18 END
 # r19 BEGIN
 # r19 END
 # r20 BEGIN
 # r20 END
 ('seishin630','精神保健福祉資料（630調査）','国立精神・神経医療研究センター','results/seishin630/FINDINGS.md','630'),
]
NSRC = sum(1 for fn in glob.glob(os.path.join(R,'publish/source_manifests/*.tsv')) for i, l in enumerate(open(fn)) if i > 0 and l.strip())  # MANIFEST の行（見出しの行を除く）
SC = json.load(open(os.path.join(R, 'results/scope/scope.json')))
LV = {3:('影響 大','結論・指標に関わる','報告書の結論や要約、政策の指標、全国の総数が変わる、または読み方が変わる'),2:('影響 中','値が食い違う','版・資料・表の間で値が違う、または欠ける'),1:('影響 小','形式の不備','機械判読用ファイルの不備。本体の値は正しい')}
# 範囲（犯罪・司法・精神医療・福祉）を絞る前に検証した統計。記録は消さずに残し、注を付ける。
PRE_FIELD = {'労働・経済'}
PRE = {'maikin', 'roudouryoku', 'cpi', 'chinkin', 'karoshi', 'kensetsu-juchu', 'sna', 'kessan', 'kessan-card'}
FIELD = [('司法・犯罪', ['hanzai-hakusho','keisatsu','stalker','saihan','moj-sexoffender','kyosei-so','yakubutsu','boryoku','shokugyo','sib','shiho','kensatsu','kyosei','kyosei-ninchi','koumuin-chokai','hogo','iryokansatsu','koutsuu']),
 ('医療・福祉', ['jisatsu','jisatsu-hakusho','seishin630','eisei','kanja','iryosd','gyakutai','shogai-gyakutai','shibo-jirei','seiho']),
 ('教育', ['monka','kyoin-chokai','futoko','monka-kihon']),
 ('人口', ['jinko-dotai','kokusei','juki-idou','jinko-suikei']),
 ('労働・経済', ['maikin','roudouryoku','cpi','chinkin','karoshi','kensetsu-juchu','sna']),
 ('白書・会計', ['shogai-hakusho','danjo-hakusho','kodomo-hakusho','kessan','kessan-card'])]

# 並び順（r26、METHODS）：分野 → 公表元（最初に名前のある機関）→ 統計名の五十音。数（照合した数・食い違い）では並べない。
# 公表元の順：行政機関は国家行政組織法・内閣府設置法の並び（内閣府とその外局を先に）、続けて人事院・会計検査院・裁判所・研究機関。
PUB_ORDER = ['内閣府', '警察庁', 'こども家庭庁', '総務省', '法務省', '文部科学省', '厚生労働省', '国土交通省', '人事院', '会計検査院', '最高裁判所', '国立精神・神経医療研究センター']
YOMI = {'hanzai-hakusho': 'はんざいはくしょ', 'keisatsu': 'はんざいとうけい', 'stalker': 'すとーかー', 'saihan': 'さいはんぼうしすいしんはくしょ',
        'moj-sexoffender': 'ほごきょくせいはんざいしゃ', 'monka': 'きょうしょくいんのちょうかいしょぶん', 'gyakutai': 'じどうぎゃくたいそうだん', 'jisatsu': 'じさつとうけい',
        'jisatsu-hakusho': 'じさつたいさくはくしょ', 'futoko': 'じどうせいとのもんだいこうどう', 'shiho': 'しほうとうけいねんぽう', 'eisei': 'えいせいぎょうせいほうこくれい',
        'jinko-dotai': 'じんこうどうたいとうけい', 'kokusei': 'こくせいちょうさ', 'juki-idou': 'じゅうみんきほんだいちょう', 'kanja': 'かんじゃちょうさ',
        'iryosd': 'いりょうしせつ', 'shogai-hakusho': 'しょうがいしゃはくしょ', 'danjo-hakusho': 'だんじょきょうどうさんかくはくしょ', 'kodomo-hakusho': 'こどもはくしょ',
        'maikin': 'まいつききんろうとうけい', 'roudouryoku': 'ろうどうりょくちょうさ', 'cpi': 'しょうひしゃぶっかしすう', 'kessan': 'けっさんけんさほうこく',
        'kyosei': 'きょうせいとうけいねんぽう', 'hogo': 'ほごとうけいねんぽう', 'kensatsu': 'けんさつとうけいねんぽう', 'iryokansatsu': 'いりょうかんさつほう',
        'koutsuu': 'こうつうじことうけい', 'seiho': 'せいかつほご', 'monka-kihon': 'がっこうきほんちょうさ', 'jinko-suikei': 'じんこうすいけい',
        'chinkin': 'ちんぎんこうぞうきほんとうけい', 'karoshi': 'かろうしとう', 'kensetsu-juchu': 'けんせつこうじじゅちゅう', 'sna': 'こくみんけいざいけいさん',
        'kessan-card': 'ちほうざいせいじょうきょうちょうさ', 'shibo-jirei': 'こどもぎゃくたいによるしぼうじれい', 'shogai-gyakutai': 'しょうがいしゃぎゃくたい',
        'kyosei-so': 'きょうせいきょくせいはんざいしゃ', 'yakubutsu': 'やくぶつじはんしゃ', 'boryoku': 'ぼうりょくぼうし', 'shokugyo': 'しょくぎょうくんれん',
        'sib': 'しょうねんいんしゅついんしゃ', 'kyosei-ninchi': 'けいじしせつのにんちしょう', 'kyoin-chokai': 'こうりつがっこうきょうしょくいん',
        'koumuin-chokai': 'こうむいんのちょうかいしょぶん', 'seishin630': 'せいしんほけんふくししりょう'}
def _pub_rank(o):
    for k, x in enumerate(PUB_ORDER):
        if o.startswith(x): return k
    raise KeyError('公表元の順が決まっていない: ' + o)
def _gojuon(y):
    # 五十音の順：濁点・半濁点と小書きの仮名は、まず清音・大きい仮名として比べる（同じなら元の表記で比べる）
    import unicodedata as _u
    base = ''.join(c for c in _u.normalize('NFD', y) if c not in '\u3099\u309a').translate(str.maketrans('ぁぃぅぇぉっゃゅょゎ', 'あいうえおつやゆよわ'))
    return (base, y)
def _ord_key(x):
    return (_pub_rank(x[2]), _gojuon(YOMI[x[0]]))
FIELD = [(fl, sorted(g, key=lambda s: _ord_key(next(x for x in STATS if x[0] == s)))) for fl, g in FIELD]
_FORDER = {s: (i, j) for i, (fl, g) in enumerate(FIELD) for j, s in enumerate(g)}
STATS_ORDERED = sorted(STATS, key=lambda x: _FORDER.get(x[0], (99, 0)))
FIELD_EN = {'司法・犯罪': 'Justice and crime', '医療・福祉': 'Health and welfare', '教育': 'Education', '人口': 'Population', '労働・経済': 'Labour and economy', '白書・会計': 'White papers and public accounts', 'その他': 'Other'}
assert all(any(x[0] in g for _, g in FIELD) for x in STATS if x[0] not in PRE), '分野のない統計がある'
_SI = {x[0]: x for x in STATS}
PRE_NOTE = '<p class="muted">この統計は、検証の範囲を犯罪・司法・精神医療・福祉に絞る前に検証した。記録はそのまま残している。</p>'
PRE_H = '<span class="muted">（範囲を絞る前に検証した統計）</span>'
ERR = [('2026-11-19','犯罪白書','HK-A4 に「列が1つずれ」と書いていた。平易版の反証（R049 Q6）で、本体の D〜J 列に対して F〜L 列にあり、2列右であることが分かった。要旨を直した。','hanzai-hakusho'),
       ('2026-11-19','薬物（保護観察）効果検証','YK-D1 の「保護観察期間６月以内は 10.3％・95.0％」は、表1の表示の割合を足した値だった。平易版の反証（R054 Q6）で、人数から計算すると 10.2％・95.1％であることが分かった。要旨を直した。','yakubutsu'),
       ('2026-11-16','630調査','「2017年も一致」と書いたが、2017年の年度別の表はシート名が違い、照合していなかった。のちに都道府県 611組を照合し不一致0。','seishin630'),
 ('2026-11-16','630調査','札幌市の長期データ F7 の年を1年ずらして書いていた（正：2016年 218・2017年 222）。','seishin630'),
 ('2026-11-16','再犯防止推進白書','割合の分母を 30,996 と計算していた（正：31,096）。別系統の検証（R006）の指摘。','saihan'),
 ('2026-11-16','再犯防止推進白書','令和6・7年版の 6,864 を「指標7」と書いていた（正：同名の項目の記載）。R006 の指摘。','saihan'),
 ('2026-11-16','児童虐待事件（警察庁）','令和7年版にも2020年の値があるように書いていた（令和7年版の表は2021年から）。R004 の指摘で書き直し、R005 で支持。','stalker'),
 ('2026-11-16','ストーカー','「762 が誤りで 768 が正しい」と書いていた（正：不一致は確定、どちらの誤りかは推定）。R004 の指摘。','stalker'),
 ('2026-11-16','文科','差し替えの告知が「ない」と書いたが、告知はファイルの中にあった（ページにはない）。','monka'),
 ('2026-11-17','保護局 効果検証','SO-H1 に「比較は『仮釈放の時期』に近い」と書いていた。別系統の反証（R007）で判定不能となり、確かめられる範囲（非受講群の76.1%が保護観察3月未満の仮釈放者）に限定した。確認の状態は「機械検証のみ」に戻した（のちに 2026-11-18 の R024 Q2 で別系統で支持）。','moj-sexoffender'),
 ('2026-11-17','保護局 効果検証','SO-H4 に「刑事施設での受講を考慮しておらず」と書いていた。R007 の指摘で「公表されたモデルは…調整しておらず」に限定した。','moj-sexoffender'),
 ('2026-11-17','保護局 効果検証','SO-P1 の文言が、R003 の指摘で直した「逆数と一致する」から「逆数である」に戻っていた。直した文言に戻した。','moj-sexoffender'),
 ('2026-11-17','検察統計年報','KS-A1 の要旨に、5か所とも「翌年の旧受と合う」と書いていた（昭和50年は合わない、昭和19年は翌年の資料がない）。別系統の反証（R009）の指摘で書き直した。','kensatsu'),
 ('2026-11-17','衛生行政報告例','ES-I1 で、年度の連続が合わない都道府県を「19件」と書いていた（正：延べ17件。19件は全国の2件を含めて数えていた）。指定都市（再掲）の2件も別に記した。別系統の反証（R008）の指摘。','eisei'),
 ('2026-11-17','自殺対策白書','JH-A1 に含めていた「参考資料2-13表（1）に令和7年の行がない」は、R008 で「当年」の意味が曖昧として判定不能。事前の基準（H008）どおり記録から外し、作業ノートに旧版の年を明記して残した。','jisatsu-hakusho'),
 # r11 ERR BEGIN
 ('2026-11-17', '死亡事例検証・矯正局 効果検証', 'SD-A1・SD-A2・KP-A1・KP-A2 の影響を「小」としていた。METHODS の規則では「小」は機械判読用など副次的なファイルだけの不備で、これらは本体の表・本文の値の食い違いなので「中」に直した。', 'shibo-jirei'),
 ('2026-11-17', '死亡事例検証', 'SD-A2 の当初の主張は、第20・21次報告の正誤表（令和8年9月1日）を見落とし「第19〜21次に正誤表がない」としていた（公開前）。R010 で判定不能。正誤表を取得して書き直し、R011 で支持された。', 'shibo-jirei'),
 # r11 ERR END
 # r12 ERR BEGIN
 ('2026-11-17', '検察統計年報・都道府県決算カード', '影響の割当てを METHODS の規則で全件見直した。KS-I1（第2表の未済）と KC-A1（単年度収支）は本体の表の値の食い違いで、「小」の条件（副次的なファイルだけの不備）に当たらないため「中」に直した。', 'kensatsu'),
 ('2026-11-17', '矯正局 効果検証', '同じ見直しで、KP-C1（罪名構成の偏り）は報告書のまとめ（全対象者で効果）の読み方に関わるため「大」に直した（保護局の SO-H1・SO-H2 と同じ扱い）。', 'kyosei-so'),
 ('2026-11-18', '検察統計年報・建設工事受注動態統計・都道府県決算カード', '影響の見直し（2026-11-17）で記録を作り直したとき、R009 の反映が元に戻っていた：KS-A1 は R009 で誤りとされた文（5か所とも翌年の旧受と合う）に戻り、KS-I1・KJ-L1 の要旨の追記が消え、KS-I1・KJ-L1・KJ-I1・KC-A1 の確認の状態が「機械検証のみ」になっていた。R009 の反映を戻し、作り直しても戻らないよう記録の元の表に書いた。', 'kensatsu'),
 ('2026-11-18', '犯罪白書', 'HK-A3 で、照合した和暦・西暦の組を「36,380組」と書いていた。令和6年版を取得し直した後の数は 50,213組（令和3〜7年版の図表・資料の Excel、同じ行の和暦と西暦）。食い違いが1件だけであることは変わらない。範囲を書き足して直した。', 'hanzai-hakusho'),
 ('2026-11-18', '犯罪白書', 'HK-A5 は「科刑状況の Excel が地方裁判所の部分を欠き、簡易裁判所だけを総数として載せる（実際の総数 42,769）」としていた。地方裁判所の部分は資料2-3 の Excel に載っており（令和元年版・令和4年版の Excel には案内の注がある）、記録の撤回の条件に当たる。元の主張を取り下げ、案内の注のない版がある（令和2・3・5・6・7年版）という事実に狭めた。別系統の反証（R022、対照の不備で判定は採らない回）の指摘を資料で確かめた。', 'hanzai-hakusho'),
 ('2026-11-18', '犯罪白書', 'HK-A9 で、令和5年版の訂正のお知らせのうち Web 版本文で訂正前の値のままの項目を「7」としていた。頁・行で数えると10か所。数え方を書いて直した。別系統の反証（R023）の指摘。', 'hanzai-hakusho'),
 ('2026-11-18', '刑事施設の認知症の把握', 'NK-K1 で、認知症スクリーニング検査の結果は「白書の本文にだけ載る」としていた。再犯防止推進白書 令和4年版では特2-1-4表として表にも載る。「白書（本文と特2-1-4表）にだけ載り、矯正統計年報にはない」に直した。別系統の反証（R023）の指摘。', 'kyosei-ninchi'),
 ('2026-11-18', '精神保健福祉資料（630調査）', '630-M1 で、長期データの内訳の和が在院患者数より小さいのを「2017年以降」としていた。2017年は一致し、差は2018年から。直した。別系統の反証（R025）の指摘。', 'seishin630'),
 ('2026-11-18', '再犯防止推進白書', 'SH-A1 で、令和2年版の正誤表の訂正を「5か所」としていた。正誤表は9か所（13・18頁の指標の5か所と、223頁の予算額の4か所）。直した。9か所とも全体版 PDF で訂正前の記載のままであることは変わらない。別系統の反証（R027）の指摘。', 'saihan'),
 ('2026-11-20', '暴力防止プログラムの効果検証（保護局）', 'BV-C1 の根拠の原文で、1枚の概要からの抜き出しが途中で切れ、要旨の「4.0％」「再犯抑止に寄与した可能性」が抜き出しに入っていなかった。抜き出す箇所を足した（要旨は変えていない）。サイトの定期の点検（2026-11-19）の指摘。', 'boryoku'),
 ('2026-11-20', 'ストーカー・DV・児童虐待事件', 'ST-I1 の根拠の原文が 762 の行だけで、年の見出し・内訳の行・相談等件数 19,131 がなかった。表の見出しと内訳の各行、19,131 の行を足し、和の式を添えた（要旨は変えていない）。サイトの定期の点検（2026-11-19）の指摘。', 'stalker'),
 ('2026-11-20', '教職員の懲戒処分（人事行政状況調査）', '「統計から探す」の記録の数で、MK-L1・MK-L2（人事行政状況調査（懲戒処分・性犯罪等）と免許失効データベースの記録）を、接頭辞が同じ「教職員の懲戒処分（人事行政状況調査）」に数えていた。記録を統計に明示して割り当て直した。サイトの定期の点検（2026-11-19）の指摘。', 'monka'),
 # r12 ERR END
]
# ---- 反証・判定不能で文を変えた記録を、訂正の記録に自動で足す（2026-11-19、点検 M7）。手で書いた行がある記録は足さない。
SB = json.load(open(os.path.join(R, 'results/refute/scoreboard.json')))
EVB = {}
for _e in SB['events']: EVB.setdefault(_e['id'], []).append(_e)
_SN = {x[4]: (x[0], x[1]) for x in STATS if x[4]}
_HAND = [t for _, _, t, _ in ERR]
_KAKU = {x['id']: x.get('確認', '') for x in json.load(open(os.path.join(R, 'publish/findings.json')))}
for _id, _es in sorted(EVB.items()):
    _es = [x for x in _es if not x.get('plain')]  # 平易版の反証は記録の訂正ではない（r43）
    for _k, _x in enumerate(_es):
        if _x['verdict'] == '支持': continue
        # 手で書いた行が同じ記録の同じ回に触れていれば足さない（2026-11-20 点検 #27：記録ごとに飛ばすと、影響の変更など別の行がある記録の書き直しが抜けた）
        if any(_id in t and _x['round'] in t for t in _HAND): continue
        # 次の回は、後の回のうち記録の「確認」の欄に書かれた回を優先する（2026-11-20 点検 #57：同じ回の別の問いを次の回と取り違えていた）
        _later = [y for y in _es[_k + 1:] if y['round'] != _x['round']]
        _kk = _KAKU.get(_id, '')
        _nx = next((y for y in _later if f"{y['round']} {y['q']}" in _kk), None) or next(iter(_later), None)
        _after = f"文を書き直し、{_nx['round']} {_nx['q']} で{_nx['verdict']}。" if _nx else '文を書き直した（再反証待ち）。'
        _pre = next((p for p in sorted(_SN, key=len, reverse=True) if _id.startswith(p + '-')), None)
        if _pre: ERR.append((_x['date'], _SN[_pre][1], f"{_id}：{_x['round']} {_x['q']} の反証で{_x['verdict']}。{_after}", _SN[_pre][0]))
ERR.sort(key=lambda r: r[0])
SENS = {'KP-C1': dict(script='checks/moj_sexoffender/c102_r2020_strata.py', rows=[
    ('全再犯', '粗いリスク比', '0.719', ''), ('全再犯', '罪名で層別（5層）の MH リスク比', '0.927', '0.784–1.096'), ('全再犯', '対照群を受講群の罪名構成に直接標準化したリスク比', '0.911', ''),
    ('性犯罪再犯', '粗いリスク比', '0.667', ''), ('性犯罪再犯', '罪名で層別（5層）の MH リスク比', '0.917', '0.723–1.162'), ('性犯罪再犯', '直接標準化したリスク比', '0.846', '')])}
SENS_EN = {'全再犯': 'All reoffending', '性犯罪再犯': 'Sexual reoffending', '粗いリスク比': 'Crude risk ratio', '罪名で層別（5層）の MH リスク比': 'MH risk ratio stratified by offence (5 strata)',
           '対照群を受講群の罪名構成に直接標準化したリスク比': 'Risk ratio, control group directly standardised to the offence mix of participants', '直接標準化したリスク比': 'Risk ratio, directly standardised'}
import csv as _csv
CAN = {r['id']: r for r in _csv.DictReader(open(os.path.join(R, 'publish/can_say.tsv'), encoding='utf-8'), delimiter='\t')}
assert all(f['id'] in CAN for f in F if f['影響'] == 3), '影響 大の記録には「言えること／言えないこと」を書く（publish/can_say.tsv）'
def cansay(f, en=False):
    c = CAN.get(f['id'])
    if not c: return ''
    if en: return f'<div class="box"><p><b>What this record supports:</b> {e(c["can_en"])}<br><b>What it does not support:</b> {e(c["cannot_en"])}</p></div>'
    return f'<div class="box"><p><b>この記録から言えること：</b>{e(c["言える"])}<br><b>言えないこと：</b>{e(c["言えない"])}</p></div>'
def sens(f, en=False):
    x = SENS.get(f['id'])
    if not x: return ''
    rows = ''.join(f'<tr><td>{SENS_EN[a] if en else a}</td><td>{SENS_EN[b] if en else b}</td><td>{c}</td><td>{d}</td></tr>' for a, b, c, d in x['rows'])
    if en:
        return f'<h2>Sensitivity of the recalculation (URAZUKE)</h2><p class="muted">Recalculated by URAZUKE from the published tables (<code>{x["script"]}</code>). None of these is the same quantity as the report’s Cox model adjusted for RAT. Follow-up time and RAT are not adjusted. One of the five strata combines three offences.</p><table><tr><th>Outcome</th><th>Measure</th><th>Value</th><th>95% CI</th></tr>{rows}</table>'
    return f'<h2>再計算の感度（URAZUKE）</h2><p class="muted">公表された表から URAZUKE が再計算した値（<code>{x["script"]}</code>）。どれも、報告書の Cox 回帰（RAT で調整）とは別の量。追跡期間と RAT は調整していない。5層のうち1層は3罪名をまとめた層。</p><table><tr><th>再犯</th><th>指標</th><th>値</th><th>95%CI</th></tr>{rows}</table>'
_RD = {x['round']: x.get('date', '') for x in SB['rounds']}
_VEN = {'支持': 'supported', '反証': 'refuted', '判定不能': 'no verdict'}
def hist(f, en=False):
    """記録の経過：反証の回（日付・問い・判定）と、訂正の記録の行。手で書いた固定の日付は使わない。"""
    ev = EVB.get(f['id'])
    if not ev:  # 記録の ID を付ける前の回（R003〜R006 など）は、確認の欄の回の番号から
        ev = [dict(round=r, q='', verdict='支持' if '別系統で支持' in f['確認'] else '', date=_RD.get(r, '')) for r in dict.fromkeys(re.findall(r'R0\d\d', f['確認']))]
    li = []
    for x in ev:
        if en: li.append(f"<li>{x['date']}　Refutation check {x['round']} {x['q']}{' (plain-language version)' if x.get('plain') else ''}: {_VEN.get(x['verdict'], 'see verification status')}.</li>")
        else: li.append(f"<li>{x['date']}　反証の回 {x['round']} {x['q']}{'（平易版の文）' if x.get('plain') else ''}：{x['verdict'] or '確認の状態の欄を参照'}。</li>")
    cor = [r for r in ERR if re.search(r'(?<![A-Z0-9-])' + re.escape(f['id']) + r'(?![0-9])', r[2])]
    for d, n, t, sl in cor:
        li.append(f'<li>{d}　' + (f'Correction: {inline(T(t, SRC_S, "err"))}' if en else f'訂正：{e(t)}') + '</li>')
    li.sort()
    banner = ''
    if cor:
        ds = '、'.join(sorted({r[0] for r in cor})) if not en else ', '.join(sorted({r[0] for r in cor}))
        banner = (f'<div class="box"><p><b>This record was corrected on {ds}.</b> See the history below and <a href="../errors.html">Corrections</a>.</p></div>' if en
                  else f'<div class="box"><p><b>この記録は {ds} に訂正しました。</b>内容は下の経過と<a href="../errors.html">訂正の記録</a>にあります。</p></div>')
    return ''.join(li) or ('<li>No refutation check yet.</li>' if en else '<li>反証の回はまだない。</li>'), banner
# 同じ接頭辞（MK）を二つの統計が使う。記録を統計に明示して割り当てる（2026-11-20 点検 #44：MK-L1・MK-L2 は人事行政状況調査（懲戒処分・性犯罪等）と免許失効データベースの記録で、kyoin-chokai のページの検査に載る）
FSLUG_FIX = {'MK-L1': 'kyoin-chokai', 'MK-L2': 'kyoin-chokai'}
def fslug(f): return FSLUG_FIX.get(f['id']) or next((x[0] for x in STATS if x[4] and f['id'].startswith(x[4] + '-')), None)
INSCOPE = [f for f in F if fslug(f) not in PRE]
OUTSCOPE = [f for f in F if fslug(f) in PRE]
NSTAT_IN = sum(1 for x in STATS if x[0] not in PRE)
BIZ = lambda f: f['業務との関係'].startswith('関わる')
n3 = sum(1 for f in INSCOPE if f['影響'] == 3); nb3 = sum(1 for f in INSCOPE if f['影響'] == 3 and BIZ(f)); nb = sum(1 for f in INSCOPE if BIZ(f))
# 確認の状態（4つ）。PROCESS §3 の終わりの規則に対応する
def STATE(f):
    c = f['確認']
    if '別系統で支持' in c: return 'sup'
    if '別系統では判定不能' in c: return 'fin'
    if re.search(r'R0\d\d', c): return 'rew'
    return 'pre'
ST_JA = {'sup': '別系統で支持', 'pre': '反証にかける前', 'rew': '書き直して再反証待ち', 'fin': '別系統では判定不能（確定）'}
ST_EN = {'sup': 'Supported by an independent model', 'pre': 'Not yet put to a refutation check', 'rew': 'Rewritten, awaiting a new refutation check', 'fin': 'Undetermined by an independent model (final)'}
ST_PEND = ('pre', 'rew', 'fin')
ST_ALL = ('sup',) + ST_PEND
ST_OPTS_JA = ''.join(f'<option value="{k}">{ST_JA[k]}</option>' for k in ST_ALL)
ST_OPTS_EN = ''.join(f'<option value="{k}">{ST_EN[k]}</option>' for k in ST_ALL)
def tiercol(lv):
    fs = [f for f in INSCOPE if f['影響'] == lv]; sup = [f for f in fs if '別系統で支持' in f['確認']]; rest = [f for f in fs if f not in sup]
    li = lambda f, c='': f'<li class="{c}"><a href="records/{f["id"]}.html"><span class="tid">{f["id"]}</span>{e(HEAD(f))}</a><span class="tmeta">{e(f["統計"].split("（")[0])}</span></li>'
    items = ''.join(li(f) for f in sup) + ''.join(f'<li class="tsep">{ST_JA[k]} {len(g)} 件</li>' + ''.join(li(f, 'pend') for f in g) for k in ST_PEND for g in [[f for f in rest if STATE(f) == k]] if g)
    m, lab, sub = LV[lv]
    return f'<div class="tier t{lv}"><div class="kick">{m}</div><div class="big"><b>{len(sup)}</b><span>件（別系統で支持）</span></div><h3>{lab}</h3><p class="tsub">{sub}</p><ul>{items}</ul></div>'
_ord = lambda f: (ST_ALL.index(STATE(f)), -f['影響'], f['id'])
_rr = lambda f: f'<tr><td><a href="records/{f["id"]}.html">{f["id"]}</a></td><td class="lv{f["影響"]}">{LV[f["影響"]][0].replace("影響 ", "")}</td><td>{tag(f["区分"])}</td><td>{e(f["統計"].split("（")[0])}</td><td>{e(HEAD(f))}</td></tr>'
_sup = [f for f in sorted(INSCOPE, key=_ord) if '別系統で支持' in f['確認']]; _pen = [f for f in sorted(INSCOPE, key=_ord) if f not in _sup]
RECS = (f'<p class="muted">重点領域の記録 {len(INSCOPE)} 件（ほかに、範囲を絞る前に検証した統計の記録 {len(OUTSCOPE)} 件を下の欄に置いています）。別系統の LLM の反証で支持された記録を先に、まだ支持されていない記録を、反証にかける前・書き直して再反証待ち・別系統では判定不能（確定）の順に後に並べます（すべての記録に同じ規則。<a href="process.html">進め方 §3</a>）。影響の大きさ（大・中・小）は<a href="method.html">方法</a>の規則で決め、<a href="records/">記録の一覧</a>で絞り込めます。</p>'
        + f'<table class="rt"><tr><th>ID</th><th>影響</th><th>区分</th><th>統計</th><th>見出し</th></tr><tr class="rsep"><td colspan="5">別系統で支持 {len(_sup)} 件</td></tr>' + ''.join(_rr(f) for f in _sup)
        + ''.join(f'<tr class="rsep"><td colspan="5">{ST_JA[k]} {len(g)} 件</td></tr>' + ''.join(_rr(f) for f in g) for k in ST_PEND for g in [[f for f in _pen if STATE(f) == k]] if g) + '</table>')
TIERS = ''
# 確かめたことの説明（何と何を照合したか）。数は verified.json から。説明つきの食い違いは、件数が想定と同じときだけ説明を出す
STAGE_OF = lambda f: {'未照会': 0, '未照会（追加の照会を送る前）': 0, '照会中': 1, '照会中・資料の改訂あり': 1, '回答あり': 2, '期限までに回答なし': 2, '期限までに回答なし・資料の改訂あり': 2}.get(f['照会'], 1)
def revblock(f):
    """資料の差し替え（publish/revisions.json）。判定はせず、検出日・資料・引用した箇所の前後・改訂前の写しを並べる（2026-11-20）。"""
    R_ = f.get('改訂') or []
    if not R_: return ''
    it = ''.join(f'<li><b>{e(r["detected"])}</b> に差し替えを検出　<a href="{e(r["url"])}">資料</a>'
                 + (f'　<a href="{e(r["wayback_before"])}">差し替え前の写し（Wayback Machine）</a>' if r.get('wayback_before') else '')
                 + f'<br><span class="muted">{e(r["label"])}：引用した箇所は{"<b>変わった</b>" if r["quote_changed"] else "同じ"}</span>'
                 + (f'<div class="qt"><span class="muted">前の版</span><br>{e(r["before"])}</div><div class="qt"><span class="muted">新しい版</span><br>{e(r["after"])}</div>' if r['quote_changed'] else '')
                 + f'<br><span class="muted">SHA-256　前 <code>{e(r["sha256_old"][:16])}…</code>　後 <code>{e(r["sha256_new"][:16])}…</code></span></li>' for r in R_)
    return ('<h2>資料の差し替え</h2><p class="muted">この記録の根拠の資料が、取得元で差し替えられたことを毎週の巡回で検出しました。差し替えの理由は判断しません。'
            '前の版のハッシュは公開リポジトリと Zenodo の版に、前の版の写しは取得できた範囲で Wayback Machine に残しています。</p><ul>' + it + '</ul>')
def _prerow(en=False):
    """範囲を絞る前に検証した統計の分を表の最後の行に出し、上の照合の数と表の合計を合わせる（2026-11-19、点検 M3）。"""
    vs = [VER[x] for x in VER if x in PRE]
    c = sum(v['compared'] for v in vs); m = sum(v['mismatched'] for v in vs); ex = sum(v.get('explained', 0) for v in vs)
    t = sum(v['checks_tallied'] for v in vs); n = sum(v['checks_compare'] for v in vs)
    lab = f'Statistics verified before the scope was narrowed ({len(vs)})' if en else f'範囲を絞る前に検証した統計（{len(vs)}）'
    return f'<tr class="rsep"><td colspan="5">{lab}</td></tr><tr><td class="muted">{"total" if en else "合計"}</td><td>{t} / {n}</td><td>{c:,}</td><td>{m:,}</td><td>{ex:,}</td></tr>'
NC = sum(v['compared'] for v in VER.values()); NM = NC - sum(v['mismatched'] for v in VER.values())
NCHK = sum(v['checks_compare'] for v in VER.values()); NTAL = sum(v['checks_tallied'] for v in VER.values())
NS = [sum(1 for f in F if STAGE_OF(f) == k) for k in range(3)]
NFIX = sum(1 for f in F if f['照会'].startswith('公表元が訂正'))
def _stg(lab, num, unit, cls=''):
    return f'<div class="stg {cls}"><span class="sl">{lab}</span><b>{num}</b><span class="su">{unit}</span></div>'
# ---- 引かれ方の枝（2026-11-19）：記録のカードから下へ出る別の流れと、代表の一例
def _cite_branch(en=False):
    recs = CV.D['records']; ncit = sum(len(r['cites']) for r in recs)
    tot = {k: 0 for k in CV.TYPES}
    for r in recs:
        for k, v in CV.counts(r).items(): tot[k] += v
    ndiff = sum(v for k, v in tot.items() if k not in ('同じ', '判定が分かれた'))
    yk = [c for c in CV.BY['YK-C1']['cites'] if c['kind'] == '公的文書' and '認められ' in c['cite_phrase']]
    eds = sorted(c['media'].replace('再犯防止推進白書 ', '') for c in yk)
    if en:
        card = (f'<div class="cbranch"><span class="cba">↳</span><div class="stg cb"><span class="sl">How the sources are cited (outside the flow above)</span>'
                f'<b>{len(recs)}</b><span class="sd">sources of the records are cited {ncit} times in news, official documents and papers; {ndiff} citations differ in form from the source (where both judges agreed). <a href="citations.html">All {len(recs)}</a></span></div></div>')
        ex = (f'<p class="note cbex">For example, <a href="citations/YK-C1.html">YK-C1</a>: the 2022 summary says a treatment effect was <span lang="ja">「示唆された」</span> (suggested); {len(eds)} editions of the White Paper on Recidivism Prevention ({len(eds)} consecutive years) cite it as <span lang="ja">「認められた」</span> (recognised).</p>')
        return card + ex
    card = (f'<div class="cbranch"><span class="cba">↳</span><div class="stg cb"><span class="sl">引かれ方（上の流れとは別に、記録の資料が外でどう引かれているか）</span>'
            f'<b>{len(recs)}</b><span class="sd">件の資料が、報道・公的文書・論文で {ncit} 回引かれている。元の文と違う形で引かれたもの {ndiff}（二つの判定が一致した分）。<a href="citations.html">{len(recs)}件の一覧</a></span></div></div>')
    ex = f'<p class="note cbex">たとえば <a href="citations/YK-C1.html">YK-C1</a>：概要の「示唆された」が、再犯防止推進白書（{"・".join(eds)}）で「認められた」と引かれている。</p>'
    return card + ex
STAGES = ('<div class="stages">' + _stg('照合', f'{NC:,}', f'件のうち一致 {NM:,}。照合の検査 {NCHK} 本のうち、数を集計できた {NTAL} 本の分', 's0') + '<span class="sa">›</span>'
          + _stg('記録（照会前）', NS[0], '件') + '<span class="sa">›</span>' + _stg('照会中', NS[1], '件') + '<span class="sa">›</span>'
          + _stg('回答あり・期限切れ', NS[2], '件') + '<span class="sa">›</span>'
          + f'<div class="stg s9"><span class="sl">決着</span><span class="sd"><b>{NFIX}</b> 公表元が訂正</span><span class="sd"><b>{len(ERR)}</b> <a href="errors.html">URAZUKE 側の訂正・変更の履歴（公開前の修正を含む延べ項目）</a></span></div></div>'
          + '<p class="muted">左から右へ進みます。照合の数は毎週の巡回で更新します。照合で食い違いが見つかり、手順の条件を満たしたものが記録になります。説明のない食い違いの数と記録の数が違うのは、同じ原因（一つの表の写し込みなど）による多数の値の食い違いを、原因ごとに1件の記録にまとめるためと、まだ調べ終えていない食い違いが残っているためです（記録になる条件は<a href="method.html">方法</a>の「発見を確定する条件」）。記録は公開の日に照会文とともに「照会中」になり（<a href="process.html">進め方 §6</a>）、回答は全文を載せます（担当職員の氏名・個人の連絡先などは省きます）。誤りが URAZUKE の側にあれば、記録を訂正・撤回します。</p>')
VDEF = ('<p class="muted">「食い違い」は、資料どうしで値が違ったもの（版の改訂、暫定値と確定値の違いを含みます）。「うち説明あり」は、そのうち違いの理由が資料の中に書かれているもの（注・正誤表・訂正の告知・暫定値や速報値であることの明記など）で、違いが正しいかどうかの判断ではありません。どれを説明ありとしたかは、各統計のページの照合の表と、作業ノート・検査のコードで確かめられます。検査が表を読み違えたもの（読み取りの失敗）は、照合の数に入れていません。</p>')
def vtab(s):
    v = VER.get(s)
    if not v or not v['checks_compare']: return ''
    agg = {}
    for q in v['parts']:
        a = agg.setdefault(q['check'], {'script': q.get('script', ''), 'note': q.get('note', ''), 'n': 0, 'c': 0, 'm': 0, 'x': 0, 'f': 0})
        a['n'] += 1; a['c'] += q['compared']; a['m'] += q['mismatched']; a['x'] += q.get('explained', 0); a['f'] += q['read_failures']
    rows = ''.join(f'<tr><td><code>{e(a["script"])}</code>' + (f'<br><span class="muted">{a["n"]} 回分</span>' if a['n'] > 1 else '') + f'</td><td>{e(a["note"])}</td><td>{a["c"]:,}</td><td>{a["m"]:,}</td><td>{a["x"]:,}</td><td>{a["f"]:,}</td></tr>' for k, a in agg.items())
    return ('<h2>照合</h2><p class="muted">照合の検査 ' + f'{v["checks_compare"]} 本のうち、要約を書き出した {v["checks_tallied"]} 本の分。照合した数 {v["compared"]:,}、食い違い {v["mismatched"]:,}（うち説明あり {v.get("explained", 0):,}）。</p>'
            '<table><tr><th>検査</th><th>照合したもの</th><th>照合した数</th><th>食い違い</th><th>うち説明あり</th><th>読み取りの失敗</th></tr>' + rows + '</table>' + VDEF)
_vrow = lambda s, n: (lambda v: f'<tr><td><a href="stats/{s}.html">{e(n)}</a></td><td>{v["checks_tallied"]} / {v["checks_compare"]}</td>' + (f'<td>{v["compared"]:,}</td><td>{v["mismatched"]:,}</td><td>{v.get("explained", 0):,}' + ('<br><span class="allx">すべて説明あり</span>' if v['mismatched'] and v.get('explained', 0) == v['mismatched'] else '') + '</td>' if v['checks_tallied'] else ('<td colspan="3" class="muted">未集計</td>' if v['checks_compare'] else '<td colspan="3" class="muted">台帳に照合の検査がない</td>')) + '</tr>')(VER.get(s, {'compared': 0, 'mismatched': 0, 'explained': 0, 'checks_compare': 0, 'checks_tallied': 0}))
VERIFIED = (f'<p class="muted">同じになるはずの数字（例：47都道府県の和と全国の数、同じ年の値の版どうし）が、公表物の中で実際に同じになっているかを照合した数です。「一致」は数字どうしに矛盾がないという意味で、数字が実態を正しく表しているかまでは示しません。</p>'
            f'<p class="muted">照合の数は、各検査が同じ形で書き出す要約（<code>lib/tally.py</code>）から数えます。' + (f'照合の検査 {NCHK} 本のすべてが要約を書き出しています。' if NTAL == NCHK else f'いま数えられるのは照合の検査 {NCHK} 本のうち {NTAL} 本で、残りは要約を書き出すように検査を直している途中です（「未集計」）。') + 'どの統計も同じ扱いで並べています。</p>'
            '<table><tr><th>統計</th><th>照合の検査（集計済み / 全体）</th><th>照合した数</th><th>食い違い</th><th>うち説明あり</th></tr>' + ''.join(f'<tr class="rsep"><td colspan="5">{e(fl)}</td></tr>' + ''.join(_vrow(s, _SI[s][1]) for s in g if s in _SI and s not in PRE) for fl, g in FIELD if fl not in PRE_FIELD) + _prerow() + '</table>' + VDEF)
out_rows = ''.join(f'<tr><td><a href="records/{f["id"]}.html">{f["id"]}</a></td><td class="lv{f["影響"]}">{LV[f["影響"]][0]}</td><td>{tag(f["区分"])}</td><td>{e(f["統計"].split("（")[0])}</td><td>{e(HEAD(f))}</td></tr>' for f in OUTSCOPE)
OUTSEC = f'<h2 class="sub">範囲を絞る前に検証した統計の記録（{len(OUTSCOPE)} 件）</h2><p class="muted">重点領域（犯罪・司法・精神医療・福祉）を決める前に検証した統計の記録です。消さずに残しています（<a href="method.html">方法</a>の手順の変更の記録 r10・r20）。</p><table><tr><th>ID</th><th>影響</th><th>区分</th><th>統計</th><th>見出し</th></tr>{out_rows}</table>'
d2 = sum(1 for f in INSCOPE if '別系統で支持' in f['確認'])
d2o = sum(1 for f in OUTSCOPE if '別系統で支持' in f['確認'])  # 点検 #38（2026-11-20）：範囲の外の記録の数も並べて示す
# ---- トップ
latest = ''.join(f'<tr><td><a href="records/{f["id"]}.html">{f["id"]}</a></td><td>{tag(f["区分"])}</td><td>{e(f["統計"].split("（")[0])}</td><td>{e(HEAD(f))}</td><td class="muted">{ST_JA[STATE(f)]}</td></tr>' for f in F[-6:][::-1])
_box = lambda s, n, o, p: f'<div class="box"><h3><a href="stats/{s}.html">{e(n)}</a></h3><p class="muted">{e(o)}</p><p class="muted">{CHK.get(s) or "記録 %d 件" % sum(1 for f in F if p and f["id"].startswith(p+"-"))}</p></div>'
boxes = ''.join(_box(s, n, o, p) for s, n, o, _, p in STATS_ORDERED if s not in PRE)
boxes_pre = ''.join(_box(s, n, o, p) for s, n, o, _, p in STATS_ORDERED if s in PRE)
page('overview.html', '統計', f"""
<h1>統計</h1><p class="muted">照合の結果、記録と照会の進み具合、統計ごとの一覧。手順は<a href="about.html">しくみ</a>にあります。</p>
{STAGES}{_cite_branch()}
<h2 class="tierh">確かめたこと</h2>{VERIFIED}
<h2 class="tierh">記録</h2>{RECS}{TIERS}
<div class="nums lead"><div><b>{NSTAT_IN}</b><span>検証した統計（重点領域）</span></div><div><b>{len(INSCOPE)}</b><span>記録（発見）</span></div><div><b>{d2}</b><span>別系統の検証で支持</span></div><div><b>{NS[1]}</b><span>照会中</span></div></div>
<h2 class="sub">検証のために取得・保存している資料</h2><div class="nums big"><div><b>{SC['numeric_cells']/1e4:,.0f}万</b><span>数値セル（取得した表に含まれる数値の個数）</span></div><div><b>{SC['files']:,}</b><span>取得した資料ファイル</span></div><div><b>{SC['pdf_pages']:,}</b><span>PDF の頁</span></div><div><b>{SC['bytes']/1e9:.1f} GB</b><span>資料の総量</span></div></div>
<p class="muted">上の数は取得した資料の規模で、すべてを個別に照合した数ではありません。数え方は<a href="data.html#scope">データ</a>に書いています。取得元の URL・sha256・取得日時の一覧（MANIFEST の {NSRC:,} 行）も公開します。数の違い（行・URL の種類・手元のファイル）は<a href="data.html#scope">データ</a>に書いています。個人名を含みうる資料は数えていません。</p>

<h2>統計から探す</h2><div class="grid3">{boxes}</div>
<h2 class="sub">範囲を絞る前に検証した統計</h2><div class="grid3">{boxes_pre}</div>
{OUTSEC}
<h2>この場所について</h2><div class="grid3">
<div class="box"><h3><a href="method.html">方法</a></h3><p class="muted">内部の整合、版の比較、他の資料との突き合わせ。確定の条件、確認の状態の意味。</p></div>
<div class="box"><h3><a href="process.html">進め方</a></h3><p class="muted">記録の区分、表示の原則、照会の手順、利益相反と独立性。</p></div>
<div class="box"><h3><a href="errors.html">訂正の記録</a></h3><p class="muted">LLM による記録の誤りと、その訂正。</p></div></div>""")
FLOW_JA = """<ol class="flow">
<li><span class="fn">1</span><b>集める</b><span>国の白書・統計・報告書</span></li>
<li><span class="fn">2</span><b>照合する</b><span>AI（Claude）が数字を突き合わせる</span></li>
<li><span class="fn">3</span><b>疑う</b><span>別の会社の AI（GPT）が、本当かを試す</span></li>
<li><span class="fn">4</span><b>記録する</b><span>試しに残ったものだけを載せる</span></li>
<li><span class="fn">5</span><b>尋ねる</b><span>担当の役所に質問する</span></li>
<li><span class="fn">6</span><b>公開する</b><span>やりとりをそのまま載せる</span></li>
</ol>"""
FLOW_EN = """<ol class="flow">
<li><span class="fn">1</span><b>Collect</b><span>White papers, statistics and reports</span></li>
<li><span class="fn">2</span><b>Compare</b><span>An AI (Claude) checks the numbers against each other</span></li>
<li><span class="fn">3</span><b>Doubt</b><span>An AI from another company (GPT) tries to refute them</span></li>
<li><span class="fn">4</span><b>Record</b><span>Only what survives is recorded</span></li>
<li><span class="fn">5</span><b>Ask</b><span>The responsible office is asked</span></li>
<li><span class="fn">6</span><b>Publish</b><span>The exchange is published as it is</span></li>
</ol>"""
# ---- トップ（r37）：理念・しくみの図・入口だけ。数の詳しいことは overview.html
page('index.html', 'トップ', f"""
<section class="vis"><p class="vlead">国の統計は、政策の裏付けになる。<br>その数字が本当に裏付けになるのかを、確かめて残す。</p>
<p class="videa">日本の犯罪・司法・精神医療・福祉の公開データを、AI が先に決めた手順で照合します。食い違いも、合っていたことも記録し、同じ版の資料を入手できれば誰でも同じ計算をやり直せるように公開します。</p></section>
<h2 class="vh">しくみ</h2>
{FLOW_JA}
<p class="loop"><b>↺</b> 間違いがこちらにあれば、訂正して残します。資料の更新は毎週見回ります。</p>
<div class="why"><b>人が判定しない理由</b><p>運営者は、加害者の治療に携わる精神科医です。調べる対象と、仕事の利害が重なります。そのため、個々の結果を見て掲載の可否を選ぶのではなく、事前に公開した手順に沿って記録します。手順の設計と訂正の責任は、運営者が負います。</p></div>
<div class="nums lead top"><div><b>{NC/1e4:,.0f}万</b><span>照合した数字</span></div><div><b>{len(INSCOPE)}</b><span>記録（重点領域）</span></div><div><b>{NSTAT_IN}</b><span>調べた統計（重点領域）</span></div></div>
<div class="grid3 entry">
<a class="ebox" href="records/"><b>記録を見る</b><span>見つかった食い違いと、その根拠</span></a>
<a class="ebox" href="overview.html"><b>統計</b><span>照合の結果、照会の進み具合、統計ごとの一覧</span></a>
<a class="ebox" href="about.html"><b>しくみ</b><span>手順、AI の役割、利益相反、訂正</span></a></div>
<p class="foot">スクリプトと根拠は <a href="https://github.com/hirokifukui/urazuke">GitHub</a> に公開しています。<a href="mailto:contact@urazuke.org">異論や追加の資料</a>を受けて訂正します。<a href="guide.html">はじめての方へ</a></p>""")
# ---- はじめての方へ（1ページで意味が伝わる案内）
FBY = {f['id']: f for f in F}
GUIDE_EX = [('MK-I1', '版によって数が違い、説明がない', '同じ年の同じ数が、刊行の年によって違う。どの版を引くかで値が変わる。'),
            ('HK-A7', '訂正が公開中のファイルに入っていない', '正誤表で訂正を告知した後も、ダウンロードできる表は訂正前の値のまま。'),
            ('BV-P1', '概要が報告書の結果より強く書かれている', '1枚の概要と報告書の本文で、効果の書き方が違う。'),
            ('YK-C1', '比べ方によって読み方が変わる', '同じデータでも、どの群を比べるかで効果の有無の読み方が変わる。'),
            ('SH-C1', '白書が報告書の但し書きを落としている', '白書の一文が、元の報告書にある再犯の分類と、効果が確認されなかった部分を書かずに効果を述べる。'),
            ('ST-D1', '数える範囲が変わったのに「最多」', '法改正で数える範囲が広がった後の件数を、それ以前の件数と並べて「最多」とする。広がった分の件数は示されていない。')]
assert all(STATE(FBY[i]) == 'sup' for i, _, _ in GUIDE_EX), 'はじめての方への例は別系統で支持された記録に限る'
_gx = ''.join(f'<div class="box"><p class="kick">{e(t)}</p><h3><a href="records/{i}.html">{e(FBY[i]["見出し"])}</a></h3><p class="muted">{e(w)}（{i}・{LV[FBY[i]["影響"]][0]}・{ST_JA["sup"]}）</p></div>' for i, t, w in GUIDE_EX)
page('guide.html', 'はじめての方へ', f"""<h1>はじめての方へ</h1>
<p class="lead">URAZUKE は、日本の犯罪・司法・精神医療・福祉の公的統計を、コードで照合し、食い違いを記録する場所です。</p>
<ul><li>国の統計の数字を、同じ資料の別の表、別の年の版、別の資料と突き合わせます。</li>
<li>合わないところを「記録」として残し、根拠（ファイル・頁・セル）と計算のスクリプトを公開します。</li>
<li>照合と記録は AI（Claude）が行います。別の会社の AI（GPT）に、主張の文を正しいか誤りかを伏せ、偽の主張と混ぜて渡し、資料だけで真偽を判定させます（反証）。</li></ul>
<div class="nums lead"><div><b>{NSTAT_IN}</b><span>検証した統計（重点領域と、その分母に使う統計）</span></div><div><b>{NC:,}</b><span>照合した数値の組（範囲を絞る前の分を含む）</span></div><div><b>{NM:,}</b><span>そのうち一致</span></div><div><b>{len(INSCOPE)}</b><span>記録（重点領域。うち別系統で支持 {d2}）。ほかに範囲を絞る前の統計の記録 {len(OUTSCOPE)}（うち別系統で支持 {d2o}）、計 {len(INSCOPE)+len(OUTSCOPE)}</span></div></div>
<p class="muted">ほとんどの数字は合っています。合っていたことも、記録と同じ手順で残しています（<a href="index.html">トップ</a>の「確かめたこと」）。</p>
<h2>見つかるものの例</h2><div class="grid2">{_gx}</div>
{CV.guide_box('ja')}
<h2>記録の読み方</h2>
<table><tr><th>項目</th><th>意味</th></tr>
<tr><td>影響</td><td>大：報告書の結論・政策の指標・全国の総数に関わる。中：版・資料・表の間で値が食い違う。小：副次的なファイルだけの不備。</td></tr>
<tr><td>確実さ</td><td>確定：資料の上で確かめられた事実。推定：資料から導いたが確定できない部分。要照会：担当部署に尋ねないと分からない部分。</td></tr>
<tr><td>確認の状態</td><td>{ST_JA['sup']}：主張の文を、真偽を伏せて偽の対照の文と混ぜて別の会社の AI に渡し、資料だけで「正しい」と判定された（対照はふつう1回に2件。対照をすべて正しく判定した回だけを採る）。{ST_JA['pre']}・{ST_JA['rew']}：その手順をまだ終えていない。{ST_JA['fin']}：手順を尽くしても判定できなかった（理由を記録に書く）。</td></tr></table>
<h2>URAZUKE がしないこと</h2>
<ul><li>作成者の意図や事情を推測しません。記録するのは、資料の上の事実だけです。</li>
<li>統計や政策の良し悪しを評価しません。</li>
<li>人が記録の内容を判断して取捨しません。手順は<a href="process.html">進め方</a>に固定し、変えたときは<a href="method.html">方法</a>に記します。</li></ul>
<h2>引用・取材の方へ</h2>
<ul><li>引用するときは、記録の ID（例：MK-I1）、ページの URL、見た日付を添えてください。記録は訂正されることがあり、訂正はすべて<a href="errors.html">訂正の記録</a>に残します。</li>
<li>担当部署への照会と回答は、<a href="inquiries.html">照会</a>に全文を載せます（照会日 {SENT['date']}）。</li>
<li>国の統計を引くときの確かめ方は<a href="checklist.html">引く前に確かめること</a>（7項目）にまとめました。</li>
<li>計算は <a href="https://github.com/hirokifukui/urazuke">GitHub</a> のスクリプトで、同じ版の資料を入手できれば誰でもやり直せます（原データは再配布しません。公表元が差し替え・削除した版は入手できないことがあります）。</li>
<li>問い合わせ：<a href="mailto:contact@urazuke.org">contact@urazuke.org</a></li></ul>""")
# ---- 引かれ方（引用の追跡 v0.1）
page('citations.html', '引かれ方', CV.index_body('ja'))
assert all(STATE(FBY[i]) == 'sup' for i in CK.ids()), '引く前にの例は別系統で支持された記録に限る'
page('checklist.html', '引く前に確かめること', CK.body('ja', FBY, None))
for _r in CV.BY: page(f'citations/{_r}.html', f'{_r} の引かれ方', CV.detail(_r, 'ja'))
# ---- 記録一覧
kinds = sorted({f['区分'].split('（')[0] for f in F}); stats = sorted({f['統計'].split('（')[0] for f in F})
_rowj = lambda f: f'<tr data-v="{f["影響"]}" data-k="{e(f["区分"].split("（")[0])}" data-s="{e(f["統計"].split("（")[0])}" data-d="{STATE(f)}"><td><a href="{f["id"]}.html">{f["id"]}</a></td><td class="lv{f["影響"]}">{LV[f["影響"]][0]}</td><td>{tag(f["区分"])}</td><td>{e(f["統計"].split("（")[0])}</td><td>{e(HEAD(f))}</td><td class="muted">{e(f["確実さ"])}</td><td class="muted">{ST_JA[STATE(f)]}</td><td class="muted">{e(f["照会"])}</td></tr>'
rows = type_rows(_rowj, F)
opts = lambda xs: ''.join(f'<option>{e(x)}</option>' for x in xs)
page('records/index.html', '記録', f"""<h1>記録</h1><p class="muted">{len(F)} 件。区分は「進め方」、確実さ・確認の状態は「方法」を参照。</p>
<div class="filters"><select id="fv"><option value="">影響：すべて</option><option value="3">影響 大：結論・指標</option><option value="2">影響 中：値の食い違い</option><option value="1">影響 小：形式の不備</option></select><select id="fk"><option value="">区分：すべて</option>{opts(kinds)}</select><select id="fs"><option value="">統計：すべて</option>{opts(stats)}</select><select id="fd"><option value="">確認の状態：すべて</option>{ST_OPTS_JA}</select></div>
<table id="t"><tr><th>ID</th><th>影響</th><th>区分</th><th>統計</th><th>見出し</th><th>確実さ</th><th>確認の状態</th><th>照会</th></tr>{rows}</table>
<script>const f=()=>{{const v=fv.value,k=fk.value,s=fs.value,d=fd.value;document.querySelectorAll('#t tr[data-k]').forEach(r=>{{r.style.display=(!v||r.dataset.v==v)&&(!k||r.dataset.k==k)&&(!s||r.dataset.s==s)&&(!d||r.dataset.d==d)?'':'none'}})}};[fv,fk,fs,fd].forEach(x=>x.onchange=f)</script>""")
# ---- 記録の個別
for f in F:
    slug = next((s for s, n, o, path, p in STATS if p and f['id'].startswith(p + '-')), None)
    page(f'records/{f["id"]}.html', f['id'], f"""<p class="muted"><a href="index.html">記録</a> ／ {e(f['統計'])}</p>{PRE_NOTE if slug in PRE else ''}
<p class="type3">{type3(f)[1]}</p><h1>{f['id']}　{tag(f['区分'])}</h1><p class="head">{e(plain(f)['見出し'] if plain(f) else f['見出し'])}</p>{hist(f)[1]}{(plain_block(f, plain(f)) + '<h3 class="yoshi">記録の要旨（反証にかけた文）</h3>') if plain(f) else ''}<p class="concl">{inline(f['要旨'])}</p>{'' if plain(f) else cansay(f)}
<div class="card"><dl>
<dt>統計</dt><dd>{e(f['統計'])}{f' — <a href="../stats/{slug}.html">検証の記録</a>' if slug else ''}</dd>
<dt>影響</dt><dd><span class="lv{f['影響']}">{LV[f['影響']][0].replace('影響 ','')}</span>　{LV[f['影響']][1]}</dd><dt>区分</dt><dd>{e(f['区分'])}</dd>
<dt>確実さ</dt><dd>{e(f['確実さ'])}</dd><dt>確認の状態</dt><dd>{e(f['確認'])}</dd>
<dt>原文の引用（頁・シート番号つき）</dt><dd>{''.join(f'<div class="qt"><span class="muted">{e(q["ラベル"])}　{e(q["ファイル"])}　{e(q["箇所"])}</span><br>「{e(q["文"])}」</div>' for q in f.get('原文の引用', [])) or '<span class="muted">準備中</span>'}</dd>
<dt>確かめ方</dt><dd><code>{e(f['再現'])}</code><br><span class="muted">スクリプト：<a href="https://github.com/hirokifukui/urazuke/tree/main">公開リポジトリ</a>（公開リポジトリは版ごとに1つのコミットとして作り、コミットの文に作業用の版を書く。このページを作った作業用の版：{COMMIT}）</span></dd>
<dt>撤回の条件</dt><dd>{e(f['撤回の条件'])}</dd>
<dt>照会先</dt><dd>{e(f['照会先'])}　<a href="../inquiries.html#{qslug(_fname(f['照会先']))}">照会文</a></dd><dt>照会の状態</dt><dd>{e(f['照会'])}</dd></dl></div>
{CV.block(f['id'], 'ja')}
{revblock(f)}<h2>回答</h2><p class="muted">{'まだ照会していません（公開の日の照会の後に記録になったため、追加の照会を送ります）。' if f['照会'].startswith('未照会') else '照会中です（照会日 ' + f.get('照会日', '') + '、回答の期限の目安 ' + f.get('期限', '') + '）。'}回答があれば、手を加えずに全文をここに載せ、論評は付けません。回答が記録の誤りを示した場合は、記録を訂正または撤回します。</p>
{sens(f)}<h2>経過</h2><ul>{hist(f)[0]}</ul>""")
# ---- 統計
def _row(s):
    s, n, o, _, p = _SI[s]
    return f'<tr><td><a href="{s}.html">{e(n)}</a></td><td class="muted">{e(o)}</td><td>{CHK.get(s) or sum(1 for f in F if p and f["id"].startswith(p+"-"))}</td></tr>'
_rest = [x[0] for x in STATS if not any(x[0] in g for _, g in FIELD)]
sb = ''.join(f'<h2>{e(fl)}{PRE_H if fl in PRE_FIELD else ''}</h2><table><tr><th>統計</th><th>公表元</th><th>記録</th></tr>' + ''.join(_row(x) for x in g if x in _SI) + '</table>' for fl, g in FIELD + ([('その他', _rest)] if _rest else []))
page('stats/index.html', '統計', '<meta http-equiv="refresh" content="0; url=../overview.html"><h1>統計</h1><p class="muted"><a href="../overview.html">統計のページ</a>へ移りました。</p>')
for s, n, o, path, p in STATS:
    t = open(os.path.join(R, path)).read()
    recs = ''.join(f'<li><a href="../records/{f["id"]}.html">{f["id"]}</a>　{tag(f["区分"])}　{e(HEAD(f))}</li>' for f in F if p and f['id'].startswith(p + '-'))
    page(f'stats/{s}.html', n, f"""<p class="muted"><a href="index.html">統計</a></p><h1>{e(n)}</h1><p class="muted">公表元：{e(o)}</p>{PRE_NOTE if s in PRE else ''}
<h2>記録</h2><ul>{recs or f'<li class="muted">{CHK.get(s, "検証中・公開記録なし")}</li>'}</ul>{vtab(s)}
<h2>作業ノート</h2><div class="box"><p><b>反証を経ていない作業の記録です。記録として引かないでください。</b>候補、未確認の食い違い、撤回した推測も含むため、サイトには載せず、公開リポジトリに置いています：<a href="https://github.com/hirokifukui/urazuke/blob/main/{path}"><code>{path}</code></a>。合っていた照合は、上の照合の表に載せています。</p></div>""")
# ---- 照会（草案）
iq = ''
for fn in sorted(glob.glob(os.path.join(R, 'publish/inquiries/*.md'))):
    iq += f'<div class="card prose" id="{qslug(os.path.basename(fn)[:-3])}">{md(open(fn).read())}</div>'
from inquiry_dest import bureau as _bureau
_iqtxt = ''.join(open(x).read() for x in glob.glob(os.path.join(R, 'publish/inquiries/*.md')))
_iqtxt += ''.join(open(_p, encoding='utf-8').read() for _p in glob.glob(os.path.join(R, 'publish/letters/追加の照会_*.md')))   # 送付前の追加の照会（公開しない）も照合する
_stale = [f['id'] for f in F if f['要旨'] not in _iqtxt]
assert not _stale, f'照会文の草案が記録の要旨と合わない（publish/build_inquiries.py を回す）: {_stale}'
by = {}
for f in F:
    if not f['照会'].startswith('未照会'): by.setdefault((_bureau(f['照会先']) + ('（追加の照会 ' + f['照会日'] + '）' if f.get('照会日') and f['照会日'] != SENT['date'] else '')), []).append(f)
_pend = [f['id'] for f in F if f['照会'].startswith('未照会')]
st = ''.join(f'<tr><td>{e(k)}</td><td>{len(v)}</td><td>照会中</td><td>{v[0]["期限"]}</td></tr>' for k, v in by.items())
if _pend: st += f'<tr><td>追加の照会（送付前）</td><td>{len(_pend)}</td><td>未照会</td><td>—</td></tr>'
page('inquiries.html', '照会', f"""<h1>照会</h1><p class="muted">照会と同時に「照会中」として公開し、回答は全文を載せます（担当職員の氏名・個人の連絡先などは省きます）。照会から30日を目安に、回答の有無を記録に記します。照会の後に記録の根拠の資料が取得元で差し替えられ、引用した箇所が変わった場合は、照会の状態に「資料の改訂あり」と添え、前後の箇所と差し替え前の写しを記録のページに載せます（差し替えの理由は判断しません）。</p>
<table><tr><th>照会先</th><th>項目</th><th>状態</th><th>期限</th></tr>{st}</table><h2>照会文（{SENT['date']} 送付。追加の照会はその日付）</h2>{iq}""")
# ---- 方法・進め方
import sys as _sys; _sys.path.insert(0, os.path.join(R, 'translate')); import tr as _tr
GLO = _tr.load_glossary()
GLO_GROUPS = [('区分', '記録の区分', 'Record categories'), ('影響', '影響の大きさ', 'Impact'), ('格付け', '格付け', 'Grades'), ('確実さ', '確実さ', 'Certainty'), ('確認', '確認の状態', 'Verification status'), ('照会', '照会', 'Inquiry'), ('用語', '用語', 'Terms')]
def glo_table(en):
    h = ''
    for g, ja_t, en_t in GLO_GROUPS:
        rows = ''.join(f'<tr><td lang="ja">{e(x["ja"])}</td><td lang="en">{e(x["en"])}</td></tr>' for x in GLO if x['group'] == g)
        h += f'<h3>{en_t if en else ja_t}</h3><table><tr><th lang="ja">日本語（正本）</th><th lang="en">English</th></tr>{rows}</table>'
    return h
GLO_JA = f'<h2 id="glossary">英語版の訳語（対訳表）</h2><p>英語版は日本語の訳で、日本語が正本です。次の訳語を固定し、すべての英語のページで同じ語を使います。意図を表す語（cover-up、manipulation、falsification、concealment など）は英語でも使いません。統計名・機関名の訳は <code>translate/glossary.tsv</code> にあります。</p>{glo_table(False)}'
# ---- 反証の成績（checks/generic/refute_scoreboard.py → results/refute/scoreboard.json）
SB = json.load(open(os.path.join(R, 'results/refute/scoreboard.json')))
AUD = [json.load(open(x)) for x in sorted(glob.glob(os.path.join(R, 'publish/audit/*.json')), reverse=True)]
def audit_section(en=False):
    """定期の点検（3か月に1回、3モデル）。publish/audit/<日付>.json から作る。"""
    if not AUD: return ''
    rows = []
    for d in AUD:
        fs = d['findings']; ver = len(fs)
        done = sum(1 for x in fs if x.get('status') in ('直した', '直さなかった', 'fixed', 'not fixed'))
        items = ''.join(f"<li>[{e(x.get('severity', ''))}・{e(x.get('kind', ''))}・{e(x.get('model', ''))}] {e(x.get('location', ''))}：{e(x.get('problem', ''))}<br><span class=\"muted\">{'Response' if en else '対応'}：{e(x.get('status', ''))}{('（' + e(x.get('response', '')) + '）') if x.get('response') else ''}</span></li>" for x in fs)
        summ = ''.join(f"<li>{e(k)}：{e(v)}</li>" for k, v in d['summaries'].items())
        if en:
            rows.append(f"<h3>{d['date']}</h3><p>Models: {', '.join(f'{k} ({v})' for k, v in d['models'].items())}. Findings: {d['n_findings']} (of which {ver} had their quoted evidence found in the material; {done} handled). Mechanical checks: {d['mechanical']['links']} internal links, {d['mechanical']['n_broken']} broken; {d['mechanical']['lint_problems']} lint problems{' (counted when the review material was assembled, during editing; 0 in the published version)' if d['mechanical'].get('note') else ''}. The findings and summaries below are the models' own words (in Japanese).</p><ul lang=\"ja\">{summ}</ul><details><summary>Each finding and the response ({len(fs)})</summary><ul lang=\"ja\">{items}</ul></details>")
        else:
            rows.append(f"<h3>{d['date']}</h3><p>モデル：{'、'.join(f'{k}（{v}）' for k, v in d['models'].items())}。指摘 {d['n_findings']}（根拠の文が点検の資料の中にあったもの {ver}、対応済み {done}）。機械の点検：内部リンク {d['mechanical']['links']:,}（切れ {d['mechanical']['n_broken']}）、公開前の検査の問題 {d['mechanical']['lint_problems']}{('（' + e(d['mechanical']['note']) + '）') if d['mechanical'].get('note') else ''}。</p><ul>{summ}</ul><details><summary>指摘と対応の一覧（{len(fs)}）</summary><ul>{items}</ul></details>")
    if en:
        return '<h2>Scheduled site review</h2><p>Every three months, three models from three companies (Claude, GPT, Gemini) are called through their APIs to read the main pages, all records and the sources of five randomly chosen records, and to look for problems. A finding is kept only if the sentence it quotes is found in the material. Display problems are fixed; problems in a record go through the refutation procedure; findings on policy, ethics or law wait for the operator’s decision. Each finding is listed with its response.</p>' + ''.join(rows)
    return '<h2>定期の点検</h2><p>3か月に1回、3社のモデル（Claude・GPT・Gemini）を API で呼び、主なページ、記録の全件、無作為に選んだ記録5件の根拠の原文を読ませて、不備を探させます。指摘は、引いた文が点検の資料の中にあるものだけを採ります。表示の不備は直し、記録の中身は反証の手順にかけ、方針・倫理・法務の指摘は運営者の判断を待ちます。指摘ごとに対応を載せます。</p>' + ''.join(rows)
def sb_table(en=False):
    hd = ('Round', 'Claims', 'Supported', 'Refuted', 'No verdict', 'Controls', 'Used') if en else ('回', '本題', '支持', '反証', '判定不能', '対照', '採否')
    rows = ''.join(f'<tr><td><a href="https://github.com/hirokifukui/urazuke/tree/main/replications">{x["round"]}</a></td><td>{x["n"]}</td><td>{x["支持"]}</td><td>{x["反証"]}</td><td>{x["判定不能"]}</td><td>{x["controls"]}</td><td>{("used" if x["adopted"] else "not used (control failed)") if en else ("採用" if x["adopted"] else "採らない（対照の不備）")}</td></tr>' for x in SB['rounds'])
    t = SB['total']
    if en:
        lead = f'<h2>Record of refutation checks</h2><p>{t["rounds"]} rounds, of which {t["rounds_adopted"]} were used (all controls answered correctly). In the rounds used, {t["n"]} claims were judged: supported {t["支持"]}, refuted {t["反証"]}, no verdict {t["判定不能"]}. A refuted or undetermined claim was rewritten or withdrawn and checked again; see Corrections. Counted by script from each round’s SCORING.md.</p>'
    else:
        lead = f'<h2>反証の成績</h2><p>{t["rounds"]}回のうち、対照をすべて正しく判定した {t["rounds_adopted"]}回の結果を採った。採った回で判定した主張は {t["n"]}：支持 {t["支持"]}、反証 {t["反証"]}、判定不能 {t["判定不能"]}。反証・判定不能の主張は書き直すか撤回し、もう一度反証にかけた（訂正の記録）。各回の SCORING.md からスクリプトで数えた。</p>'
    return lead + '<table><tr>' + ''.join(f'<th>{h}</th>' for h in hd) + f'</tr>{rows}</table>'
page('method.html', '方法', f'<div class="prose">{md(open(os.path.join(R,"METHODS.md")).read())}{sb_table()}{audit_section()}{GLO_JA}</div>')
page('terms.html', '規約', f'<div class="prose">{md(open(os.path.join(R,"TERMS.md")).read())}</div>')
page('process.html', '進め方', f'<div class="prose">{md(open(os.path.join(R,"PROCESS.md")).read())}</div>')
# ---- 訂正の記録
er = ''.join(f'<tr><td class="muted">{d}</td><td><a href="stats/{s}.html">{e(n)}</a></td><td>{e(t)}</td></tr>' for d, n, t, s in ERR)
page('errors.html', '訂正の記録', f'<h1>訂正の記録</h1><p class="muted">LLM による記録に誤りが見つかった場合は、元の記録と同じ目立ち方で訂正し、ここに残します（進め方 §8）。多くは、別系統の AI による反証で見つかっています。</p><table><tr><th>日付</th><th>対象</th><th>内容</th></tr>{er}</table>')
# ---- データ
os.makedirs(os.path.join(OUT, 'data'), exist_ok=True)
shutil.copy(os.path.join(R, 'publish/findings.json'), os.path.join(OUT, 'data/findings.json'))
shutil.copy(os.path.join(R, 'publish/findings.tsv'), os.path.join(OUT, 'data/findings.tsv'))
nman = len(glob.glob(os.path.join(R, 'publish/source_manifests/*')))
page('data.html', 'データ', f"""<h1>データと再現</h1><ul><li><a href="data/findings.json">findings.json</a>・<a href="data/findings.tsv">findings.tsv</a>（記録の一覧）</li>
<li>スクリプト・記録・取得元の一覧（{nman} の MANIFEST）は、固定したバージョンとともに GitHub で公開しています。</li>
<li>DOI：10.5281/zenodo.24357841（予約済み。公開の日に、公開リポジトリと同じ版を Zenodo に置いて有効にします）。</li>
<li>取得元の指紋：全 MANIFEST をまとめた一覧（URL・sha256・取得日時）と、2026-11-18 に各 URL へ送った HEAD の応答（状態・長さ・Last-Modified・ETag）を results/fingerprint/ に置いています。手元の写しの sha256 は、計算し直して MANIFEST と照らしました。週1回の巡回で、この控えと比べて差し替えを見つけています。巡回ごとの報告は results/crawl/ にあります。</li>
</ul><h2 id="scope">取得した資料の数え方</h2><ul><li>数の違い：MANIFEST の行 {NSRC:,}（同じ URL を別の統計の MANIFEST にも載せたものを含む）、URL の種類 8,462（取得元の指紋で HEAD を送った対象は、このうち web.archive.org を除く 8,423）、手元のファイル {SC['files']:,}（個人名を含みうる資料を除き、MANIFEST の外の派生ファイルを含む）。上部の帯の「取得元」は最後の取得の回で数えた URL の種類。</li><li>対象：取得した原データのうち、個人名を含みうる資料（教育委員会の処分ごとの発表）を除いたすべて。{SC['files']:,} ファイル、{SC['bytes']/1e9:.2f} GB。</li><li>数値セル {SC['numeric_cells']:,}：Excel（xlsx {SC['xlsx']:,}・xls {SC['xls']:,}）の数値型のセルと、CSV（{SC['csv']}）の数値の欄を数えた。同じ表の別の版、年報と白書の重複、機械判読用と閲覧用の重複を含む。PDF の中の数値は含まない。</li><li>PDF {SC['pdf']:,} ファイル・{SC['pdf_pages']:,} 頁、HTML {SC['html']:,} ファイル。</li><li>これは取得した資料の規模で、照合した値の数ではない。照合した数は、各統計のページの照合の表（と公開リポジトリの作業ノート）に検査ごとに書いている。</li><li>数えるスクリプト：<code>checks/generic/count_scope.py</code>、結果：<code>results/scope/scope.json</code>。</li></ul><h2>再配布について</h2><ul><li>原データそのものは再配布しません。取得元の URL・sha256・Last-Modified を公開します。</li>
<li>個人名を含みうる資料（教育委員会の処分ごとの発表など）は、ファイルも URL も載せません。</li></ul>""")
# ==== 英語版（/en/）。日本語が正本、英語は訳。訳文は translate/en/ から原文の sha256 で引く（生成の時に LLM は呼ばない）。
TS = _tr.Store()
def T(ja, src, group=None): return TS.t(ja, src, group)
def stat_name_en(n): return T(n, SRC_S, 'stats')
def mdT(text, src): return md('\n'.join(T(c, src) for c in _tr.chunks(text)))
_WDE = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
def jde(s):
    d = _dt.date.fromisoformat(s); return f'{_WDE[d.weekday()]} {d.day} {d.strftime("%B")} {d.year}'
CRAWL_EN = (f'''<div class="crawl"><div class="cin"><span class="dot"></span><span class="cl"><b class="wk">Weekly automatic check</b>　{'Last' if _last['kind'] == '週1回の巡回' else 'Last fetch'}</span><b>{jde(_last['date'])}</b><span class="sep"></span><span class="cl">Changed sources</span><b>{_n(CRN['changed'])}</b><span class="sep"></span><span class="cl">Next</span><b>{jde(CR['next'])}</b><a class="cmore" href="@PRE@about.html#crawl">How it works</a></div></div>''' if CR.get('active') else f'''<div class="crawl"><div class="cin"><span class="dot off"></span><span class="cl">Sources fetched</span><b>{jde(_last['date'])}</b><span class="sep"></span><span class="cl">Scheduled crawl (every {CR['interval_days']} days)</span><b>In preparation</b><span class="cn">A system to fetch the {_last['sources']:,} sources again and have an LLM check and record any change is in preparation</span></div></div>''')
NAV_EN = [('records/', 'Records'), ('overview.html', 'Statistics'), ('citations.html', 'Citations'), ('inquiries.html', 'Inquiries'), ('about.html', 'How it works')]
def page_en(path, title, body, srcs=''):
    body = add_lead(path, body, True)
    d = path.count('/'); pre = '../' * d; root = '../' * (d + 1)
    nav = ''.join(f'<a href="{pre}{h}">{t}</a>' for h, t in NAV_EN) + f'<a href="{root}{path}" hreflang="ja" lang="ja">日本語</a>'
    notice = f'<p class="muted" style="border:1px solid var(--line);background:#fff;padding:.6rem .9rem">This page is an English translation. <strong>The Japanese version is authoritative</strong>; where the two differ, the Japanese prevails. <a href="{root}{path}" lang="ja" hreflang="ja">日本語（正本）</a>{srcs}</p>'
    doc = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><link rel="alternate" hreflang="ja" href="{root}{path}">{head_extra(root, "og-en.png", "en/" + path, title, "Verifying public data on crime, justice, psychiatry and welfare in Japan with reproducible methods, and keeping a record.", "en_US")}<title>{e(title)} — URAZUKE (draft)</title><link rel="stylesheet" href="{root}style.css"><script>window.va = window.va || function () {{ (window.vaq = window.vaq || []).push(arguments); }};</script><script defer src="/_vercel/insights/script.js"></script></head><body>
<div class="draft">DRAFT — NOT PUBLIC. Before review by legal counsel. The content is not final.</div>
{CRAWL_EN.replace('@PRE@', pre)}
<header class="site"><a class="logo" href="{pre}index.html">{MARK}URAZUKE</a><nav>{nav}</nav></header>
<main>{notice}{body}</main>
<footer>URAZUKE — Verifying public data on crime, justice, psychiatry and welfare in Japan, and keeping a record.<br><a href="{pre}errors.html">Corrections</a>　<a href="{pre}terms.html">Terms and Privacy</a><br>Objections, additional sources, reports of errors: <a href="mailto:contact@urazuke.org">contact@urazuke.org</a> (Japanese or English)</footer></body></html>"""
    doc = _mobile(doc)
    p = os.path.join(OUT, 'en', path); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w').write(doc)
SRC_F = 'publish/findings.json'
def ftr(f, k): return T(HEAD(f) if k == '見出し' else f[k], SRC_F, f['id'])
def kind_en(k): return _tr.GL.get(k.split('（')[0], k.split('（')[0])
def tag_en(k): return f'<span class="tag {kcls(k)}">{e(kind_en(k))}</span>'
def stat_short_en(f):
    # 一覧・絞り込み用の短い名前。訳が原題を `…` で残している場合は、原題を除いて英語の部分だけにする
    t = T(f['統計'].split('（')[0], SRC_F, f['id'])
    u = re.sub(r'\s*\(\s*\)', '', re.sub(r'`[^`]*`', '', t)).strip()
    u = re.sub(r'^\((.*)\)$', r'\1', u).strip(' ,;')
    return u or t
LV_EN = {3: ('Impact: High', 'Affects conclusions or indicators', 'A report’s conclusion or summary, a policy indicator, or a national total changes, or its reading changes'),
         2: ('Impact: Medium', 'Values disagree', 'Values differ, or are missing, between editions, sources or tables'),
         1: ('Impact: Low', 'Format defect', 'A defect in a machine-readable file only; the main values are correct')}
SUP = lambda f: '別系統で支持' in f['確認']
CONF = lambda f: T(f['確認'].replace('（順次、人が確認中）', ''), SRC_F, f['id'])
SRC_S = 'site/build_site.py'
def tiercol_en(lv):
    fs = [f for f in INSCOPE if f['影響'] == lv]; sup = [f for f in fs if SUP(f)]; rest = [f for f in fs if f not in sup]
    li = lambda f, c='': f'<li class="{c}"><a href="records/{f["id"]}.html"><span class="tid">{f["id"]}</span>{inline(ftr(f, "見出し"))}</a><span class="tmeta">{e(stat_short_en(f))}</span></li>'
    items = ''.join(li(f) for f in sup) + ''.join(f'<li class="tsep">{ST_EN[k]}: {len(g)}</li>' + ''.join(li(f, 'pend') for f in g) for k in ST_PEND for g in [[f for f in rest if STATE(f) == k]] if g)
    m, lab, sub = LV_EN[lv]
    return f'<div class="tier t{lv}"><div class="kick">{m.upper()}</div><div class="big"><b>{len(sup)}</b><span>supported by an independent model</span></div><h3>{lab}</h3><p class="tsub">{sub}</p><ul>{items}</ul></div>'
_rr_en = lambda f: f'<tr><td><a href="records/{f["id"]}.html">{f["id"]}</a></td><td class="lv{f["影響"]}">{LV_EN[f["影響"]][0].replace("Impact: ", "")}</td><td>{tag_en(f["区分"])}</td><td>{e(stat_short_en(f))}</td><td>{inline(ftr(f, "見出し"))}</td></tr>'
RECS_EN = (f'<p class="muted">{len(INSCOPE)} records in the focus areas (a further {len(OUTSCOPE)} records on statistics verified before the scope was narrowed are listed further below). Records supported by a refutation check by an independent LLM come first; records not yet supported follow, in this order: not yet put to a refutation check, rewritten and awaiting a new check, and undetermined by an independent model (final) (the same rule for every record; <a href="process.html">Process §3</a>). Impact (high, medium, low) is set by the rules in <a href="method.html">Methods</a> and can be filtered in the <a href="records/">list of records</a>.</p>'
        + f'<table class="rt"><tr><th>ID</th><th>Impact</th><th>Category</th><th>Statistic</th><th>Heading</th></tr><tr class="rsep"><td colspan="5">Supported by an independent model: {len(_sup)}</td></tr>' + ''.join(_rr_en(f) for f in _sup)
        + ''.join(f'<tr class="rsep"><td colspan="5">{ST_EN[k]}: {len(g)}</td></tr>' + ''.join(_rr_en(f) for f in g) for k in ST_PEND for g in [[f for f in _pen if STATE(f) == k]] if g) + '</table>')
TIERS_EN = ''
STAGES_EN = ('<div class="stages">' + _stg('Compared', f'{NC:,}', f'of which {NM:,} matched; from the {NTAL} of {NCHK} comparison checks whose counts have been tallied', 's0') + '<span class="sa">›</span>'
          + _stg('Recorded (before inquiry)', NS[0], 'records') + '<span class="sa">›</span>' + _stg('Inquiry pending', NS[1], 'records') + '<span class="sa">›</span>'
          + _stg('Response received or deadline passed', NS[2], 'records') + '<span class="sa">›</span>'
          + f'<div class="stg s9"><span class="sl">Settled</span><span class="sd"><b>{NFIX}</b> corrected by the publisher</span><span class="sd"><b>{len(ERR)}</b> <a href="errors.html">entries in URAZUKE’s log of corrections and changes (including pre-publication fixes)</a></span></div></div>'
          + '<p class="muted">Read from left to right. The comparison counts are updated by the weekly crawl. A mismatch found in comparison becomes a record when it meets the conditions of the procedure. On the day of publication, records become “inquiry pending” together with the inquiry letters (<a href="process.html">Process §6</a>), and responses are published in full (staff names and personal contact details are omitted). If the error is on URAZUKE’s side, the record is corrected or withdrawn.</p>')
VDEF_EN = ('<p class="muted">A “mismatch” is a case where the sources give different values (including revisions between editions and differences between preliminary and final figures). “Of which explained” counts the mismatches whose reason is stated in the sources themselves (a note, an errata sheet, a correction notice, or a statement that the figure is preliminary); it is not a judgement on whether the difference is right. Which mismatches were counted as explained can be checked in the comparison table on each statistic’s page, in the working notes and in the code of each check. Cases where a check misread a table (read failures) are not counted as comparisons.</p>')
def vtab_en(s):
    v = VER.get(s)
    if not v or not v['checks_compare']: return ''
    agg = {}
    for q in v['parts']:
        a = agg.setdefault(q['check'], {'script': q.get('script', ''), 'note': q.get('note', ''), 'n': 0, 'c': 0, 'm': 0, 'x': 0, 'f': 0})
        a['n'] += 1; a['c'] += q['compared']; a['m'] += q['mismatched']; a['x'] += q.get('explained', 0); a['f'] += q['read_failures']
    rows = ''.join(f'<tr><td><code>{e(a["script"])}</code>' + (f'<br><span class="muted">{a["n"]} runs</span>' if a['n'] > 1 else '') + f'</td><td>{inline(T(a["note"], SRC_S, "vnote")) if a["note"] else ""}</td><td>{a["c"]:,}</td><td>{a["m"]:,}</td><td>{a["x"]:,}</td><td>{a["f"]:,}</td></tr>' for k, a in agg.items())
    return ('<h2>Comparisons</h2><p class="muted">' + f'From the {v["checks_tallied"]} of {v["checks_compare"]} comparison checks that write a summary: {v["compared"]:,} comparisons, {v["mismatched"]:,} mismatches (of which {v.get("explained", 0):,} explained).</p>'
            '<table><tr><th>Check</th><th>What was compared</th><th>Comparisons</th><th>Mismatches</th><th>of which explained</th><th>Read failures</th></tr>' + rows + '</table>' + VDEF_EN)
_vrow_en = lambda s, n: (lambda v: f'<tr><td><a href="stats/{s}.html">{e(stat_name_en(n))}</a></td><td>{v["checks_tallied"]} / {v["checks_compare"]}</td>' + (f'<td>{v["compared"]:,}</td><td>{v["mismatched"]:,}</td><td>{v.get("explained", 0):,}' + ('<br><span class="allx">all explained</span>' if v['mismatched'] and v.get('explained', 0) == v['mismatched'] else '') + '</td>' if v['checks_tallied'] else ('<td colspan="3" class="muted">not yet tallied</td>' if v['checks_compare'] else '<td colspan="3" class="muted">no comparison checks in the register</td>')) + '</tr>')(VER.get(s, {'compared': 0, 'mismatched': 0, 'explained': 0, 'checks_compare': 0, 'checks_tallied': 0}))
VERIFIED_EN = (f'<p class="muted">The number of comparisons of figures that should be the same (for example, the sum of the 47 prefectures and the national figure, or the same year’s value in different editions) to see whether they are in fact the same in the published material. “Matched” means the figures do not contradict each other; it does not show whether the figures correctly reflect reality.</p>'
            f'<p class="muted">The counts come from summaries that each check writes in the same format (<code>lib/tally.py</code>). ' + (f'All {NCHK} comparison checks write the summary. ' if NTAL == NCHK else f'At present {NTAL} of the {NCHK} comparison checks can be counted; the others are being modified to write the summary (“not yet tallied”). ') + 'Every statistic is listed in the same way.</p>'
            '<table><tr><th>Statistic</th><th>Comparison checks (tallied / all)</th><th>Comparisons</th><th>Mismatches</th><th>of which explained</th></tr>' + ''.join(f'<tr class="rsep"><td colspan="5">{FIELD_EN[fl]}</td></tr>' + ''.join(_vrow_en(s, _SI[s][1]) for s in g if s in _SI and s not in PRE) for fl, g in FIELD if fl not in PRE_FIELD) + _prerow(True) + '</table>' + VDEF_EN)
OUTSEC_EN = f'<h2 class="sub">Records on statistics verified before the scope was narrowed ({len(OUTSCOPE)})</h2><p class="muted">Records on statistics verified before the focus areas (crime, justice, psychiatry and welfare) were set. They are kept, not deleted (Methods, change record r10 and r20).</p><table><tr><th>ID</th><th>Impact</th><th>Category</th><th>Statistic</th><th>Heading</th></tr>' + ''.join(f'<tr><td><a href="records/{f["id"]}.html">{f["id"]}</a></td><td class="lv{f["影響"]}">{LV_EN[f["影響"]][0].replace("Impact: ", "")}</td><td>{tag_en(f["区分"])}</td><td>{e(stat_short_en(f))}</td><td>{inline(ftr(f, "見出し"))}</td></tr>' for f in OUTSCOPE) + '</table>'
def chk_en(s, p):
    if CHK.get(s): return T(CHK[s], SRC_S, 'chk')
    n = sum(1 for f in F if p and f['id'].startswith(p + '-'))
    return f'{n} record' + ('' if n == 1 else 's')
_box_en = lambda s, n, o, p: f'<div class="box"><h3><a href="stats/{s}.html">{e(stat_name_en(n))}</a></h3><p class="muted">{inline(T(o, SRC_S, "stats"))}</p><p class="muted">{inline(chk_en(s, p))}</p></div>'
boxes_en = ''.join(_box_en(s, n, o, p) for s, n, o, _, p in STATS_ORDERED if s not in PRE)
boxes_pre_en = ''.join(_box_en(s, n, o, p) for s, n, o, _, p in STATS_ORDERED if s in PRE)
IDEA = 'その数字を裏付けとして使えるかどうかを、使う人が確かめられるように。合っていたことも、食い違っていたことも、まだ決着のつかない論点も、同じ手順で残します。'
HERO1 = '検証は AI が行います。照合と記録は Claude（Anthropic）がコードで行います。反証は、照合に関わらない GPT（OpenAI）が行います。主張の文を、真偽の分かっている対照の文と混ぜて渡し、渡した資料だけで判定させます（独立の専門家の査読ではありません）。検証の状態は各記録に示します。個々の記録の文と判定は人が書き換えません。運営者は対象の選択と手順・表示の設計を決め（変更は方法に記録）、訂正を担い、最終的な責任を負います。'
HERO2 = 'スクリプト、取得した資料の一覧、各記録の根拠は GitHub に公開し、同じ版の資料を入手できれば同じ計算を誰でもやり直せるようにしています（取得した版は sha256 で識別します。原データは再配布せず、公表元が差し替え・削除した版は入手できないことがあります）。URAZUKE の記録そのものも検証の対象です。異論や追加の資料を受けて、更新し、訂正します。'
page_en('overview.html', 'Statistics', f"""
<h1>Statistics</h1><p class="muted">Comparison results, the progress of records and inquiries, and a list by statistic. The procedure is under <a href="about.html">How it works</a>.</p>
{STAGES_EN}{_cite_branch(True)}
<h2 class="tierh">What was confirmed</h2>{VERIFIED_EN}
<h2 class="tierh">Records</h2>{RECS_EN}{TIERS_EN}
<div class="nums lead"><div><b>{NSTAT_IN}</b><span>statistics verified (focus areas)</span></div><div><b>{len(INSCOPE)}</b><span>records (findings)</span></div><div><b>{d2}</b><span>supported by an independent model</span></div><div><b>{NS[1]}</b><span>inquiries pending</span></div></div>
<h2 class="sub">Sources fetched and stored for verification</h2><div class="nums big"><div><b>{SC['numeric_cells']/1e6:,.1f} million</b><span>numeric cells (numbers contained in the fetched tables)</span></div><div><b>{SC['files']:,}</b><span>source files fetched</span></div><div><b>{SC['pdf_pages']:,}</b><span>PDF pages</span></div><div><b>{SC['bytes']/1e9:.1f} GB</b><span>total size of sources</span></div></div>
<p class="muted">These figures describe the size of the fetched sources, not the number of values individually checked. How they are counted is described under <a href="data.html#scope">Data</a>. A list of source URLs, sha256 hashes and fetch times ({NSRC:,} entries) is also published. Sources that may contain personal names are not counted.</p>
<h2>Browse by statistic</h2><div class="grid3">{boxes_en}</div>
<h2 class="sub">Statistics verified before the scope was narrowed</h2><div class="grid3">{boxes_pre_en}</div>
{OUTSEC_EN}
<h2>About this site</h2><div class="grid3">
<div class="box"><h3><a href="method.html">Methods</a></h3><p class="muted">Internal consistency, comparison of editions, cross-checks with other sources. Conditions for establishing a finding, what the verification statuses mean, what the operator decides and why no person rewrites individual records. Glossary of fixed English terms.</p></div>
<div class="box"><h3><a href="process.html">Process</a></h3><p class="muted">Record categories, display principles, inquiry procedure, conflicts of interest and independence.</p></div>
<div class="box"><h3><a href="errors.html">Corrections</a></h3><p class="muted">Errors in records made by the LLMs, and their corrections.</p></div></div>""")
# ---- Home (r37)
page_en('index.html', 'Home', f"""
<section class="vis"><p class="vlead">National statistics underpin policy.<br>We check whether the numbers can bear that weight, and keep a record.</p>
<p class="videa">Public data on crime, justice, psychiatry and welfare in Japan are compared by AI following a procedure fixed in advance. Mismatches and matches alike are recorded and published so that anyone who can obtain the same versions of the sources can redo the same calculations.</p></section>
<h2 class="vh">HOW IT WORKS</h2>
{FLOW_EN}
<p class="loop"><b>↺</b> If the error is ours, we correct it and keep the record. Sources are checked for updates every week.</p>
<div class="why"><b>Why no person decides</b><p>The operator is a psychiatrist who treats people who have offended. The subjects examined overlap with the operator’s work. So results are not selected for publication after they are seen; they are recorded by a procedure published in advance. The operator is responsible for the design of the procedure and for corrections.</p></div>
<div class="nums lead top"><div><b>{NC/1e6:,.2f} million</b><span>numbers compared</span></div><div><b>{len(INSCOPE)}</b><span>records (focus areas)</span></div><div><b>{NSTAT_IN}</b><span>statistics examined (focus areas)</span></div></div>
<div class="grid3 entry">
<a class="ebox" href="records/"><b>Records</b><span>Mismatches found and their evidence</span></a>
<a class="ebox" href="overview.html"><b>Statistics</b><span>Comparison results, inquiry progress, list by statistic</span></a>
<a class="ebox" href="about.html"><b>How it works</b><span>Procedure, roles of the AI, conflicts of interest, corrections</span></a></div>
<p class="foot">Scripts and evidence are published on <a href="https://github.com/hirokifukui/urazuke">GitHub</a>. We correct records in response to <a href="mailto:contact@urazuke.org">objections or further sources</a>. <a href="guide.html">In brief</a></p>""")
# ---- しくみ（r39）：運営の裏側の入口
page('about.html', 'しくみ', f"""<h1>しくみ</h1><p class="plain">URAZUKE がどう動いているかの入口です。流れは下の図のとおりです。詳しいことは、知りたいことに合わせて下のページへ進んでください。</p>
{FLOW_JA}
<p class="loop"><b>↺</b> 間違いがこちらにあれば、訂正して残します。資料の更新は毎週見回ります。</p>
<h2 id="crawl">毎週の自動巡回</h2><p>取得元を毎週問い合わせ、変わった資料を取り直して検査し、AI が確かめてから記録に反映します。公開の前に機械の関門を通し、個人情報などを含むものは止めます。</p>
<table class="crn"><tr><th>取得元</th><th>前回から変わった</th><th>新しい記録</th><th>保留中</th><th>最終 → 次回</th></tr><tr><td>{_n(CRN['sources'])}</td><td>{_n(CRN['changed'])}</td><td>{_n(CRN['new'])}</td><td>{_n(CRN['hold'])}</td><td>{jd(_last['date'])} → {jd(CR['next'])}</td></tr></table>
<p class="crflow"><b>日</b> 資料を問い合わせて照合　→　<b>月</b> AI が確かめる　→　公開・Zenodo に版</p>
<ul class="crscope"><li><b>統計の資料</b>　<a href="overview.html">{len(STATS)}の統計</a>（犯罪白書、犯罪統計・警察白書、再犯防止推進白書、児童虐待相談対応件数など）</li>
<li><b>新しい版の入口</b>　{_n(CRN['entry'])}ページ（白書・年報の版の一覧、e-Stat の新着、警察庁・法務省・厚生労働省・文部科学省の報道発表など）</li>
<li><b>検討会・審議会</b>　警察庁・法務省・厚生労働省・こども家庭庁・文部科学省・内閣府男女共同参画局（これまでに拾った資料 {_n(CRN['council_docs'])}）</li>
<li><b>国会</b>　会議録の発言と、質問主意書・答弁書。記録のある資料の数字が、どう引かれているか</li></ul>
<p class="muted">手順の細部（関門で止めるもの、1回に照合する件数、記録に加える条件）は<a href="method.html">方法</a>に。</p>
<div class="grid3 entry">
<a class="ebox" href="guide.html"><b>はじめての方へ</b><span>記録の読み方と、代表的な例</span></a>
<a class="ebox" href="method.html"><b>方法</b><span>何を照合し、いつ確定とし、AI がどう反証するか</span></a>
<a class="ebox" href="process.html"><b>進め方</b><span>記録の区分、照会の手順、利益相反と独立性</span></a>
<a class="ebox" href="errors.html"><b>訂正の記録</b><span>URAZUKE の側の誤りと、その訂正</span></a>
<a class="ebox" href="data.html"><b>データ</b><span>取得した資料の数え方と出どころ</span></a>
<a class="ebox" href="checklist.html"><b>引く前に確かめること</b><span>国の統計を引くときの7つの確かめ方</span></a></div>""")
page_en('about.html', 'How it works', f"""<h1>How it works</h1><p class="plain">The entry point to how URAZUKE operates. The flow is shown below. For details, go to the page that matches what you want to know.</p>
{FLOW_EN}
<p class="loop"><b>↺</b> If the error is ours, we correct it and keep the record. Sources are checked for updates every week.</p>
<h2 id="crawl">Weekly automatic check</h2><p>Every week the sources are queried; changed sources are fetched again and checked, and AI verifies the result before it reaches the records. Before publication a mechanical gate holds anything containing personal information and the like.</p>
<table class="crn"><tr><th>Sources</th><th>Changed since last</th><th>New records</th><th>On hold</th><th>Last → next</th></tr><tr><td>{_n(CRN['sources'])}</td><td>{_n(CRN['changed'])}</td><td>{_n(CRN['new'])}</td><td>{_n(CRN['hold'])}</td><td>{jde(_last['date'])} → {jde(CR['next'])}</td></tr></table>
<p class="crflow"><b>Sun</b> query and compare sources　→　<b>Mon</b> AI verifies　→　publish, new Zenodo version</p>
<ul class="crscope"><li><b>Statistics</b>　<a href="overview.html">{len(STATS)} statistics</a> (White Paper on Crime, crime statistics and the Police White Paper, the White Paper on Recidivism Prevention, child abuse consultations, and others)</li>
<li><b>Entry pages for new editions</b>　{_n(CRN['entry'])} pages (edition lists of white papers and annual reports, e-Stat new releases, press releases of the NPA, MOJ, MHLW and MEXT, and others)</li>
<li><b>Study groups and councils</b>　NPA, MOJ, MHLW, Children and Families Agency, MEXT, Gender Equality Bureau ({_n(CRN['council_docs'])} documents picked up so far)</li>
<li><b>Diet</b>　Statements in the Diet minutes, and written questions and answers: how numbers from sources with records are cited</li></ul>
<p class="muted">Details of the procedure (what the gate holds, how many items are checked per run, the conditions for adding a record) are in <a href="method.html">Methods</a>.</p>
<div class="grid3 entry">
<a class="ebox" href="guide.html"><b>In brief</b><span>How to read a record, with typical examples</span></a>
<a class="ebox" href="method.html"><b>Methods</b><span>What is compared, when a finding is established, how AI tries to refute it</span></a>
<a class="ebox" href="process.html"><b>Process</b><span>Record categories, inquiry procedure, conflicts of interest and independence</span></a>
<a class="ebox" href="errors.html"><b>Corrections</b><span>Errors on URAZUKE’s side and their corrections</span></a>
<a class="ebox" href="data.html"><b>Data</b><span>How the fetched sources are counted and where they come from</span></a>
<a class="ebox" href="checklist.html"><b>Before citing</b><span>Seven checks before citing national statistics</span></a></div>""")


# In brief (one-page guide)
_gx_en = ''.join(f'<div class="box"><p class="kick">{t}</p><h3><a href="records/{i}.html">{inline(ftr(FBY[i], "見出し"))}</a></h3><p class="muted">{w} ({i} · {LV_EN[FBY[i]["影響"]][0]} · {ST_EN["sup"]})</p></div>' for i, t, w in [
    ('MK-I1', 'The same figure differs between editions, without a note', 'The same figure for the same year differs by the year of publication. The value depends on which edition is cited.'),
    ('HK-A7', 'A published correction is not in the downloadable file', 'After a correction notice, the downloadable table still holds the value before correction.'),
    ('BV-P1', 'A summary states the result more strongly than the report', 'The one-page summary and the report body describe the effect differently.'),
    ('YK-C1', 'The reading changes with the comparison', 'With the same data, whether an effect appears depends on which groups are compared.'),
    ('SH-C1', 'A white paper drops the qualifications of the report', 'A sentence in the white paper states an effect without the type of reoffending and the part where no effect was confirmed, both stated in the original report.'),
    ('ST-D1', 'A "record high" after the scope of counting widened', 'After a legal amendment widened what is counted, the new count is set beside earlier counts and called a record high. The count added by the wider scope is not shown.')])
page_en('guide.html', 'In brief', f"""<h1>In brief</h1>
<p class="lead">URAZUKE checks Japan’s official statistics on crime, justice, psychiatric care and welfare with code, and records the discrepancies it finds.</p>
<ul><li>Figures in government statistics are compared with other tables in the same publication, with other editions, and with other sources.</li>
<li>Where they do not agree, a “record” is kept, with its basis (file, page, cell) and the scripts used for the calculation.</li>
<li>The checking and recording are done by an AI (Claude). Each claim is then given to an AI from another company (GPT), mixed with false claims (controls) and without saying which are true, and GPT judges each from the sources alone (the refutation check).</li></ul>
<div class="nums lead"><div><b>{NSTAT_IN}</b><span>statistics verified (focus areas and statistics used as their denominators)</span></div><div><b>{NC:,}</b><span>pairs of figures compared (including statistics verified before the scope was narrowed)</span></div><div><b>{NM:,}</b><span>of which agree</span></div><div><b>{len(INSCOPE)}</b><span>records in the focus areas ({d2} supported by an independent model); a further {len(OUTSCOPE)} on statistics verified before the scope was narrowed ({d2o} supported), {len(INSCOPE)+len(OUTSCOPE)} in all</span></div></div>
<p class="muted">Most figures agree. What agreed is kept by the same procedure as the records (“What was confirmed” on the <a href="index.html">home page</a>).</p>
<h2>Examples of what is found</h2><div class="grid2">{_gx_en}</div>
{CV.guide_box('en')}
<h2>How to read a record</h2>
<table><tr><th>Item</th><th>Meaning</th></tr>
<tr><td>Impact</td><td>High: affects a report’s conclusion, a policy indicator or a national total. Medium: values disagree between editions, sources or tables. Low: a defect only in a secondary file.</td></tr>
<tr><td>Certainty</td><td>Established: a fact checked against the source. Inferred: derived from the source but not confirmable. Requires inquiry: can only be settled by asking the responsible office.</td></tr>
<tr><td>Verification status</td><td>{ST_EN['sup']}: the claim was given to an AI from another company, without saying whether it was true and mixed with false control claims, and was judged correct from the sources alone (usually two controls per round; only rounds in which all controls were judged correctly are used). {ST_EN['pre']} / {ST_EN['rew']}: that check is not yet complete. {ST_EN['fin']}: the check could not reach a verdict after the full procedure (the reason is written in the record).</td></tr></table>
<h2>What URAZUKE does not do</h2>
<ul><li>It does not guess at the intentions or circumstances of those who produced a statistic. Records state only facts found in the sources.</li>
<li>It does not judge whether a statistic or a policy is good or bad.</li>
<li>No person selects or drops records by their content. The procedure is fixed in <a href="process.html">Process</a>, and changes are noted in <a href="method.html">Methods</a>.</li></ul>
<h2>For citation and press enquiries</h2>
<ul><li>When citing, please give the record ID (for example MK-I1), the page URL and the date you viewed it. Records can be corrected; every correction is kept in <a href="errors.html">Corrections</a>.</li>
<li>Inquiries to the responsible offices and their replies are published in full (staff names and personal contact details omitted) under <a href="inquiries.html">Inquiries</a> (no inquiries have been sent yet).</li>
<li>Checks to make when citing a government statistic are listed in <a href="checklist.html">Before citing a statistic</a> (seven items).</li>
<li>Anyone who can obtain the same versions of the sources can redo the calculations with the scripts on <a href="https://github.com/hirokifukui/urazuke">GitHub</a> (the raw data are not redistributed, and versions the publisher has replaced or removed may no longer be obtainable).</li>
<li>Contact: <a href="mailto:contact@urazuke.org">contact@urazuke.org</a></li></ul>""")
page_en('citations.html', 'How sources are cited', CV.index_body('en', lambda x: T(x, CV.SRC, 'cit-index')))
page_en('checklist.html', 'Before citing a statistic', CK.body('en', FBY, None, lambda k: CV.TYPE_EN[k]))
for _r in CV.BY: page_en(f'citations/{_r}.html', f'How {_r} is cited', CV.detail(_r, 'en', lambda x, _i=_r: T(x, CV.SRC, 'cit-' + _i)))
# 記録の一覧
kinds_en = sorted({kind_en(f['区分']) for f in F}); stats_en = sorted({stat_short_en(f) for f in F})
_rowe = lambda f: f'<tr data-v="{f["影響"]}" data-k="{e(kind_en(f["区分"]))}" data-s="{e(stat_short_en(f))}" data-d="{STATE(f)}"><td><a href="{f["id"]}.html">{f["id"]}</a></td><td class="lv{f["影響"]}">{LV_EN[f["影響"]][0].replace("Impact: ", "")}</td><td>{tag_en(f["区分"])}</td><td>{e(stat_short_en(f))}</td><td>{inline(ftr(f, "見出し"))}</td><td class="muted">{inline(ftr(f, "確実さ"))}</td><td class="muted">{ST_EN[STATE(f)]}</td><td class="muted">{inline(ftr(f, "照会"))}</td></tr>'
rows_en = type_rows(_rowe, F, True)
page_en('records/index.html', 'Records', f"""<h1>Records</h1><p class="muted">{len(F)} records. For categories see Process; for certainty and verification status see Methods.</p>
<div class="filters"><select id="fv"><option value="">Impact: all</option><option value="3">High: conclusions and indicators</option><option value="2">Medium: values disagree</option><option value="1">Low: format defects</option></select><select id="fk"><option value="">Category: all</option>{opts(kinds_en)}</select><select id="fs"><option value="">Statistic: all</option>{opts(stats_en)}</select><select id="fd"><option value="">Verification status: all</option>{ST_OPTS_EN}</select></div>
<table id="t"><tr><th>ID</th><th>Impact</th><th>Category</th><th>Statistic</th><th>Heading</th><th>Certainty</th><th>Verification status</th><th>Inquiry</th></tr>{rows_en}</table>
<script>const f=()=>{{const v=fv.value,k=fk.value,s=fs.value,d=fd.value;document.querySelectorAll('#t tr[data-k]').forEach(r=>{{r.style.display=(!v||r.dataset.v==v)&&(!k||r.dataset.k==k)&&(!s||r.dataset.s==s)&&(!d||r.dataset.d==d)?'':'none'}})}};[fv,fk,fs,fd].forEach(x=>x.onchange=f)</script>""")
PRE_NOTE_EN = '<p class="muted">This statistic was verified before the scope was narrowed to crime, justice, psychiatry and welfare. Its records are kept as they were.</p>'
PRE_H_EN = ' <span class="muted">(verified before the scope was narrowed)</span>'
for f in F:
    slug = next((s for s, n, o, path, p in STATS if p and f['id'].startswith(p + '-')), None)
    quotes = ''.join(f'<div class="qt"><span class="muted">{inline(ftr_q)}　<code>{e(q["ファイル"])}</code>　{inline(T(q["箇所"], SRC_F, f["id"]))}</span><br><span lang="ja">「{e(q["文"])}」</span></div>' for q in f.get('原文の引用', []) for ftr_q in [T(q['ラベル'], SRC_F, f['id'])]) or '<span class="muted">In preparation</span>'
    page_en(f'records/{f["id"]}.html', f['id'], f"""<p class="muted"><a href="index.html">Records</a> / {inline(ftr(f, '統計'))}</p>{PRE_NOTE_EN if slug in PRE else ''}
<p class="type3">{type3(f)[2]}</p><h1>{f['id']}　{tag_en(f['区分'])}</h1><p class="head">{inline(T(plain(f)['見出し'], SRC_F, f['id'])) if plain(f) else inline(ftr(f, '見出し'))}</p>{hist(f, True)[1]}{(plain_block(f, plain(f), True) + '<h3 class="yoshi">Summary of the record (the text put to the refutation check)</h3>') if plain(f) else ''}<p class="concl">{inline(ftr(f, '要旨'))}</p>{'' if plain(f) else cansay(f, True)}
<div class="card"><dl>
<dt>Statistic</dt><dd>{inline(ftr(f, '統計'))}{f' — <a href="../stats/{slug}.html">verification notes</a>' if slug else ''}</dd>
<dt>Impact</dt><dd><span class="lv{f['影響']}">{LV_EN[f['影響']][0].replace('Impact: ', '')}</span>　{LV_EN[f['影響']][1]}</dd><dt>Category</dt><dd>{inline(ftr(f, '区分'))}</dd>
<dt>Certainty</dt><dd>{inline(ftr(f, '確実さ'))}</dd><dt>Verification status</dt><dd>{inline(CONF(f))}</dd>
<dt>Quotations from the source (with page or sheet), in the original Japanese</dt><dd>{quotes}</dd>
<dt>How to reproduce</dt><dd><code>{e(f['再現'])}</code><br><span class="muted">Scripts: <a href="https://github.com/hirokifukui/urazuke/tree/main">public repository</a> (each release of the public repository is one commit whose message names the working version; working version when this page was built: {COMMIT})</span></dd>
<dt>Withdrawal condition</dt><dd>{inline(ftr(f, '撤回の条件'))}</dd>
<dt>Addressee of inquiry</dt><dd>{inline(ftr(f, '照会先'))}　<a href="../../inquiries.html#{qslug(_fname(f['照会先']))}">inquiry letter (Japanese only)</a></dd><dt>Inquiry status</dt><dd>{inline(ftr(f, '照会'))}</dd></dl></div>
{CV.block(f['id'], 'en', lambda x, _i=f['id']: T(x, CV.SRC, 'cit-' + _i))}
<h2>Response</h2><p class="muted">{'No inquiry sent yet (this record was added after the inquiries of the publication day; a further inquiry will be sent).' if f['照会'].startswith('未照会') else 'Inquiry pending (sent ' + f.get('照会日', '') + '; response expected by ' + f.get('期限', '') + ').'} Any response will be published here in full, unedited and without comment. If a response shows the record to be wrong, the record will be corrected or withdrawn.</p>
{sens(f, True)}<h2>History</h2><ul>{hist(f, True)[0]}</ul>""")
# 統計
def _row_en(s):
    s, n, o, _, p = _SI[s]
    return f'<tr><td><a href="{s}.html">{e(stat_name_en(n))}</a></td><td class="muted">{inline(T(o, SRC_S, "stats"))}</td><td>{inline(chk_en(s, p))}</td></tr>'
sb_en = ''.join(f'<h2>{FIELD_EN[fl]}{PRE_H_EN if fl in PRE_FIELD else ""}</h2><table><tr><th>Statistic</th><th>Publisher</th><th>Records</th></tr>' + ''.join(_row_en(x) for x in g if x in _SI) + '</table>' for fl, g in FIELD + ([('その他', _rest)] if _rest else []))
page_en('stats/index.html', 'Statistics', '<meta http-equiv="refresh" content="0; url=../overview.html"><h1>Statistics</h1><p class="muted">Moved to the <a href="../overview.html">Statistics page</a>.</p>')
for s, n, o, path, p in STATS:
    t = open(os.path.join(R, path)).read()
    recs = ''.join(f'<li><a href="../records/{f["id"]}.html">{f["id"]}</a>　{tag_en(f["区分"])}　{inline(ftr(f, "見出し"))}</li>' for f in F if p and f['id'].startswith(p + '-'))
    page_en(f'stats/{s}.html', stat_name_en(n), f"""<p class="muted"><a href="index.html">Statistics</a></p><h1>{e(stat_name_en(n))}</h1><p class="muted">Publisher: {inline(T(o, SRC_S, 'stats'))}</p>{PRE_NOTE_EN if s in PRE else ''}
<h2>Records</h2><ul>{recs or f'<li class="muted">{inline(T(CHK[s], SRC_S, "chk")) if CHK.get(s) else "Under verification; no published records"}</li>'}</ul>{vtab_en(s)}
<h2>Working notes</h2><div class="box"><p><b>These are working notes that have not been through the refutation check. Please do not cite them as records.</b> They include candidates, unconfirmed discrepancies and withdrawn inferences, so they are kept in the public repository, not on the site (Japanese only): <a href="https://github.com/hirokifukui/urazuke/blob/main/{path}"><code>{path}</code></a>. Checks that agreed are listed in the table of checks above.</p></div>""")
# 照会（照会文は日本語だけ）
st_en = ''.join(f'<tr><td>{inline(T(k, SRC_F, "inq"))}</td><td>{len(v)}</td><td>Inquiry pending</td><td>{v[0]["期限"]}</td></tr>' for k, v in by.items())
page_en('inquiries.html', 'Inquiries', f"""<h1>Inquiries</h1><p class="muted">Each inquiry is published as “inquiry pending” when it is sent, and responses are published in full, omitting only staff names, personal contact details and details that could identify third parties. Whether a reply was received is noted in the record about 30 days after the inquiry.</p>
<table><tr><th>Addressee</th><th>Items</th><th>Status</th><th>Deadline</th></tr>{st_en}</table><h2>Inquiry letters (sent {SENT['date']})</h2><p>The inquiry letters are addressed to Japanese government bodies and are written in Japanese only. See the <a href="../inquiries.html" lang="ja" hreflang="ja">Japanese page</a>.</p><p>If, after an inquiry, a source behind a record is replaced at its origin and the quoted passage changes, the inquiry status is marked “source revised”, and the record page shows the passage before and after and a pre-revision copy (Wayback Machine) where available. We do not judge the reason for the revision.</p>""")
GLO_EN = f'<h2 id="glossary">Glossary of English terms</h2><p>The English version is a translation; the Japanese is authoritative. The following renderings are fixed and used on every English page. Words that attribute intent (cover-up, manipulation, falsification, concealment and the like) are not used in English either. Translations of the names of statistics and agencies are in <code>translate/glossary.tsv</code>.</p>{glo_table(True)}'
page_en('method.html', 'Methods', f'<div class="prose">{mdT(open(os.path.join(R, "METHODS.md")).read(), "METHODS.md")}{sb_table(True)}{audit_section(True)}{GLO_EN}</div>')
page_en('process.html', 'Process', f'<div class="prose">{mdT(open(os.path.join(R, "PROCESS.md")).read(), "PROCESS.md")}</div>')
page_en('terms.html', 'Terms', f'<div class="prose">{mdT(open(os.path.join(R, "TERMS.md")).read(), "TERMS.md")}</div>')
er_en = ''.join(f'<tr><td class="muted">{d}</td><td><a href="stats/{s}.html">{inline(T(n, SRC_S, "err"))}</a></td><td>{inline(T(t, SRC_S, "err"))}</td></tr>' for d, n, t, s in ERR)
page_en('errors.html', 'Corrections', f'<h1>Corrections</h1><p class="muted">When an error is found in a record made by the LLMs, it is corrected with the same prominence as the original record and kept here (Process §8). Most were found by refutation checks by an independent model.</p><table><tr><th>Date</th><th>Subject</th><th>Content</th></tr>{er_en}</table>')
page_en('data.html', 'Data', f"""<h1>Data and reproduction</h1><ul><li><a href="../data/findings.json">findings.json</a> · <a href="../data/findings.tsv">findings.tsv</a> (list of records, in Japanese, the authoritative version)</li>
<li>The scripts, records and source lists ({nman} MANIFEST files) are published on GitHub together with a fixed version.</li>
<li>DOI: 10.5281/zenodo.24357841 (reserved; it becomes active on the day of publication, when the same release as the public repository is deposited on Zenodo).</li>
<li>Source fingerprints: a combined list of all MANIFEST files (URL, sha256, time obtained) and the responses to a HEAD request sent to each URL on 2026-11-18 (status, length, Last-Modified, ETag) are in results/fingerprint/. The sha256 of each local copy was recomputed and checked against the MANIFEST. The weekly crawl compares against this baseline to detect replaced files; the report of each crawl is in results/crawl/.</li>
<li>The English translations are kept in <code>translate/en/</code>. Each entry stores the Japanese source text, its sha256 and the commit of the source file at the time of translation; the English pages are built from these files without calling an LLM.</li>
</ul><h2 id="scope">How the fetched sources are counted</h2><ul><li>Why the counts differ: {NSRC:,} MANIFEST rows (including URLs listed in the MANIFEST of more than one statistic); 8,462 distinct URLs (8,423 of them, excluding web.archive.org, received a HEAD request for the source fingerprints); {SC['files']:,} local files (excluding sources that may contain personal names, and including derived files outside the MANIFEST). The “sources” in the banner is the number of distinct URLs at the latest fetch.</li><li>Scope: all fetched raw sources except those that may contain personal names (individual disciplinary announcements by boards of education). {SC['files']:,} files, {SC['bytes']/1e9:.2f} GB.</li><li>{SC['numeric_cells']:,} numeric cells: numeric cells in Excel files (xlsx {SC['xlsx']:,}, xls {SC['xls']:,}) and numeric fields in CSV files ({SC['csv']}). Includes other editions of the same table, overlaps between annual reports and white papers, and overlaps between machine-readable and viewing versions. Numbers inside PDFs are not included.</li><li>PDF: {SC['pdf']:,} files, {SC['pdf_pages']:,} pages; HTML: {SC['html']:,} files.</li><li>These figures describe the size of the fetched sources, not the number of values checked. The number checked is given for each check in the working notes on each statistic’s page.</li><li>Counting script: <code>checks/generic/count_scope.py</code>; result: <code>results/scope/scope.json</code>.</li></ul><h2>Redistribution</h2><ul><li>The raw sources themselves are not redistributed. Their URLs, sha256 hashes and Last-Modified dates are published.</li>
<li>Sources that may contain personal names (such as individual disciplinary announcements by boards of education) are listed neither as files nor as URLs.</li></ul>""")
_nm = TS.save_missing()
print('en: translations missing', _nm, '(run translate/translate.py, then build again)' if _nm else '')
open(os.path.join(OUT, 'robots.txt'), 'w').write('User-agent: *\nDisallow: /\n')
json.dump({"headers": [{"source": "/(.*)", "headers": [{"key": "X-Robots-Tag", "value": "noindex, nofollow"}]}], "cleanUrls": False}, open(os.path.join(OUT, 'vercel.json'), 'w'))
print('pages', sum(len(fs) for _, _, fs in os.walk(OUT)))
# 公開後（2026-11-20〜）：publish/LIVE があれば、草案の印（noindex・robots の拒否・帯・題名の（草案））を外す
if os.path.exists(os.path.join(R, 'publish', 'LIVE')):
    import subprocess, sys as _s2
    subprocess.run([_s2.executable, os.path.join(R, 'publish', 'public_build.py'), '--inplace'], check=True)
