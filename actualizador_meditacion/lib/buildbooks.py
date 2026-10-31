"""Construye los libros MedOD, SCE y HCD7 (trozos html + meta) y el índice MEDI."""
import re, html, hashlib, json, sys
from convert import parse_blocks, plain, tidy_inline
from epublib import nrm, find_date

FN_RX = re.compile(r'^\s*\[\s*\d+\s*\]')

def is_skip_unit(bid, u):
    f = u['file'].lower(); lab = nrm(u['label'] or '')
    if bid == 'MedOD' and (f.startswith('indice') or f.startswith('cover')): return True
    if re.search(r'(^|/)(cover|con_el(-8)?\.html|hcd\d\.html)$', f): return True
    if lab in ('contraportada', 'solapa izquierda', 'solapa derecha', 'indice'): return True
    if bid == 'HCD7' and re.search(r'_000[23]\.xhtml$', f): return True     # portadilla y página en blanco / índice
    if bid == 'SCE' and re.search(r'_0001\.html$', f): return True          # portada
    return False

def nice_title(bid, u):
    t = (u['label'] or '').strip()
    t = re.sub(r'\s+', ' ', t)
    if bid == 'SCE' or t.isupper():
        # MAYÚSCULAS -> Tipo frase (respetando siglas cortas)
        def cap(m):
            w = m.group(0)
            return w if len(w) <= 1 else w[0] + w[1:].lower()
        low = re.sub(r"[A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ]+", cap, t)
        low = re.sub(r'\b(De|Del|La|Las|El|Los|Y|En|A|Al|O)\b', lambda m: m.group(0).lower(), low)
        low = re.sub(r'\bCiclo ([abc])\b', lambda m: 'Ciclo ' + m.group(1).upper(), low, flags=re.I)
        low = re.sub(r'\b(Ii|Iii|Iv|Vi|Vii|Viii|Ix|Xi|Xii)\b', lambda m: m.group(0).upper(), low)
        t = low[0].upper() + low[1:] if low else low
    t = t.replace('Sabado', 'Sábado').replace('Miercoles', 'Miércoles').replace('Epifania', 'Epifanía').replace('Santisim', 'Santísim')
    t = t.replace('Maria ', 'María ').replace('Maria$', 'María')
    return t

def unit_blocks(bid, u, uid):
    """Bloques limpios de una meditación: [(kind, html, ids)] ; kind: p, sm (resumen), h3, h4, note."""
    bl = parse_blocks(u['raw'])
    # objetivos de enlaces internos
    targets = set()
    for b in bl:
        for x in b['parts']:
            if isinstance(x, tuple) and x[0] == 'A': targets.add(x[1])
    out = []
    for b in bl:
        txt = plain(b['parts']).strip()
        cls = b['cls'].split(); tag = b['tag']
        if not txt: continue
        if bid == 'HCD7' and 'ref' in cls: continue                       # [Siguiente día]
        if bid == 'HCD7' and 'ind' in cls: continue                       # listas de enlaces de las portadillas
        note = bool(set(b['ids']) & targets) and bool(FN_RX.match(txt))
        # html con notas
        h = []; in_a = None
        for x in b['parts']:
            if isinstance(x, tuple):
                if x[0] == 'A': in_a = x[1]; h.append(('A', x[1]))
                else: h.append(('/A',)); in_a = None
            else: h.append(x)
        s = ''
        i = 0
        while i < len(h):
            x = h[i]
            if isinstance(x, tuple) and x[0] == 'A':
                # recoger el texto del enlace
                j = i + 1; inner = ''
                while j < len(h) and not (isinstance(h[j], tuple) and h[j][0] == '/A'):
                    if isinstance(h[j], str): inner += h[j]
                    j += 1
                itxt = re.sub(r'<[^>]+>', '', inner).strip()
                if not note and re.match(r'^\[?\s*\d{1,3}\s*\]?$', itxt) and x[1] in targets:
                    num = re.sub(r'[^\d]', '', itxt)
                    s += '<a class="fn" data-f="%s_%s">%s</a>' % (uid, re.sub(r'[^\w-]', '', x[1]), num)
                else:
                    s += re.sub(r'</?(sup)>', '', inner) if note else inner
                i = j + 1
                continue
            if isinstance(x, str): s += x
            i += 1
        s = tidy_inline(s)
        s = re.sub(r'<sup>\s*(<a class="fn"[^>]*>\d+</a>)\s*</sup>', r'\1', s)
        if not s: continue
        if note:
            nid = next(i_ for i_ in b['ids'] if i_ in targets)
            num = re.search(r'\d+', txt).group(0)
            s = re.sub(r'\[\s*%s\s*\]' % num, '', s, count=1)
            s = tidy_inline(re.sub(r'<(sup|i|b)>\s*</\1>', '', s))
            s = '<b>%s.</b> %s' % (num, s)
            out.append(('note', s, '%s_%s' % (uid, re.sub(r'[^\w-]', '', nid))))
            continue
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'): kind = 'h'
        elif 'peq' in cls or 'entradilla' in cls or tag == 'blockquote': kind = 'sm'
        elif 'tit' in cls or 'fies' in cls: kind = 'h3'
        elif 'neg' in cls and txt.lower().startswith('notas'): kind = 'h4'
        else: kind = 'p'
        out.append((kind, s, None))
    # quitar el título original (lo sustituye el nuestro)
    if bid == 'MedOD':
        for k in range(min(4, len(out))):
            t = plain([out[k][1]]).strip()
            if re.match(r'^\d{1,4}\.?\s', t) and len(t) < 200:
                out = out[k + 1:]; break
        # resumen inicial: líneas cortas antes del primer párrafo largo
        k = 0
        while k < len(out) and k < 5 and out[k][0] == 'p' and len(plain([out[k][1]])) < 260: k += 1
        if 0 < k <= 5 and k < len(out): out = [('sm', o[1], o[2]) if i_ < k else o for i_, o in enumerate(out)]
    elif bid in ('SCE', 'HCD7'):
        if out and out[0][0] == 'h': out = out[1:]
    return out

def heading_date(u):
    ps = [html.unescape(re.sub(r'<[^>]+>', '', p)).strip() for p in re.findall(r'<p\b[^>]*>(.*?)</p>', u['raw'], re.S)]
    ps = [p for p in ps if p][:3]
    for h in ps:
        t = nrm(re.sub(r'^\d+\.?\s*"?', '', h)).strip('"')
        d = find_date(t)
        if d: return d
    return None

def build_book(bid, title, author, units, vol_names, chunk_kb=260):
    """Devuelve (chunks, meta, entries)."""
    idx = 1
    def nxt():
        nonlocal idx
        idx += 1; return idx - 1
    meds = []      # (title, html, off, keys, cyc, vol, parents)
    for n, u in enumerate(units):
        if is_skip_unit(bid, u): continue
        keys = list(u['keys']); cyc = u['cyc']
        if bid == 'MedOD':
            hd = heading_date(u)
            if hd and any(k.startswith('F') for k in keys) and hd not in keys:
                keys = [hd if k.startswith('F') else k for k in keys]
        t = nice_title(bid, u) if u['label'] else ''
        bl = unit_blocks(bid, u, '%s%d' % (bid, n))
        if not bl: continue
        if not t:
            t = plain([bl[0][1]])[:80]; bl = bl[1:]
        off = nxt()
        parts = ['<h2 id="o%d" data-o="%d">%s</h2>' % (off, off, html.escape(t))]
        for kind, s, nid in bl:
            o = nxt()
            if kind == 'note': parts.append('<p class="fnn" id="n%s" data-o="%d">%s</p>' % (nid, o, s))
            elif kind == 'h': parts.append('<h3 data-o="%d">%s</h3>' % (o, s))
            elif kind == 'h3': parts.append('<h3 data-o="%d">%s</h3>' % (o, s))
            elif kind == 'h4': parts.append('<h4 class="fnh" data-o="%d">%s</h4>' % (o, s))
            elif kind == 'sm': parts.append('<p class="sm" data-o="%d">%s</p>' % (o, s))
            else: parts.append('<p data-o="%d">%s</p>' % (o, s))
        meds.append({'t': t, 'h': '\n'.join(parts), 'o': off, 'k': keys, 'c': cyc, 'vol': u['vol'], 'par': u['parents'], 'is_med': bool(keys) or len(bl) > 8})
    # índice (trozo 0)
    toc = ['<p data-o="0" style="text-align:center"><b><span style="font-size:1.3em">%s</span></b></p>' % html.escape(title)]
    if author: toc.append('<p style="text-align:center" class="sm">%s</p>' % html.escape(author))
    toc.append('<h2>Índice</h2>')
    last_sec = None
    for m in meds:
        sec = section_of(bid, m, vol_names)
        if sec != last_sec:
            toc.append('<h3>%s</h3>' % html.escape(sec)); last_sec = sec
        toc.append('<p class="toc"><a href="#/d/%s/%d">%s</a></p>' % (bid, m['o'], html.escape(m['t'])))
    chunks = ['\n'.join(toc)]; starts = [0]
    cur = []; cur_len = 0; cur_start = None
    for m in meds:
        if cur and cur_len + len(m['h']) > chunk_kb * 1024:
            chunks.append('\n'.join(cur)); starts.append(cur_start); cur = []; cur_len = 0
        if not cur: cur_start = m['o']
        cur.append(m['h']); cur_len += len(m['h'])
    if cur: chunks.append('\n'.join(cur)); starts.append(cur_start)
    # navegación al final de cada trozo
    N = len(chunks)
    for k in range(1, N):
        nav = '<p class="toc dnx"><a href="#/dp/%s/0">☰ Índice</a>%s</p>' % (bid, (' · <a href="#/dp/%s/%d">Seguir leyendo →</a>' % (bid, k + 1)) if k + 1 < N else '')
        chunks[k] = chunks[k] + '\n' + nav
    starts[0] = 0
    if len(starts) > 1 and starts[1] == 0: raise SystemExit('offsets')
    meta = {'title': title, 'starts': starts, 'x': {}, 'v': hashlib.md5(''.join(chunks).encode()).hexdigest()[:8], 'kb': sum(len(c.encode()) for c in chunks) // 1024}
    entries = [[m['o'], m['t'], m['k'], m['c']] for m in meds if m['k']]
    return chunks, meta, entries

def section_of(bid, m, vol_names):
    if bid == 'MedOD':
        par = [p for p in m['par'] if p]
        return ' · '.join(par[:2]) if par else 'Presentación'
    if bid == 'SCE':
        return vol_names[m['vol'] - 1]
    if bid == 'HCD7':
        par = [p for p in m['par'] if p and not p.startswith('Hablar con Dios')]
        v = vol_names[m['vol'] - 1]
        return v + (' · ' + par[-1] if par else '')
    return ''
