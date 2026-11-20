"""R065（H041：記録の候補2件 SK-A1・ST-C1）の盲検フォルダを作る（2026-11-20、週1回の巡回・LLM の段）。
python3 checks/generic/make_blind_r65.py R065
職業訓練の論文（矯正研究 第8号）は画像の PDF で文字が埋め込まれていないため、表の頁を 150dpi の PNG にした写しも入れる。"""
import importlib.util, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sp = importlib.util.spec_from_file_location('m', os.path.join(HERE, 'make_blind_r22_25.py')); m = importlib.util.module_from_spec(sp)
sys_argv = sys.argv; sys.argv = ['x']; sp.loader.exec_module(m); sys.argv = sys_argv
RAW = m.RAW
PG = os.path.join(m.ROOT, 'data/derived/r065_pages')
K = os.path.join(RAW, 'stalker/npa_kentokai')
m.ROUNDS = {'R065': dict(
  H='H041', title='記録の候補（SK-A1・ST-C1）',
  intro='''このフォルダには、法務省と警察庁の公表資料の写しがあります。
- shokugyo_2025.pdf：中村・佐々木「受刑者に対する職業訓練が就労に与える影響についての検証―性差を踏まえた傾向スコアマッチングによる検討―」（矯正研究 第8号 38〜60頁、令和7年6月。法務省のファイル番号 001459810）。画像の PDF で、文字は埋め込まれていない。
- shokugyo_pages/pg-06.png〜pg-11.png：同じ PDF の 6〜11頁（印刷の43〜48頁。表1〜表12）を 150dpi の画像にしたもの。
- kentokai1_shiryou1.pdf・kentokai1_shiryou3.pdf・kentokai1_gaiyou.pdf：警察庁「ストーカー行為等の規制等の在り方に関する有識者検討会」第1回の資料1、資料3（資料3-1〜3-6）、議事概要。''',
  files=[(os.path.join(RAW, 'moj_kyosei_kensho/001459810.pdf'), 'shokugyo_2025.pdf'), (PG, 'shokugyo_pages'),
         (os.path.join(K, '1shiryou1.pdf'), 'kentokai1_shiryou1.pdf'), (os.path.join(K, '1shiryou3.pdf'), 'kentokai1_shiryou3.pdf'),
         (os.path.join(K, '1gaiyou.pdf'), 'kentokai1_gaiyou.pdf')],
  qs=[('ST-C1', '有識者検討会 第1回の資料3-3（kentokai1_shiryou3.pdf）は、「令和４年７月から令和７年６月までの３年間に禁止命令等を受けた者6,548人のうち、497人（約7.6％）はその後再発」とし、続けて「大多数は禁止命令等によりその後ストーカー行為等を行うことはないものの、１割弱の者については禁止命令等のみでは十分な再発防止効果を得られていない」と書く。同じ頁の注は、再発を「対象者が、禁止命令等期間中に、同一被害者に対し、再度、つきまとい行為によりストーカー規制法の罪に当たる行為をした割合」とする。注の範囲は、禁止命令等の期間中・同一の被害者・ストーカー規制法の罪に当たる行為に限られ、期間の後の行為、別の相手への行為、同法の罪に当たらないつきまとい行為は含まれない。「その後ストーカー行為等を行うことはない」は注の範囲より広い。渡した資料（資料1・資料3・議事概要）には、禁止命令等を受けなかった者との比較は示されていない。'),
      ('CTRL', '有識者検討会 第1回の資料3-3（kentokai1_shiryou3.pdf）は、禁止命令等を受けた者のうち、警察による受診等勧奨を受けて令和７年中に治療・カウンセリングにつながった者を 174人（令和７年中に禁止命令等を受けた者は 3,037人）とする。'),
      ('SK-A1', '職業訓練の論文（shokugyo_2025.pdf）の表6（男性受刑者）で、職業訓練の希望あり群の「犯罪傾向の進度」は A 702人（32.1％）・B 1,484人（67.9％）で、和は 2,186人である。同じ論文の表1 の男性の希望あり群は 1,937人で、表5 の出所時年齢・懲罰回数の希望あり群の人数も 1,937人である。表6 の同じ行の χ²値 48.046 は、2×2表を A 702・B 1,235（＝1,937－702）／希望なし A 1,484・B 3,852 として連続修正なしで計算すると再現し（48.05）、B を 1,484 とすると 13.92 になる。表10（男性。希望あり群を職業訓練の実施の有無に分けた表）の犯罪傾向の進度は、実施あり A 149・B 161、実施なし A 553・B 1,074 で、A の和は 702、B の和は 1,235 である。表6 の希望あり群の B の 1,484 は、同じ表の希望なし群の A の値と同じである。'),
      ('CTRL', '職業訓練の論文（shokugyo_2025.pdf）の表10（男性受刑者）で、職業訓練の実施あり群のうち犯罪傾向の進度が A の者は 161人（51.9％）である。')])}

if __name__ == '__main__':
    for r in sys.argv[1:]:
        m.build(r)
