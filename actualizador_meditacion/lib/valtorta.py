"""Libro «María Valtorta · La vida de Jesús» (docs/Valtorta) con las referencias a los Evangelios en cada pasaje."""
import re, html, json, hashlib, zipfile, posixpath

BKN = {'Mt': 46, 'Mc': 47, 'Lc': 48, 'Jn': 49}

def leer_epub(path):
    z = zipfile.ZipFile(path)
    cont = z.read('META-INF/container.xml').decode('utf-8')
    opf = re.search(r'full-path="([^"]+)"', cont).group(1); base = posixpath.dirname(opf)
    o = z.read(opf).decode('utf-8'); man = {}
    for it in re.findall(r'<item\b[^>]*>', o):
        i = re.search(r'\bid="([^"]+)"', it); h = re.search(r'\bhref="([^"]+)"', it)
        if i and h: man[i.group(1)] = h.group(1)
    spine = [man[i] for i in re.findall(r'<itemref\b[^>]*idref="([^"]+)"', o) if i in man]
    parts, scenes = [], []
    for f in spine:
        t = z.read(posixpath.join(base, f) if base else f).decode('utf-8')
        b = t[t.find('<body'):]
        for m in re.finditer(r'<(h1|h2|p)\b([^>]*)>(.*?)</\1>', b, re.S):
            tag, attr, inner = m.groups()
            txt = html.unescape(re.sub(r'<[^>]+>', '', inner)).strip()
            if tag == 'h1':
                parts.append(txt); continue
            if tag == 'h2':
                scenes.append({'n': len(scenes) + 1, 't': txt, 'part': len(parts), 'sub': '', 'p': []}); continue
            if not scenes: continue
            cls = re.search(r'class="([^"]+)"', attr)
            if cls and 'sub' in cls.group(1).split() and not scenes[-1]['p']:
                scenes[-1]['sub'] = txt; continue
            scenes[-1]['p'].append(inner.strip())
    return parts, scenes

def limpia(h):
    out = []
    for tok in re.split(r'(<[^>]+>)', h):
        if tok.startswith('<'):
            m = re.match(r'<(/?)(i|em|b|strong|sup|br)\b', tok, re.I)
            if m:
                tg = {'em': 'i', 'strong': 'b'}.get(m.group(2).lower(), m.group(2).lower())
                out.append('<br>' if tg == 'br' else '<%s%s>' % (m.group(1), tg))
        else:
            out.append(tok)
    return re.sub(r'\s+', ' ', ''.join(out)).strip()

def slug(k): return re.sub(r'[^a-z]', '', k.lower())

def atlas_prep(path):
    """Itinerario del Atlas de Valtorta: pasos por capítulo y primera línea de cada capítulo."""
    A = json.load(open(path, encoding='utf-8'))
    L = {slug(k): v for k, v in A['lugares'].items()}
    P = [[c, slug(k), f, mi, ch, t, by] for c, k, f, mi, ch, t, by in A['pasos']]
    porch = {}
    for i, p in enumerate(P):
        if p[4]: porch.setdefault(p[4], []).append(i)
    first = {}
    for ch, sj in A['chpar'].items():
        first.setdefault(tuple(sj), []).append(int(ch))
    return {'L': L, 'C': A['ciclos'], 'P': P, 'F': A['fiestas']}, porch, first

def linea_atlas(ATL, porch, chs):
    """«📍 Lugar → Lugar · fecha · ciclo» para los capítulos que empiezan en un párrafo."""
    out = []
    for ch in sorted(chs):
        ids = porch.get(ch) or []
        if not ids: continue
        P = ATL['P']; names = []
        for i in ids:
            n = ATL['L'][P[i][1]][0]
            if not names or names[-1] != n: names.append(n)
        p0 = P[ids[0]]; cy = ATL['C'][p0[0]][0].split(' · ')[0]
        out.append('<div class="vwh"><a href="#/mapa/p/%d">📍 %s</a><span>%s%s</span></div>' % (
            ids[0], html.escape(' → '.join(names)), html.escape(p0[2] + ' · ' if p0[2] else ''), html.escape(cy)))
    return ''.join(out)

def construir(epub_path, enlaces_path, chunk_kb=260, atlas_path=None):
    """Devuelve (chunks, meta, VAL, falt, ATL) ; VAL = {libro: {cap_idx: [[v_ini, v_fin, off, alusion, paso], ...]}}"""
    parts, scenes = leer_epub(epub_path)
    E = json.load(open(enlaces_path, encoding='utf-8'))['enlaces']
    ATL, porch, first = atlas_prep(atlas_path) if atlas_path else (None, {}, {})
    por_par = {}
    for b, c, a, z, s, j, par, ch in E: por_par.setdefault((s, j), []).append((b, c, a, z, par))
    idx = 1; secs = []; offs = {}; toc = []
    for s in scenes:
        part = parts[s['part'] - 1] if s['part'] else ''
        o = idx; idx += 1
        h = ['<h2 id="o%d" data-o="%d">%s</h2>' % (o, o, html.escape(s['t']))]
        if s['sub']:
            h.append('<p class="sm" data-o="%d">%s</p>' % (idx, html.escape(s['sub']))); idx += 1
        for j, p in enumerate(s['p']):
            refs = por_par.get((s['n'], j))
            po = idx; idx += 1; offs[(s['n'], j)] = po
            wh = linea_atlas(ATL, porch, first.get((s['n'], j), [])) if ATL else ''
            if wh:
                for ch in first[(s['n'], j)]:
                    for i in porch.get(ch, []): ATL['P'][i].append(po) if len(ATL['P'][i]) == 7 else None
                h.append(wh)
            if refs:
                seen = []; lab = []
                for b, c, a, z, par in sorted(refs, key=lambda r: (BKN[r[0]], r[1], r[2])):
                    key = (b, c, a, z)
                    if key in seen: continue
                    seen.append(key)
                    t = '%s %d,%d%s' % (b, c, a, '' if a == z else '-%d' % z)
                    lab.append('<a href="#/r/%d/%d/%d"%s>%s</a>' % (BKN[b], c - 1, a, ' class="al" title="alusión"' if par else '', t))
                h.append('<div class="vrf">%s</div>' % ' · '.join(lab))
                h.append('<p id="o%d" data-o="%d">%s</p>' % (po, po, limpia(p)))
            else:
                h.append('<p%s data-o="%d">%s</p>' % (' id="o%d"' % po if wh else '', po, limpia(p)))
        secs.append((o, part, s['t'], '\n'.join(h)))
    # índice
    t0 = ['<p data-o="0" style="text-align:center"><b><span style="font-size:1.3em">La vida de Jesús</span></b></p>',
          '<p style="text-align:center" class="sm">según las visiones de María Valtorta</p>',
          '<p class="sm" style="text-align:center">Los pasajes que tienen correspondencia con los Evangelios llevan encima sus citas: tócalas para ir a la Biblia.</p>',
          ]
    if ATL: t0.append('<p class="vatl"><a href="#/mapa">🗺 Mapa de los viajes</a><a href="#/viajes">📜 Cronología</a><a href="#/lugares">📍 Lugares</a></p>')
    t0.append('<h2>Índice</h2>')
    last = None
    for o, part, t, _ in secs:
        if part != last: t0.append('<h3>%s</h3>' % html.escape(part)); last = part
        t0.append('<p class="toc"><a href="#/d/Valtorta/%d">%s</a></p>' % (o, html.escape(t)))
    chunks = ['\n'.join(t0)]; starts = [0]; cur = []; n = 0; cs = None
    for o, part, t, h in secs:
        if cur and n + len(h) > chunk_kb * 1024:
            chunks.append('\n'.join(cur)); starts.append(cs); cur = []; n = 0
        if not cur: cs = o
        cur.append(h); n += len(h)
    if cur: chunks.append('\n'.join(cur)); starts.append(cs)
    N = len(chunks)
    for k in range(1, N):
        chunks[k] += '\n<p class="toc dnx"><a href="#/dp/Valtorta/0">☰ Índice</a>%s</p>' % ((' · <a href="#/dp/Valtorta/%d">Seguir leyendo →</a>' % (k + 1)) if k + 1 < N else '')
    meta = {'title': 'María Valtorta · La vida de Jesús', 'starts': starts, 'x': {},
            'v': hashlib.md5(''.join(chunks).encode()).hexdigest()[:8], 'kb': sum(len(c.encode()) for c in chunks) // 1024}
    VAL = {}
    falt = 0
    for b, c, a, z, s, j, par, ch in E:
        off = offs.get((s, j))
        if off is None: falt += 1; continue
        st = (porch.get(ch) or [-1])[0]
        VAL.setdefault(str(BKN[b]), {}).setdefault(str(c - 1), []).append([a, z, off, par, st])
    for b in VAL:
        for c in VAL[b]: VAL[b][c].sort()
    if ATL:
        for p in ATL['P']:
            if len(p) == 7: p.append(0)
    return chunks, meta, VAL, falt, ATL
