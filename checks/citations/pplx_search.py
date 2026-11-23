# Perplexity API で引用の候補を探す（H034 の追加の検索）。答えの文は公開しない（results/citations/perplexity/ は公開ファイルから外す）。
# キーは環境変数 PERPLEXITY_API_KEY から読む。なければ運営者の指定したファイルから pplx- の値だけを読む。表示しない。
import os, re, json, sys, time, datetime, urllib.request
KEYF = os.path.expanduser('~/Library/Mobile Documents/com~apple~CloudDocs/APIキー.txt')
key = os.environ.get('PERPLEXITY_API_KEY') or re.search(r'pplx-[A-Za-z0-9]+', open(KEYF).read()).group(0)
OUT = 'results/citations/perplexity'; os.makedirs(OUT, exist_ok=True)
Q = [
 ('KP-C1', '刑事施設の性犯罪者処遇プログラムの受講者の再犯率（27.3％と38.0％、0.79倍）を報じた記事・論文・公的文書'),
 ('SO-P1', '保護観察所の性犯罪者処遇プログラムの受講者の再犯率（0.67倍、15.1％と26.2％）を引いた記事・資料'),
 ('YK-C1', '刑事施設と保護観察所の薬物事犯者に対するプログラムの効果検証（令和4年）の処遇効果を引いた記事・資料'),
 ('GY-Q1', '2022年度の児童虐待相談対応件数（速報値21万9170件、確定値21万4843件）を報じた記事'),
 ('JH-A1', '2024年の小中高生の自殺者数（529人）と2025年（538人）を報じた記事'),
 ('ST-I2', 'ストーカー規制法違反の検挙件数が過去最多とした2024年・2025年の記事'),
 ('NK-K1', '60歳以上の受刑者の約14％に認知症傾向、約1300人と推計した法務省調査を引いた記事'),
 ('630-D1', '精神科病院の在院患者数の都道府県別の減少を630調査から論じた記事・資料'),
 ('HK-A9', '配偶者暴力の相談件数や検挙件数を犯罪白書・警察庁統計から報じた記事'),
 ('BV-P1', '暴力防止プログラムの効果を法務省の報告から報じた記事'),
 ('MK-I1', '公立学校教職員の懲戒処分の件数を文部科学省の人事行政状況調査から報じた記事'),
 ('ES-I1', '医療観察法の入院処遇・通院処遇の対象者数を報じた記事'),
 # 2026-11-20 追加（記録が増えた分）
 ('SH-C1', '刑事施設の性犯罪再犯防止指導の受講群の再犯率が7.7ポイント低いとした再犯防止推進白書・記事・資料'),
 ('ST-D1', '配偶者からの暴力事案等の相談等件数が過去最多（2024年94,937件、2025年98,289件）と報じた記事'),
 ('SK-C1', '刑事施設の職業訓練の効果検証（有職率78.7％と74.0％、傾向スコアマッチング）を引いた記事・資料'),
 ('ST-C1', 'ストーカー禁止命令等を受けた者の再発率約7.6％（6,548人中497人）を報じた記事・資料'),
 # 2026-11-23 追加
 ('SK-A1', '受刑者の職業訓練の性差を傾向スコアマッチングで検証した矯正研究第8号の論文（中村・佐々木、2025年）を引いた記事・資料'),
]
SYS = '日本語の報道・公的文書・論文を探す。各項目について、媒体名、掲載日、URL、その資料に書かれた数字の文をそのまま示す。見つからなければ見つからないと書く。'
def call(q):
    body = json.dumps({'model': 'sonar-pro', 'messages': [{'role': 'system', 'content': SYS}, {'role': 'user', 'content': q}], 'max_tokens': 1500}).encode()
    req = urllib.request.Request('https://api.perplexity.ai/chat/completions', data=body, headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=180))
only = set(sys.argv[1:])
for rid, q in Q:
    if only and rid not in only: continue
    try:
        r = call(q)
    except Exception as ex:
        print(rid, 'error', type(ex).__name__, str(ex)[:120]); continue
    rec = dict(rec=rid, query=q, utc=datetime.datetime.utcnow().isoformat(timespec='seconds') + 'Z', model=r.get('model'),
               answer=r['choices'][0]['message']['content'], citations=r.get('citations') or [], search_results=r.get('search_results') or [])
    json.dump(rec, open(f'{OUT}/{rid}.json', 'w'), ensure_ascii=False, indent=1)
    print(rid, len(rec['citations']), 'urls')
    time.sleep(1)
