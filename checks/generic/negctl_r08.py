"""陰性対照（r08 で足した統計の検査）：原データの写しの1か所を変え、検査がそれを検出することを確かめる。
作業用の根（/tmp/urazuke_negctl/<case>/）に lib・checks を symlink し、data/raw は対象の統計だけ写しを置く（他は symlink）。
results は作業用の根の中に書かれ、本体の results は変わらない。
使い方: ~/.venvs/urazuke/bin/python checks/generic/negctl_r08.py [case ...]"""
import os, sys, shutil, subprocess, json, re, openpyxl
R = os.getcwd(); PY = os.path.expanduser('~/.venvs/urazuke/bin/python')
def mut_xlsx(path, sheet, cell, delta):
    wb = openpyxl.load_workbook(path); ws = wb[sheet]; ws[cell].value = ws[cell].value + delta; wb.save(path)
def mut_find(path, sheet, value, delta, idx=0):
    wb = openpyxl.load_workbook(path); ws = wb[sheet] if sheet else wb.worksheets[0]; k = 0
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, (int, float)) and c.value == value:
                if k == idx: c.value = value + delta; wb.save(path); return
                k += 1
    raise ValueError(value)
def _to_text(path, sheet, cell):
    wb = openpyxl.load_workbook(path); ws = wb[sheet]; ws[cell].value = str(int(ws[cell].value)); wb.save(path)
def mut_text(path, old, new):
    t = open(path, encoding='utf-8').read(); assert old in t, old; open(path, 'w', encoding='utf-8').write(t.replace(old, new, 1))
def mut_csv(path, old, new, enc='cp932'):
    t = open(path, 'rb').read().decode(enc); assert old in t, old; open(path, 'wb').write(t.replace(old, new, 1).encode(enc))
CASES = {
 # 自殺対策白書：2-1表の男の値を1増やす → (a) 総数≠男+女
 'jisatsu_hakusho_2-1': ('jisatsu_hakusho', lambda d: mut_xlsx(f'{d}/r2026/sanko2_001760475.xlsx', '参考資料2-1表', 'D10', 1), 'checks/jisatsu_hakusho/c1102_internal_cross.py', r'2-1 総数≠男\+女'),
 # 自殺対策白書：令和7年版の2-2表の値を変える → 版間の差
 'jisatsu_hakusho_ed': ('jisatsu_hakusho', lambda d: mut_xlsx(f'{d}/r2026/sanko2_001760475.xlsx', '参考資料2-2表', 'D20', 1), 'checks/jisatsu_hakusho/c1101_sanko_editions.py', r'参考資料2-2表 common \d+ diff [1-9]'),
 # 問題行動調査：令和5年度の都道府県表の北海道の値を変える → 和≠全国
 'futoko_pref': ('futoko', None, 'checks/futoko/c1202_pref_sums.py', r'r05/kekka tables \d+ cols \d+ issues [1-9]'),
 # 司法統計：第1表 令和7年版の値を変える → 総数≠訴訟＋以外
 'shiho_t1': ('shiho', lambda d: mut_xlsx(f'{d}/r07/keiji_16676.xlsx', '1', 'F28', 1), 'checks/shiho/c1303_table1_internal.py', r"'r07', '\(a\)', '全裁判所', 2025"),
 # 衛生行政報告例：第2表-1 全国の新規を変える → 流れの不一致
 'eisei_flow': ('eisei', None, 'checks/eisei/c1401_seishin_tables.py', r'\(b\)前年度末\+新規−解除≠本年度末'),
 # 人口動態統計：第4表 北海道 出生 男 11,066 を1増やす → 総数≠男+女
 'jinko_dotai_t4': ('jinko_dotai', lambda d: mut_find(f'{d}/kakutei25/06_hyoR07.xlsx', '第４表', 11066, 1), 'checks/jinko_dotai/c1501_kakutei.py', r'第4表 総数≠男\+女'),
 # 国勢調査：2025年 北海道 男 2,355,051 を1増やす → 総数≠男+女
 'kokusei_mf': ('kokusei', lambda d: mut_find(f'{d}/2025/shuyo_000040507382.xlsx', None, 2355051, 1), 'checks/kokusei/c1601_shuyo.py', r'\(a\)総数≠男\+女'),
 # 医療施設：統計表10 北海道 病院病床 86,584 を1増やす → 病院の病床≠種類の和
 'iryosd_t10': ('iryosd', lambda d: mut_find(f'{d}/2025/07sisetutoukei07.xlsx', '統計表10', 86584, 1), 'checks/iryosd/c1801_shisetsu.py', r'\(a\)病院の病床≠種類の和'),
 # 患者調査：表2 総数行 入院 病院 1148.6 を変える → 総数≠病院+一般
 'kanja_t2': ('kanja', lambda d: mut_find(f'{d}/2023/hyo.xlsx', '表2', 1148.6, 1), 'checks/kanja/c1901_kanja.py', r'\(a\)入院 総数≠病院\+一般診療所'),
 # 障害者白書：図表1 精神障害者 総計の外来 576.4 を 578.4 に → 総数≠内訳の和
 'shogai_z1': ('shogai_hakusho', lambda d: mut_text(f'{d}/r08/ref.txt', '603.0          576.4', '603.0          578.4'), 'checks/shogai_hakusho/c2101_zuhyo1.py', r'総数≠内訳の和'),
 # 男女共同参画白書：19,567 を 19,568 に → 不一致
 'danjo_st': ('danjo_hakusho', lambda d: mut_text(f'{d}/r08/06.txt', '19,567', '19,568'), 'checks/danjo_hakusho/c2201_vs_sources.py', r'19568, 19567, False'),
 # こども白書：重大事態 2024年度 1,404 を 1,405 に → 不一致
 'kodomo_jd': ('kodomo_hakusho', lambda d: mut_text(f'{d}/r08/2-1.txt', '919 1,306 1,404', '919 1,306 1,405'), 'checks/kodomo_hakusho/c2001_vs_sources.py', r'1404\], False'),
 # 毎勤：第1表 調査産業計 きまって支給 287,427 を1増やす
 'maikin_t1': ('maikin', lambda d: mut_find(f'{d}/2025/25cc01r.xlsx', None, 287427, 5), 'checks/maikin/c2301_maikin.py', r'\(a\)'),
 # CPI：CSV の 2025年 総合 111.9 を 112.0 に
 'cpi_pdf': ('cpi', lambda d: mut_csv(f'{d}/2025/chubunrui_index_000032103936.csv', '2025  ,111.9,', '2025  ,112.0,'), 'checks/cpi/c2401_cpi.py', r'\(b\)PDF≠CSV'),
 # 労働力調査：概要の労働力人口 7004 を 7014 に
 'roudou_lf': ('roudouryoku', lambda d: mut_text(f'{d}/2025/gaiyou.txt', '7004万人', '7014万人'), 'checks/roudouryoku/c2501_gaiyou.py', r'\(a\)労働力≠就業者'),
 # 決算検査報告：不当事項 211 件 を 212 件 に
 'kessan_ken': ('kessan', lambda d: mut_text(f'{d}/r07/fy07_01_gaiyou.txt', '211 件     111 億', '212 件     111 億'), 'checks/kessan/c2601_taiyo.py', r'事項計＝不当'),
 # 自殺対策白書：令和7年版 2-15表の数値1つを文字列にする → 文字列の数字を検出
 'jisatsu_hakusho_text': ('jisatsu_hakusho', lambda d: _to_text(f'{d}/r2025/sanko2_001593171.xlsx', '参考資料2-15表', 'C20'), 'checks/jisatsu_hakusho/c1103_text_numbers.py', r'r2025 numeric \d+ text-numbers [1-9]'),
 # 住基：表1 北海道 転入 総数 53,656 を1増やす → 総数≠男+女
 'juki_t1': ('juki_idou', lambda d: mut_find(f'{d}/2025/t1_000040407038.xlsx', None, 53656, 1), 'checks/juki_idou/c1701_idou.py', r'\(a\)総数≠男\+女'),
}
def futoko_mut(d):
    p = f'{d}/r05/kekka.txt'; t = open(p, encoding='utf-8').read()
    m = re.search(r'(\n\s*01\s+北海道\s+)([\d,]+)', t); assert m
    v = int(m[2].replace(',', '')) + 1
    open(p, 'w', encoding='utf-8').write(t[:m.start(2)] + f'{v:,}' + t[m.end(2):])
def eisei_mut(d):
    import glob
    p = glob.glob(f'{d}/r07/t2-1_*.csv')[0]; mut_csv(p, '全国,1365,7982,', '全国,1365,7983,')
FN = {'futoko_pref': futoko_mut, 'eisei_flow': eisei_mut}
out = {}
for case in (sys.argv[1:] or CASES):
    slug, fn, script, pat = CASES[case]; fn = fn or FN[case]
    root = f'/tmp/urazuke_negctl/{case}'; shutil.rmtree(root, ignore_errors=True); os.makedirs(f'{root}/data/raw')
    for x in ('lib', 'checks'): os.symlink(f'{R}/{x}', f'{root}/{x}')
    os.makedirs(f'{root}/results/{slug}', exist_ok=True)
    for x in os.listdir(f'{R}/data/raw'):
        if x != slug: os.symlink(f'{R}/data/raw/{x}', f'{root}/data/raw/{x}')
    shutil.copytree(f'{R}/data/raw/{slug}', f'{root}/data/raw/{slug}', symlinks=True)
    base = subprocess.run([PY, script], cwd=root, capture_output=True, text=True).stdout
    before = bool(re.search(pat, base))
    fn(f'{root}/data/raw/{slug}')
    after_out = subprocess.run([PY, script], cwd=root, capture_output=True, text=True)
    after = bool(re.search(pat, after_out.stdout))
    out[case] = {'script': script, 'pattern': pat, 'detected_before_mutation': before, 'detected_after_mutation': after, 'pass': (not before) and after, 'stderr_tail': after_out.stderr[-300:]}
    print(case, 'before', before, 'after', after, 'PASS' if out[case]['pass'] else 'FAIL')
os.makedirs('results/scope', exist_ok=True)
prev = json.load(open('results/scope/negctl_r08.json')) if os.path.exists('results/scope/negctl_r08.json') else {}
prev.update(out); json.dump(prev, open('results/scope/negctl_r08.json', 'w'), ensure_ascii=False, indent=1)
