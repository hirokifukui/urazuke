"""c103: H001 の検定。補集合 = 高密度全体(表23) − 部分集団(表35 / 表40)。"""
import math
def rr(a,n1,c,n0): return (a/n1)/(c/n0)
def ci(a,n1,c,n0):
    se=math.sqrt(1/a-1/n1+1/c-1/n0); r=rr(a,n1,c,n0); return r*math.exp(-1.96*se), r*math.exp(1.96*se)
tot={'全':(156,350,62,131),'性':(87,350,40,131)}
sub={'A指標者':{'全':(36,117,20,43),'性':(17,117,14,43)},'m指定なし':{'全':(133,312,49,103),'性':(73,312,33,103)}}
comp={'A指標者':'B指標者','m指定なし':'m指定者'}
for k,v in sub.items():
    for o in ('全','性'):
        a,n1,c,n0=v[o]; A,N1,C,N0=tot[o]
        ca,cn1,cc,cn0=A-a,N1-n1,C-c,N0-n0
        lo,hi=ci(a,n1,c,n0); clo,chi=ci(ca,cn1,cc,cn0)
        print(f'{o}再犯 報告={k}: 受講 {a}/{n1}={a/n1:.1%} 対照 {c}/{n0}={c/n0:.1%} RR {rr(a,n1,c,n0):.2f} [{lo:.2f}-{hi:.2f}]  |  未報告={comp[k]}: 受講 {ca}/{cn1}={ca/cn1:.1%} 対照 {cc}/{cn0}={cc/cn0:.1%} RR {rr(ca,cn1,cc,cn0):.2f} [{clo:.2f}-{chi:.2f}]')
