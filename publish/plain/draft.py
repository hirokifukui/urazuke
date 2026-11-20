"""記録の平易版の下書きを作る（2026-11-19、r43）。
python3 publish/plain/draft.py [ID ...]   # 引数なしなら、まだ下書きのない記録すべて
見本（examples.json）の3件はそのまま使う。ほかは Claude（API）に、記録の要旨・原文の引用・言えること・照会・作業ノートだけを材料として渡して書かせる。
出力：publish/plain/drafts/<ID>.json"""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT); sys.path.insert(0, 'crawl')
import site_audit as SA
OUT = 'publish/plain/drafts'; os.makedirs(OUT, exist_ok=True)
F = {f['id']: f for f in json.load(open('publish/findings.json'))}
EX = json.load(open('publish/plain/examples.json'))
SRC = open('publish/build_inquiries.py').read()
CAN = {l.split('\t')[0]: l.rstrip('\n').split('\t') for l in open('publish/can_say.tsv') if '\t' in l}


def inquiry(i):
    m = re.search(r"'%s':'([^']*)'" % re.escape(i), SRC)
    return m.group(1) if m else ''


def notes(path, i, cap=24000):
    if not os.path.exists(path): return ''
    t = open(path).read()
    if len(t) <= cap: return t
    k = t.find(i); k = 0 if k < 0 else max(0, k - cap // 3)
    return t[k:k + cap]


RULES = """あなたは、日本の公的統計の検証記録を、一般の読者に伝わる形に書き直す。
次の材料（記録の要旨、原文の引用、言えること・言えないこと、照会の問い、作業ノート）にある事実だけを使う。材料にない数字・事実・推測を足さない。
計算で出した数（差・比）を書くときは、必ず「（a − b）」「（1 ÷ b）」のように式を添える。
意図を表す語（隠す・ごまかす・改ざん・不正・意図的 など）、価値判断（問題だ・不適切・ずさん など）、ぼかし（〜と思われる・〜かもしれない）は使わない。
「ミス」「誤り」と決めつけない。区分が「誤り」の記録でも、事実（どの値がどの資料で違うか）だけを書く。
文は短く、です・ます調。専門用語は、使うなら一言で言い換える。
「大きく」「わずかに」「大幅に」など程度の副詞は使わず、数で示す。
"書かれていること" は120字程度まで。表やシートの行の数字の並び（生の行）は書かない。細かい根拠（シート名・セル番地）は書かない。

出力は JSON 一つだけ。キーは次のとおり：
- "id"
- "見出し"：何が書かれていて、資料の中身がどうなっているかを一文で。60字程度まで。
- "書かれていること"：公表物の該当の記載。資料名と頁を添え、原文の引用にある文はかぎ括弧でそのまま引く。欠落の記録なら「何がどの資料にあり、何がないか」。
- "表"：{"head": [...], "rows": [[...], ...]}。比べるべき数や項目を並べる。2〜5行。数字は材料にあるものだけ。
- "読み違え"：2〜4項目。「こう書かれていると、こう受け取られる。資料ではこうなる」という事実だけ。
- "向き"：違いがどちらの方向に効くかを一文で事実として（例：「表の割合で比べると、受講群の再犯は概要の書き方より少なく見えます」「翌年の版で上方に改訂され、初めの値は小さく見えます」）。向きが決まらないときは「どちらの値を使うかで〜の見え方が変わります」。都合のよい向きか悪い向きかを問わず、同じ調子で書く。
- "言えないこと"：1〜2項目。理由を一言添える。
- "照会"：照会の問いを1文で（材料の照会の問いを短くしたもの）。
"""


def prompt(f):
    c = CAN.get(f['id'])
    can = f"言えること：{c[1]}\n言えないこと：{c[2]}" if c else '（言えること・言えないことの欄はない）'
    qs = '\n'.join(f"- {q['ラベル']}（{q['ファイル']}、{q['箇所']}）：「{q['文']}」" for q in f.get('原文の引用', []))
    ex = json.dumps(EX, ensure_ascii=False, indent=1)
    return f"""{RULES}

## 見本（この3件の形と調子に合わせる）
{ex}

## 書き直す記録
- id：{f['id']}
- 統計：{f['統計']}
- 区分：{f['区分']}
- 今の見出し：{f['見出し']}
- 要旨：{f['要旨']}
- 確実さ：{f['確実さ']}
- 原文の引用：
{qs or '（なし）'}
- {can}
- 照会の問い：{inquiry(f['id'])}

## 作業ノート（材料。ここにある事実も使ってよい）
{notes(f['根拠'], f['id'])}
"""


def run(i):
    p = os.path.join(OUT, i + '.json')
    ex = next((e for e in EX if e['id'] == i), None)
    if ex: json.dump(ex, open(p, 'w'), ensure_ascii=False, indent=1); return 'example'
    t = SA.ask('claude', prompt(F[i]))
    m = re.search(r'\{.*\}', t, re.S); d = json.loads(m.group(0)); d['id'] = i
    json.dump(d, open(p, 'w'), ensure_ascii=False, indent=1); return 'ok'


if __name__ == '__main__':
    ids = sys.argv[1:] or [i for i in F if not os.path.exists(os.path.join(OUT, i + '.json'))]
    for i in ids:
        try: print(i, run(i), flush=True)
        except Exception as ex: print(i, 'ERR', type(ex).__name__, str(ex)[:200], flush=True)
