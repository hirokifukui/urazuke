"""R075（2026-11-22）：認知症スクリーニング検査の平成30年の人数（答弁書 衆200-64 の 904名と、再犯防止推進白書 令和4年版 特2-1-4表の 893人）の照合を、
GPT と Gemini に判定させる。主張（不整合かどうか）は伏せ、二つの資料の原文だけを渡して、答えが決まる問いにする。
対照：同じ白書の表の令和2年 930人と、犯罪白書 令和3年版の本文の令和2年 930人（一致するのが正答）。対照に正答した呼び出しだけを使う。
各判定者に5回。過半で答えを決める。"""
import json, os, sys, datetime, collections, concurrent.futures as cf
sys.path.insert(0, 'kokkai'); import llm
OUT = 'replications/R075_ninchi_904'; os.makedirs(OUT, exist_ok=True)
A = open('data/raw/kokkai_src/shuisho/shu/200/064_a.txt', encoding='utf-8').read()
i = A.find('一について'); ANS = A[i:A.find('二について', i)].strip()
SRC = f"""## 資料1：内閣の答弁書（内閣衆質200第64号、令和元年11月15日）の「一について」
{ANS}

## 資料2：再犯防止推進白書 令和4年版（法務省）18頁の表 特2-1-4「刑事施設で認知症と診断を受けた者の数の推移（平成30年～令和3年）」
年次｜新受刑者数 総数｜新受刑者数 60歳以上｜認知症スクリーニング検査実施者｜医師による診察｜認知症診断者
平成30年｜18,272｜3,294｜893｜131｜35
令和元年｜17,464｜3,296｜908｜206｜50
令和2年｜16,620｜3,160｜930｜195｜54
令和3年｜16,152｜3,284｜973｜183｜55
注　法務省調査による。

## 資料3：同じ白書の本文（18頁）
入所時の年齢が 60 歳以上又はその言動や生活状況等から認知症が疑われる者に対し、一部の刑事施設において、認知症スクリーニング検査を実施し、その結果、認知症が疑われる場合（特 2-1-4 参照）には、医師による診察を実施する（以下略）

## 資料4：犯罪白書 令和3年版（法務総合研究所）の本文
平成 30 年度から，各矯正管区の基幹施設（札幌刑務所，宮城刑務所，府中刑務所，名古屋刑務所，大阪刑務所，広島刑務所，高松刑務所及び福岡刑務所）において，入所受刑者のうち，入所時の年齢が 60 歳以上のものなどに対して，認知症スクリーニング検査を実施し，認知症が疑われると判定された受刑者に対して，医師による診察を実施する取組を行っている。令和元年から実施対象施設に栃木刑務所及び和歌山刑務所が追加され，２年においては，930 人に対して検査を実施し，そのうち，医師による診察を受けた者が 195 人，認知症と診断された者が 54 人であった（法務省矯正局の資料による。）。
"""
Q = """
次の問いに、資料に書かれていることだけから答えてください。推測で補わないでください。JSON だけを返してください。
C1：資料4の令和2年の検査実施 930人と、資料2の表の令和2年の検査実施者 930人は、値が一致しますか。（"はい"／"いいえ"）
Q1：資料1の 904名と資料2の表の平成30年の検査実施者 893人は、どちらも平成30年の、同じ取組（法務省の通知に基づく刑事施設の認知症スクリーニング検査）の検査を受けた人数として示されていますか。（"はい"／"いいえ"）
Q2：資料1の 904名は、平成30年の検査実施者 893人（資料2）より多いですか。（"はい"／"いいえ"）
Q3：資料3が示す検査の対象（入所時60歳以上又は認知症が疑われる者）は、資料1の検査の対象（入所時60歳以上の者）を含む、より広い範囲ですか。（"はい"／"いいえ"）
Q4：資料1と資料2のどちらかに、904 と 893 の違いを説明する記述（数え方の基準日、年と年度の別、対象施設の違いなど）がありますか。（"はい"／"いいえ"）
Q5：資料1・2から、904 と 893 のどちらが正しいか、または両方が別の数え方で正しいかを決められますか。（"はい"／"いいえ"）
Q6：資料1の「認知症傾向がある者」109名と、資料2の平成30年の「医師による診察」131人は、資料の上で同じ量として示されていますか。（"はい"／"いいえ"）
形式：{"C1":"…","Q1":"…","Q2":"…","Q3":"…","Q4":"…","Q5":"…","Q6":"…","根拠":"各問の根拠を一文ずつ"}
"""
P = SRC + Q
def call(job):
    name, n = job
    try: t = (llm.gpt if name == 'gpt' else llm.gemini)(P)
    except Exception as ex: t = f'ERROR {type(ex).__name__}'
    j = llm.js(t) or {}
    return dict(judge=name, n=n, ok=j.get('C1') == 'はい', ans={k: j.get(k) for k in ['Q1','Q2','Q3','Q4','Q5','Q6']}, basis=j.get('根拠', ''), raw=t)
jobs = [(nm, n) for nm in ('gpt', 'gemini') for n in range(5)]
with cf.ThreadPoolExecutor(5) as ex: res = list(ex.map(call, jobs))
with open(f'{OUT}/calls.jsonl', 'w') as w:
    for x in res: w.write(json.dumps(x, ensure_ascii=False) + '\n')
open(f'{OUT}/PROMPT.md', 'w').write(P)
out = dict(round='R075', date=datetime.date.today().isoformat(), control_ok=sum(x['ok'] for x in res), calls=len(res), major={})
for nm in ('gpt', 'gemini'):
    ok = [x for x in res if x['judge'] == nm and x['ok']]
    out['major'][nm] = {q: (lambda c: c[0][0] if c and c[0][1] * 2 > len(ok) else '過半なし')(collections.Counter(x['ans'][q] for x in ok).most_common(1)) for q in ['Q1','Q2','Q3','Q4','Q5','Q6']}
    out['major'][nm]['使えた呼び出し'] = len(ok)
json.dump(out, open('results/kyosei_ninchi/R075.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
