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

def navegacion(chunks):
    """Flechas ◀ ▶ junto al título de cada punto para pasar al anterior o al siguiente."""
    rx = re.compile(r'<h2 id="o(\d+)" data-o="\1">(.*?)</h2>')
    offs = [int(m.group(1)) for c in chunks[1:] for m in rx.finditer(c)]
    pos = {o: i for i, o in enumerate(offs)}
    def rep(m):
        o = int(m.group(1)); i = pos[o]
        prv = '<a class="vnv" href="#/d/Valtorta/%d" aria-label="Punto anterior">◀</a>' % offs[i - 1] if i > 0 else '<span class="vnv off">◀</span>'
        nxt = '<a class="vnv" href="#/d/Valtorta/%d" aria-label="Punto siguiente">▶</a>' % offs[i + 1] if i + 1 < len(offs) else '<span class="vnv off">▶</span>'
        return '<div class="vhd2">%s%s%s</div>' % (prv, m.group(0), nxt)
    return [chunks[0]] + [rx.sub(rep, c) for c in chunks[1:]]

def construir(epub_path, enlaces_path, chunk_kb=260, atlas_path=None, subt_path=None):
    """Devuelve (chunks, meta, VAL, falt, ATL) ; VAL = {libro: {cap_idx: [[v_ini, v_fin, off, alusion, paso], ...]}}"""
    parts, scenes = leer_epub(epub_path)
    E = json.load(open(enlaces_path, encoding='utf-8'))['enlaces']
    ATL, porch, first = atlas_prep(atlas_path) if atlas_path else (None, {}, {})
    por_par = {}
    for b, c, a, z, s, j, par, ch in E: por_par.setdefault((s, j), []).append((b, c, a, z, par))
    idx = 1; secs = []; offs = {}; toc = []
    SUBT = {}
    if subt_path:
        for k, l in json.load(open(subt_path, encoding='utf-8')).items():
            if not k.startswith('_'):
                for j, t in l: SUBT[(int(k), j)] = t
    subs = {}
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
            st = SUBT.get((s['n'], j))
            if st:   # subtítulo dentro de un punto largo (lleva el ancla del párrafo)
                h.append('<h3 class="vsub" id="o%d">%s</h3>' % (po, html.escape(st))); subs.setdefault(o, []).append((po, st))
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
                h.append('<p%s data-o="%d">%s</p>' % ('' if st else ' id="o%d"' % po, po, limpia(p)))
            else:
                h.append('<p%s data-o="%d">%s</p>' % (' id="o%d"' % po if wh and not st else '', po, limpia(p)))
        secs.append((o, part, s['t'], '\n'.join(h)))
    # índice
    t0 = ['<p data-o="0" style="text-align:center"><b><span style="font-size:1.3em">La vida de Jesús</span></b></p>',
          '<p style="text-align:center" class="sm">según las visiones de María Valtorta</p>',
          '<p class="sm" style="text-align:center">Los pasajes que tienen correspondencia con los Evangelios llevan encima sus citas: tócalas para ir a la Biblia.</p>',
          ]
    if ATL: t0.append('<p class="vatl"><a href="#/mapa">🗺 Mapa de los viajes</a><a href="#/viajes">📜 Cronología</a><a href="#/lugares">📍 Lugares</a></p>')
    # índice agrupado por las ocho partes: cada parte se despliega con sus puntos
    t0.append('<h2>Índice</h2>')
    t0.append('<div class="vgo"><input id="vgo" type="number" inputmode="numeric" min="1" max="%d" placeholder="Ir al punto nº…" aria-label="Ir al punto número"><button class="btn" id="vgob">Ir</button></div>' % len(secs))
    grupos = []
    for o, part, t, _ in secs:
        if not grupos or grupos[-1][0] != part: grupos.append((part, []))
        grupos[-1][1].append((o, t))
    for part, items in grupos:
        m = re.match(r'Parte\s+([IVXL]+)\s*·\s*(.*)', part)
        num, tit = (m.group(1), m.group(2)) if m else ('', part)
        nn = [re.match(r'(\d+)\.\s*(.*)', t) for _, t in items]
        a_, z_ = (nn[0].group(1), nn[-1].group(1)) if nn[0] and nn[-1] else ('', '')
        t0.append('<details class="vpart" name="vpart"><summary><span class="vpn">%s</span><span class="vpt"><b>%s</b><small>%d puntos · %s–%s</small></span></summary><div class="vpl">' % (num, html.escape(tit), len(items), a_, z_))
        for (o, t), mm in zip(items, nn):
            n_, tt = (mm.group(1), mm.group(2)) if mm else ('', t)
            t0.append('<a class="vsc" data-n="%s" href="#/d/Valtorta/%d"><span>%s</span>%s</a>' % (n_, o, n_, html.escape(tt)))
            for po_, st_ in subs.get(o, []):
                t0.append('<a class="vss" href="#/d/Valtorta/%d">%s</a>' % (po_, html.escape(st_)))
        t0.append('</div></details>')
    chunks = ['\n'.join(t0)]; starts = [0]; cur = []; n = 0; cs = None
    for o, part, t, h in secs:
        if cur and n + len(h) > chunk_kb * 1024:
            chunks.append('\n'.join(cur)); starts.append(cs); cur = []; n = 0
        if not cur: cs = o
        cur.append(h); n += len(h)
    if cur: chunks.append('\n'.join(cur)); starts.append(cs)
    chunks = navegacion(chunks)
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
