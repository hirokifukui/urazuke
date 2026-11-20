"""htmltables.py HTML の <table> を行（セル文字列のリスト）の並びにする。rowspan/colspan は展開する。
tables(path) → [ {'caption':直前の見出し文字列, 'rows':[[str,...],...]}, ... ]"""
import re, html as H
from html.parser import HTMLParser

class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.tabs = []; self.stack = []; self.last_text = ''; self.cur = None; self.cell = None
    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag == 'table':
            self.stack.append({'caption': self.last_text.strip(), 'grid': [], 'pending': {}})
        elif self.stack and tag == 'tr':
            self.cur = []
        elif self.stack and tag in ('td', 'th') and self.cur is not None:
            self.cell = {'t': '', 'rs': int(a.get('rowspan', 1) or 1), 'cs': int(a.get('colspan', 1) or 1)}
        elif tag == 'br' and self.cell is not None:
            self.cell['t'] += ' '
    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None and self.cur is not None:
            self.cur.append(self.cell); self.cell = None
        elif tag == 'tr' and self.stack and self.cur is not None:
            t = self.stack[-1]; row = []; col = 0; cells = list(self.cur)
            pend = t['pending']
            while cells or col in pend:
                if col in pend:
                    txt, left = pend[col]; row.append(txt)
                    if left > 1: pend[col] = (txt, left - 1)
                    else: del pend[col]
                    col += 1; continue
                c = cells.pop(0)
                for k in range(c['cs']):
                    row.append(c['t'].strip())
                    if c['rs'] > 1: pend[col] = (c['t'].strip(), c['rs'] - 1)
                    col += 1
            t['grid'].append(row); self.cur = None
        elif tag == 'table' and self.stack:
            t = self.stack.pop(); self.tabs.append({'caption': t['caption'], 'rows': t['grid']})
    def handle_data(self, d):
        if self.cell is not None: self.cell['t'] += d
        elif d.strip(): self.last_text = d.strip()

def tables(path):
    p = P(); p.feed(open(path, encoding='utf-8', errors='replace').read()); return p.tabs

def num(s):
    s = re.sub(r'[名床件人,\s]', '', H.unescape(str(s)))
    s = s.replace('－', '0').replace('-', '0') if s in ('－', '-', '―') else s
    return int(s) if re.fullmatch(r'-?\d+', s) else None
