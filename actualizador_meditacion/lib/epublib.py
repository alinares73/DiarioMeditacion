"""Lectura de los ePub de meditaciones: unidades (archivo del spine) con etiqueta del índice, contexto y claves litúrgicas."""
import re, html, os, posixpath, unicodedata

def nrm(s):
    s = unicodedata.normalize('NFD', s.lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', s).strip()

def read_epub(path):
    """Lee un .epub (zip): devuelve las unidades del spine con su etiqueta del índice (la más profunda)."""
    import zipfile
    z = zipfile.ZipFile(path)
    rd = lambda p: z.read(p).decode('utf-8', 'replace')
    names = set(z.namelist())
    cont = rd('META-INF/container.xml')
    opf = re.search(r'full-path="([^"]+)"', cont).group(1)
    o = rd(opf)
    base = posixpath.dirname(opf)
    J = lambda *p: posixpath.normpath(posixpath.join(*p)).lstrip('./') if p else ''
    man = {}
    for it in re.findall(r'<item\b[^>]*>', o):
        i = re.search(r'\bid="([^"]+)"', it); h = re.search(r'\bhref="([^"]+)"', it)
        if i and h: man[i.group(1)] = html.unescape(h.group(1))
    spine = [man[i] for i in re.findall(r'<itemref\b[^>]*idref="([^"]+)"', o) if i in man]
    ncxid = re.search(r'<spine[^>]*toc="([^"]+)"', o)
    ncx = man.get(ncxid.group(1)) if ncxid else next(v for v in man.values() if v.endswith('.ncx'))
    s = rd(J(base, ncx)) if base else rd(ncx)
    entries = []; stack = []
    for m in re.finditer(r'(<navPoint\b[^>]*>)|(</navPoint>)|<text>(.*?)</text>|<content\s+src="([^"]*)"', s, re.S):
        if m.group(1): stack.append(None)
        elif m.group(2): stack.pop()
        elif m.group(3) is not None and stack: stack[-1] = html.unescape(re.sub(r'<[^>]+>', '', m.group(3))).strip()
        elif m.group(4) and stack:
            src = html.unescape(m.group(4)); f = src.split('#')[0]
            entries.append({'label': stack[-1], 'parents': [x for x in stack[:-1] if x], 'file': posixpath.normpath(posixpath.join(posixpath.dirname(ncx), f))})
    byfile = {}
    for e in entries: byfile.setdefault(e['file'], []).append(e)
    units = []
    for f in spine:
        fp = posixpath.normpath(f)
        es = byfile.get(fp, [])
        e = max(es, key=lambda x: len(x['parents'])) if es else None
        zp = J(base, fp) if base else fp
        if zp not in names:
            from urllib.parse import unquote
            zp = unquote(zp)
        raw = rd(zp)
        units.append({'file': fp, 'label': e['label'] if e else None, 'parents': e['parents'] if e else [], 'raw': raw})
    return units

# ---------------------------------------------------------------- ordinales
UNITS = {'primer': 1, 'primero': 1, 'primera': 1, 'segundo': 2, 'segunda': 2, 'tercer': 3, 'tercero': 3, 'tercera': 3, 'cuarto': 4, 'cuarta': 4,
         'quinto': 5, 'quinta': 5, 'sexto': 6, 'sexta': 6, 'septimo': 7, 'septima': 7, 'octavo': 8, 'octava': 8, 'noveno': 9, 'novena': 9}
TENS = {'decimo': 10, 'decima': 10, 'vigesimo': 20, 'vigesima': 20, 'trigesimo': 30, 'trigesima': 30}
SPECIAL = {'undecimo': 11, 'undecima': 11, 'duodecimo': 12, 'duodecima': 12, 'ultimo': 34}
ROM = {'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5, 'vi': 6, 'vii': 7, 'viii': 8, 'ix': 9, 'x': 10, 'xi': 11, 'xii': 12, 'xiii': 13, 'xiv': 14, 'xv': 15,
       'xvi': 16, 'xvii': 17, 'xviii': 18, 'xix': 19, 'xx': 20, 'xxi': 21, 'xxii': 22, 'xxiii': 23, 'xxiv': 24, 'xxv': 25, 'xxvi': 26, 'xxvii': 27,
       'xxviii': 28, 'xxix': 29, 'xxx': 30, 'xxxi': 31, 'xxxii': 32, 'xxxiii': 33, 'xxxiv': 34}

def word_ord(t):
    """Primer ordinal escrito en palabras (admite 'vigesimoprimer', 'décimo tercer', 'trigésimo')."""
    t = re.sub(r'(vigesim|trigesim|decim)octav', r'\1o octav', t)
    t = re.sub(r'(vigesim[oa]|trigesim[oa]|decim[oa])(?=[a-z])', r'\1 ', t)
    toks = re.findall(r'[a-z]+', t)
    for i, w in enumerate(toks):
        if w in SPECIAL: return SPECIAL[w]
        if w in TENS:
            n = TENS[w]
            if i + 1 < len(toks) and toks[i + 1] in UNITS: n += UNITS[toks[i + 1]]
            return n
        if w in UNITS: return UNITS[w]
    return None

DOW = {'domingo': 0, 'lunes': 1, 'martes': 2, 'miercoles': 3, 'jueves': 4, 'viernes': 5, 'sabado': 6}
MES = {'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6, 'junios': 6, 'julio': 7, 'agosto': 8, 'septiembre': 9, 'setiembre': 9,
       'octubre': 10, 'noviembre': 11, 'marzon': 3, 'diciembre': 12}

def find_dow(t):
    m = re.search(r'\b(domingo|lunes|martes|miercoles|jueves|viernes|sabado)\b', t)
    return DOW[m.group(1)] if m else None

def find_date(t):
    m = re.match(r'^\s*(?:[a-z ]+[.,]\s*)?(\d{1,2}) de ([a-z]+)\b', t)
    if m and m.group(2) in MES: return 'F%02d-%02d' % (MES[m.group(2)], int(m.group(1)))
    return None

def find_week(t):
    m = re.search(r'\b(\d{1,2})\s*\.?\s*[ªa]\b', t)
    if m: return int(m.group(1))
    m = re.search(r'\b(?:domingo|semana|lunes|martes|miercoles|jueves|viernes|sabado)\s+([ivx]+)\b', t)
    if m and m.group(1) in ROM: return ROM[m.group(1)]
    m = re.match(r'^([ivx]+) domingo\b', t)
    if m and m.group(1) in ROM: return ROM[m.group(1)]
    m = re.search(r'\bdel? ([ivx]+) del to\b', t)
    if m and m.group(1) in ROM: return ROM[m.group(1)]
    return word_ord(t)

def cycle(t):
    m = re.search(r'\bciclo ([abc])\b|\(([abc])\)', t)
    return (m.group(1) or m.group(2)).upper() if m else ''
