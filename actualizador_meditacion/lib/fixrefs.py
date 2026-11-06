"""Corrige enlaces bíblicos partidos en los libros copiados del Diario.
En algunos textos el número del versículo venía cortado por el formato (p. ej. «<i>Lc 14, 1</i>5-24»), y el enlace
solo cogía la primera cifra: #/r/48/13/1 en vez de #/r/48/13/15. Se une la cifra siguiente si el versículo existe."""
import re, os, glob, json, hashlib
RX = re.compile(r'(<a href="#/r/(\d+)/(\d+)/)(\d+)("[^>]*>)((?:<(?:i|b|em|strong|span)\b[^>]*>)*)([^<]*?)(\d+)'
                r'((?:</(?:i|b|em|strong|span)>)*)(</a>)((?:</?(?:i|b|em|strong|span)\b[^>]*>)*)(\d+)')

def versos(data_dir):
    V = {}
    for f in glob.glob(os.path.join(data_dir, 'b*.json')):
        m = re.search(r'b(\d+)\.json$', f)
        if not m: continue
        d = json.load(open(f, encoding='utf-8'))
        V[int(m.group(1))] = [max([int(x) for x in re.findall(r'class="vs[^"]*" data-v="(\d+)', c.get('h', ''))] or [0]) for c in d['ch']]
    return V

def fix(html, V):
    n = 0
    def rep(m):
        nonlocal n
        b, c, v, txtnum, nxt = int(m.group(2)), int(m.group(3)), m.group(4), m.group(8), m.group(12)
        if txtnum != v: return m.group(0)
        nv = int(v + nxt)
        try:
            if nv > V[b][c]: return m.group(0)
        except (KeyError, IndexError): return m.group(0)
        n += 1
        return m.group(1) + str(nv) + m.group(5) + m.group(6) + m.group(7) + m.group(8) + nxt + m.group(9) + m.group(10) + m.group(11)
    return RX.sub(rep, html), n

def fix_docs(dst, skip=()):
    """Corrige todos los libros de dst/docs (salvo skip). Devuelve {libro: nº de enlaces corregidos}."""
    V = versos(os.path.join(dst, 'data')); res = {}
    for d in sorted(os.listdir(os.path.join(dst, 'docs'))):
        if d in skip: continue
        for f in glob.glob(os.path.join(dst, 'docs', d, '*.html')):
            s = open(f, encoding='utf-8').read(); o, n = fix(s, V)
            if n:
                res[d] = res.get(d, 0) + n
                with open(f, 'w', encoding='utf-8', newline='') as fh: fh.write(o)
    # recuerda qué libros llevan correcciones (para su número de versión aunque hoy no se haya copiado nada)
    reg = os.path.join(dst, 'docs', 'refs_corregidos.json')
    old = json.load(open(reg)) if os.path.exists(reg) else {}
    for k, n in res.items(): old[k] = max(old.get(k, 0), n)
    if res: json.dump(old, open(reg, 'w'), sort_keys=True)
    return res, old

def fix_day(D, V):
    """Lecturas de la portada (DAY[fecha].r = [href, 'Lc 14, 1', '5-24', título]) con el versículo partido."""
    n = 0
    for v in D.values():
        for r in v.get('r', []):
            m = re.match(r'#/r/(\d+)/(\d+)/(\d+)$', r[0]); t = re.search(r'(\d+)$', r[1]); d = re.match(r'(\d+)(.*)$', r[2] or '')
            if not (m and t and d) or t.group(1) != m.group(3): continue
            nv = int(m.group(3) + d.group(1))
            try:
                if nv > V[int(m.group(1))][int(m.group(2))]: continue
            except (KeyError, IndexError): continue
            r[0] = '#/r/%s/%s/%d' % (m.group(1), m.group(2), nv); r[1] = r[1] + d.group(1); r[2] = d.group(2); n += 1
    return n
