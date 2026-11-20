"""c3601 学校基本統計 表1（初等中等教育機関、専修学校・各種学校の学校数、在学者数、教員数）。
令和8年度速報（令和8年8月26日）と令和7年度確定（令和7年12月26日）の公表資料（PDF）。
各行は「（前年度差）」の行と「値」の行の組。
(a) 計=国立+公立+私立（学校数・在学者数）
(b) 女性の比率 = うち女性/計（小数1位、±0.051）
(c) 版間：速報の 値−前年度差 が、前年度の確定の値と同じか（女性の比率は 差が比率の差）
使い方: c3601_hyo1.py [root]   出力: results/monka_kihon/c3601.tsv"""
import sys, os, re, subprocess, unicodedata
root = sys.argv[1] if len(sys.argv) > 1 else '.'
D = os.path.join(root, 'data/raw/monka_kihon/kihon')
out = []; n = 0
ROWS = ['幼稚園', '幼保連携型認定こども園', '小学校', '中学校', '義務教育学校', '高等学校(全日制・定時制)', '高等学校(通信制)', '中等教育学校', '特別支援学校', '専修学校', '専修学校うち高等課程を置く学校', '各種学校']

def chk(ed, where, what, a, b, tol=0):
    global n
    n += 1
    if abs(a - b) > tol + 1e-9: out.append((ed, where, what, a, round(b, 3)))

def num(x):
    x = x.replace(',', '').replace('－', '-').replace('−', '-')
    return 0.0 if x == '-' else float(x)

KEYS = [('幼保連携', '幼保連携型認定こども園'), ('幼稚園', '幼稚園'), ('小学校', '小学校'), ('義務教育', '義務教育学校'),
        ('中等教育', '中等教育学校'), ('中学校', '中学校'), ('通信制', '高等学校(通信制)'), ('高等学校', '高等学校(全日制・定時制)'),
        ('特別支援', '特別支援学校'), ('高等課程', '専修学校うち高等課程を置く学校'), ('専修学校', '専修学校'), ('各種学校', '各種学校')]

def label_of(text):
    t = re.sub(r'[\s\d,.()\-－]', '', text)
    for k, name in KEYS:
        if k in t: return name

def parse(fn):
    t = unicodedata.normalize('NFKC', subprocess.run(['pdftotext', '-layout', os.path.join(D, fn), '-'], capture_output=True, text=True).stdout)
    i = t.index('表1'); j = t.find('表2', i)
    seg = t[i:j if j > 0 else i + 8000].split('\n')
    res = {}; diff = None; buf = ''
    for l in seg:
        toks = re.findall(r'\((-?[\d,.]+|-)\)', l)
        rest = re.sub(r'\((-?[\d,.]+|-)\)', ' ', l)
        vals = re.findall(r'(?<![\w.\-])(-?[\d,]+(?:\.\d)?|-)(?![\w\d\-])', rest)
        buf += ' ' + re.sub(r'[\d,.()\-]', ' ', l)
        if len(toks) >= 11:
            diff = [num(x) for x in toks[:11]]
        if diff and len(vals) >= 11:
            name = label_of(buf)
            if name and name not in res: res[name] = (diff, [num(x) for x in vals[-11:]])
            diff = None; buf = ''
        if l.strip().startswith('(注)'): break
    return res

P = {}
for ed, fn in (('R08速報', 'R08_sokuho.pdf'), ('R07確定', 'R07_kakutei.pdf')):
    P[ed] = parse(fn)
    miss = [r for r in ROWS if r not in P[ed] and not (ed == 'R07確定' and r == '高等学校(通信制)')]  # 令和7年度確定の表1には通信制の行がない
    if miss: out.append((ed, '', '読めない行', ','.join(miss), ''))
    for name, (d, v) in P[ed].items():
        chk(ed, name, '学校数 計=国+公+私', v[0], v[1] + v[2] + v[3])
        chk(ed, name, '在学者数 計=国+公+私', v[4], v[5] + v[6] + v[7])
        chk(ed, name, '女性比率', v[10], v[9] / v[8] * 100 if v[8] else 0, 0.051)
        chk(ed, name, '前年度差 計=国+公+私（学校数）', d[0], d[1] + d[2] + d[3])
        chk(ed, name, '前年度差 計=国+公+私（在学者数）', d[4], d[5] + d[6] + d[7])
if 'R08速報' in P and 'R07確定' in P:
    labels = ['学校数計', '国立', '公立', '私立', '在学者数計', '国立', '公立', '私立', '教員数計', 'うち女性', '女性比率']
    for name in ROWS:
        if name not in P['R08速報'] or name not in P['R07確定']: continue
        d, v = P['R08速報'][name]; v7 = P['R07確定'][name][1]
        for k in range(11):
            chk('版間', name, f'{labels[k]}：速報の値−差=前年度確定', v7[k], v[k] - d[k], 0.051 if k == 10 else 0)
os.makedirs(os.path.join(root, 'results/monka_kihon'), exist_ok=True)
with open(os.path.join(root, 'results/monka_kihon/c3601.tsv'), 'w') as fo:
    fo.write('版\t行\t式\t表の値\t計算値\n')
    for o in out: fo.write('\t'.join(map(str, o)) + '\n')
print('式の数', n, '不一致', len(out))
for o in out: print(*o)

# 照合の要約（lib/tally.py）：単位は式。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('monka_kihon', 'c3601', note='学校基本調査 表1：計＝国立＋公立＋私立、比率、版間', script=__file__)
_t.set(compared=n, mismatched=len(out), read_failures=0, explained=None); print('tally', _t.save())
