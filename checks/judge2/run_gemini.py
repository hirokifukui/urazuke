# H037：各回の PROMPT.md を Gemini（二つ目の判定者）に渡し、REPORT_gemini.md を replications/<回>/ に置く。
import os, re, json, sys, glob, urllib.request, datetime, hashlib
MODEL = 'gemini-4-argon'
T = open(os.path.expanduser('~/Library/Mobile Documents/com~apple~CloudDocs/APIキー.txt')).read(); GK = re.findall(r'AIza[0-9A-Za-z_\-]{35}', T)[1]
ROUNDS = sys.argv[1:] or ['R029_gpt_types', 'R030_gpt_types', 'R031_gpt_types', 'R035_h036_KP-C1', 'R037_h036_YK-C1', 'R039_h036_JH-A1', 'R040_h036_ST-I2',
          'R042_h036_630-D1', 'R043_h036_SO-P1', 'R044_h036_GY-Q1', 'R045_h036_NK-K1']
def ask(p):
    body = json.dumps({'contents': [{'parts': [{'text': p}]}]}).encode()
    r = json.load(urllib.request.urlopen(urllib.request.Request(f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={GK}', data=body, headers={'Content-Type': 'application/json'}), timeout=900))
    return ''.join(x.get('text', '') for x in r['candidates'][0]['content']['parts'])
for rn in ROUNDS:
    d = f'replications/{rn}'; out = f'{d}/REPORT_gemini.md'
    if os.path.exists(out): print(rn, 'exists'); continue
    P = open(f'{d}/PROMPT.md').read()
    P = re.sub(r'REPORT\.md に、', 'REPORT.md に書く内容を、そのまま返答として出力する。', P)
    for attempt in range(3):
        try: a = ask(P); break
        except Exception as ex: a = ''; print(rn, 'retry', type(ex).__name__, str(ex)[:100], flush=True)
    if not a: continue
    open(out, 'w').write(a)
    open(f'{d}/REPORT_gemini_META.json', 'w').write(json.dumps({'model': MODEL, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'), 'prompt_sha256': hashlib.sha256(P.encode()).hexdigest()}, indent=1))
    print(rn, 'ok', len(a), flush=True)
print('done')
