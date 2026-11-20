"""検査の台帳（checks/TALLY.tsv）を作る：どの検査が照合の検査か、どの統計のページに属するか、要約（tally）があるか。
- kind=照合：資料の値どうし、または再計算と公表値を照合する検査。要約（results/<dir>/tally/<検査>*.json）を書くべきもの
- kind=補助：照合ではない検査（取得の準備、Last-Modified の外れ値、文字列セルの数え上げ、消えた区分の検出、公表方針の読み取り、仮説の検定など）
状態（status）は要約ファイルの有無から決める：集計済み（検査が書いた）／集計済み（既存の出力から）／未集計／対象外。
使い方: python checks/generic/build_tally_registry.py"""
import os, glob, json, re
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 照合ではない検査
AUX = {'gyakutai/c700_teisei_yotei.py', 'keisatsu/c404_lastmod_outliers.py', 'jisatsu_hakusho/c1103_text_numbers.py',
       'kyosei_ninchi/c4301_ninchi.py', 'kyosei_ninchi/c4501_vanish_kyosei.py', 'kyosei_ninchi/c4502_zero_past.py',
       'monka/c604_kouhyou_policy.py', 'kyoin_chokai/c4603_kohyo_r4.py', 'saihan/c504_moj_seigo_grep.py',
       'moj_sexoffender/c102_r2020_strata.py', 'moj_sexoffender/c103_H001.py', 'stalker/c414_kankei.py'}
# 後の版の検査に置き換わった検査・参考扱いの検査（同じ値を二重に数えないため。r26、METHODS に記載）
#   c009（71↔72 をファイル名で対応）・c009g（任意の2版をファイル名で対応）→ c009h（中身で対応）に置き換え。図表番号の振り直しで表を取り違えるため
#   c011（行ごとの照合）→ c012 → c012g に置き換え。c012 は c012g の令和5年版と同じ処理
#   c008（前年版の同じセル位置）：偶然の一致が多く判定に使えない（作業ノート）。参考扱い
AUX |= {'hanzai_hakusho/c008_prev_edition.py', 'hanzai_hakusho/c009_revisions_all.py', 'hanzai_hakusho/c009g_revisions_pair.py',
        'hanzai_hakusho/c011_view_vs_machine.py', 'hanzai_hakusho/c012_view_vs_machine_multiset.py',
        'cross/c505_moj_seigo_vs_hakusho.py',
        'gyakutai/c703_keisatsu_tsukoku.py',
        'saihan/c601_kouka_wording.py'}  # c601（saihan）：効果検証の書き方の文を抜き出すだけ（値の照合ではない）。検査の番号が monka/c601 と重なり、monka の要約を saihan に数えていた（2026-11-20）  # c703：定義の違う2つの数（年度の件数と暦年の人数）を並べるだけ。一致を期待しない  # c505：正誤情報の数値の文字列を白書から探す候補の検索（値の照合ではない。c504 と同じ扱い）
# 検査のフォルダと統計のページが一致しないもの
SLUG = {'gyakutai/c4001_shibo_hyo12.py': 'shibo-jirei', 'gyakutai/c4003_shibo_tables.py': 'shibo-jirei',
        'gyakutai/c4002_shogai_press.py': 'shogai-gyakutai', 'gyakutai/c4004_shogai_houkoku.py': 'shogai-gyakutai',
        'gyakutai/c4005_shogai_pref.py': 'shogai-gyakutai', 'gyakutai/c4006_shogai_tate.py': 'shogai-gyakutai',
        'moj_sexoffender/c101_r2020.py': 'kyosei-so', 'moj_sexoffender/c102_r2020_strata.py': 'kyosei-so', 'moj_sexoffender/c103_H001.py': 'kyosei-so',
        'moj_sexoffender/c104_hogo.py': 'moj-sexoffender', 'cross/c406_hanzaihakusho_vs_toukei.py': 'hanzai-hakusho',
        'cross/c505_moj_seigo_vs_hakusho.py': 'saihan', 'stalker/c414_kankei.py': 'keisatsu', 'moj_kensho2/c4201_recalc.py': 'shokugyo', 'moj_kyosei_kensho/c4701_shokugyo_seisa.py': 'shokugyo',
        'moj_yakubutsu/c4101_recalc.py': 'yakubutsu', 'saihan/c3901_sainyu.py': 'saihan', 'saihan/c3902_5310.py': 'saihan', 'saihan/c3903_542.py': 'saihan'}
DIR2SLUG = {'hanzai_hakusho': 'hanzai-hakusho', 'moj_sexoffender': 'moj-sexoffender', 'kyoin_chokai': 'kyoin-chokai', 'kyosei_ninchi': 'kyosei-ninchi',
            'jisatsu_hakusho': 'jisatsu-hakusho', 'jinko_dotai': 'jinko-dotai', 'juki_idou': 'juki-idou', 'shogai_hakusho': 'shogai-hakusho',
            'danjo_hakusho': 'danjo-hakusho', 'kodomo_hakusho': 'kodomo-hakusho', 'monka_kihon': 'monka-kihon', 'jinko_suikei': 'jinko-suikei',
            'kensetsu_juchu': 'kensetsu-juchu', 'kessan_card': 'kessan-card'}
rows = []
for f in sorted(glob.glob(os.path.join(R, 'checks', '*', 'c*.py'))):
    rel = os.path.relpath(f, os.path.join(R, 'checks'))
    d, fn = rel.split('/')
    if d in ('generic', 'quotes'):
        continue
    check = re.match(r'(c\d+[a-z]?)', fn).group(1)
    slug = SLUG.get(rel) or DIR2SLUG.get(d, d.replace('_', '-'))
    kind = '補助' if rel in AUX else '照合'
    tal = glob.glob(os.path.join(R, 'results', '*', 'tally', check + '.json')) + glob.glob(os.path.join(R, 'results', '*', 'tally', check + '__*.json'))
    if kind == '補助':
        status = '対象外'
    elif not tal:
        status = '未集計'
    else:
        src = {json.load(open(t))['source'] for t in tal}
        status = '集計済み（検査が書いた）' if src == {'check'} else '集計済み（既存の出力から）'
    rows.append((rel, check, slug, kind, status))
with open(os.path.join(R, 'checks', 'TALLY.tsv'), 'w', encoding='utf-8') as w:
    w.write('script\tcheck\tslug\tkind\tstatus\n')
    for r in rows:
        w.write('\t'.join(r) + '\n')
import collections
dup = [c for c, n in collections.Counter(r[1] for r in rows if r[3] == '照合').items() if n > 1]
if dup: print('注意：照合の検査で番号が重なっている（要約を取り違える）:', dup)
print(collections.Counter((r[3], r[4]) for r in rows))
