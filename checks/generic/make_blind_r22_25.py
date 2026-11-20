"""R022〜R025 の盲検フォルダを作る（2026-11-18）。
主張は publish/findings.json の要旨をそのまま使う（反証にかける前・書き直して再反証待ちの全記録）。
資料はデータの写し（APFS の clone）。PROMPT・資料の sha256 を replications/RXXX_gpt_refute/FIXED_SHA256.txt に書く。
使い方：python3 checks/generic/make_blind_r22_25.py R022 [R023 ...]（引数なしで全部）
"""
import json, os, sys, subprocess, hashlib, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(ROOT, 'data/raw')
HB = os.path.join(RAW, 'hanzai_hakusho')
BL = os.path.expanduser('~/mitodoke_blind')
F = {f['id']: f for f in json.load(open(os.path.join(ROOT, 'publish/findings.json')))}
Y = lambda i: F[i]['要旨']

HEAD = '''# 課題：主張の検証（反証の試み）

{intro}

以下の主張は、ある検証者が書いたものです。**正しいものも、誤っているものも含まれています。**あなたの役割は、各主張をこのフォルダの資料に基づいて独立に確かめ、誤りがあれば見つけることです。検証者の結論に合わせる必要はありません。

## 判定の規則（先に固定する。これ以外の判定はしない）
- **支持**：主張の中の数値・事実を、資料の該当箇所（ファイル名・頁・表・セル）で自分で確かめ、すべて一致した。
- **反証**：主張の中の数値・事実の少なくとも1つが、資料の該当箇所と矛盾する。矛盾する箇所と値を示す。
- **判定不能**：資料に確かめる材料がない、または解釈によって結論が変わる。何が足りないか、どの解釈で結論が変わるかを書く。

各主張について：1. 確かめた箇所と読んだ値、2. 主張を弱める別の説明（定義の違い、注記、別の箇所の記述など）を資料の中から探して挙げる、3. 言い過ぎがないか。計算・抽出はコードで行い（pdftotext -layout、openpyxl、pandas など）、要点を残す。資料の事実は資料だけで確かめる。統計の一般的な性質は知識として使ってよい。その場合は、そう明記する。主張が「〜がない」と言う場合は、渡した資料の範囲で確かめ、範囲を書く。

## 主張
{qs}

## 出力
REPORT.md に、主張ごとに「判定（支持／反証／判定不能）」「確かめた箇所と値」「別の説明」「言い過ぎの指摘」を書く。最後に、全体の要約を3行以内で書く。
'''

ED = {'r01': '66_20261116T095154Z', 'r02': '67_20261116T094520Z', 'r03': '68_20261116T085457Z', 'r04': '69_20261116T085457Z',
      'r05': '70_20261116T073025Z', 'r06': '71_20261116T090659Z', 'r07': '72'}
R015 = os.path.join(BL, 'R015'); R016 = os.path.join(BL, 'R016')

ROUNDS = {
 'R022': dict(
   H='H027', title='犯罪白書の図表 Excel（HK-A1・A2・A3・A5・A10）',
   intro='''このフォルダには、法務省の公表資料の写しがあります。
- r01/〜r07/：犯罪白書 令和元年版〜令和7年版の図表（zuhyo/）と資料（shiryo/）の Excel。ファイル名は図表番号（例：5-4-4.xlsx は 5-4-4表）。1つのファイルに「閲覧用」「機械判読用」など複数のシートがあることがある。
- pdf/hanzai_r05.pdf・hanzai_r06.pdf・hanzai_r07.pdf：犯罪白書 令和5・6・7年版（PDF）。
- seigohyo/：法務省が公表した犯罪白書の正誤表・訂正のお知らせ（HTML・PDF）。''',
   files=[*[(f'{HB}/{d}/{sub}', f'{k}/{sub}') for k, d in ED.items() for sub in ('zuhyo', 'shiryo')],
          (f'{HB}/pdf/r05_001410095.pdf', 'pdf/hanzai_r05.pdf'), (f'{HB}/pdf/r06_001432725.pdf', 'pdf/hanzai_r06.pdf'),
          (f'{HB}/pdf/r07_001455836.pdf', 'pdf/hanzai_r07.pdf'), (f'{HB}/seigohyo', 'seigohyo')],
   qs=[('HK-A5', Y('HK-A5')),
       ('CTRL', '令和7年版 4-8-2-2図① の Excel で、2004年（平成16年）の総数は 32,190 である。'),
       ('HK-A1', Y('HK-A1')),
       ('HK-A3', Y('HK-A3')),
       ('HK-A10', Y('HK-A10')),
       ('CTRL', '令和5年版 5-4-4表 の閲覧用シートで、1989年（平成元年）の「計（B）」は 1,168 である。'),
       ('HK-A2', Y('HK-A2'))]),
 'R023': dict(
   H='H028', title='白書の本文と訂正（HK-A9・NK-K1・SH-A1）',
   intro='''このフォルダには、法務省の公表資料の写しがあります。
- hanzai_r04.pdf〜hanzai_r07.pdf：犯罪白書 令和4〜7年版（PDF。令和6年版は法務省のファイル番号 001432725）。
- r04_web/・r05_web/・hanzai_r06_web/：犯罪白書 令和4・5・6年版の Web 版本文（HTML、2026-11-16 取得）。
- r04_teisei.html・r05_teisei.html・hanzai_r06_teisei.html：法務省「令和４年版犯罪白書の訂正のお知らせ」（ページ番号 s_00122）・「令和５年版…」（s_00130）・「令和６年版…」（s_00140）。
- hanzai_r07_4-10-2-1.xlsx：犯罪白書 令和7年版 4-10-2-1表 の Excel。
- kyosei/：矯正統計年報の Excel。2025年は全表（25-00-*.xlsx）、2020〜2024年は第88表（休養患者の病名別）・第93表（死亡者の病名別）。ファイル名は「年の下2桁-00-表番号」。
- saihan_h30.pdf・saihan_r01.pdf〜saihan_r07.pdf：再犯防止推進白書 平成30年版・令和元〜7年版の全体版（PDF）。
- saihan_seigo.pdf：再犯防止推進白書の正誤表（PDF）。''',
   files=[*[(f'{R015}/{x}', x) for x in ('hanzai_r04.pdf', 'hanzai_r05.pdf', 'hanzai_r06.pdf', 'hanzai_r07.pdf', 'hanzai_r06_web', 'hanzai_r06_teisei.html', 'kyosei')],
          *[(f'{R016}/{x}', x) for x in ('r04_web', 'r05_web', 'r04_teisei.html', 'r05_teisei.html')],
          (os.path.join(BL, 'R017/hanzai_r07_4-10-2-1.xlsx'), 'hanzai_r07_4-10-2-1.xlsx'),
          *[(f'{RAW}/saihan/{d}/{fn}', f'saihan_{d.lower()}.pdf') for d, fn in (('H30', 'zentai_001283071.pdf'), ('R01', 'zentai_001313763.pdf'), ('R02', 'zentai_001362421.pdf'), ('R03', 'zentai_001365515.pdf'), ('R04', 'zentai_001389118.pdf'), ('R05', 'zentai_001407646.pdf'), ('R06', 'zentai_001433241.pdf'), ('R07', 'zentai_001451882.pdf'))],
          (f'{RAW}/saihan/R02/seigo_001452648.pdf', 'saihan_seigo.pdf')],
   qs=[('HK-A9', Y('HK-A9')),
       ('CTRL', '令和6年版犯罪白書の訂正のお知らせで、生活環境の調整を開始した受刑者の人員の訂正後の値は 2万8,559人である。'),
       ('NK-K1', Y('NK-K1')),
       ('SH-A1', Y('SH-A1')),
       ('CTRL', '矯正統計年報 2025年 第88表 で、「血管性及び詳細不明の認知症」（男）の総数は 25人である。')]),
 'R024': dict(
   H='H029', title='法務省の効果検証と検察統計（SO-H1・SO-H4・KP-C1・KS-A1）',
   intro='''このフォルダには、法務省の公表資料の写しがあります。
- 001318218.pdf：法務省保護局「保護観察所における性犯罪者処遇プログラム受講者の再犯等に関する分析」（令和2年3月）。001466396.pdf：その概要。001322889.pdf：平成24年の同種の分析。
- kyosei_R02_report.pdf：法務省矯正局「刑事施設における性犯罪者処遇プログラム受講者の再犯等に関する分析」（令和2年3月）。kyosei_H24_report.pdf：同じ題名の報告書（平成24年12月）。
- kensatsu_r07_t01.xlsx・kensatsu_r07_t02.xlsx：検察統計年報（令和7年、e-Stat）第1表「被疑事件の受理、既済及び未済件数の累年比較」・第2表「被疑事件の受理、既済及び未済人員の累年比較」。''',
   files=[*[(os.path.join(BL, 'R007', x), x) for x in ('001318218.pdf', '001466396.pdf', '001322889.pdf')],
          *[(os.path.join(BL, 'R010', x), x) for x in ('kyosei_R02_report.pdf', 'kyosei_H24_report.pdf')],
          *[(os.path.join(BL, 'R009', x), x) for x in ('kensatsu_r07_t01.xlsx', 'kensatsu_r07_t02.xlsx')]],
   qs=[('KS-A1', Y('KS-A1')),
       ('SO-H1', Y('SO-H1')),
       ('CTRL', '検察統計年報 第2表 の昭和37年の既済総数のセルは 6,744,659 である。'),
       ('KP-C1', Y('KP-C1')),
       ('SO-H4', Y('SO-H4')),
       ('CTRL', '矯正局の令和2年3月の報告の表1で、比較対照群 324名のうち迷惑行為防止条例違反者は 46名である。')]),
 'R025': dict(
   H='H030', title='厚生労働省・こども家庭庁・文部科学省の統計（630-D1・630-M1・ES-I1・GY-Q1・MK-L2）',
   intro='''このフォルダには、日本の公的統計のファイルと公表ページの写しがあります。
- seishin630/longterm_1998_2025.xlsx：精神保健福祉資料（630調査）の長期データ（1998〜2025年）。seishin630/h30/・r5/・r6/：同じ調査の平成30年度・令和5年度・令和6年度の集計ファイル（回答率の表を含む）。
- eisei_2023_t2-1.csv・eisei_2024_t2-1.csv・eisei_2025_t2-1.csv：衛生行政報告例 第2表-1 精神障害者措置入院・仮退院状況（2023〜2025年度、Shift_JIS）。eisei_seigo_2023_20260928.xlsx：衛生行政報告例 令和5年度（2023年度）の正誤情報（2026年9月28日）。
- gyakutai/sokuhou/：児童虐待相談対応件数の速報値の資料（R4_sokuhou_cfa_20230401_19.pdf が令和4年度）。gyakutai/kakutei_gaiyo/：福祉行政報告例の結果の概要（gyousei222_kekka_gaiyo.pdf が令和4年度）。gyakutai/estat/：令和4年度（FY2022）の e-Stat の表（都道府県・指定都市・中核市別を含む）。gyakutai/teisei/：こども家庭庁「福祉行政報告例の訂正予定について」の資料（訂正予定の自治体の一覧を含む）。
- mext_00001_20261117.html：文部科学省「教育職員等による児童生徒性暴力等の防止等について」のページ（2026-11-17 取得）。mext_00001_20240422103757.html・mext_00001_20250422043151.html・mext_00001_20260421043116.html：同じページの Internet Archive の写し（ファイル名の数字は写しの日時）。db_chosa.pdf：「令和７年度教員性暴力等防止法に基づくデータベース活用状況等調査の結果について」。r05_2-5-1_jokyo.pdf・r06_2-5-1_jokyo.pdf：公立学校教職員の人事行政状況調査 令和5年度・令和6年度の資料 2-5-1「性犯罪・性暴力等に係る懲戒処分等の状況」。''',
   files=[(f'{RAW}/seishin630/longterm_1998_2025.xlsx', 'seishin630/longterm_1998_2025.xlsx'),
          *[(f'{RAW}/seishin630/{d}', f'seishin630/{d}') for d in ('h30', 'r5', 'r6')],
          *[(os.path.join(BL, 'R008', x), x) for x in ('eisei_2023_t2-1.csv', 'eisei_2024_t2-1.csv', 'eisei_2025_t2-1.csv', 'eisei_seigo_2023_20260928.xlsx')],
          (f'{RAW}/gyakutai/sokuhou', 'gyakutai/sokuhou'), (f'{RAW}/gyakutai/kakutei_gaiyo', 'gyakutai/kakutei_gaiyo'), (f'{RAW}/gyakutai/teisei', 'gyakutai/teisei'),
          *[(f'{RAW}/gyakutai/estat/{x}', f'gyakutai/estat/{x}') for x in sorted(os.listdir(f'{RAW}/gyakutai/estat')) if x.startswith('FY2022')],
          *[(os.path.join(BL, 'R020', x), x) for x in ('mext_00001_20261117.html', 'mext_00001_20240422103757.html', 'mext_00001_20250422043151.html', 'mext_00001_20260421043116.html', 'db_chosa.pdf', 'r05_2-5-1_jokyo.pdf', 'r06_2-5-1_jokyo.pdf')]],
   qs=[('630-M1', Y('630-M1')),
       ('GY-Q1', Y('GY-Q1')),
       ('CTRL', '630調査の長期データで、長野県の2018年の在院患者数は 3,968人である。'),
       ('ES-I1', Y('ES-I1')),
       ('630-D1', Y('630-D1')),
       ('MK-L2', Y('MK-L2')),
       ('CTRL', '令和4年度の児童虐待相談対応件数の確定値は 219,170件である。')]),
}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def build(r):
    R = ROUNDS[r]; d = os.path.join(BL, r)
    assert not os.path.exists(d), d + ' がすでにある'
    os.makedirs(d)
    for src, dst in R['files']:
        assert os.path.exists(src), src
        t = os.path.join(d, dst); os.makedirs(os.path.dirname(t), exist_ok=True)
        subprocess.run(['cp', '-cR' if os.path.isdir(src) else '-c', src, t], check=True)
    qs = '\n'.join(f'- **Q{n}** {q}' for n, (_, q) in enumerate(R['qs'], 1))
    open(os.path.join(d, 'PROMPT.md'), 'w').write(HEAD.format(intro=R['intro'], qs=qs))
    rep = os.path.join(ROOT, 'replications', r + '_gpt_refute'); os.makedirs(rep, exist_ok=True)
    lines = []
    for base, _, fs in os.walk(d):
        for fn in sorted(fs):
            if fn.startswith('.'): continue
            p = os.path.join(base, fn); lines.append(f'{sha(p)}  {os.path.relpath(p, d)}')
    open(os.path.join(rep, 'FIXED_SHA256.txt'), 'w').write('\n'.join(sorted(lines, key=lambda l: l.split('  ', 1)[1])) + '\n')
    key = {f'Q{n}': i for n, (i, _) in enumerate(R['qs'], 1)}
    json.dump(key, open(os.path.join(rep, 'KEY.json'), 'w'), ensure_ascii=False, indent=1)
    sh = os.path.join(BL, f'run_{r}.sh')
    open(sh, 'w').write(f'''#!/bin/sh
codex exec --json --skip-git-repo-check -s workspace-write -C ~/mitodoke_blind/{r} -o ~/mitodoke_blind/{r}_lastmsg.md - < ~/mitodoke_blind/{r}/PROMPT.md > ~/mitodoke_blind/{r}_events.jsonl 2> ~/mitodoke_blind/{r}_err.log
echo "exit=$? $(date '+%F %T')" > ~/mitodoke_blind/{r}.done
''')
    os.chmod(sh, 0o755)
    print(r, len(lines), 'files', {k: v for k, v in key.items()})


if __name__ == '__main__':
    for r in (sys.argv[1:] or sorted(ROUNDS)):
        build(r)
