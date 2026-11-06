"""Libro «Meditaciones del año litúrgico» (VV. AA.): trozos html, meta e índice de meditaciones por día litúrgico (MEDI['MAL'])."""
import re, html, hashlib, zipfile, posixpath
from classify import classify
from epublib import nrm

SEASON = {'c01': 'Tiempo de Adviento', 'c02': 'Tiempo de Navidad', 'c03': 'Tiempo de Cuaresma', 'c04': 'Semana Santa',
          'c05': 'Tiempo de Pascua', 'web01': 'Tiempo ordinario', 'web02': 'Fiestas y solemnidades del Tiempo ordinario'}
HINT = {'c01': 'adviento', 'c02': 'navidad', 'c03': 'cuaresma', 'c04': '', 'c05': 'pascua', 'web01': 'tiempo ordinario', 'web02': ''}
# títulos que el clasificador general no sabe fechar
FIX = [(r'san esteban', ['F12-26']), (r'santos inocentes', ['F12-28']), (r'santa maria,? madre de dios', ['F01-01']),
       (r'^2\.?[aª]? domingo de navidad', ['NAV2']), (r'conversion de san pablo', ['F01-25']), (r'timoteo y tito', ['F01-26']),
       (r'fundacion de la seccion femenina', ['F02-14']), (r'catedra de san pedro', ['F02-22']), (r'^11 (de )?junio', ['F06-11']),
       (r'transfiguracion', ['F08-06']), (r'^san lucas', ['F10-18']), (r'dedicacion de las basilicas', ['F11-18']),
       (r'^2 de febrero', ['F02-02']), (r'^29 de diciembre', ['F12-29']), (r'^30 de diciembre', ['F12-30']), (r'^31 de diciembre', ['F12-31']),
       (r'^(2|4|5) de enero', None)]

def clean_label(t):
    t = html.unescape(re.sub(r'<[^>]+>', '', t)).strip()
    t = re.sub(r'\s+', ' ', t)
    return t

def key_label(t):
    """Etiqueta preparada para el clasificador (ordinales con º/°, octava de Pascua...)."""
    t = re.sub(r'(\d)\s*\.?\s*[º°]', r'\1.ª', t)
    if re.match(r'^(lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado) de pascua$', t, re.I): t += ' (octava de pascua)'
    t = re.sub(r'despu[eé]s de la epifan', 'después de epifan', t, flags=re.I)
    return t

def cycles(t):
    n = nrm(t)
    m = re.search(r'ciclos? ([abc])(?:,? ([abc]))?(?: y ([abc]))?', n)
    if not m: return ['']
    cs = [c.upper() for c in m.groups() if c]
    return [''] if len(cs) >= 3 else cs

INL = re.compile(r'</?(?:i|em|b|strong|sup|sub|br)\b[^>]*>', re.I)
def inline(s, fnmap, uid):
    """html en línea limpio; las llamadas a notas pasan a <a class="fn">."""
    def fn(m):
        href = html.unescape(m.group(1)); num = re.sub(r'\D', '', re.sub(r'<[^>]+>', '', m.group(2)))
        key = href.split('#')[-1]
        if key in fnmap and num:
            return '<a class="fn" data-f="%s_%s">%s</a>' % (uid, re.sub(r'[^\w-]', '', key), num)
        return re.sub(r'<[^>]+>', '', m.group(2))
    s = re.sub(r'<a\b[^>]*href="([^"]*)"[^>]*>(.*?)</a>', fn, s, flags=re.S)
    out = []
    for tok in re.split(r'(<[^>]+>)', s):
        if tok.startswith('<'):
            if tok.startswith('<a class="fn"') or tok == '</a>': out.append(tok); continue
            m = re.match(r'<(/?)(i|em|b|strong|sup|sub|br)\b', tok, re.I)
            if m:
                tg = {'em': 'i', 'strong': 'b'}.get(m.group(2).lower(), m.group(2).lower())
                out.append('<br>' if tg == 'br' else '<%s%s>' % (m.group(1), tg))
        else: out.append(tok)
    s = re.sub(r'\s+', ' ', ''.join(out)).strip()
    s = re.sub(r'<sup>\s*(<a class="fn"[^>]*>\d+</a>)\s*</sup>', r'\1', s)
    s = re.sub(r'<(i|b|sup)>\s*</\1>', '', s)
    return s

def leer(path):
    z = zipfile.ZipFile(path); rd = lambda p: z.read(p).decode('utf-8', 'replace')
    opf = re.search(r'full-path="([^"]+)"', rd('META-INF/container.xml')).group(1); base = posixpath.dirname(opf)
    o = rd(opf); man = {}
    for it in re.findall(r'<item\b[^>]*>', o):
        i = re.search(r'\bid="([^"]+)"', it); h = re.search(r'\bhref="([^"]+)"', it)
        if i and h: man[i.group(1)] = h.group(1)
    spine = [man[i] for i in re.findall(r'<itemref\b[^>]*idref="([^"]+)"', o) if i in man]
    J = lambda f: posixpath.join(base, f) if base else f
    # notas finales (epub3) del archivo notas.xhtml
    notes3 = {}
    nf = next((f for f in spine if f.endswith('notas.xhtml')), None)
    if nf:
        for m in re.finditer(r'<div[^>]*epub:type="footnote"[^>]*id="([^"]+)"[^>]*>(.*?)</div>', rd(J(nf)), re.S):
            body = re.sub(r'<a\b[^>]*role="doc-backlink"[^>]*>.*?</a>', '', m.group(2), flags=re.S)
            notes3[m.group(1)] = ' '.join(re.findall(r'<p\b[^>]*>(.*?)</p>', body, re.S)) or body
    units = []
    for f in spine:
        stem = posixpath.basename(f).split('.')[0]
        grp = stem.split('_')[0]
        if grp not in SEASON or stem == grp and grp.startswith('web'): continue
        t = rd(J(f)); body = t[t.find('<body'):]
        parts = re.split(r'(<h2\b[^>]*>.*?</h2>)', body, flags=re.S)
        for k in range(1, len(parts), 2):
            units.append({'label': clean_label(parts[k]), 'grp': grp, 'raw': parts[k + 1], 'notes3': notes3})
    return units

def blocks(u, uid):
    raw = u['raw']
    # notas al pie de los archivos web (_ftnN) y finales (footnote-N)
    local = {}
    for m in re.finditer(r'<p\b[^>]*>\s*<a\b[^>]*href="#_ftnref\d+"[^>]*id="(_ftn\d+)"[^>]*>.*?</a>(.*?)</p>', raw, re.S):
        local[m.group(1)] = m.group(2)
    raw = re.sub(r'<p\b[^>]*>\s*<a\b[^>]*href="#_ftnref\d+"[^>]*>.*?</a>.*?</p>', '', raw, flags=re.S)
    fnmap = dict(local)
    for k in re.findall(r'href="notas\.xhtml#([^"]+)"', raw):
        if k in u['notes3']: fnmap[k] = u['notes3'][k]
    out = []; order = []
    for m in re.finditer(r'<(p|li|hr|h3|h4|blockquote)\b([^>]*)>(.*?)</\1>|<hr\s*/?>', raw, re.S):
        if m.group(0).startswith('<hr'): out.append(('sep', '')); continue
        tag, attr, inner = m.groups()
        txt = html.unescape(re.sub(r'<[^>]+>', '', inner)).strip()
        if not txt: continue
        if txt.startswith('Fuente:'): continue
        s = inline(inner, fnmap, uid)
        for k in re.findall(r'data-f="%s_([\w-]+)"' % uid, s):
            if k not in order: order.append(k)
        if tag == 'li': out.append(('sm', '– ' + s))
        elif tag in ('h3', 'h4'): out.append(('h3', s))
        elif tag == 'p' and re.match(r'^\s*<(em|i)>.*</\1>\s*$', inner.strip(), re.S) and not out: out.append(('sm', s))
        else: out.append(('p', s))
    # separadores: solo entre párrafos de texto
    res = []
    for kind, s in out:
        if kind == 'sep':
            if res and res[-1][0] == 'p': res.append(('sep', ''))
            continue
        res.append((kind, s))
    while res and res[-1][0] == 'sep': res.pop()
    notes = []
    for i, k in enumerate(order):
        body = inline(fnmap[k], {}, uid)
        num = re.findall(r'data-f="%s_%s">(\d+)<' % (uid, re.escape(re.sub(r'[^\w-]', '', k))), ''.join(s for _, s in res))
        notes.append(('%s_%s' % (uid, re.sub(r'[^\w-]', '', k)), num[0] if num else str(i + 1), body))
    return res, notes

def titulo(t):
    t = re.sub(r'\s+', ' ', t).strip()
    return t[:1].upper() + t[1:]

def construir(path, chunk_kb=260):
    units = leer(path)
    idx = 1; meds = []; falt = []
    for n, u in enumerate(units):
        bl, notes = blocks(u, 'MAL%d' % n)
        if not bl: continue
        lab = u['label']; t = titulo(lab)
        nl = nrm(key_label(lab))
        keys = None
        for rx, ks in FIX:
            if re.search(rx, nl): keys = ks; break
        if keys is None:
            keys, _ = classify(key_label(lab), [SEASON[u['grp']]], HINT[u['grp']])
        keys = keys or []
        off = idx; idx += 1
        h = ['<h2 id="o%d" data-o="%d">%s</h2>' % (off, off, html.escape(t))]
        for kind, s in bl:
            o = idx; idx += 1
            if kind == 'sep': h.append('<p class="sm" data-o="%d" style="text-align:center">· · ·</p>' % o)
            elif kind == 'sm': h.append('<p class="sm" data-o="%d">%s</p>' % (o, s))
            elif kind == 'h3': h.append('<h3 data-o="%d">%s</h3>' % (o, s))
            else: h.append('<p data-o="%d">%s</p>' % (o, s))
        if notes:
            o = idx; idx += 1; h.append('<h4 class="fnh" data-o="%d">Notas</h4>' % o)
            for nid, num, body in notes:
                o = idx; idx += 1; h.append('<p class="fnn" id="n%s" data-o="%d"><b>%s.</b> %s</p>' % (nid, o, num, body))
        meds.append({'t': t, 'h': '\n'.join(h), 'o': off, 'k': keys, 'cs': cycles(lab), 'sec': SEASON[u['grp']]})
        if not keys: falt.append(t)
    toc = ['<p data-o="0" style="text-align:center"><b><span style="font-size:1.3em">Meditaciones del año litúrgico</span></b></p>',
           '<p style="text-align:center" class="sm">VV. AA.</p>', '<h2>Índice</h2>']
    last = None
    for m in meds:
        if m['sec'] != last: toc.append('<h3>%s</h3>' % html.escape(m['sec'])); last = m['sec']
        toc.append('<p class="toc"><a href="#/d/MAL/%d">%s</a></p>' % (m['o'], html.escape(m['t'])))
    chunks = ['\n'.join(toc)]; starts = [0]; cur = []; ln = 0; cs = None
    for m in meds:
        if cur and ln + len(m['h']) > chunk_kb * 1024:
            chunks.append('\n'.join(cur)); starts.append(cs); cur = []; ln = 0
        if not cur: cs = m['o']
        cur.append(m['h']); ln += len(m['h'])
    if cur: chunks.append('\n'.join(cur)); starts.append(cs)
    N = len(chunks)
    for k in range(1, N):
        chunks[k] += '\n<p class="toc dnx"><a href="#/dp/MAL/0">☰ Índice</a>%s</p>' % ((' · <a href="#/dp/MAL/%d">Seguir leyendo →</a>' % (k + 1)) if k + 1 < N else '')
    meta = {'title': 'Meditaciones del año litúrgico', 'starts': starts, 'x': {},
            'v': hashlib.md5(''.join(chunks).encode()).hexdigest()[:8], 'kb': sum(len(c.encode()) for c in chunks) // 1024}
    entries = []
    for m in meds:
        if not m['k']: continue
        for c in m['cs']: entries.append([m['o'], m['t'], m['k'], c])
    return chunks, meta, entries, falt
