"""陰性対照（r09 で足した統計の検査）：原データの写しの1か所を変え、検査がそれを検出することを確かめる。
作業用の根（/tmp/urazuke_negctl/<case>/）に lib・checks を symlink し、data/raw は対象の統計だけ写しを置く（他は symlink）。
results は作業用の根の中に書かれ、本体の results は変わらない。
使い方: ~/.venvs/urazuke/bin/python checks/generic/negctl_r09.py [case ...]"""
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
def mut_cell(path, old, new, sheet=None, idx=0):
    """xlsx の中で値が old（数値か文字列）のセルを new にする（idx 番目）。"""
    wb = openpyxl.load_workbook(path, data_only=True)  # 式のセルは値に置き換えて保存する（式のまま保存すると計算済みの値が消える）
    wss = [wb[sheet]] if sheet else wb.worksheets; k = 0
    for ws in wss:
        for row in ws.iter_rows():
            for c in row:
                if c.value is not None and str(c.value).strip() == str(old):
                    if k == idx:
                        c.value = type(c.value)(new) if not isinstance(c.value, str) else str(new); wb.save(path); return
                    k += 1
    raise ValueError(old)
def mut_xls(path, row_label, col, delta):
    """xls（xlrd で読み、xlutils で書く）：A列の見出しが row_label の最初の行の col 列に delta を足す。"""
    import xlrd, xlutils.copy
    bk = xlrd.open_workbook(path, formatting_info=True); sh = bk.sheet_by_index(0)
    i = next(i for i in range(sh.nrows) if str(sh.cell_value(i, 0)).replace(' ', '') == row_label)
    wb = xlutils.copy.copy(bk); wb.get_sheet(0).write(i, col, sh.cell_value(i, col) + delta); wb.save(path)
CASES = {
 # 建設工事受注：受注高時系列 R6年度 受注高合計の計（1列目の数値）を 100 増やす → 計=土木+建築+機械 などが崩れる
 'kensetsu_fy': ('kensetsu_juchu', lambda d: mut_xls(f'{d}/nendo/R06_jikeiretsu.xls', 'R6年度', 1, 100), 'checks/kensetsu_juchu/c3101_nendo.py', r'不一致 [1-9]'),
 # 矯正：令和7年 第17表 総数 満期釈放 5557（正）を 5556（誤）に戻す → 未反映を検出
 'kyosei_seigo': ('kyosei', lambda d: mut_cell(f'{d}/2025/25-00-17.xlsx', '5557', '5556'), 'checks/kyosei/c2701_seigo_applied.py', r'NOT_APPLIED 2025'),
 # 保護：令和5年 第59表 総数 前年からの繰越し 1045（正）を 1053（誤）に → 未反映
 'hogo_seigo': ('hogo', lambda d: mut_cell(f'{d}/2023/kansatsu/23-00-59.xlsx', '1045', '1053'), 'checks/hogo/c2702_seigo_applied.py', r'TABLE 2025-11-28 2023 kansatsu 59'),
 # 検察：第2表 令和7年 受理総数 939782 を1増やす → 受理総数=旧受+新受 が崩れる
 'kensatsu_t2': ('kensatsu', lambda d: mut_cell(f'{d}/2025/25-00-02.xlsx', '939782', '939783'), 'checks/kensatsu/c2901_flow.py', r'不一致 11[6-9]'),
 # 人口推計：2024年 第2表 北海道 男女計 5043 → 5045
 'suikei_t2': ('jinko_suikei', lambda d: mut_cell(f'{d}/2024np/05k2024-2.xlsx', '5043', '5045'), 'checks/jinko_suikei/c2801_suikei.py', r'2024 第2表 北海道'),
 # 医療観察（厚労省）：入院対象者 ステージ別 合計 749名 → 750名
 'mhoa_nyuin': ('iryokansatsu', lambda d: mut_text(f'{d}/mhlw/nyuin.html', '749名', '750名'), 'checks/iryokansatsu/c3001_mhlw.py', r'男\+女=合計'),
 # 医療観察（保護統計）：令和7年版 精神保健観察 令和3年 繰越 576 → 577
 'mhoa_hogo': ('iryokansatsu', lambda d: mut_cell(f'{d}/hogo/2025/25-00-75.xlsx', '576', '577'), 'checks/iryokansatsu/c3002_hogo_mhoa.py', r'不一致 [1-9]'),
 # 賃金構造：令和7年版 第1表 2025年 男女計 340.6 → 341.6
 'chinkin_t1': ('chinkin', lambda d: mut_cell(f'{d}/2025/zuhyo.xlsx', '340.6', '341.6', sheet='第１表'), 'checks/chinkin/c3201_tab1.py', r'不一致 [1-9]'),
 # 国民経済計算：2024年度 GDP（支出側）の値を 1 増やす → GDP=1+2+3+4
 'sna_gdp': ('sna', lambda d: mut_cell(f'{d}/2024/2024ffm1n_jp.xlsx', '522040.3', '522041.3'), 'checks/sna/c3701_ffm1n.py', r'GDP=1\+2\+3\+4'),
 # 決算カード：令和6年度 沖縄県 実質収支 4096140 → 4096145
 'card_okinawa': ('kessan_card', lambda d: mut_cell(f'{d}/pref/R06_pref_card.xlsx', '4096140', '4096145', sheet='48沖縄県'), 'checks/kessan_card/c3801_pref.py', r'R06 沖縄県 当年度 実質収支'),
}
FN = {}
# PDF を読む検査：pdftotext の出力を置き換える包み（checks/generic/bin/pdftotext_negctl.sh）を PATH の先頭に置く
PDFCASES = {
 'seiho_m': ('checks/seiho/c3301_monthly.py', 'm2026_08.pdf', '1,965,132       1,985,720', '1,965,133       1,985,720', r'不一致 [1-9]'),
 'karoshi_t': ('checks/karoshi/c3401_tables.py', 'b1_noushinzou.pdf', '257 ( 9 )', '258 ( 9 )', r'不一致 [1-9]'),
 'koutsuu_r': ('checks/koutsuu/c3501_nenkan.py', 'R07nenkan.pdf', '55.9%', '56.9%', r'不一致 [1-9]'),
 'monka_h1': ('checks/monka_kihon/c3601_hyo1.py', 'R08_sokuho.pdf', '5,654,461', '5,654,462', r'不一致 [1-9]'),
 'monka_tb': ('checks/monka_kihon/c3602_taibatsu.py', '000046407_33.pdf', '    合 計      393', '    合 計      394', r'不一致 [1-9]'),
}
out = {}
import shutil as _sh
_bin = '/tmp/urazuke_negctl_bin'; os.makedirs(_bin, exist_ok=True); _sh.copy(f'{R}/checks/generic/bin/pdftotext_negctl.sh', f'{_bin}/pdftotext'); os.chmod(f'{_bin}/pdftotext', 0o755)
for case in [c for c in (sys.argv[1:] or list(PDFCASES)) if c in PDFCASES]:
    script, fpat, old, new, pat = PDFCASES[case]
    root = f'/tmp/urazuke_negctl/{case}'; shutil.rmtree(root, ignore_errors=True); os.makedirs(f'{root}/data'); os.makedirs(f'{root}/results')
    for x in ('lib', 'checks'): os.symlink(f'{R}/{x}', f'{root}/{x}')
    os.symlink(f'{R}/data/raw', f'{root}/data/raw')
    for x in os.listdir(f'{R}/results'): os.makedirs(f'{root}/results/{x}', exist_ok=True)
    env0 = dict(os.environ, PATH=f"{_bin}:{os.environ['PATH']}", NEGCTL_FILE='__none__', NEGCTL_OLD='x', NEGCTL_NEW='x')
    base = subprocess.run([PY, script], cwd=root, capture_output=True, text=True, env=env0).stdout
    env1 = dict(env0, NEGCTL_FILE=fpat, NEGCTL_OLD=old, NEGCTL_NEW=new)
    aft = subprocess.run([PY, script], cwd=root, capture_output=True, text=True, env=env1)
    before = bool(re.search(pat, base)); after = bool(re.search(pat, aft.stdout))
    out[case] = {'script': script, 'pattern': pat, 'mutation': f'{fpat}: {old} → {new}（pdftotext の出力で置き換え）', 'detected_before_mutation': before, 'detected_after_mutation': after, 'pass': (not before) and after, 'stderr_tail': aft.stderr[-300:]}
    print(case, 'before', before, 'after', after, 'PASS' if out[case]['pass'] else 'FAIL')
for case in [c for c in (sys.argv[1:] or CASES) if c in CASES]:
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
prev = json.load(open('results/scope/negctl_r09.json')) if os.path.exists('results/scope/negctl_r09.json') else {}
prev.update(out); json.dump(prev, open('results/scope/negctl_r09.json', 'w'), ensure_ascii=False, indent=1)
