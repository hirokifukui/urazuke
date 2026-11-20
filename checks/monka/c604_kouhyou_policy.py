"""文科 2-6「懲戒処分の公表に関する取組状況一覧」（令和4年度調査＝令和5年11月1日現在、67自治体）を
自治体ごとに切り出し、公表の範囲を読む手がかりの語を拾う。(c) 全数照合の前段：どの自治体のどの処分が
公表対象かを決めるため。語の有無は手がかりで、判定は本文を読んで行う（本文は results に保存）。"""
import subprocess, re, sys, json
f = sys.argv[1]
t = subprocess.run(['pdftotext', '-layout', f, '-'], capture_output=True, text=True).stdout
lines = t.splitlines()
NAMES = "北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 群馬県 埼玉県 千葉県 東京都 神奈川県 新潟県 富山県 石川県 福井県 山梨県 長野県 岐阜県 静岡県 愛知県 三重県 滋賀県 京都府 大阪府 兵庫県 奈良県 和歌山県 鳥取県 島根県 岡山県 広島県 山口県 徳島県 香川県 愛媛県 高知県 福岡県 佐賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県 札幌市 仙台市 さいたま市 千葉市 川崎市 横浜市 相模原市 新潟市 静岡市 浜松市 名古屋市 京都市 大阪市 堺市 神戸市 岡山市 広島市 北九州市 福岡市 熊本市".split()
pos = {}
for i, l in enumerate(lines):
    m = re.match(r'\s*(\d{1,2})\s+(\S+)', l)
    if m and 1 <= int(m.group(1)) <= 67 and m.group(2) == NAMES[int(m.group(1)) - 1] and int(m.group(1)) not in pos:
        pos[int(m.group(1))] = i
# 各自治体のブロック：標識行の前後（前の自治体の標識行と次の標識行の中間で区切る）
keys = sorted(pos)
out = {}
for k_i, k in enumerate(keys):
    lo = (pos[keys[k_i-1]] + pos[k]) // 2 + 1 if k_i else 0
    hi = (pos[k] + pos[keys[k_i+1]]) // 2 + 1 if k_i + 1 < len(keys) else len(lines)
    txt = re.sub(r'\s+', '', ''.join(lines[lo:hi]))
    out[NAMES[k-1]] = txt
miss = [n for n in NAMES if n not in out]
print('found', len(out), 'missing', miss)
KW = {'訓告':'訓告', 'HP':'ホームページ|ＨＰ|HP|ウェブ|Web|web', '報道':'報道', '全件':'全て|全件|すべて', '交通除外':'交通', '氏名':'氏名'}
print('自治体\t' + '\t'.join(KW))
for n in NAMES:
    if n in out:
        print(n + '\t' + '\t'.join('○' if re.search(p, out[n]) else '' for p in KW.values()))
json.dump(out, open('results/monka/c604_kouhyou_policy_R04.json', 'w'), ensure_ascii=False, indent=1)
