"""陰性対照（r10 で足した検査）：原データの写しの1か所を変え、検査がそれを検出することを確かめる。
作業用の根（/tmp/urazuke_negctl/<case>/）に lib・checks を symlink し、対象の統計だけ写しを置く。
使い方: ~/.venvs/urazuke/bin/python checks/generic/negctl_r10.py [case ...]"""
import os, sys, shutil, subprocess, json, re, openpyxl
R = os.getcwd(); PY = os.path.expanduser('~/.venvs/urazuke/bin/python')


def mut_text(path, old, new):
    t = open(path, encoding='utf-8').read(); assert old in t, old
    open(path, 'w', encoding='utf-8').write(t.replace(old, new, 1))


def mut_bytes(path, old, new):
    b = open(path, 'rb').read(); assert old in b, old
    open(path, 'wb').write(b.replace(old, new, 1))


def mut_cell(path, old, new, idx=0):
    wb = openpyxl.load_workbook(path, data_only=True); k = 0
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if c.value is not None and str(c.value).strip() == str(old):
                    if k == idx:
                        c.value = type(c.value)(new); wb.save(path); return
                    k += 1
    raise ValueError(old)


CASES = {
 # 死亡事例：第21次 表2（心中）総数の例数の括弧 8 → 9 → 第21次でも括弧の合計が崩れる
 'shibo_21': ('shibo_jirei', lambda d: mut_text(f'{d}/21/04_kobetsu.txt', '469（8）', '469（9）'),
              'checks/gyakutai/c4001_shibo_hyo12.py', r'"版": 21, "表": "表2自殺"'),
 # 死亡事例：第20次 表1（心中以外）第18次の人数 49(15) → 50(15) → 版間（20→21）が崩れる
 'shibo_20v': ('shibo_jirei', lambda d: mut_text(f'{d}/20/04_kobetsu.txt', '49(15)', '50(15)'),
               'checks/gyakutai/c4001_shibo_hyo12.py', r'"版": "20→21"'),
 # 障害者虐待：令和5年度 発表 養護者 通報 9,972 → 9,973 → 前回調査・経年グラフが崩れる
 'shogai_r05': ('shogai_gyakutai', lambda d: mut_text(f'{d}/press_R05.txt', '9,972 件', '9,973 件'),
                'checks/gyakutai/c4002_shogai_press.py', r'不一致 [1-9]'),
 # 障害者虐待：令和6年度 発表 施設 判断の増減 73 件 → 74 件 → 増減率の文が崩れる
 'shogai_rate': ('shogai_gyakutai', lambda d: mut_text(f'{d}/press_R06.txt', '73 件（6.1％）', '74 件（6.1％）'),
                 'checks/gyakutai/c4002_shogai_press.py', r'不一致 [1-9]'),
 # 矯正統計：令和7年 第64表 平成30年 満期釈放 計 8523 → 8524 → 版間・白書との照合が崩れる
 'kyosei_64': ('kyosei', lambda d: mut_cell(f'{d}/2025/25-00-64.xlsx', '8523', '8524'),
               'checks/saihan/c3901_sainyu.py', r'不一致 [1-9]'),
 # r11：死亡事例 第22次 表59 保護者の自殺を伴う よく活用している 26(1) → 25(1)
 'shibo_t59': ('shibo_jirei', lambda d: mut_text(f'{d}/22/04_kobetsu.txt', '26(1)       96.3%', '25(1)       96.3%'),
               'checks/gyakutai/c4003_shibo_tables.py', r'"版": 22, "表": "表 59[^"]*", "行": \d+, "列": 1, "検査": "内訳の和'),
 # r11：障害者虐待 結果報告書 表3-2 主たる障害が身体 151 → 152 → 合計 1,383 と合わない
 'shogai_h32': ('shogai_gyakutai', lambda d: mut_text(f'{d}/R06_houkoku.txt', '151      260      812', '152      260      812'),
                'checks/gyakutai/c4004_shogai_houkoku.py', r'不一致 [1-9]'),
 # r12：犯罪白書 令和7年版 5-3-10図① 平成8年 出所 男性 20410 → 20411 → 男＋女＝計 が崩れる
 'hk_5310': ('hanzai_hakusho', lambda d: mut_cell(f'{d}/72/zuhyo/5-3-10.xlsx', '20410', '20411'),
             'checks/saihan/c3902_5310.py', r'不一致 [1-9]'),
 # r12：犯罪白書 令和7年版 5-4-2図① 平成28年 終了人員 13506 → 13507 → 再処分率が崩れる
 'hk_542': ('hanzai_hakusho', lambda d: mut_cell(f'{d}/72/zuhyo/5-4-2.xlsx', '13506', '13507'),
            'checks/saihan/c3903_542.py', r'"版": "令和7年版", "シート": "（H28～R６）①", "年": "平成28年"'),
 # r12：障害者虐待 結果報告書 表1 北海道 681 → 682 → 47の和＝合計 が崩れる
 'shogai_pref': ('shogai_gyakutai', lambda d: mut_text(f'{d}/R06_houkoku.txt', '北海道       681', '北海道       682'),
                 'checks/gyakutai/c4005_shogai_pref.py', r'不一致 [1-9]'),
 # r13：厚労省 入院対象者の状況（現行の版）ステージ別 合計 749名 → 750名
 'mhoa_wb': ('iryokansatsu', lambda d: mut_text(f'{d}/mhlw/nyuin.html', '749名', '750名'),
             'checks/iryokansatsu/c3003_nyuin_wayback.py', r'不一致 [1-9]'),
 # r15：令和6年版犯罪白書 Web 版本文の認知症スクリーニング 125人 → 126人（訂正後の値）→ 「誤0 正1」になる
 'r06_seigo': ('hanzai_hakusho', lambda d: mut_text(f'{d}/71_20261116T090659Z/honbun/n71_2_4_8_2_2.html', '診断された者が125人', '診断された者が126人'),
               'checks/kyosei_ninchi/c4301_ninchi.py', r'235頁 診断 +Web本文 誤0 正1'),
 # r16：矯正統計年報 2024年 第22表 総数 14822 → 14823 → 犯罪白書 4-8-2-3図との照合で崩れる
 'settou': ('kyosei', lambda d: mut_cell(f'{d}/2024/24-00-22.xlsx', 14822, 14823),
            'checks/kyosei_ninchi/c4401_settou_korei.py', r'不一致 2024 総数 総数'),
 # r16：障害者虐待 結果報告書 表9 1,749 → 1,759 → 構成割合の再計算が崩れる
 'shogai_tate': ('shogai_gyakutai', lambda d: mut_text(f'{d}/R06_houkoku.txt', '1,749     37.1%', '1,759     37.1%'),
                 'checks/gyakutai/c4006_shogai_tate.py', r'不一致 [1-9]'),
 # r16：医療観察 2014年の写し（Shift_JIS）急性期 男 93名 → 94名
 'mhoa_wb2014': ('iryokansatsu', lambda d: mut_bytes(f'{d}/wayback/nyuin_20141115014515.html', '93名'.encode('cp932'), '94名'.encode('cp932')),
                 'checks/iryokansatsu/c3003_nyuin_wayback.py', r'不一致 [1-9]'),
 # r17：矯正統計年報 2024年版 第37表 2023年の発達障害 80 → 0 → 過去の年がすべて 0 の列として拾われる
 'zero_past': ('kyosei', lambda d: mut_cell(f'{d}/2024/24-00-37.xlsx', 80, 0),
               'checks/kyosei_ninchi/c4502_zero_past.py', r'2024 24-00-37.*発達障害'),
 # r18：文科省 令和6年度の結果のページに「公表に関する取組状況一覧」の資料を足す → 「消えた」が「一時的に消えた」に変わる
 'kohyo_vanish': ('kyoin_chokai', lambda d: mut_text(f'{d}/pages/1411820_00009.htm', '</body>', '<a href="/content/x.pdf">2-6　懲戒処分に関する処分基準の作成及び懲戒処分の公表に関する取組状況一覧（教育職員）（PDF:1KB）</a></body>'),
                  'checks/kyoin_chokai/c4602_jokyo.py', r'一時的に消えた：2022年度調査まで「懲戒処分に関する処分基準の作成及び懲戒処分の公表'),
}
out = {}
for case in [c for c in (sys.argv[1:] or CASES) if c in CASES]:
    slug, fn, script, pat = CASES[case]
    root = f'/tmp/urazuke_negctl/{case}'; shutil.rmtree(root, ignore_errors=True); os.makedirs(f'{root}/data/raw')
    for x in ('lib', 'checks'):
        os.symlink(f'{R}/{x}', f'{root}/{x}')
    os.makedirs(f'{root}/results/{slug}', exist_ok=True)
    for x in os.listdir(f'{R}/data/raw'):
        if x != slug:
            os.symlink(f'{R}/data/raw/{x}', f'{root}/data/raw/{x}')
    shutil.copytree(f'{R}/data/raw/{slug}', f'{root}/data/raw/{slug}', symlinks=True)
    base = subprocess.run([PY, script], cwd=root, capture_output=True, text=True).stdout
    before = bool(re.search(pat, base))
    fn(f'{root}/data/raw/{slug}')
    a = subprocess.run([PY, script], cwd=root, capture_output=True, text=True)
    after = bool(re.search(pat, a.stdout))
    out[case] = {'script': script, 'pattern': pat, 'detected_before_mutation': before,
                 'detected_after_mutation': after, 'pass': (not before) and after, 'stderr_tail': a.stderr[-300:]}
    print(case, 'before', before, 'after', after, 'PASS' if out[case]['pass'] else 'FAIL')
os.makedirs('results/scope', exist_ok=True)
prev = json.load(open('results/scope/negctl_r10.json')) if os.path.exists('results/scope/negctl_r10.json') else {}
prev.update(out); json.dump(prev, open('results/scope/negctl_r10.json', 'w'), ensure_ascii=False, indent=1)
