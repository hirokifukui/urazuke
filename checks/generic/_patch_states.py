import re
p = 'site/build_site.py'
s = open(p).read()
L = s.split('\n')
i = next(n for n, l in enumerate(L) if "fs = [f for f in INSCOPE if f['影響'] == lv]" in l)
while not L[i].startswith('def '):
    i -= 1
DEF = r'''# 確認の状態（4つ）。PROCESS §3 の終わりの規則に対応する
def STATE(f):
    c = f['確認']
    if '別系統で支持' in c: return 'sup'
    if '別系統では判定不能' in c: return 'fin'
    if re.search(r'R0\d\d', c): return 'rew'
    return 'pre'
ST_JA = {'sup': '別系統で支持', 'pre': '反証にかける前', 'rew': '書き直して再反証待ち', 'fin': '別系統では判定不能（確定）'}
ST_EN = {'sup': 'Supported by an independent model', 'pre': 'Not yet put to a refutation check', 'rew': 'Rewritten, awaiting a new refutation check', 'fin': 'Undetermined by an independent model (final)'}
ST_PEND = ('pre', 'rew', 'fin')
ST_ALL = ('sup',) + ST_PEND'''
L[i:i] = DEF.split('\n')
s = '\n'.join(L)
if not re.search(r'^import re\b|^import .*, re\b', s, re.M):
    s = 'import re\n' + s

def rep(old, new, cnt=1):
    global s
    assert s.count(old) == cnt, (old[:80], s.count(old))
    s = s.replace(old, new)

rep("""(f'<li class="tsep">検証中（別系統の支持なし）{len(rest)} 件</li>' + ''.join(li(f, 'pend') for f in rest) if rest else '')""",
    """''.join(f'<li class="tsep">{ST_JA[k]} {len(g)} 件</li>' + ''.join(li(f, 'pend') for f in g) for k in ST_PEND for g in [[f for f in rest if STATE(f) == k]] if g)""")
rep("""(f'<li class="tsep">Under verification (not yet supported by an independent model): {len(rest)}</li>' + ''.join(li(f, 'pend') for f in rest) if rest else '')""",
    """''.join(f'<li class="tsep">{ST_EN[k]}: {len(g)}</li>' + ''.join(li(f, 'pend') for f in g) for k in ST_PEND for g in [[f for f in rest if STATE(f) == k]] if g)""")
rep("_ord = lambda f: (0 if '別系統で支持' in f['確認'] else 1, -f['影響'], f['id'])",
    "_ord = lambda f: (ST_ALL.index(STATE(f)), -f['影響'], f['id'])")
rep("""まだ支持されていない記録を「検証中」として後に並べます（すべての記録に同じ規則）。""",
    """まだ支持されていない記録を、反証にかける前・書き直して再反証待ち・別系統では判定不能（確定）の順に後に並べます（すべての記録に同じ規則。<a href="process.html">進め方 §3</a>）。""")
rep("""+ f'<tr class="rsep"><td colspan="5">検証中（別系統の支持なし）{len(_pen)} 件</td></tr>' + ''.join(_rr(f) for f in _pen) + '</table>')""",
    """+ ''.join(f'<tr class="rsep"><td colspan="5">{ST_JA[k]} {len(g)} 件</td></tr>' + ''.join(_rr(f) for f in g) for k in ST_PEND for g in [[f for f in _pen if STATE(f) == k]] if g) + '</table>')""")
rep("""records not yet supported follow under “Under verification” (the same rule for every record).""",
    """records not yet supported follow, in this order: not yet put to a refutation check, rewritten and awaiting a new check, and undetermined by an independent model (final) (the same rule for every record; <a href="process.html">Process §3</a>).""")
rep("""+ f'<tr class="rsep"><td colspan="5">Under verification (not yet supported by an independent model): {len(_pen)}</td></tr>' + ''.join(_rr_en(f) for f in _pen) + '</table>')""",
    """+ ''.join(f'<tr class="rsep"><td colspan="5">{ST_EN[k]}: {len(g)}</td></tr>' + ''.join(_rr_en(f) for f in g) for k in ST_PEND for g in [[f for f in _pen if STATE(f) == k]] if g) + '</table>')""")
rep('''data-d="{1 if "別系統で支持" in f["確認"] else 0}"''', '''data-d="{STATE(f)}"''')
rep('''data-d="{1 if SUP(f) else 0}"''', '''data-d="{STATE(f)}"''')
rep('''<label class="muted"><input type="checkbox" id="fd"> 別系統の検証で支持されたものだけ</label>''',
    '''<select id="fd"><option value="">確認の状態：すべて</option>{ST_OPTS_JA}</select>''')
rep('''<label class="muted"><input type="checkbox" id="fd"> Only records supported by an independent model</label>''',
    '''<select id="fd"><option value="">Verification status: all</option>{ST_OPTS_EN}</select>''')
s = s.replace("ST_ALL = ('sup',) + ST_PEND", "ST_ALL = ('sup',) + ST_PEND\nST_OPTS_JA = ''.join(f'<option value=\"{k}\">{ST_JA[k]}</option>' for k in ST_ALL)\nST_OPTS_EN = ''.join(f'<option value=\"{k}\">{ST_EN[k]}</option>' for k in ST_ALL)", 1)
rep("d=fd.checked;", "d=fd.value;", 2)
rep("(!d||r.dataset.d=='1')", "(!d||r.dataset.d==d)", 2)
open(p, 'w').write(s)
print('ok')
