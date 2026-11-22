# 巡回の報告（2026-11-22、前回 2026-11-20）
**状態：変化あり**

- HEAD を送った URL：8557。前回 200 で今回 200 以外：2。
- 取り直して比べた URL：2836。中身が変わった資料：0。取得に失敗：0。

## 200 以外を返した URL
- https://www.jbaudit.go.jp/report/new/summary07/pdf/fy07_01_gaiyou.pdf（404）
- https://www.jbaudit.go.jp/report/new/summary07/pdf/fy07_03_futo.pdf（404）

## 入口のページの新しいリンク（1回目の実行で拾ったもの）
1回目の実行（13:02）は watch.py が Dropbox の「Resource deadlock avoided」で止まった。そのときに既に見たリンクとして記録されたため、2回目の実行では新規として出ない。記録は logs/crawl/failed_2026-11-22_1302/。
  - 会議資料 npa｜警察庁 ストーカー総合対策・有識者検討会（一覧の中の会議のページ）｜議事次第｜https://www.npa.go.jp/bureau/safetylife/stalker/3gijishidai.pdf
  - 会議資料 npa｜警察庁 ストーカー総合対策・有識者検討会（一覧の中の会議のページ）｜資料１｜https://www.npa.go.jp/bureau/safetylife/stalker/3shiryou1.pdf
  - 会議資料 cfa｜こどもの自殺対策に関する関係省庁連絡会議｜議事次第（PDF／181KB）｜https://www.cfa.go.jp/assets/contents/node/basic_page/field_ref_resources/f2569aa2-dd99-4e14-931b-8e7529037c0c/1d6a0251/20261120_councils_kodomonojisatsutaisaku-kaigi_f2569aa2_00.pdf
  - 会議資料 cfa｜こどもの自殺対策に関する関係省庁連絡会議｜出席者名簿（PDF／198KB）｜https://www.cfa.go.jp/assets/contents/node/basic_page/field_ref_resources/f2569aa2-dd99-4e14-931b-8e7529037c0c/486165ed/20261120_councils_kodomonojisatsutaisaku-kaigi_f2569aa2_09.pdf
  - 会議資料 cfa｜こどもの自殺対策に関する関係省庁連絡会議｜資料1 こどもの自殺対策緊急強化プランの取組状況及びロードマップ（PDF／582KB）｜https://www.cfa.go.jp/assets/contents/node/basic_page/field_ref_resources/f2569aa2-dd99-4e14-931b-8e7529037c0c/5d197d00/20261120_councils_kodomonojisatsutaisaku-kaigi_f2569aa2_07.pdf
  - 会議資料 cfa｜こどもの自殺対策に関する関係省庁連絡会議｜資料2 こども家庭庁における自殺対策の取組について（PDF／4MB）｜https://www.cfa.go.jp/assets/contents/node/basic_page/field_ref_resources/f2569aa2-dd99-4e14-931b-8e7529037c0c/47ff5642/20261120_councils_kodomonojisatsutaisaku-kaigi_f2569aa2_03.pdf
  - 会議資料 cfa｜こどもの自殺対策に関する関係省庁連絡会議｜資料3 内閣府孤独・孤立対策推進室提出資料（PDF／2MB）｜https://www.cfa.go.jp/assets/contents/node/basic_page/field_ref_resources/f2569aa2-dd99-4e14-931b-8e7529037c0c/b05cba10/20261120_councils_kodomonojisatsutaisaku-kaigi_f2569aa2_04.pdf
  - 会議資料 cfa｜こどもの自殺対策に関する関係省庁連絡会議｜資料4 文部科学省提出資料（PDF／938KB）｜https://www.cfa.go.jp/assets/contents/node/basic_page/field_ref_resources/f2569aa2-dd99-4e14-931b-8e7529037c0c/74249e43/20261120_councils_kodomonojisatsutaisaku-kaigi_f2569aa2_08.pdf
  - 会議資料 cfa｜こどもの自殺対策に関する関係省庁連絡会議｜資料5 厚生労働省提出資料（PDF／3.7MB）｜https://www.cfa.go.jp/assets/contents/node/basic_page/field_ref_resources/f2569aa2-dd99-4e14-931b-8e7529037c0c/494da170/20261120_councils_kodomonojisatsutaisaku-kaigi_f2569aa2_06.pdf
