"""c102: 令和2年報告の公表表だけを用いた再分析。
(1) 罪名で層別した Mantel-Haenszel 統合（リスク比・オッズ比）。罪名構成の差が全体の効果をどれだけ説明するか。
(2) 密度別の表から逆算した、集中・調整プログラム受講者（155名）の再犯率。"""
import math
# 層: (受講再犯, 受講n, 対照再犯, 対照n)  全再犯 / 性犯罪再犯
S_all={'強姦':(105,480,25,73),'強制わいせつ':(194,653,23,92),'迷惑条例':(51,81,46,82),'児福等':(22,176,6,36)}
S_sex={'強姦':(45,480,12,73),'強制わいせつ':(118,653,17,92),'迷惑条例':(39,81,36,82),'児福等':(8,176,3,36)}
# 残余層（わいせつ目的・粗暴・その他）＝全体−4層
def resid(S,tot):
    a=tot[0]-sum(v[0] for v in S.values()); n1=tot[1]-sum(v[1] for v in S.values())
    c=tot[2]-sum(v[2] for v in S.values()); n0=tot[3]-sum(v[3] for v in S.values())
    S=dict(S); S['その他']=(a,n1,c,n0); return S
S_all=resid(S_all,(394,1444,123,324)); S_sex=resid(S_sex,(217,1444,73,324))
def mh(S):
    num=den=0; onum=oden=0
    for a,n1,c,n0 in S.values():
        N=n1+n0; b=n1-a; d=n0-c
        num+=a*n0/N; den+=c*n1/N; onum+=a*d/N; oden+=b*c/N
    return num/den, onum/oden
def crude(S):
    a=sum(v[0] for v in S.values()); n1=sum(v[1] for v in S.values()); c=sum(v[2] for v in S.values()); n0=sum(v[3] for v in S.values())
    return (a/n1)/(c/n0), a/n1, c/n0
# 直接標準化: 受講群の罪名構成を標準として対照群の期待再犯率
def std(S):
    n1=sum(v[1] for v in S.values())
    exp_c=sum(v[1]*(v[2]/v[3]) for v in S.values())/n1
    return exp_c
for name,S in (('全再犯',S_all),('性犯罪再犯',S_sex)):
    rr,p1,p0=crude(S); mrr,mor=mh(S); e=std(S)
    print(f'== {name}')
    for k,(a,n1,c,n0) in S.items(): print(f'  {k:8s} 受講 {a}/{n1}={a/n1:.3f}  対照 {c}/{n0}={c/n0:.3f}  RR={(a/n1)/(c/n0):.2f}')
    print(f'  粗リスク比 {rr:.3f}（受講 {p1:.3f} / 対照 {p0:.3f}）')
    print(f'  罪名で層別 MH リスク比 {mrr:.3f}、MH オッズ比 {mor:.3f}')
    print(f'  対照群を受講群の罪名構成に標準化した再犯率 {e:.3f}（実測 {p0:.3f}）→ 標準化リスク比 {p1/e:.3f}')
# (2) 集中・調整の逆算
for name,tot,dens in (('全再犯',517,(218,204,10)),('性犯罪再犯',290,(127,109,4))):
    r=tot-sum(dens); print(f'集中・調整プログラム受講者 155名の{name}: {r}名 = {100*r/155:.1f}%（受講群全体 {100*(394 if tot==517 else 217)/1444:.1f}%）')
for name,(h,m,l) in (('全',(156,145,8)),('性',(87,77,3))):
    print(f'受講群 {name}再犯: 高 {h}/350={h/3.5:.1f}% 中 {m}/747={100*m/747:.1f}% 低 {l}/192={100*l/192:.1f}%')
# Greenland-Robins 分散による MH リスク比の 95%CI
def mh_ci(S):
    R=Sx=P=0
    for a,n1,c,n0 in S.values():
        N=n1+n0; m=a+c
        R+=a*n0/N; Sx+=c*n1/N; P+=(n1*n0*m - a*c*N)/N**2
    rr=R/Sx; se=math.sqrt(P/(R*Sx)); return rr, rr*math.exp(-1.96*se), rr*math.exp(1.96*se)
for name,S in (('全再犯',S_all),('性犯罪再犯',S_sex)):
    rr,lo,hi=mh_ci(S); print(f'{name}: 罪名層別 MH リスク比 {rr:.3f} [95%CI {lo:.3f}–{hi:.3f}]')
