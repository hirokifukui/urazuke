"""R028 の採点の反映（H033、2026-11-18）。"""
import os
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'apply_r22_25.py')).read()
ns = {}; exec(src.split('# ---- 支持（別系統で支持）')[0], ns)
setf, rep = ns['setf'], ns['rep']
setf('SH-A1', '確認', '別系統で支持（R028 Q1。R023 Q4 は判定不能、R027 Q8 は反証（訂正の数 5→9）→ 直した）')
rep('SH-A1', 'どの全体版 PDF にもない', 'どの全体版 PDF の文字として抽出できる部分にもない')
setf('HK-A9', '確認', '別系統で支持（R028 Q3。R015 Q1・R027 Q2 は判定不能、R023 Q1 は反証（令和5年版の数 7→10）→ そのつど直した。R016 Q2 は支持）')
open(ns['p'], 'w').write(ns['s']); print('ok')
