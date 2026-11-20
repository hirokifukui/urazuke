#!/usr/bin/env python3
"""保護局 2020（001318218）・2012（001322889）・概要（001466396）の再計算。"""
import math
from scipy.stats import chi2, norm

def pearson(p1,n1,p2,n2):
    a=round(p1*n1); c=round(p2*n2); b=n1-a; d=n2-c; N=n1+n2
    e=[(a+c)*n1/N,(b+d)*n1/N,(a+c)*n2/N,(b+d)*n2/N]
    x=sum((o-ee)**2/ee for o,ee in zip([a,b,c,d],e))
    return a,c,x,chi2.sf(x,1)

print("== 2020 表1〜3 合計")
t1={'仮釈放':(582,251,833),'執行猶予':(319,46,365),'全体':(901,297,1198)}
for k,(a,b,t) in t1.items(): print(k, a+b==t)
t2=[(177,30,207),(39,7,46),(327,106,433),(100,21,121),(13,3,16),(245,130,375)]
print('表2 行', all(a+b==t for a,b,t in t2), '列', sum(r[0] for r in t2), sum(r[1] for r in t2), sum(r[2] for r in t2))
t3=[(5,0,226,20,251),(7,0,0,39,46),(12,0,226,59,297)]
print('表3 行', [sum(r[:4])==r[4] for r in t3], '列', [t3[0][i]+t3[1][i]==t3[2][i] for i in range(5)])
print('受講率 2014', 901/1198, '（目的の 76.6% は 2014–2018）')
print('執行猶予の割合 受講群', 319/901, '非受講群', 46/297)
print('非受講群のうち 保護観察期間3月未満', 226/297)

print("== 2020 表4")
a,c,x,p=pearson(.151,901,.262,297)
print(f'概算件数 受講{a} 非受講{c}  Pearson χ²={x:.2f} p={p:.2g}  （報告 log-rank 17.11, p=.00004）')
print('報告χ²17.11 の p =', chi2.sf(17.11,1))
print('粗リスク比', .151/.262, ' 差', .262-.151)

print("== 2020 表5")
for nm,hr,lo,hi,prep in [('受講なし',1.485,1.101,2.004,'.009'),('RAT',1.442,1.346,1.545,'.001')]:
    b=math.log(hr); se=(math.log(hi)-math.log(lo))/(2*1.959964); mid=math.exp((math.log(hi)+math.log(lo))/2)
    z=b/se; print(f'{nm}: CI中点 {mid:.3f}（報告 {hr}） SE {se:.4f} z {z:.2f} p {2*norm.sf(abs(z)):.2g}（報告 {prep}）')
print('概要の「0.67倍」 = 1/1.485 =', 1/1.485, '（ハザード比の逆数。再犯率の比ではない。表4の粗比は', round(.151/.262,3),'）')

print("== 2012")
print('仮釈放', 2528+285, '執行猶予', 1310+125, '全体', 3838+410)
print('表3 罪種別人数の合計', 1264+1531+1390, '→ 全体との差', 4248-(1264+1531+1390))
for nm,n1,n2,p1,p2,xr,pr in [('全再犯 仮釈放',2528,285,.226,.300,5.01,'.025'),('全再犯 執行猶予',1310,125,.220,.356,12.00,'.001'),
                             ('性 仮釈放',2528,285,.155,.216,5.09,'.024'),('性 執行猶予',1310,125,.179,.333,18.89,'.00001')]:
    a,c,x,p=pearson(p1,n1,p2,n2)
    print(f'{nm}: 4年KM率で概算 Pearson χ²={x:.2f}（報告 log-rank {xr}）  報告χ²のp={chi2.sf(xr,1):.2g}（報告 {pr}）')

# 照合の要約（lib/tally.py）：数えるのは、資料の数どうしを照合できる項目だけ。
#  2020 表1〜3 の行・列の和（17）、表5 の信頼区間の中点とハザード比（2）、報告されたχ²値と p 値（5）、2012 表3 の罪種別の和と全体（1：63名の差＝欠落）。
#  率から人数を逆算した Pearson χ² と log-rank の比較は概算のため数えない。
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))); from lib.tally import Tally
_t = Tally('moj_sexoffender', 'c104', note='保護局 性犯罪者処遇プログラム効果検証（2020・2012）：表の和、ハザード比と信頼区間、χ²と p 値', script=__file__)
_ok = [a + b == t for a, b, t in t1.values()] + [a + b == t for a, b, t in t2] + [sum(r[:4]) == r[4] for r in t3] + [t3[0][i] + t3[1][i] == t3[2][i] for i in range(5)]
_ok += [abs(math.exp((math.log(1.101) + math.log(2.004)) / 2) - 1.485) < 0.0015, abs(math.exp((math.log(1.346) + math.log(1.545)) / 2) - 1.442) < 0.0015]
_ok += [abs(chi2.sf(x, 1) - float(p)) <= 0.5 * 10 ** -(len(p.split('.')[1])) + 1e-12 for x, p in ((17.11, '.00004'), (5.01, '.025'), (12.00, '.001'), (5.09, '.024'), (18.89, '.00001'))]
_ok += [4248 == 1264 + 1531 + 1390]
_t.set(compared=len(_ok), mismatched=_ok.count(False)); print('tally', _t.save())
