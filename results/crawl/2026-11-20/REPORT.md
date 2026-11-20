# 巡回の報告（2026-11-20、前回 2026-11-18）
**状態：正常**（手で前倒しした回。下の2行は呼び出しの不具合で、審議会の資料は確認できている：入口8、PDF 1636、新しいもの0。crawl/weekly_machine.py と councils.py を直した）

- HEAD を送った URL：8479。前回 200 で今回 200 以外：0。
- 取り直して比べた URL：2821。中身が変わった資料：7。取得に失敗：0。

## エラー
- crawl/councils.py が終了コード 1
- 検討会・審議会の資料の確認が AttributeError
- 検査をやり直した統計：koutsuu、kyoin_db、shibo_jirei

## 照合の数の変化
| 統計 | 前（照合・食い違い） | 後 |
|---|---|---|
| saihan | 3543・17 | 6969・19 |

## 中身が変わった資料
- https://www.cfa.go.jp/councils/shingikai/gyakutai_boushi/hogojirei/21-houkoku/（data/raw/shibo_jirei/pages/21.html）新しいリンク 1
- https://www.cfa.go.jp/councils/shingikai/gyakutai_boushi/hogojirei/19-houkoku/（data/raw/shibo_jirei/pages/19.html）新しいリンク 1
- https://www.cfa.go.jp/councils/shingikai/gyakutai_boushi/hogojirei/kekka（data/raw/shibo_jirei/pages/kekka.html）新しいリンク 1
- https://www.cfa.go.jp/councils/shingikai/gyakutai_boushi/hogojirei/22-houkoku/（data/raw/shibo_jirei/pages/22.html）新しいリンク 1
- https://www.cfa.go.jp/councils/shingikai/gyakutai_boushi/hogojirei/20-houkoku/（data/raw/shibo_jirei/pages/20.html）新しいリンク 1
- https://www.mext.go.jp/a_menu/shotou/kyoin/mext_00001.html（data/raw/kyoin_db/mext_00001.html）新しいリンク 1
- https://www.npa.go.jp/publications/statistics/koutsuu/toukeihyo.html（data/raw/koutsuu/index/toukeihyo.html）新しいリンク 1

## 入口のページの新しいリンク（前回からの新規。詳しくは WATCH.md）
  - 人口動態調査　https://www.e-stat.go.jp/stat-search/files?page=1&toukei=00450011

## 新しく現れたリンク（新しい版・新しいファイルの候補）
- https://www.cfa.go.jp/councils/shingikai/gyakutai_boushi/hogojirei/21-houkoku/：/assets/contents/css/css_2AQrxs6umwtf4MkBqfxeXBQvYA8Lpif5a-5oX0wKe0k.css?delta=0&language=ja&theme=gov_theme_cfa_2023&include=eJx1jF0KgCAMgC9kGHagMXXZYCa4YXj76K2Hev5-ShtgB1WCiEoQ1rD5Ii2iLGpT-CyufCiD6aL-QmnHvzhVhZqBMlvrHrtxEnI61aj6Z3kDtjMxcA
- https://www.cfa.go.jp/councils/shingikai/gyakutai_boushi/hogojirei/19-houkoku/：/assets/contents/css/css_2AQrxs6umwtf4MkBqfxeXBQvYA8Lpif5a-5oX0wKe0k.css?delta=0&language=ja&theme=gov_theme_cfa_2023&include=eJx1jF0KgCAMgC9kGHagMXXZYCa4YXj76K2Hev5-ShtgB1WCiEoQ1rD5Ii2iLGpT-CyufCiD6aL-QmnHvzhVhZqBMlvrHrtxEnI61aj6Z3kDtjMxcA
- https://www.cfa.go.jp/councils/shingikai/gyakutai_boushi/hogojirei/kekka：/assets/contents/css/css_2AQrxs6umwtf4MkBqfxeXBQvYA8Lpif5a-5oX0wKe0k.css?delta=0&language=ja&theme=gov_theme_cfa_2023&include=eJx1jF0KgCAMgC9kGHagMXXZYCa4YXj76K2Hev5-ShtgB1WCiEoQ1rD5Ii2iLGpT-CyufCiD6aL-QmnHvzhVhZqBMlvrHrtxEnI61aj6Z3kDtjMxcA
- https://www.cfa.go.jp/councils/shingikai/gyakutai_boushi/hogojirei/22-houkoku/：/assets/contents/css/css_2AQrxs6umwtf4MkBqfxeXBQvYA8Lpif5a-5oX0wKe0k.css?delta=0&language=ja&theme=gov_theme_cfa_2023&include=eJx1jF0KgCAMgC9kGHagMXXZYCa4YXj76K2Hev5-ShtgB1WCiEoQ1rD5Ii2iLGpT-CyufCiD6aL-QmnHvzhVhZqBMlvrHrtxEnI61aj6Z3kDtjMxcA
- https://www.cfa.go.jp/councils/shingikai/gyakutai_boushi/hogojirei/20-houkoku/：/assets/contents/css/css_2AQrxs6umwtf4MkBqfxeXBQvYA8Lpif5a-5oX0wKe0k.css?delta=0&language=ja&theme=gov_theme_cfa_2023&include=eJx1jF0KgCAMgC9kGHagMXXZYCa4YXj76K2Hev5-ShtgB1WCiEoQ1rD5Ii2iLGpT-CyufCiD6aL-QmnHvzhVhZqBMlvrHrtxEnI61aj6Z3kDtjMxcA
- https://www.mext.go.jp/a_menu/shotou/kyoin/mext_00001.html：https://warp.ndl.go.jp/web/latest/https://www.mext.go.jp/b_menu/houdou/mext_01036.html
- https://www.npa.go.jp/publications/statistics/koutsuu/toukeihyo.html：https://www.e-stat.go.jp/stat-search/files?page=1&layout=datalist&lid=000001495005
