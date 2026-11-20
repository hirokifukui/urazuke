"""反証で支持されなかった平易版を、反証の報告を受けて書き直す（2026-11-19、r43）。
python3 publish/plain/revise.py        # STATUS.json で支持でない記録すべて
前の版は publish/plain/drafts_prev/<ID>_<回>.json に残す。"""
import json, os, re, sys, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(ROOT)
sys.path.insert(0, 'publish/plain'); sys.path.insert(0, 'crawl')
import draft as DR, site_audit as SA
BL = os.path.expanduser('~/mitodoke_blind'); S = json.load(open('publish/plain/STATUS.json'))
os.makedirs('publish/plain/drafts_prev', exist_ok=True)


def section(r, q):
    t = open(os.path.join(BL, r, 'REPORT.md')).read()
    m = re.search(r'(?m)^#+\s*\**%s\b' % q, t)
    if not m: return ''
    n = re.search(r'(?m)^#+\s*\**Q\d+\b', t[m.end():])
    return t[m.start(): m.end() + (n.start() if n else len(t))]


RULE = """前の版の平易版を、別の検証者（反証役）の報告を受けて書き直す。
- 報告が「資料と矛盾する」と示した点は、資料の値に合わせて直すか、その主張を外す。
- 報告が「資料で確かめられない」とした点は、確かめられる範囲に狭めるか、外す。範囲を狭めたことは書かなくてよい。
- 報告の「言い過ぎの指摘」も反映する。
- 新しい事実を足さない。報告に資料の値として示されたものは使ってよい。
- 形（キー）と調子は前の版と同じ。出力は JSON 一つだけ。"""


def run(i):
    st = S[i]; d = json.load(open(f'publish/plain/drafts/{i}.json'))
    shutil.copy(f'publish/plain/drafts/{i}.json', f'publish/plain/drafts_prev/{i}_{st["round"]}.json')
    p = DR.prompt(DR.F[i]) + f"\n\n## 前の版\n{json.dumps(d, ensure_ascii=False, indent=1)}\n\n## 反証役の報告（{st['round']} {st['q']}、判定：{st['verdict']}）\n{section(st['round'], st['q'])}\n\n## 指示\n{RULE}"
    t = SA.ask('claude', p); m = re.search(r'\{.*\}', t, re.S); n = json.loads(m.group(0)); n['id'] = i
    json.dump(n, open(f'publish/plain/drafts/{i}.json', 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    ids = sys.argv[1:] or sorted(i for i, v in S.items() if not (v['adopted'] and v['verdict'] == '支持'))
    for i in ids:
        try: run(i); print(i, 'revised', flush=True)
        except Exception as ex: print(i, 'ERR', type(ex).__name__, str(ex)[:200], flush=True)
