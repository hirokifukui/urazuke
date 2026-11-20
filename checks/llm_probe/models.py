# 使えるモデルの一覧を取る（キーは環境変数、なければ運営者の指定したファイルから。表示しない）。
import os, re, json, urllib.request
KEYF = os.path.expanduser('~/Library/Mobile Documents/com~apple~CloudDocs/APIキー.txt')
TXT = open(KEYF).read()
def k(env, pat):
    return os.environ.get(env) or (re.findall(pat, TXT) or [None])
def get(url, h):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30))
out = {}
try: out['anthropic'] = [m['id'] for m in get('https://api.anthropic.com/v1/models?limit=50', {'x-api-key': os.environ['ANTHROPIC_API_KEY'], 'anthropic-version': '2023-06-01'})['data']]
except Exception as ex: out['anthropic'] = str(ex)[:80]
try: out['openai'] = sorted(m['id'] for m in get('https://api.openai.com/v1/models', {'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY']})['data'] if re.match(r'(gpt|o\d)', m['id']))[-40:]
except Exception as ex: out['openai'] = str(ex)[:80]
gk = re.findall(r'AIza[0-9A-Za-z_\-]{35}', TXT); out['gemini'] = []
for i, g in enumerate(gk):
    try: out['gemini'] = [m['name'] for m in get('https://generativelanguage.googleapis.com/v1beta/models?pageSize=100&key=' + g, {})['models'] if 'generateContent' in m.get('supportedGenerationMethods', [])][-30:]; out['gemini_key_index'] = i; break
    except Exception as ex: out['gemini'] = str(ex)[:80]
xk = re.findall(r'xai-[0-9A-Za-z]+', TXT); out['xai'] = []
for i, x in enumerate(xk):
    try: out['xai'] = [m['id'] for m in get('https://api.x.ai/v1/models', {'Authorization': 'Bearer ' + x})['data']]; out['xai_key_index'] = i; break
    except Exception as ex: out['xai'] = str(ex)[:80]
print(json.dumps(out, ensure_ascii=False, indent=1))
