"""«Él y yo»: puntos separados por capítulo (tema). Si un mismo apunte del diario aparece en varios
capítulos del libro de R. Sada, cada capítulo da un punto distinto (antes se unían en uno)."""
import re, html, zipfile, posixpath

_MIN = {'a','de','del','la','las','el','los','en','y','que','te','me','por','con','al','o','u','un','una','lo','se','su','sus','mi','tu','nuestro','nuestra'}
def txt(h): return html.unescape(re.sub(r'<[^>]+>', '', h)).replace('\xa0', ' ').strip()
def bonito(t):
    m = re.match(r'^(\d+\.\s*)(.*)$', t); pre, t = (m.group(1), m.group(2)) if m else ('', t)
    out = []
    for i, w in enumerate(t.split(' ')):
        core = w.lstrip('¿¡')
        if i > 0 and core.lower() in _MIN: w = w[:len(w) - len(core)] + core.lower()
        out.append(w)
    return pre + ' '.join(out)
def _limpia(h, allow=('i',)):
    out = []
    for tok in re.split(r'(<[^>]+>)', h):
        if tok.startswith('<'):
            m = re.match(r'<(/?)([a-z]+)\b', tok, re.I)
            if m:
                tag = {'em': 'i'}.get(m.group(2).lower(), m.group(2).lower())
                if tag in allow: out.append('<%s%s>' % (m.group(1), tag))
        else: out.append(html.unescape(tok).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
    return re.sub(r'\s+', ' ', ''.join(out)).strip()

def leer(path):
    z = zipfile.ZipFile(path)
    opf = re.search(r'full-path="([^"]+)"', z.read('META-INF/container.xml').decode('utf-8')).group(1)
    o = z.read(opf).decode('utf-8'); base = posixpath.dirname(opf); man = {}
    for it in re.findall(r'<item\b[^>]*>', o):
        i = re.search(r'\bid="([^"]+)"', it); h = re.search(r'\bhref="([^"]+)"', it)
        if i and h: man[i.group(1)] = h.group(1)
    files = [man[i] for i in re.findall(r'<itemref idref="([^"]+)"', o) if i in man]
    grp = {}; themes = []
    for f in files:
        if not re.match(r'(capitulo|sin-titulo)', posixpath.basename(f)): continue
        s = z.read(posixpath.join(base, f).lstrip('./')).decode('utf-8'); body = s[s.find('<body'):]
        h1 = re.search(r'<h1[^>]*>(.*?)</h1>', body, re.S)
        th = bonito(re.sub(r'^\d+\.\s*', '', txt(h1.group(1)))) if h1 else f
        if th not in themes: themes.append(th)
        ti = themes.index(th); cur = None
        for m in re.finditer(r'<p\b([^>]*)>(.*?)</p>', body, re.S):
            c = re.search(r'class="([^"]*)"', m.group(1)); c = c.group(1).split()[0] if c else ''
            inner = m.group(2).strip(); plain = txt(inner)
            mm = re.match(r'^(\d{1,4})\.\s+', plain) or (re.match(r'^(\d{1,4})\s+', plain) if c == 'first' else None)
            if mm:
                n = int(mm.group(1)); inner = re.sub(r'^\s*\d{1,4}\.?\s+', '', inner, count=1)
                cur = [_limpia(inner)]
                grp.setdefault(n, []).append((ti, cur))
            elif cur is not None and c == 'subsq': cur.append(_limpia(inner))
    P = []
    for n in sorted(grp):
        porTema = []   # [(ti, [frag...], [plain...])]
        vistos = []
        for ti, f_ in grp[n]:
            pl = re.sub(r'<[^>]+>', '', ' '.join(f_)); pl = re.sub(r'^\d{1,2} de [a-záéíóú]+\.\s*', '', pl).strip()
            if any(pl and pl in q for q in vistos): continue          # repetido en otro capítulo
            vistos.append(pl)
            g = next((x for x in porTema if x[0] == ti), None)
            if not g: g = (ti, [], []); porTema.append(g)
            g[1].append('\n'.join(f_)); g[2].append(pl)
        for k, (ti, fr, _) in enumerate(porTema):
            P.append([n if k == 0 else round(n + k / 100, 2), fr, [ti]])
    return {'th': themes, 'p': P}
