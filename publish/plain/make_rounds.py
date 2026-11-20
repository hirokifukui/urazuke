"""平易版の反証の回を作る（2026-11-19、r43）。
python3 publish/plain/make_rounds.py plan            # 回の割り振りを publish/plain/ROUNDS.json に書く（まだ作らない）
python3 publish/plain/make_rounds.py build R049 ...  # 盲検フォルダと run_RXXX.sh を作る
各記録の主張＝平易版の「書かれていること」「表」「向き」。資料＝その記録の原文の引用にあるファイル（全体）。
対照は回ごとに2件：本題のうち2件の主張の数字を1つずつ変えたもの（偽）。"""
import importlib.util, json, os, re, sys, io, contextlib
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(ROOT)
sp = importlib.util.spec_from_file_location('mb', 'checks/generic/make_blind_r22_25.py'); M = importlib.util.module_from_spec(sp)
a = sys.argv; sys.argv = ['x']
with contextlib.redirect_stdout(io.StringIO()): sp.loader.exec_module(M)
sys.argv = a
F = {f['id']: f for f in json.load(open('publish/findings.json'))}
D = 'publish/plain/drafts'; PLAN = 'publish/plain/ROUNDS.json'
FIRST = 49; MAXN = 8


def claim(d):
    t = d['表']; rows = []
    for r in t['rows']:
        rows.append('、'.join(f'{h}：{c}' for h, c in zip(t['head'], r) if c not in ('—', '')))
    return f"要するに：{d['見出し']}。{d['書かれていること']} 表にまとめると、" + '／'.join(rows) + f"。{d['向き']}"


EXTRA = {'YK-C1': ['hanzai_hakusho']}  # 原文の引用にないが、平易版の表が引く資料（YK-C1 は犯罪白書の再入率）
def files(i): return sorted({q['ファイル'].split('/')[0] for q in F[i].get('原文の引用', [])} | set(EXTRA.get(i, [])))


def plan(ids):
    groups = {}
    for i in ids: groups.setdefault(i.split('-')[0], []).append(i)
    chunks = []
    for g in groups.values():
        for k in range(0, len(g), MAXN): chunks.append(g[k:k + MAXN])
    chunks.sort(key=len, reverse=True); rounds = []
    for c in chunks:  # 小さい組は同じ回にまとめる
        tgt = next((r for r in rounds if len(r) + len(c) <= MAXN), None)
        (tgt.extend(c) if tgt is not None else rounds.append(list(c)))
    return {f'R{FIRST + n:03d}': r for n, r in enumerate(rounds)}


NUMRE = re.compile(r'(?<![\d.,])(\d{1,3}(?:,\d{3})+|\d{2,})(?:\.\d+)?')


def falsify(text):
    for m in NUMRE.finditer(text):
        s = m.group(0); v = float(s.replace(',', ''))
        if v < 10 or re.match(r'(19|20)\d\d$', s) or s.startswith('0') or (len(s) >= 6 and ',' not in s): continue
        nv = v + max(1, round(v * 0.07))
        ns = (f'{nv:,.0f}' if ',' in s else (f'{nv:.{len(s.split(".")[1])}f}' if '.' in s else f'{nv:.0f}'))
        if ns in text: continue
        return text[:m.start()] + ns + text[m.end():], (s, ns)
    return None, None


def build(r, ids):
    ds = {i: json.load(open(f'{D}/{i}.json')) for i in ids}
    fl = sorted({x for i in ids for x in files(i)})
    intro = 'このフォルダには、日本の行政機関の公表資料の写しがあります。フォルダは取得元の分類ごとで、中の MANIFEST（.tsv）に各ファイルの取得元の URL と取得日がある場合があります。番号のついたフォルダ（例 66_…〜72）は版ごとの取得で、MANIFEST で版を確かめられます。\n' + '\n'.join(f'- {x}/' for x in fl)
    qs = [(i, claim(ds[i])) for i in ids]
    ctl = []
    for i in ids:
        t, ch = falsify(claim(ds[i]))
        if t: ctl.append((i, t, ch))
        if len(ctl) == 2: break
    assert len(ctl) >= 1, r + ' 対照を作れない'
    # 対照を本題の間に挟む（2番目と最後の手前）
    allq = list(qs)
    allq.insert(min(1, len(allq)), ('CTRL', ctl[0][1]))
    if len(ctl) > 1: allq.insert(len(allq) - 1, ('CTRL', ctl[1][1]))
    M.ROUNDS = {r: dict(H='H041', title='記録の平易版', intro=intro,
                        files=[(os.path.join(M.RAW, x), x) for x in fl], qs=allq)}
    M.build(r)
    json.dump({'ids': ids, 'controls': [dict(of=c[0], changed=c[2]) for c in ctl]},
              open(os.path.join(ROOT, 'replications', r + '_gpt_refute', 'PLAIN.json'), 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    if sys.argv[1] == 'replan':  # replan 57 ID ...（支持でない記録だけで回を組み直す）
        FIRST = int(sys.argv[2]); P = plan(sys.argv[3:]); json.dump(P, open(PLAN, 'w'), ensure_ascii=False, indent=1)
        for k, v in P.items(): print(k, len(v), v)
    elif sys.argv[1] == 'plan':
        ids = sorted(i for i in F if os.path.exists(f'{D}/{i}.json'))
        P = plan(ids); json.dump(P, open(PLAN, 'w'), ensure_ascii=False, indent=1)
        for k, v in P.items(): print(k, len(v), v)
    else:
        P = json.load(open(PLAN))
        for r in sys.argv[2:]: build(r, P[r])
