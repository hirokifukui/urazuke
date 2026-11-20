"""「確かめて合っていたもの」の数を、各検査が書いた要約（results/<資料名>/tally/*.json、lib/tally.py）から数える（手で書いた数を使わない）。
出力: results/scope/verified.json  {slug: {compared, mismatched, read_failures, checks_compare, checks_tallied, parts:[...]}}
- compared：照合した数（検査が「一致」「食い違い」のどちらかに判定したもの。読み取りの失敗は数えない）
- mismatched：資料どうしの食い違いの数（説明のある違いを含む。説明は作業ノートにある）
- explained：mismatched のうち、違いの理由が資料の中に書かれているもの（注・正誤表・告知・暫定値の明記など）
- read_failures：読み取りの失敗・対応の取れなかったもの
処理：1) 台帳（checks/TALLY.tsv）を作り直す。2) 台帳の「照合」の検査ごとに要約を集め、統計ごとに足す。
（r25 の移行用の書き起こし source=adapter は r26 でやめた。全検査が自分で要約を書く。）
使い方: python checks/generic/count_verified.py"""
import csv, json, os, sys
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = lambda *a: os.path.join(R, *a)
# 1) 台帳を作り直す
import subprocess
subprocess.run([sys.executable, P('checks/generic/build_tally_registry.py')], check=True, stdout=subprocess.DEVNULL)
# 2) 台帳と要約から、統計ごとに数える
import glob
reg = list(csv.DictReader(open(P('checks/TALLY.tsv'), encoding='utf-8'), delimiter='\t'))
out = {}
for r in reg:
    if r['kind'] != '照合':
        continue
    o = out.setdefault(r['slug'], {'compared': 0, 'mismatched': 0, 'explained': 0, 'read_failures': 0, 'checks_compare': 0, 'checks_tallied': 0, 'parts': []})
    o['checks_compare'] += 1
    tal = sorted(glob.glob(P('results', '*', 'tally', r['check'] + '.json')) + glob.glob(P('results', '*', 'tally', r['check'] + '__*.json')))
    if tal:
        o['checks_tallied'] += 1
    for t in tal:
        d = json.load(open(t, encoding='utf-8'))
        o['compared'] += d['compared']; o['mismatched'] += d['mismatched']; o['read_failures'] += d['read_failures']; o['explained'] += d['explained'] or 0
        o['parts'].append({'check': d['check'], 'label': d['label'], 'source': d['source'], 'compared': d['compared'], 'mismatched': d['mismatched'], 'read_failures': d['read_failures'], 'explained': d['explained'] or 0, 'note': d.get('note', ''), 'script': r['script'], 'file': os.path.relpath(t, R)})
os.makedirs(P('results/scope'), exist_ok=True)
json.dump(out, open(P('results/scope/verified.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
tc = sum(v['checks_compare'] for v in out.values()); tt = sum(v['checks_tallied'] for v in out.values())
print('statistics', len(out), 'compare checks', tc, 'tallied', tt)
for k, v in out.items():
    if v['checks_tallied']:
        print(k, v['compared'], v['mismatched'], f"{v['checks_tallied']}/{v['checks_compare']}")
