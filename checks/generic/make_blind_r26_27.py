"""R026（R022 の対照を直したやり直し）と R027（R023〜R025 で書き直した記録）の盲検フォルダを作る（2026-11-18）。
資料は R022〜R025 の盲検フォルダの写し（APFS の clone。報告・PROMPT・作業ファイルは除く）。主張は publish/findings.json の要旨。"""
import importlib.util, os, sys, json, shutil, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sp = importlib.util.spec_from_file_location('m', os.path.join(HERE, 'make_blind_r22_25.py')); m = importlib.util.module_from_spec(sp)
sys_argv = sys.argv; sys.argv = ['x']; sp.loader.exec_module(m); sys.argv = sys_argv
BL = m.BL; Y = m.Y


def keep(src):
    """盲検フォルダから資料だけを選ぶ（報告・PROMPT・回答側が作ったファイルを除く）。"""
    fixed = os.path.join(m.ROOT, 'replications', os.path.basename(src) + '_gpt_refute', 'FIXED_SHA256.txt')
    return [l.split('  ', 1)[1].strip() for l in open(fixed) if l.strip() and not l.split('  ', 1)[1].startswith('PROMPT.md')]


R22, R23, R24, R25 = (os.path.join(BL, r) for r in ('R022', 'R023', 'R024', 'R025'))
m.ROUNDS = {
 'R026': dict(
   H='H031', title='犯罪白書の図表 Excel（R022 のやり直し：HK-A1・A2・A3・A5・A10）',
   intro=m.ROUNDS['R022']['intro'],
   files=[(os.path.join(R22, x), x) for x in keep(R22)],
   qs=[('HK-A1', Y('HK-A1')),
       ('CTRL', '令和5年版 5-4-4表 の閲覧用シート（「5-4-4表※閲覧用」）の③（保護観察付全部執行猶予者）で、1989年（平成元年、57行目）の「計（B）」（セル AL57）は 1,168 である。'),
       ('HK-A5', Y('HK-A5')),
       ('HK-A2', Y('HK-A2')),
       ('HK-A10', Y('HK-A10')),
       ('CTRL', '令和7年版 4-8-2-2図 の Excel（シート「4-8-2-2図①」）で、2004年（平成16年、22行目）の総数（セル D22）は 32,190 である。'),
       ('HK-A3', Y('HK-A3'))]),
 'R027': dict(
   H='H032', title='書き直した記録の再反証（HK-A9・NK-K1・SH-A1・KP-C1・630-M1・GY-Q1）',
   intro=m.ROUNDS['R023']['intro'] + '\n' + '\n'.join(l for l in m.ROUNDS['R024']['intro'].split('\n') if l.startswith('- kyosei_')) + '\n'
         + '\n'.join(l for l in m.ROUNDS['R025']['intro'].split('\n') if l.startswith('- seishin630') or l.startswith('- gyakutai')),
   files=[(os.path.join(R23, x), x) for x in keep(R23)]
         + [(os.path.join(R24, x), x) for x in ('kyosei_R02_report.pdf', 'kyosei_H24_report.pdf')]
         + [(os.path.join(R25, x), x) for x in keep(R25) if x.startswith('seishin630/') or x.startswith('gyakutai/')],
   qs=[('630-M1', Y('630-M1')),
       ('HK-A9', Y('HK-A9')),
       ('CTRL', '矯正局の令和2年3月の報告（kyosei_R02_report.pdf）の表1で、受講群は 1,444名、比較対照群は 342名である。'),
       ('KP-C1', Y('KP-C1')),
       ('NK-K1', Y('NK-K1')),
       ('GY-Q1', Y('GY-Q1')),
       ('CTRL', '630調査の長期データ（seishin630/longterm_1998_2025.xlsx）の「在院患者数」シートで、2018年の全国合計は 280,851人である。'),
       ('SH-A1', Y('SH-A1'))]),
}

# ---- R028（R027 で書き直した HK-A9・SH-A1）。python3 checks/generic/make_blind_r26_27.py R028
R27 = os.path.join(BL, 'R027')
m.ROUNDS['R028'] = dict(
   H='H033', title='書き直した記録の再反証（HK-A9・SH-A1）',
   intro=m.ROUNDS['R027']['intro'].split('\n- kyosei_R02_report')[0],
   files=[(os.path.join(R27, x), x) for x in keep(R27) if not (x.startswith('seishin630/') or x.startswith('gyakutai/') or x.startswith('kyosei_'))],
   qs=[('SH-A1', Y('SH-A1')),
       ('CTRL', '令和6年版犯罪白書の訂正のお知らせ（hanzai_r06_teisei.html）で、88頁7行の訂正は「40人」を「38人」に直すものである。'),
       ('HK-A9', Y('HK-A9')),
       ('CTRL', '再犯防止推進白書の正誤表（saihan_seigo.pdf）で、18頁の指標12の平成30年の出院者数の訂正後の値は 2,190人である。')])
if __name__ == '__main__':
    for r in sys.argv[1:]:
        m.build(r)
