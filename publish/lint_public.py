"""公開物の点検：ヘッジ語・意図を表す語・個人名らしき記述・サイト内リンク切れ。英語版（site/out/en/）には、英語の意図語・ヘッジ語、訳の残り（[translation pending]・訳されていない日本語）、正本の注記の有無も確かめる。
対象：site/out/**/*.html と publish/PUBLIC_FILES.tsv に載る .md（作業ノート・記録・照会文など）。
個人名は、照会先の担当者名などが入りうる「氏名＋（課長補佐）」「担当者」「係長 …」の形を探す（機械的な目安。最後は目で見る）。
使い方: lint_public.py [root]   終了コード 0=問題なし"""
import sys, os, re, glob, html
root = sys.argv[1] if len(sys.argv) > 1 else '.'
HEDGE = ['と思われる', 'かもしれない', 'と考えられる', 'おそらく', 'ではないか', 'と見られる', '可能性がある', 'らしい']
INTENT = ['隠蔽', '改ざん', '改竄', '捏造', '操作した', '意図的', '故意', '粉飾', '偽装']
NAME = [r'担当者[^\n]{0,20}[一-龥]{2,4}\s?[一-龥]{1,3}', r'（課長補佐）', r'（係\s*長）', r'参\s*事\s*官\s+[一-龥]{1,3}\s[一-龥]{1,3}']
HEDGE_EN = [r'\bprobably\b', r'\bperhaps\b', r'\bpresumably\b', r'\bseemingly\b', r'\bit seems\b', r'\bappears to\b', r'\bmight\b', r'\ballegedly\b']
INTENT_EN = [r'cover[- ]?ups?\b', r'covered up', r'manipulat', r'falsif', r'fabricat', r'conceal', r'tamper', r'\bdoctored\b', r'\bdeliberate', r'\bintentional', r'\bon purpose\b', r'window[- ]dress', r'cook(ed|ing) the books', r'\brigged\b', r'whitewash', r'\bhid(e|den|ing)\b', r'deceiv', r'decepti', r'mislead']
JA = re.compile(r'[\u3040-\u30fa\u30fc-\u30ff\u3400-\u9fff]')  # 中黒（・）は記号として除く
files = glob.glob(os.path.join(root, 'site/out/**/*.html'), recursive=True)
pub = os.path.join(root, 'publish/PUBLIC_FILES.tsv')
if os.path.exists(pub):
    for l in open(pub):
        p = l.split('\t')[0].strip()
        if p.endswith('.md') and os.path.exists(os.path.join(root, p)) and not re.match(r'replications/R\d+[^/]*/REPORT', p) and not re.match(r'replications/R\d+_h036_[^/]*/PROMPT', p): files.append(os.path.join(root, p))  # 別系統の報告、AI の答えをそのまま渡した判定の課題文は原文のまま公開するため対象外
bad = []
for f in files:
    t = open(f, encoding='utf-8', errors='replace').read()
    txt = html.unescape(re.sub(r'<[^>]+>', ' ', t)) if f.endswith('.html') else t
    # 反証を経ていない作業の文をサイトに出さない（2026-11-19、点検 H4）
    if f.endswith('.html'):
        for w in ['丸写し', '記録にしない', '作業ノートのみ', '確実さ：候補', '（未確認）', '未確認）']:
            if w in txt: bad.append((os.path.relpath(f, root), '作業の文：' + w, txt[max(0, txt.index(w) - 40):txt.index(w) + 40].replace('\n', ' ')))
    en = f.endswith('.html') and os.sep + 'en' + os.sep in os.path.relpath(f, root)
    if en:
        # 日本語のまま載せる部分（lang="ja" の要素：原文の引用・対訳表の日本語・言語の切替）と <code> を除いて調べる
        body = re.sub(r'<(\w+)[^>]*\blang="ja"[^>]*>.*?</\1>', ' ', t, flags=re.S)
        body = re.sub(r'<code>.*?</code>', ' ', body, flags=re.S)
        body = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', body, flags=re.S)
        body = re.sub(r'<head>.*?</head>', ' ', body, flags=re.S)   # title・description は本文の見出し・要旨から作る（本文の側で調べる。2026-11-25）
        etxt = html.unescape(re.sub(r'<[^>]+>', ' ', body))
        if 'The Japanese version is authoritative' not in etxt: bad.append((os.path.relpath(f, root), '正本の注記なし', ''))
        if '[translation pending]' in etxt: bad.append((os.path.relpath(f, root), '訳なし', str(etxt.count('[translation pending]')) + ' 箇所'))
        for m in JA.finditer(etxt):
            bad.append((os.path.relpath(f, root), '訳されていない日本語', etxt[max(0, m.start() - 30):m.end() + 30].replace('\n', ' '))); break
        for pat in HEDGE_EN + INTENT_EN:
            for m in re.finditer(pat, etxt, re.I):
                ctx = etxt[max(0, m.start() - 120):m.end() + 120].replace('\n', ' ')
                if re.search(r'Direction of the difference', etxt[max(0, m.start() - 500):m.start()]): continue  # 平易版の「違いの向き」（数で示した見え方の説明）
                if re.search(r'not used|are not used|is not used|do not use|never use|attribut\w* intent|imply\w* intent', ctx, re.I): continue  # 規則の説明
                bad.append((os.path.relpath(f, root), 'EN:' + pat, ctx))
    for w in HEDGE + INTENT:
        for m in re.finditer(re.escape(w), txt):
            ctx = txt[max(0, m.start() - 30):m.end() + 30].replace('\n', ' ')
            # 規則の説明として語を挙げている箇所（「…などを使わない」）は除く
            if re.search(r'使わない|使いません|書かない|対象にしない|表示は|used in English', ctx): continue
            bad.append((os.path.relpath(f, root), w, ctx))
    for pat in NAME:
        for m in re.finditer(pat, txt):
            bad.append((os.path.relpath(f, root), '個人名の形', txt[max(0, m.start() - 20):m.end() + 20].replace('\n', ' ')))
    if f.endswith('.html'):
        for href in re.findall(r'href="([^"#:]+)(?:#[^"]*)?"', t):
            if href.startswith(('http', 'mailto', '//')): continue
            # / で始まるもの（404.html）はサイトの根（site/out）から
            target = os.path.normpath(os.path.join(root, 'site/out', href.lstrip('/')) if href.startswith('/') else os.path.join(os.path.dirname(f), href))
            if not os.path.exists(target) and not os.path.exists(target + '.html') and not os.path.exists(os.path.join(target, 'index.html')):
                bad.append((os.path.relpath(f, root), 'リンク切れ', href))
print('files', len(files), 'problems', len(bad))
for b in bad[:300]: print(*b, sep=' | ')
sys.exit(1 if bad else 0)
