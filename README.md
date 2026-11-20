# URAZUKE（裏付け）

日本の犯罪・司法・精神医療・福祉に関する公開データを、再現可能な方法で検証し、継続的に記録する。
サイトの主役は「不正や誤りの発見」でなくてよい。

- GitHub：再現する人のための場所（コード、取得した元データの URL・SHA256・取得日時、判定の記録）。元データのファイルは再配布しない（publish/source_manifests/ の MANIFEST から取得し、SHA256 で同じものか確かめる）
- サイト（urazuke.org）：結果を使う人のための場所。各結果は公開リポジトリ（版ごとに1つのコミット。コミットの文と CITATION.cff に作業用の版と日付を書く）のスクリプトで確かめられる

## 構成
- `sources/<資料名>/fetch.py`  取得スクリプト（資料ごと）。`sources/estat/list_tables.py` は e-Stat の表一覧の取得
- `data/raw/<資料名>/<版>/`     取得した元データと MANIFEST.tsv（URL・SHA256・HTTP 状態・取得時刻）
- `lib/xlsx.py`                 標準ライブラリだけの .xlsx 読み取り器（外部依存なし）
- `checks/<資料名>/cNNN_*.py`   検算スクリプト（1 本 1 テーマ）
- `results/<資料名>/cNNN_*.tsv` 検算結果（1 行 1 検算: 種類・内容・年・期待値・観測値・差・判定）
- `logs/`                       実行ログ、陰性対照の結果
- `checks/RUN.tsv`              引数を取る検査の実行の記録（コマンドと出力先）。引数なしで動く検査は `python checks/<資料名>/cNNN_*.py` で回る
- `requirements.txt`             検査に使う Python パッケージ（Python 3.14）と外部コマンド（pdftotext）
- `TERMS.md`・`LICENSE`          利用規約とプライバシー、コードのライセンス（MIT。記録とデータは CC BY 4.0）

## 取得済み
- 犯罪白書 令和7年版（hakusyo1.moj.go.jp/jp/72/nfm/）：資料編 Excel 38、図表データ Excel 308、本文 HTML 172。
  図表目次にある 316 図表のうち 8 図表は Excel が公開されておらず画像のみ（404。results/hanzai_hakusho/FINDINGS.md）。

## 検算
- c001 刑法犯（資料1-1 ↔ 1-1-1-1図 ↔ 本文、昭和21年〜令和6年の 79 年分）：2,303 件すべて一致（2026-11-16）。
  A 資料1-1 内部整合 711／B 1-1-1-1図 内部整合 869／C 両資料の突き合わせ 474／D 総数＝刑法犯＋危険運転等 237／E 本文の数値 12。
  陰性対照：令和6年の認知件数を 1 件だけ増やすと 6 件の食い違いとして検出される（logs/c001_negative_control.tsv）。
- c002 再犯・再入（第5編：5-1-1、5-3-1・2、5-3-6〜10、資料5-1、本文・図中の数値）：3,286 件。
  数値はすべて一致。5-3-9図の Excel 見出しに分母の誤記（J/D と書かれているが値は J/E）を 1 件確認（FINDINGS.md）。
  陰性対照：令和6年の再犯者人員を 1 人だけ増やすと食い違いとして検出される（logs/c002_negative_control.tsv）。
- c003 一次資料との突き合わせ（探索。矯正統計年報 24-00-23・検察統計年報 24-00-49 ↔ 5-3-1・5-3-2・資料5-1・資料5-2・5-2-1表）：1,320 件すべて一致。
  罪名の対応表と、白書が除外している人（前科不詳など）の確認を含む（FINDINGS.md）。
- c004 版をまたいだ比較（探索）：刑法犯の平成14〜26年の値が令和4年版から遡って改訂されている（危険運転致死傷の扱いの変更。FINDINGS.md）。
  取得は `sources/hanzai_hakusho/find_by_title.py`（版ごとに番号・ファイル名が違うので表題で探す）。
- c005 警察庁の犯罪統計との突き合わせ（探索）：令和6年の刑法犯総数・窃盗犯は一致。平成29年分の警察庁の訂正（平成31年3月）は、令和元年版以降の白書に反映されている（FINDINGS.md）。
- 2026-11-16：名称を Mitodoke から URAZUKE（urazuke.org）に変更。作業フォルダ名（Scripts/Mitodoke）と、実行済みの再現・反証の記録（replications/R001〜R003）は、記録の同一性を保つため旧名のまま残す。
- 2026-11-16：犯罪白書・自殺統計・630調査を10年分に拡張。旧様式の Excel 用に lib/yearseries.py（和暦の行ラベル → 西暦）と checks/hanzai_hakusho/c009v（値で列を対応させる版間比較）、.xls 用に lib/xls.py（xlrd、~/.venvs/urazuke）を追加。

## 次の5統計（2026-11-16 着手）
作業端末はブリッジ上の名前「hirokinomini」、実体の hostname は `hermes`（Mac mini）。

| 統計 | 範囲 | 取得 | 検査 | 記録 |
|---|---|---|---|---|
| 犯罪統計資料・犯罪統計書・警察白書（警察庁） | 平成27〜令和7年、白書 平成28〜令和8年版 | data/raw/keisatsu（1,075＋Wayback 3） | c401〜c405、cross/c406 | results/keisatsu/FINDINGS.md |
| ストーカー・DV 等の対応状況（警察庁） | 平成26〜令和7年（平成28年は見つからず） | data/raw/stalker | c411 | results/stalker/FINDINGS.md |
| 児童虐待相談対応件数（福祉行政報告例） | 平成26〜令和6年度＋速報値 | data/raw/gyakutai | c700〜c702 | results/gyakutai/FINDINGS.md |
| 教職員の懲戒処分（人事行政状況調査） | 平成27〜令和6年度 | data/raw/monka | c601 | results/monka/FINDINGS.md |
| 再犯防止推進白書（法務省） | 平成30〜令和7年版 | data/raw/saihan | c501 | results/saihan/FINDINGS.md |

道具（追加分）
- `sources/generic/links.py`：ページのリンク（`<a>` と画像マップの `<area>`）を TSV に。URL 探索用、取得はしない。
- `sources/generic/estat_search.py`：e-Stat のファイル検索結果を statInfId・形式・表題の TSV に。
- `sources/generic/run_queue.sh`：取得の順番待ち（queue.tsv の一覧を1本ずつ fetch_list.py にかける。30分空けば終わる）。`pgrep -f run_queue.sh` で確かめる。
- `fetch_list.py` の変更：429 のときは 30・90・180 秒待って取り直す。Wayback のときは curl の UA（Python の UA だと 429）。接続失敗も記録して続ける。間隔は環境変数 FETCH_SLEEP。
- `lib/npa_csv.py`：犯罪統計資料 CSV の表の読み取り（表の標識が2列目の表、1つの標識の下に複数の表、3段の見出しに対応）。
- `lib/fukushi_csv.py`：福祉行政報告例 CSV の読み取り（単位行の有無、再掲列、全角空白）。
- `checks/keisatsu/c404_lastmod_outliers.py`：MANIFEST の Last-Modified の外れ値（差し替えの手がかり）。ほかの統計の MANIFEST にも使える。

注意（execute_command）：/bin/sh なので `echo -e` は「-e」を書き込む（printf を使う）。`<(...)` は使えない。

### 追記（2026-11-16 夜）
- 道具：checks/generic/pdf_token_diff.py（PDF 2版の語単位の差分）、checks/monka/c603・c604、checks/gyakutai/c703、checks/saihan/c502〜c504、checks/stalker/c412。
- 新しい取得：data/raw/moj_seigo/（法務省 統計の正誤情報 矯正・保護 48本）、data/raw/hogo_toukei/hogo38/（保護統計 表38）、data/raw/kyosei_toukei/kijuu/（矯正統計 表84）、文科の差し替え前の版（data/raw/monka/wayback/）、平成26年度 2-1。
- 結果の要点：文科 平成27年度2-1の参考行で平成26年度総計 9,677→8,445（平成26年度版は 9,677 のまま）／再犯防止白書の版間の変化は矯正・保護統計の正誤情報で説明がつく（2件とも要照会から外す）／ストーカー 2022年 動機の小計 762（内訳と総数は 768）／児童虐待 経路「警察等」と警察庁の通告児童数の比 0.95〜1.04。
- Wayback は http（80番）が拒否される時間帯があり、https で通った。一時的に「Temporarily Offline」も返る。
