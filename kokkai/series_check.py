"""「渡した資料と別の資料」とされた答弁を、その版の資料の原文で照らし直す（2026-11-21）。
いまは二つの系列：死亡事例検証報告（第1〜22次）と児童虐待相談対応件数（令和6年度速報の推移の表）。
答弁の漢数字を算用数字に直し、その数を含む行を資料の原文から抜き出して Claude に渡す。出力は classified2.jsonl（refute.py に渡せる形）。
python3 kokkai/series_check.py <日付>"""
import glob, json, os, re, subprocess, sys, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import llm, kansuji
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); day = sys.argv[1] if len(sys.argv) > 1 else ''; D = os.path.join(ROOT, 'results/kokkai', day)
# 死亡事例検証報告の公表年月（各次）。答弁の日より前に出た最新の次を既定にする
PUB = {1: '2005-04', 2: '2006-03', 3: '2007-06', 4: '2008-03', 5: '2009-07', 6: '2010-07', 7: '2011-07', 8: '2012-07', 9: '2013-07', 10: '2014-09', 11: '2015-10',
       12: '2016-09', 13: '2017-08', 14: '2018-08', 15: '2019-08', 16: '2020-09', 17: '2021-08', 18: '2022-09', 19: '2023-09', 20: '2024-09', 21: '2025-09', 22: '2026-09'}
def txt(p):
    t = p[:-4] + '.txt'
    if not os.path.exists(t): subprocess.run(['pdftotext', '-layout', p, t], capture_output=True)
    return open(t, encoding='utf-8', errors='ignore').read() if os.path.exists(t) else ''
def shibo_text(n):
    ps = glob.glob(os.path.join(ROOT, f'data/raw/kokkai_src/shibo/{n:02d}/*.pdf')) + glob.glob(os.path.join(ROOT, f'data/raw/shibo_jirei/{n}/*.pdf'))
    return '\n'.join(txt(p) for p in sorted(ps))
def edition(c):
    m = re.search(r'第([〇一二三四五六七八九十]+)次', c['passage'])
    if m: return int(kansuji._pos(m.group(1)))
    ym = c['date'][:7]; return max(n for n, d in PUB.items() if d < ym)
def excerpt(text, nums, cap=6000):
    L = text.splitlines(); keep = set()
    forms = kansuji.forms(nums)
    for i, l in enumerate(L):
        if any(f in l for f in forms): keep |= set(range(max(0, i - 2), min(len(L), i + 3)))
    s = '\n'.join(L[i] for i in sorted(keep))
    return (s[:cap] if s else text[:3000]), bool(s)
def source_for(c):
    nums = kansuji.numbers(c['passage'])
    if 'SH2' in c['qids']:
        n = edition(c); t = shibo_text(n)
        if not t: return None
        ex, hit = excerpt(t, nums); return dict(name=f'子ども虐待による死亡事例等の検証結果等について 第{n}次報告', text=ex, hit=hit, nums=nums)
    if 'JG1' in c['qids']:
        t = txt(os.path.join(ROOT, 'data/raw/gyakutai/sokuhou/R6_sokuhou_cfa_20260130.pdf'))[:9000]
        return dict(name='令和6年度 児童相談所における児童虐待相談対応件数（速報値。平成2年度からの推移の表を含む）', text=t, hit=True, nums=nums)
    return None
def prompt(c, s):
    return f"""あなたは日本の公的資料の引用を点検する係です。以下は国会での政府側の答弁の一部と、その答弁が引いたと考えられる資料の原文の抜粋です（抜粋は、答弁に出てくる数を含む行とその前後を機械で切り出したもの。表の段組みは崩れていることがあります）。
答弁の数字や結論を資料の原文と比べ、次の型のどれか一つを選んでください。
- 数字の不一致：答弁の数字が資料の数字と合わない
- 範囲のずれ：数字の対象・年度・指標が、答弁が当てはめる範囲と違う
- 限定が落ちる：資料にある限定が答弁で落ち、結論が強くなっている（結論に影響しない細目は含めない）
- 食い違いなし：答弁は資料と食い違わない
- 判定不能：抜粋では判断できない（答弁の数が抜粋に見当たらない、別の資料を引いている、など）
決まり：推測で補わない。答弁からの引用（speech_quote）と資料からの引用（source_quote）は、下の文からそのまま写す（60字以内）。食い違いなし・判定不能以外なら、explanation に2文以内で書く。
JSON だけを出力：{{"type": "...", "speech_quote": "...", "source_quote": "...", "explanation": "..."}}

【答弁】{c['date']} {c['house']} {c['meeting']} {c['speaker']}
{c['passage']}

【資料】{s['name']}
{s['text']}
"""
norm = lambda x: re.sub(r'\s+', '', x or '')
def run(c):
    s = source_for(c)
    if not s: return None
    try: j = llm.js(llm.claude(prompt(c, s))) or {}
    except Exception as ex: j = {'type': 'エラー', 'explanation': type(ex).__name__}
    j['speech_quote_ok'] = bool(j.get('speech_quote')) and norm(j['speech_quote']) in norm(c['passage'])
    j['source_quote_ok'] = bool(j.get('source_quote')) and norm(j['source_quote']) in norm(s['text'])
    j['record_ids'] = []
    return {**c, 'source': s, 'claude': j}
if __name__ == '__main__':
    C = [json.loads(l) for l in open(os.path.join(D, 'classified.jsonl'), encoding='utf-8')]
    C = [c for c in C if c['claude'].get('type') in ('渡した資料と別の資料', '判定不能') and set(c['qids']) & {'SH2', 'JG1'}]
    print('対象', len(C), flush=True)
    with cf.ThreadPoolExecutor(4) as ex, open(os.path.join(D, 'classified2.jsonl'), 'w', encoding='utf-8') as w:
        for r in ex.map(run, C):
            if not r: continue
            w.write(json.dumps(r, ensure_ascii=False) + '\n'); w.flush()
            print(r['date'], r['speaker'], r['source']['name'][-12:], r['claude'].get('type'), r['claude'].get('speech_quote_ok'), r['claude'].get('source_quote_ok'), flush=True)
