"""translate/missing.json（site/build_site.py が書き出す、訳のない原文）を訳し、translate/en/ に保管する。

使い方: ~/.venvs/urazuke/bin/python translate/translate.py [--limit N] [--workers 4] [--dry]
- API キーは環境変数 ANTHROPIC_API_KEY から読む（表示しない）。
- 同じ「束」（記録1件、文書の一つ）の原文をまとめて1回で訳し、文脈と訳語をそろえる。
- 保管する項目：原文 ja・ja_sha256・en・原文のファイル（src）・訳した時点の原文のコミット（src_commit）・model・date。
- 訳した後、意図を表す語・ヘッジ語が入っていないかを確かめ、入っていれば保管せずに報告する。
"""
import json, os, sys, time, datetime, urllib.request, subprocess, re, argparse, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tr import R, D, MISSING, load_glossary, store_name, sha

MODEL = 'claude-opus-5-5'
ap = argparse.ArgumentParser()
ap.add_argument('--limit', type=int, default=0)
ap.add_argument('--workers', type=int, default=4)
ap.add_argument('--dry', action='store_true')
ap.add_argument('--only', default='')
A = ap.parse_args()

BANNED = re.compile(r'cover[- ]?up|covered up|manipulat|falsif|fabricat|conceal|tamper|doctored|deliberate|intentional|on purpose|window[- ]dress|cook(ed|ing) the books|rigged|whitewash|\bhid(e|den|ing)\b|deceiv|decept|mislead|\bpresumably\b|\bprobably\b|\bperhaps\b|\bseemingly\b', re.I)

GLOSS = '\n'.join(f"{g['ja']}\t{g['en']}" + (f"\t({g['note']})" if g['note'] else '') for g in load_glossary())
SYSTEM = f"""You translate the Japanese text of URAZUKE, a site that verifies Japanese public statistics, into English.
The Japanese is authoritative; the English is a faithful translation. Rules:
1. Translate faithfully and completely. Do not add, omit, soften, strengthen, summarise or explain. Keep the same level of certainty as the Japanese.
2. Never use words that attribute intent or motive: cover-up, manipulation, falsification, fabrication, concealment, tampering, deliberate, intentional, fraud, misleading, hide/hidden, whitewash. Describe only facts (e.g. "values do not match", "missing", "revised without a note"). If the Japanese itself names such a word in order to prohibit it, translate the prohibited Japanese word literally inside a rule (e.g. "words implying intent, such as 'concealment' or 'falsification', are not used").
3. Do not add hedges (probably, perhaps, presumably, seemingly) that are not in the Japanese.
4. Use the glossary terms exactly. When a glossary term appears, use its English rendering every time. Capitalise a glossary term only when it stands alone as a label (a table cell, a status value, a page name); in running text write it in lower case ("gaps and unexplained revisions").
5. Keep unchanged: record IDs (HK-A1, R007, H001 …), numbers, years, file paths, URLs, code, script names (c009h …), Markdown syntax (headings #, lists -, tables with the same number of | cells, **bold**, `code`, [text](url)).
6. Japanese identifiers that must stay in Japanese to be found in the source (Excel sheet names, file names, table titles quoted from the source, original Japanese terms you cite) go inside backticks, e.g. sheet `5-4-4表③※機械判読用`. Apart from backticked text, the output must contain no Japanese characters.
7. Japanese era years: give the Western year; add the era form in parentheses only where the Japanese edition name uses it (令和5年版 → 2023 edition (Reiwa 5)). 年度 → fiscal year (FY2023).
8. Use plain, neutral, formal English. Agencies' names as in the glossary.

Glossary (Japanese<TAB>English<TAB>(note)):
{GLOSS}

Input: a JSON array of Japanese strings that belong together (one record, or consecutive parts of one document). Output: only a JSON array of the English translations, same length and order, nothing else."""


def call(items):
    body = json.dumps({'model': MODEL, 'max_tokens': 16000, 'system': SYSTEM,
                       'messages': [{'role': 'user', 'content': json.dumps([i['ja'] for i in items], ensure_ascii=False)}]}).encode()
    for attempt in range(5):
        try:
            req = urllib.request.Request('https://api.anthropic.com/v1/messages', data=body, headers={
                'x-api-key': os.environ['ANTHROPIC_API_KEY'], 'anthropic-version': '2023-06-01', 'content-type': 'application/json'})
            r = json.load(urllib.request.urlopen(req, timeout=600))
            txt = ''.join(b.get('text', '') for b in r['content']).strip()
            txt = re.sub(r'^```(?:json)?\s*|\s*```$', '', txt)
            out = json.loads(txt)
            if len(out) != len(items):
                raise ValueError(f'length {len(out)} != {len(items)}')
            return out
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            print('  retry', attempt + 1, type(ex).__name__, flush=True)
            err = (ex.read()[:300].decode("utf-8", "replace") if hasattr(ex, "read") else str(ex)[:200])
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(err)


def commit_of(src):
    p = src.split('#')[0]
    c = subprocess.run(['git', 'log', '-1', '--format=%h', '--', p], cwd=R, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(['git', 'status', '--porcelain', '--', p], cwd=R, capture_output=True, text=True).stdout.strip()
    return (c or 'untracked') + ('+uncommitted' if dirty else '')


sys.stdout.reconfigure(line_buffering=True)
if not os.environ.get('ANTHROPIC_API_KEY') and not A.dry:
    sys.exit('ANTHROPIC_API_KEY が環境変数にありません')
miss = json.load(open(MISSING, encoding='utf-8'))
if A.only:
    miss = [m for m in miss if A.only in m['src']]
# 束にまとめ、1回あたり原文 6000 字までに分ける
groups = {}
for m in miss:
    groups.setdefault(m['group'], []).append(m)
batches = []
for g, ms in groups.items():
    cur, n = [], 0
    for m in ms:
        if cur and n + len(m['ja']) > 6000:
            batches.append(cur); cur, n = [], 0
        cur.append(m); n += len(m['ja'])
    if cur:
        batches.append(cur)
if A.limit:
    batches = batches[:A.limit]
print('missing', len(miss), 'batches', len(batches), 'chars', sum(len(m['ja']) for b in batches for m in b))
if A.dry:
    sys.exit(0)

os.makedirs(D, exist_ok=True)
commits = {}
def work(b):
    return b, call(b)

done, flagged = 0, []
today = datetime.date.today().isoformat()
with cf.ThreadPoolExecutor(A.workers) as ex:
    for fut in cf.as_completed([ex.submit(work, b) for b in batches]):
        try:
            b, out = fut.result()
        except Exception as e:
            print('FAILED batch:', str(e)[:200]); continue
        bystore = {}
        for m, en in zip(b, out):
            if BANNED.search(en) and not re.search(r'not used|are not used|is not used|do not use|never use|avoid', en, re.I):
                flagged.append((m['src'], BANNED.search(en).group(0), en[:160])); continue
            if m['src'] not in commits:
                commits[m['src']] = commit_of(m['src'])
            bystore.setdefault(store_name(m['src'].split('#')[0]), []).append(
                (m['sha'], {'ja': m['ja'], 'en': en, 'src': m['src'], 'src_commit': commits[m['src']], 'model': MODEL, 'date': today}))
        for fn, items in bystore.items():
            p = os.path.join(D, fn)
            st = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {
                'note': 'English translation of URAZUKE (Japanese is authoritative). Each entry keeps the Japanese source text, its sha256, and the commit of the source file at translation time.',
                'entries': {}}
            for k, v in items:
                st['entries'][k] = v
            st['entries'] = dict(sorted(st['entries'].items(), key=lambda kv: kv[1]['src']))
            json.dump(st, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        done += 1
        print(f'{done}/{len(batches)}', flush=True)
print('flagged', len(flagged))
for f in flagged:
    print(*f, sep=' | ')
