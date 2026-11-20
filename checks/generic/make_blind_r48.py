"""R048（H040：記録の候補3件 SH-C1・ST-D1・SH-A2）の盲検フォルダを作る（2026-11-18）。
python3 checks/generic/make_blind_r48.py R048
白書の全体版 PDF は大きいので、該当頁の前後を qpdf で抜き出した写しを入れる（抜き出した頁は intro に書く）。"""
import importlib.util, os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sp = importlib.util.spec_from_file_location('m', os.path.join(HERE, 'make_blind_r22_25.py')); m = importlib.util.module_from_spec(sp)
sys_argv = sys.argv; sys.argv = ['x']; sp.loader.exec_module(m); sys.argv = sys_argv
RAW = m.RAW
EX = os.path.join(m.ROOT, 'data/derived/r048_extracts'); os.makedirs(EX, exist_ok=True)


def extract(src, pages, dst):
    out = os.path.join(EX, dst)
    if not os.path.exists(out):
        subprocess.run(['qpdf', '--empty', '--pages', src, pages, '--', out], check=False, stderr=subprocess.DEVNULL); assert os.path.exists(out)
    return out


S = os.path.join(RAW, 'saihan'); N = os.path.join(RAW, 'stalker/npa')
h30 = extract(os.path.join(S, 'H30/zentai_001283071.pdf'), '90-95', 'saihan_h30_p090-095.pdf')
r01 = extract(os.path.join(S, 'R01/zentai_001313763.pdf'), '92-97', 'saihan_r01_p092-097.pdf')
r05 = extract(os.path.join(S, 'R05/zentai_001407646.pdf'), '55-57', 'saihan_r05_p055-057.pdf')

m.ROUNDS = {'R048': dict(
  H='H040', title='記録の候補（SH-C1・ST-D1・SH-A2）',
  intro='''このフォルダには、法務省と警察庁の公表資料の写しがあります。
- saihan_h30_p090-095.pdf：再犯防止推進白書 平成30年版 全体版 PDF（法務省のファイル番号 001283071）の PDF 90〜95頁を抜き出したもの（抜き出した PDF の1頁目が元の90頁）。
- saihan_r01_p092-097.pdf：再犯防止推進白書 令和元年版 全体版 PDF（001313763）の PDF 92〜97頁を抜き出したもの（1頁目が元の92頁）。
- moj_sexoffender_2012.pdf：法務省矯正局「刑事施設における性犯罪者処遇プログラム受講者の再犯等に関する分析」研究報告書（平成24年12月、法務省矯正局成人矯正課、ファイル番号 000105286）。
- npa_r6.pdf：警察庁「令和６年におけるストーカー事案、配偶者からの暴力事案等、児童虐待事案等への対応状況について」（令和7年6月5日）。
- npa_r7.pdf：警察庁「令和７年におけるストーカー事案、配偶者からの暴力事案等、児童虐待事案等への対応状況について」（令和8年3月19日）。
- npa_r6_dv.csv・npa_r7_dv.csv：同じ公表の配偶者からの暴力事案等の CSV（Shift_JIS の場合がある）。
- saihan_r05_seigo.pdf：再犯防止推進白書 令和5年版（令和４年度再犯の防止等に関する施策）の正誤表（ファイル番号 001452655）。
- saihan_r05_p055-057.pdf：再犯防止推進白書 令和5年版 全体版 PDF（001407646）の PDF 55〜57頁を抜き出したもの（1頁目が元の55頁。印刷の頁番号は各頁の下にある）。
- saihan_r05_n2110000.html：令和5年版の Web 版（HTML）の該当節（https://www.moj.go.jp/hisho/saihanboushi/r05/html/n2110000.html、2026-11-18 取得）。''',
  files=[(h30, 'saihan_h30_p090-095.pdf'), (r01, 'saihan_r01_p092-097.pdf'),
         (os.path.join(RAW, 'moj_sexoffender/000105286.pdf'), 'moj_sexoffender_2012.pdf'),
         (os.path.join(N, 'R6_STDVRP_CA_kouhoushiryou.pdf'), 'npa_r6.pdf'), (os.path.join(N, 'R7_STDVRPCA_kouhou.pdf'), 'npa_r7.pdf'),
         (os.path.join(N, 'R6_DV.csv'), 'npa_r6_dv.csv'), (os.path.join(N, '02_R7_DV.csv'), 'npa_r7_dv.csv'),
         (os.path.join(S, 'R05/seigo_001452655.pdf'), 'saihan_r05_seigo.pdf'), (r05, 'saihan_r05_p055-057.pdf'),
         (os.path.join(S, 'html/R05/n2110000.html'), 'saihan_r05_n2110000.html')],
  qs=[('SH-C1', '再犯防止推進白書 平成30年版と令和元年版は、どちらも印刷の頁番号80頁（平成30年版は元の PDF 93頁で抜き出した PDF の4頁目、令和元年版は元の PDF 95頁で抜き出した PDF の4頁目）では、刑事施設の性犯罪再犯防止指導について、2012年度（平成24年度）の効果検証で受講群の再犯率が非受講群より 7.7ポイント低いことが示され「一定の再犯抑止効果が認められている」と書く。2012年の分析（moj_sexoffender_2012.pdf）では、7.7ポイントは「全ての犯罪」の出所3年後の推定再犯率（受講群 21.9％、非受講群 29.6％、表5）の差である。同じ表5で性犯罪の再犯（12.8％、15.4％）の差は有意でなく、RAT を投入した性犯罪再犯の分析でも「効果を確認するまでには至らなかった」と書かれている。同じ分析は、結果の精度に「一定の限界がある」と書く。白書の当該の段落は、7.7ポイントが全ての犯罪の再犯であること、性犯罪の再犯では効果が確認されなかったこと、精度の限界のいずれも書いていない。'),
      ('CTRL', '2012年の分析（moj_sexoffender_2012.pdf）の表5で、性犯罪の出所3年後の推定再犯率は、受講群 10.9％、非受講群 15.4％で、1％水準で有意である。'),
      ('ST-D1', '警察庁の令和6年の対応状況（npa_r6.pdf 5頁）は配偶者からの暴力事案等の相談等件数を 94,937件、令和7年（npa_r7.pdf 7頁）は 98,289件とし、どちらも「ＤＶ防止法施行後最多」と書く。同じ頁の注3は、令和6年4月1日施行以降、自由、名誉又は財産に対する脅迫についても計上すると書く（平成16・20・26年の範囲の拡大も同じ注にある）。二つの資料（PDF と CSV）は、令和6年4月以降に新たに計上した脅迫の相談等の件数を示していない。令和6・7年の件数は、令和5年以前と計上の範囲が違い、範囲を揃えた比較は資料からはできない。'),
      ('SH-A2', '再犯防止推進白書 令和5年版の正誤表（saihan_r05_seigo.pdf）は、38頁 第２章 第１節 １（２）【施策番号 2】脚注※３の「刑事施設 75 庁（前年：76 庁）」を「刑事施設 75 庁（前年：75 庁）」に訂正する。令和5年版の全体版 PDF の38頁（抜き出した PDF の2頁目、元の PDF 56頁）の※３と、Web 版（saihan_r05_n2110000.html）の同じ脚注は、どちらも「前年：76庁」のままである。'),
      ('CTRL', '再犯防止推進白書 令和5年版の全体版 PDF の38頁（元の PDF 56頁）の※４で、就労支援専門官は 2023年（令和5年）4月現在、刑事施設 32庁（前年：28庁）に配置されている。')])}

if __name__ == '__main__':
    for r in sys.argv[1:]:
        m.build(r)
