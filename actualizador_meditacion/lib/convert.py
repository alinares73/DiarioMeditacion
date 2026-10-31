"""Convierte el <body> de un archivo de ePub en bloques HTML limpios para la app."""
import re, html
from html.parser import HTMLParser

BLOCK = {'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'li', 'div'}
VOID = {'br', 'img', 'hr', 'meta', 'link', 'input'}

class _P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []      # dict(tag, cls, parts, ids)
        self.cur = None
        self.stack = []       # (tag, closing-output or None)
        self.skip = 0
    def _new(self, tag, cls):
        self._end()
        self.cur = {'tag': tag, 'cls': cls, 'parts': [], 'ids': []}
    def _end(self):
        if self.cur is not None:
            self.blocks.append(self.cur); self.cur = None
    def _ensure(self):
        if self.cur is None: self.cur = {'tag': 'p', 'cls': '', 'parts': [], 'ids': []}
    def handle_starttag(self, tag, attrs):
        a = dict(attrs); cls = a.get('class') or ''
        if tag in ('script', 'style', 'head', 'title'): self.skip += 1; return
        if self.skip: return
        if a.get('id'):
            self._ensure() if tag not in BLOCK else None
        if tag in BLOCK:
            if tag == 'div' and self.cur is not None and not ''.join(p for p in self.cur['parts'] if not p.startswith('<')).strip():
                pass
            if tag != 'div': self._new(tag, cls)
            if a.get('id'):
                self._ensure(); self.cur['ids'].append(a['id'])
            self.stack.append((tag, None)); return
        if tag in VOID:
            if tag == 'br': self._ensure(); self.cur['parts'].append('<br>')
            return
        self._ensure()
        if a.get('id'): self.cur['ids'].append(a['id'])
        out = None
        if tag in ('i', 'em') or (tag == 'span' and 'italic' in cls.split()): out = 'i'
        elif tag in ('b', 'strong') or (tag == 'span' and ('bold' in cls.split() or 'gran' in cls.split())): out = 'b'
        elif tag == 'sup' or (tag == 'span' and 'super' in cls.split()): out = 'sup'
        elif tag == 'sub': out = 'sub'
        elif tag == 'a':
            href = a.get('href') or ''
            if href.startswith('#') or ('#' in href and not href.startswith('http')):
                self.cur['parts'].append(('A', href.split('#', 1)[1])); self.stack.append((tag, 'A')); return
        if out: self.cur['parts'].append('<%s>' % out)
        self.stack.append((tag, out))
    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'head', 'title'): self.skip = max(0, self.skip - 1); return
        if self.skip: return
        if tag in VOID: return
        # desapilar hasta encontrar la etiqueta
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                for t, out in reversed(self.stack[i:]):
                    if t in BLOCK:
                        if t != 'div': self._end()
                    elif out == 'A':
                        if self.cur is not None: self.cur['parts'].append(('/A',))
                    elif out and self.cur is not None: self.cur['parts'].append('</%s>' % out)
                del self.stack[i:]
                return
    def handle_data(self, d):
        if self.skip: return
        if not d.strip() and self.cur is None: return
        self._ensure(); self.cur['parts'].append(html.escape(d, quote=False))
    def close(self):
        super().close(); self._end()

def parse_blocks(raw):
    b = raw.find('<body'); body = raw[b:] if b >= 0 else raw
    p = _P(); p.feed(body); p.close()
    return p.blocks

def plain(parts):
    return html.unescape(re.sub(r'<[^>]+>', '', ''.join(x for x in parts if isinstance(x, str)))).replace('\xa0', ' ')

def tidy_inline(h):
    h = re.sub(r'<(i|b|sup|sub)>(\s*)</\1>', r'\2', h)
    for _ in range(3): h = re.sub(r'</(i|b)>(\s*)<\1>', r'\2', h)
    h = re.sub(r'\s+', ' ', h).replace('\xa0', ' ').strip()
    h = re.sub(r'^(<br>\s*)+|(\s*<br>)+$', '', h)
    return h
