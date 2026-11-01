#!/usr/bin/env python3
"""
Genera la app «Diario» (con meditación diaria) a partir de la app «Epacta» (carpeta «Diario app», sin tocarla) y de los ePub de meditaciones.

Uso:   python generar.py                      (rutas de config.json)
       python generar.py --diario "C:/.../Diario app" --medis "C:/.../medis" --destino ".."

Qué hace:
  1. Copia de la app Diario a la carpeta destino lo que haya cambiado (index de base, data/, docs/, iconos);
     nunca escribe en la carpeta de la app Diario.
  2. Convierte los ePub (Meditaciones 7 tomos, Siempre con Él 1-9, Hablar con Dios 1-7) en tres libros
     de la app (docs/MedOD, docs/SCE) y crea el índice de meditaciones por día litúrgico.
  3. Parchea el index.html: botón «Meditación diaria» en la portada, pantalla del día, libros nuevos en
     «Libros», resaltado de texto en todos los libros y pantalla «Mis resaltados».
  4. Escribe sw.js y manifest propios (caché independiente de la app Diario).
Sin librerías externas: Python 3.8 o superior.
"""
import os, sys, re, json, glob, shutil, hashlib, argparse, time, base64
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'lib'))
from epublib import read_epub
from classify import classify
from buildbooks import build_book
from hcd_diario import entradas_hcd
import valtorta
import elyo

T0 = time.time()
def log(*a): print('[%3ds]' % (time.time() - T0), *a, flush=True)

VOLN = {'SCE': ['1. Tiempo Ordinario, semanas I-VI', '2. Cuaresma y Semana Santa', '3. Pascua', '4. Tiempo Ordinario, semanas VII-XIII',
                '5. Tiempo Ordinario, semanas XIV-XX', '6. Tiempo Ordinario, semanas XXI-XXVII', '7. Tiempo Ordinario, semanas XXVIII-XXXIV',
                '8. Adviento y Navidad', '9. Fiestas y santos'],
        'HCD7': ['Tomo I', 'Tomo II', 'Tomo III', 'Tomo IV', 'Tomo V', 'Tomo VI', 'Tomo VII'], 'MedOD': []}
SCE_HINT = {1: 'tiempo ordinario', 2: 'cuaresma', 3: 'pascua', 4: 'tiempo ordinario', 5: 'tiempo ordinario', 6: 'tiempo ordinario',
            7: 'tiempo ordinario', 8: 'adviento', 9: ''}
BOOKS = [('MedOD', 'Meditaciones (7 tomos)', '', 'Meditaciones*.epub', None),
         ('SCE', 'Siempre con Él', 'Fulgencio Espa y otros', 'Siempre con*.epub', r'l (\d+)\.'),
        ]   # «Hablar con Dios»: se usa el libro que ya trae el Diario (docs/HCD), con sus enlaces

def libro(bid, files):
    units = []
    for vi, f in enumerate(files, 1):
        for u in read_epub(f):
            k, c = classify(u['label'], u['parents'], SCE_HINT[vi] if bid == 'SCE' else '')
            u.update(vol=vi, keys=k, cyc=c); units.append(u)
    return units

def write_if_changed(path, data):
    b = data.encode('utf-8') if isinstance(data, str) else data
    if os.path.exists(path) and open(path, 'rb').read() == b: return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f: f.write(b)
    return True

def sync_tree(src, dst, keep=()):
    """Copia src -> dst solo lo que cambia (tamaño o fecha). Devuelve nº de archivos copiados."""
    n = 0
    for root, dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        top = rel.split(os.sep)[0]
        if top in keep: continue
        for f in files:
            s = os.path.join(root, f); d = os.path.join(dst, rel, f)
            try:
                if os.path.exists(d):
                    a, b = os.stat(s), os.stat(d)
                    if a.st_size == b.st_size and int(a.st_mtime) <= int(b.st_mtime): continue
                os.makedirs(os.path.dirname(d), exist_ok=True); shutil.copy2(s, d); n += 1
            except OSError as e: print('   aviso: no se pudo copiar', s, e)
    return n

# ------------------------------------------------------------------ parches del index.html
def parchear(src, metas, medi, js, VAL=None, EY=None, ATL=None):
    def rep(old, new, count=1):
        nonlocal src
        if src.count(old) != count:
            sys.exit('No encuentro en index.html el trozo a modificar (%d veces, esperaba %d):\n   %s\n¿Ha cambiado la app Diario? Hay que adaptar generar.py.' % (src.count(old), count, old[:100]))
        src = src.replace(old, new)
    if EY:
        me = re.search(r'\nconst EY=(\{.*?\});\n', src, re.S)
        if me: src = src[:me.start(1)] + json.dumps(EY, ensure_ascii=False, separators=(',', ':')) + src[me.end(1):]
        # número del apunte (sin el decimal que distingue capítulos)
        src = src.replace('<div class="ph"><b>${p[0]}</b>', '<div class="ph"><b>${Math.floor(p[0])}</b>')
        src = src.replace("(first?'**'+p[0]+'.** ':'')", "(first?'**'+Math.floor(p[0])+'.** ':'')")
        src = src.replace("(first?'{\\\\b '+p[0]+'.} ':'')", "(first?'{\\\\b '+Math.floor(p[0])+'.} ':'')")
    m = re.search(r'const CAT=(\{.*?\});\nconst DAY=', src, re.S)
    if not m: sys.exit('No encuentro CAT/DAY en el index.html del Diario.')
    C = json.loads(m.group(1))
    for k, v in metas.items(): C['docs'][k] = v
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':'))
    src = src.replace('const CAT=' + m.group(1) + ';\n', 'const CAT=' + J(C) + ';\nconst MEDI=' + J(medi) + ';\nconst VAL=' + J(VAL or {}) + ';\nconst ATL=' + J(ATL) + ';\n', 1)
    # nombre de la app: «Diario» (la app de origen se llama ahora «Epacta»)
    src = re.sub(r'<title>[^<]*</title>', '<title>Diario</title>', src, count=1)
    src = re.sub(r'<h1 id="ht">[^<]*</h1>', '<h1 id="ht">Diario</h1>', src, count=1)
    src = re.sub(r"setHead\('(?:Epacta|Diario)',iso===today\?'':'#/'\)", "setHead('Diario',iso===today?'':'#/')", src, count=1)
    rep('<meta name="theme-color" content="#101a2a">', '<meta name="theme-color" content="#101a2a">\n<meta name="description" content="Diario con meditación diaria">')
    rep("const TITLES={", "const TITLES={MedOD:'Meditaciones (7 tomos)',SCE:'Siempre con Él',Valtorta:'María Valtorta · La vida de Jesús',")
    rep('</style>', CSS + '</style>')
    rep('<button id="hh" aria-label="Inicio">⌂</button>', '<button id="hval" aria-label="Mostrar u ocultar los pasajes de María Valtorta" title="Pasajes en María Valtorta" style="display:none"></button><button id="hh" aria-label="Inicio">⌂</button>')
    rep('<div id="sheet">', '<div id="hlb"><button class="btn" id="hlb-do">🖍 Resaltar</button><button class="btn" id="hlb-cp">Copiar</button></div>\n<div id="pop"></div>\n<div id="sheet">')
    # portada: botón nuevo justo debajo de «Sagrada Escritura»
    rep('''<div class="row one"><a class="btn" href="#/biblia">📖 Sagrada Escritura</a></div>''',
        '''<div class="row one"><a class="btn" href="#/biblia">📖 Sagrada Escritura</a></div><div class="row one med"><a class="btn" href="#/med/\'+iso+\'">🙏 Meditación diaria</a></div>''')
    # Valtorta: punto naranja en las lecturas del día y en los capítulos de los Evangelios
    rep("h+=D.r.map(r=>r[0]?`<a class=\"rd\" href=\"${r[0]}\"><b>${esc(r[1])}${esc(r[2])}</b><span>${esc(r[3])}</span></a>`:`<div class=\"rd\"><span>${esc(r[1])}</span></div>`).join('');",
        "h+=D.r.map(rdHtml).join('');")
    rep("M.querySelectorAll('.vs').forEach(e=>{if(hl[b+':'+c+':'+e.dataset.v])e.classList.add('hl');e.addEventListener('click',ev=>{if(ev.target.closest('a'))return;toggleSel(e)})});",
        "M.querySelectorAll('.vs').forEach(e=>{if(hl[b+':'+c+':'+e.dataset.v])e.classList.add('hl');e.addEventListener('click',ev=>{if(ev.target.closest('a'))return;toggleSel(e)})});valDots(b,c);")
    # rutas
    rep("  else if(k==='docs'){setHead('Libros enlazados','#/','doc');renderDocs()}",
        "  else if(k==='docs'){setHead('Libros','#/','doc');renderDocs()}\n  else if(k==='med'){renderMed(h[1])}\n  else if(k==='resaltados'){renderUH()}\n  else if(k==='mapa'){renderMapa(h[1],h[2])}\n  else if(k==='viajes'){renderViajes(h[1])}\n  else if(k==='lugares'){renderLugares()}\n  else if(k==='lugar'){renderLugar(h[1])}")
    rep("$('#fab').style.display='';$('#sfab').style.display='none';$('#hstar').style.display='none';bar(null);window.scrollTo(0,0);",
        "$('#fab').style.display='';$('#sfab').style.display='none';$('#hstar').style.display='none';bar(null);window.scrollTo(0,0);uhCur=null;$('#hval').style.display='none';$('#hlb').classList.remove('on');$('#pop').classList.remove('on');")
    rep("if(doc==='ElYo')eyMarkAll();if(o.i!==undefined)focusPar(o.i,o.q);",
        "if(doc==='ElYo')eyMarkAll();hcdSep(doc);noTTS();uhApply(doc,k);if(o.i!==undefined)focusPar(o.i,o.q);")
    # pantalla Libros
    a = src.index('function renderDocs(){'); b = src.index('\n', a)
    src = src[:a] + RENDER_DOCS + src[b:]
    rep('function renderDocs(){', js + '\nfunction renderDocs(){')
    return src

CSS = r'''
:root{--uh:rgba(143,178,255,.26);--uhb:rgba(143,178,255,.75)}
body[data-theme=light]{--uh:rgba(29,79,184,.13);--uhb:rgba(29,79,184,.55)}
body[data-theme=sepia]{--uh:rgba(138,75,18,.16);--uhb:rgba(138,75,18,.6)}
.doc mark.uh,.uht{background:var(--uh);color:inherit;border-radius:3px;box-shadow:inset 0 -2px 0 var(--uhb);-webkit-box-decoration-break:clone;box-decoration-break:clone;cursor:pointer}
.doc mark.uh mark{background:var(--hl)}
#hlb{position:fixed;left:12px;right:84px;bottom:calc(16px + env(safe-area-inset-bottom));z-index:30;display:none;gap:8px;max-width:520px}
#hlb.on{display:flex}
/* sin guionado automático: en Chrome Android descoloca los tiradores de la selección */
.doc.just p,.doc p{-webkit-hyphens:manual;hyphens:manual}#hlb{-webkit-user-select:none;user-select:none}#hlb .btn{flex:1;min-height:48px;font-size:17px;box-shadow:0 4px 14px #0006}#hlb .btn:first-child{background:var(--link);color:var(--bg);border-color:var(--link)}
#pop{position:fixed;left:12px;right:12px;bottom:calc(16px + env(safe-area-inset-bottom));z-index:45;display:none;background:var(--card);border:1px solid var(--bd);border-radius:16px;padding:14px 40px 14px 16px;box-shadow:0 6px 24px #0008;max-width:736px;margin:0 auto;max-height:50vh;overflow:auto}
#pop.on{display:block}#pop .x{position:absolute;top:8px;right:6px}.pnote{font:16px/1.5 var(--ff)}.pnote b:first-child{color:var(--link);margin-right:.3em}.pact{display:flex;gap:10px}.pact .btn{flex:1;min-height:46px;font-size:16px}
.doc a.fn{font:600 .62em/1 var(--ui);vertical-align:super;color:var(--link);text-decoration:none;padding:3px 3px;margin-left:1px;cursor:pointer}
.doc p.sm{color:var(--mut);font-size:.9em;line-height:1.45;margin:.25em 0 .25em 1em}
.doc p.fnn{font-size:.8em;line-height:1.4;color:var(--mut);margin:.3em 0;text-align:left}
.doc h4.fnh{font:700 12px var(--ui);letter-spacing:.08em;text-transform:uppercase;color:var(--mut);margin:2em 0 .4em;padding-top:.8em;border-top:1px solid var(--bd)}
.doc h3{font:600 .9em/1.35 var(--ui);letter-spacing:.03em;color:var(--link);margin:1em 0 .6em}
.doc p.dnx{margin:2.4em 0 1em;text-align:center;font:600 16px var(--ui)}
.row.one.med{margin-top:12px}
.rdw{position:relative}.rdw .rd{padding-right:30px}.rdw:not(:last-of-type) .rd{border-bottom:1px solid var(--bd)}.card .rdw:last-of-type .rd{border-bottom:0}
.vdot,#hval{background:#e8862b;border-radius:50%;display:inline-block;box-shadow:0 0 0 2px var(--bg)}
.vhd{position:absolute;right:-6px;top:2px;width:44px;height:44px;background:none;box-shadow:none;border-radius:0;z-index:2}.vhd::after{content:'';position:absolute;right:10px;top:12px;width:16px;height:16px;border-radius:50%;background:#e8862b;box-shadow:0 0 0 2px var(--card)}
.vdot{display:none;width:.62em;height:.62em;margin:0 .35em 0 0;vertical-align:.08em;cursor:pointer}.vdot.al{background:transparent;box-shadow:inset 0 0 0 2px #e8862b}
#txt.von .vdot{display:inline-block}
header #hval{width:24px;height:24px;min-width:24px;border:0;padding:0;margin:0 10px 0 4px;cursor:pointer;opacity:.5;transition:opacity .2s;flex:none}header #hval.on{opacity:1;box-shadow:0 0 0 2px var(--bar),0 0 0 4px #e8862b}
.doc .vrf{font:600 13px/1.5 var(--ui);margin:1.1em 0 .2em;padding:3px 0 3px 10px;border-left:3px solid #e8862b;color:var(--mut)}.doc .vrf a{color:#e8862b;text-decoration:none;white-space:nowrap}.doc .vrf a.al{font-weight:400;font-style:italic}
.doc b.mtit{display:block;margin-top:1.6em;padding-top:1em;border-top:1px solid var(--bd)}.doc p.mtitp{margin-top:2.2em;padding-top:1em;border-top:1px solid var(--bd)}
.mtop .dhero{text-align:center}.mtop .dnum{font-size:clamp(72px,20vw,120px)}.mtop .dmon{font-size:clamp(22px,5.8vw,32px)}
.mbh{display:flex;align-items:baseline;justify-content:space-between;gap:10px;flex-wrap:wrap}.mbh .sh{margin:0;font-size:15px}.mbh .cap{margin:0}
.mrd b{font:600 12px var(--ui);letter-spacing:.05em;text-transform:uppercase;color:var(--mut)}.mrd span{color:var(--link);font-weight:600}
.mbk .cm{margin-top:10px}
.bkm{display:grid;grid-template-columns:1fr;gap:10px;margin:0 0 8px}.bkm .btn{justify-content:flex-start;text-align:left;gap:14px;padding:12px 16px}.bkm .btn small{display:block;font:400 14px var(--ui);color:var(--mut);margin-top:2px}.bkm .ic{font-size:26px}
.uhi{position:relative;padding:12px 30px 12px 4px;border-bottom:1px solid var(--bd)}.uhi a{color:var(--fg);text-decoration:none;display:block;font:17px/1.5 var(--ff)}.uhi b{display:block;font:600 14px var(--ui);color:var(--link);margin-bottom:4px}.uhi small{display:block;margin-top:4px;font-size:13px}.uhi .x{position:absolute;right:0;top:10px}
.uhf{flex-wrap:wrap}.uhf .btn{flex:0 1 auto;padding:6px 12px;min-height:36px;font-size:14px}
.rdw .vloc{display:block;margin:-6px 0 8px;padding:0 34px 2px 0;font:500 13px/1.35 var(--ui);color:#e8862b;text-decoration:none}
#txt .vpl{display:none;margin:.9em 0 .2em;font:600 13px/1.4 var(--ui);color:#e8862b;text-decoration:none}#txt.von .vpl{display:block}
.doc .vwh{font:600 13px/1.45 var(--ui);margin:1.2em 0 .25em;padding:4px 0 4px 10px;border-left:3px solid #4f9d69;color:var(--mut)}.doc .vwh a{color:#4f9d69;text-decoration:none;margin-right:.5em}.doc .vwh span{font-weight:400}
.doc .vatl{display:flex;flex-wrap:wrap;justify-content:center;gap:8px 18px;font:600 15px var(--ui)}.doc .vatl a{text-decoration:none}
.atlr .btn{font-size:15px}
.atl{margin:-8px -8px 0}
.achips{display:flex;gap:6px;overflow-x:auto;padding:2px 2px 10px;scrollbar-width:none;-webkit-overflow-scrolling:touch}.achips::-webkit-scrollbar{display:none}
.achips .chip{flex:none;font:600 13px var(--ui);padding:7px 12px;border-radius:16px;border:1px solid var(--bd);background:var(--card);color:var(--fg);cursor:pointer;user-select:none;-webkit-user-select:none;border-left:4px solid var(--mut)}
.achips .chip.tG{border-left-color:#4f9d69}.achips .chip.tJ{border-left-color:#e8862b}.achips .chip.on{background:var(--link);color:var(--bg);border-color:var(--link)}
.mapw{position:relative;height:min(58vh,620px);border:1px solid var(--bd);border-radius:14px;overflow:hidden;background:var(--card)}
#amap{width:100%;height:100%;display:block;touch-action:none;user-select:none;-webkit-user-select:none;cursor:grab}
#amap{--asea:#3b6279;--ariv:#6497b8}body[data-theme=light] #amap{--asea:#c3dfee;--ariv:#6ea5c8}body[data-theme=sepia] #amap{--asea:#bdd5db;--ariv:#6c9cb0}
#amap .aland{fill:var(--card)}#amap .asea{fill:var(--asea)}#amap .acoast{fill:none;stroke:var(--ariv);stroke-opacity:.8;stroke-width:1.2;vector-effect:non-scaling-stroke}
#amap .alake{fill:var(--asea);stroke:var(--ariv);stroke-opacity:.8;stroke-width:1;vector-effect:non-scaling-stroke}
#amap .ariv{fill:none;stroke:var(--ariv);stroke-opacity:.9;stroke-width:1.6;stroke-linejoin:round;stroke-linecap:round;vector-effect:non-scaling-stroke}
#amap .areg text{font:600 calc(var(--s,1)*12px) var(--ui);letter-spacing:.25em;fill:var(--mut);opacity:.75;text-anchor:middle;paint-order:stroke;stroke:var(--card);stroke-width:2px;stroke-opacity:.6}
#amap .amt path{fill:var(--mut);opacity:0}#amap .amt text{font:italic calc(var(--s,1)*10px) var(--ff);fill:var(--mut);opacity:.7}
#amap .awat text{font:italic calc(var(--s,1)*12px) var(--ff);fill:var(--fg);opacity:.55;text-anchor:middle;letter-spacing:.08em}
#amap .asyr rect{fill:none;stroke:var(--mut);stroke-dasharray:4 4;stroke-opacity:.6;vector-effect:non-scaling-stroke}#amap .asyr text{font:calc(var(--s,1)*9px) var(--ui);fill:var(--mut);text-anchor:middle}
#amap .ascale path{stroke:var(--fg);stroke-width:1.5;fill:none;vector-effect:non-scaling-stroke}#amap .ascale text{font:11px var(--ui);fill:var(--mut)}#amap .anor{font:700 calc(var(--s,1)*12px) var(--ui);fill:var(--mut)}
.doc .vwh+p{scroll-margin-top:3.5em}
#amap .aseg{fill:none;stroke:var(--mut);stroke-opacity:.35;stroke-width:1.6;stroke-dasharray:3 4;vector-effect:non-scaling-stroke;stroke-linecap:round}
#amap .aseg.done{stroke:#e8862b;stroke-opacity:.9;stroke-width:2.6;stroke-dasharray:none}#amap .aseg.done.boat{stroke-dasharray:6 4}#amap .aseg.last{stroke-width:3.6}
#amap .aseg.all{stroke:#e8862b;stroke-opacity:.22;stroke-width:1.2;stroke-dasharray:none}
#amap .apt{fill:var(--bg);stroke:var(--mut);stroke-width:1.4;vector-effect:non-scaling-stroke}#amap .apt.done{fill:#e8862b;stroke:var(--bg)}#amap .apt.sel{fill:var(--link);stroke:var(--bg);stroke-width:2}
#amap .alb{font-family:var(--ui);font-weight:600;fill:var(--fg);paint-order:stroke;stroke:var(--card);stroke-width:3px;stroke-linejoin:round;pointer-events:none}#amap .alb.fut{fill:var(--mut);font-weight:400}#amap .alb.cur{fill:#e8862b;font-weight:700}
#amap .acurd{fill:#e8862b;stroke:var(--bg);stroke-width:2;vector-effect:non-scaling-stroke}
#amap .apulse{fill:#e8862b;fill-opacity:.25;stroke:#e8862b;stroke-width:1.5;vector-effect:non-scaling-stroke;transform-box:fill-box;transform-origin:center;animation:apul 1.6s ease-out infinite}
@keyframes apul{0%{transform:scale(.6);opacity:1}100%{transform:scale(2.2);opacity:0}}
.mz{position:absolute;right:8px;bottom:8px;display:flex;flex-direction:column;gap:6px}.mz .btn{width:40px;height:40px;min-height:40px;padding:0;font-size:20px;opacity:.92;box-shadow:0 2px 8px #0004}
.mapc{margin-top:10px}.mapc .sh{font-size:16px}
.astep{display:flex;align-items:center;gap:8px;margin:10px 0 8px}.astep .btn{width:48px;min-height:44px;padding:0;font-size:20px;flex:none}.astep .anum{flex:1;text-align:center;font:600 15px var(--ui);color:var(--mut)}
.aplace b{font:700 18px var(--ui);color:#e8862b;margin-right:8px}.aplace .cap{display:inline}
.atit{font:17px/1.5 var(--ff);margin:6px 0 4px}
.ach{font:600 12px var(--ui);letter-spacing:.06em;text-transform:uppercase;color:var(--mut);margin:14px 0 2px}
.ard b{font:500 13px var(--ui);color:var(--mut)}.ard span{color:var(--fg)}
.aribbon{display:flex;height:30px;border-radius:8px;overflow:hidden;margin:12px 0 6px;gap:2px}.aribbon a{display:flex;align-items:center;justify-content:center;font:700 12px var(--ui);color:#fff;text-decoration:none;min-width:14px}
.aribbon .tG,.aleg .tG::before{background:#4f9d69}.aribbon .tJ,.aleg .tJ::before{background:#e8862b}.aribbon .tC,.aleg .tC::before{background:var(--mut)}
.aleg{display:flex;gap:16px;font:13px var(--ui);color:var(--mut);margin-bottom:12px}.aleg span::before{content:'';display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px}
.acy{border-left:4px solid var(--mut)}.acy.tG{border-left-color:#4f9d69}.acy.tJ{border-left-color:#e8862b}
.acy details{margin-top:10px}.acy summary{font:600 15px var(--ui);color:var(--link);cursor:pointer;padding:6px 0}
.arow{padding:9px 0;border-bottom:1px solid var(--bd)}.arow .apl{font:700 15px var(--ui);color:#e8862b;text-decoration:none;margin-right:8px}.arow small{font:13px var(--ui);color:var(--mut)}.arow .atl2{display:block;font:16px/1.45 var(--ff);color:var(--fg);text-decoration:none;margin-top:2px}
.afest{margin:10px 0 2px;font:700 13px var(--ui);color:var(--link);letter-spacing:.03em}
.alug{display:flex;justify-content:space-between;align-items:center}.alug b{font:600 13px var(--ui);color:var(--mut);background:var(--bg);border-radius:10px;padding:2px 8px}
'''

RENDER_DOCS = r'''function renderDocs(){const MB=['MedOD','SCE','HCD','Valtorta'].filter(d=>DOCS[d]),IC={MedOD:'🕯️',SCE:'📿',HCD:'🙏',Valtorta:'🌿'},SUB={MedOD:'Libro de meditaciones · 7 tomos',SCE:'F. Espa y otros · 9 tomos en uno',HCD:'F. Fernández-Carvajal · con enlaces a la Biblia',Valtorta:'Escenas enlazadas con los Evangelios'};const names=Object.keys(DOCS).filter(d=>!MB.includes(d));const nu=uhGroups().length;
  $('#main').innerHTML='<h2 class="t">Libros</h2><h3 class="thm" style="margin-top:0">Libros de meditación</h3><div class="bkm">'+MB.map(d=>`<a class="btn bk" href="#/dp/${d}/0"><span class="ic">${IC[d]}</span><span>${esc(dTitle(d))}<small>${SUB[d]} · ${Math.round(DOCS[d].kb/102.4)/10} MB</small></span></a>`).join('')+'</div>'+(ATL?'<div class="row atlr"><a class="btn" href="#/mapa">🗺 Mapa</a><a class="btn" href="#/viajes">📜 Cronología</a><a class="btn" href="#/lugares">📍 Lugares</a></div><p class="mut" style="margin:2px 0 12px;font-size:14px">Los viajes de Jesús según María Valtorta, a partir del atlas de J. Webster.</p>':'')+'<div class="row" style="margin-top:4px"><a class="btn" href="#/med">🙏 Meditación de hoy</a><a class="btn" href="#/resaltados">🖍 Mis resaltados'+(nu?' ('+nu+')':'')+'</a></div><p class="mut" style="margin:14px 0 0">En cualquier libro puedes buscar con 🔍 y resaltar: selecciona un texto y pulsa «🖍 Resaltar».</p><h3 class="thm">Comentarios y libros enlazados</h3><p class="mut">Se abren también desde los números de versículo de la Biblia y desde los enlaces del propio texto.</p><div class="grid">'+names.map(d=>`<a class="btn bk" href="#/dp/${d}/0" style="flex-direction:column"><span>${esc(dTitle(d))}</span><small class="mut">${Math.round(DOCS[d].kb/102.4)/10} MB</small></a>`).join('')+'</div>'}'''

def parchear_sw(txt, metas, cat_docs):
    m = re.search(r"const DOCV=(\{.*?\});", txt)
    if not m: sys.exit('No encuentro DOCV en sw.js del Diario.')
    docv = json.loads(m.group(1))
    for k, v in cat_docs.items(): docv[k] = v['v']
    txt = txt.replace(m.group(0), 'const DOCV=' + json.dumps(docv, ensure_ascii=False) + ';')
    txt = re.sub(r"const CACHE='[^']*';", "const CACHE='diariomed';", txt)
    txt = txt.replace("for(const k of await caches.keys())if(k!==CACHE)await caches.delete(k);",
                      "for(const k of await caches.keys())if(k!==CACHE&&k.startsWith('diariomed'))await caches.delete(k);")
    b = hashlib.md5(json.dumps(docv, sort_keys=True).encode() + txt.encode()).hexdigest()[:10]
    txt = re.sub(r"const BUILD='[^']*';", "const BUILD='m%s';" % b, txt)
    return txt.replace('/* Generado automaticamente por actualizar.py - no editar a mano */', '/* Generado por actualizador_meditacion/generar.py - no editar a mano */')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--diario'); ap.add_argument('--medis'); ap.add_argument('--destino')
    ap.add_argument('--sin-copiar', action='store_true', help='no sincroniza data/ y docs/ desde el Diario')
    a = ap.parse_args()
    cfgp = os.path.join(HERE, 'config.json'); cfg = json.load(open(cfgp, encoding='utf-8')) if os.path.exists(cfgp) else {}
    rel = lambda p: p if os.path.isabs(p) else os.path.normpath(os.path.join(HERE, p))
    DIA = rel(a.diario or cfg.get('diario', '../../Diario app')); MED = rel(a.medis or cfg.get('medis', 'C:/Users/alina/Desktop/medis'))
    DST = rel(a.destino or cfg.get('destino', '..'))
    if os.path.normcase(os.path.abspath(DIA)) == os.path.normcase(os.path.abspath(DST)): sys.exit('El destino no puede ser la carpeta de la app Diario.')
    if not os.path.exists(os.path.join(DIA, 'index.html')): sys.exit('No encuentro %s/index.html' % DIA)
    log('Diario:', DIA); log('ePub:', MED); log('Destino:', DST)
    # 1. copiar lo de la app Diario
    if not a.sin_copiar:
        n = 0
        for f in ('icon-192.png', 'icon-512.png', 'catalog.json'):
            if os.path.exists(os.path.join(DIA, f)):
                s, d = os.path.join(DIA, f), os.path.join(DST, f)
                if not os.path.exists(d) or os.stat(s).st_size != os.stat(d).st_size: shutil.copy2(s, d); n += 1
        n += sync_tree(os.path.join(DIA, 'data'), os.path.join(DST, 'data'))
        n += sync_tree(os.path.join(DIA, 'docs'), os.path.join(DST, 'docs'), keep=('MedOD', 'SCE', 'Valtorta'))
        log('copiados desde el Diario: %d archivos' % n)
    # 2. libros de meditación
    metas, medi = {}, {}
    for bid, title, author, pat, numrx in BOOKS:
        files = glob.glob(os.path.join(MED, pat))
        if bid == 'HCD7': files = [f for f in files if re.search(numrx, os.path.basename(f))]
        if numrx: files.sort(key=lambda f: int(re.search(numrx, os.path.basename(f)).group(1)))
        if not files: sys.exit('No encuentro los ePub de %s (%s) en %s' % (title, pat, MED))
        log('%s: %d ePub' % (title, len(files)))
        chunks, meta, entries = build_book(bid, title, author, libro(bid, files), VOLN[bid])
        dd = os.path.join(DST, 'docs', bid); ch = 0
        for k, c in enumerate(chunks): ch += write_if_changed(os.path.join(dd, '%d.html' % k), c)
        for f in glob.glob(os.path.join(dd, '*.html')):
            if int(os.path.basename(f).split('.')[0]) >= len(chunks):
                try: os.remove(f)
                except OSError: pass
        metas[bid] = meta; medi[bid] = entries
        log('   %d trozos (%d cambiados), %d KB, %d meditaciones con día asignado' % (len(chunks), ch, meta['kb'], len(entries)))
    # Valtorta
    VAL = {}; ATL = None
    vep = rel(cfg.get('valtorta', 'valtorta/Valtorta_La_vida_de_Jesus.epub'))
    if os.path.exists(vep):
        atp = os.path.join(HERE, 'valtorta_atlas.json')
        vch, vmeta, VAL, falt, ATL = valtorta.construir(vep, os.path.join(HERE, 'valtorta_enlaces.json'), atlas_path=atp if os.path.exists(atp) else None)
        if ATL: log('Atlas de los viajes: %d pasos en %d lugares, %d enlazados con el libro' % (len(ATL['P']), len(ATL['L']), sum(1 for p in ATL['P'] if p[7])))
        dd = os.path.join(DST, 'docs', 'Valtorta'); ch = 0
        for k, c in enumerate(vch): ch += write_if_changed(os.path.join(dd, '%d.html' % k), c)
        metas['Valtorta'] = vmeta
        log('María Valtorta: %d trozos (%d cambiados), %d KB, %d enlaces con los Evangelios%s' % (len(vch), ch, vmeta['kb'], sum(len(x) for b in VAL.values() for x in b.values()), (', %d sin párrafo' % falt) if falt else ''))
    else:
        log('AVISO: no encuentro %s; la app se genera sin el libro de Valtorta.' % vep)
    medi['HCD'] = entradas_hcd(DIA)
    log('Hablar con Dios (del Diario): %d meditaciones con día asignado' % sum(1 for e in medi['HCD'] if e[2]))
    old = os.path.join(DST, 'docs', 'HCD7')
    if os.path.isdir(old): shutil.rmtree(old, ignore_errors=True)
    # 3. index.html
    js = '\n'.join(open(os.path.join(HERE, 'js', f), encoding='utf-8').read() for f in ('liturgia.js', 'med_ui.js', 'hl.js', 'valtorta.js', 'atlas.js'))
    js = js.replace("if(typeof module!=='undefined')module.exports=LIT;", '')
    rel_img = os.path.join(HERE, 'relieve.webp')
    js = js.replace('__RELIEVE__', ('data:image/webp;base64,' + base64.b64encode(open(rel_img, 'rb').read()).decode()) if os.path.exists(rel_img) else '')
    src = open(os.path.join(DIA, 'index.html'), encoding='utf-8').read()
    EY = None
    epy = glob.glob(os.path.join(DIA, 'actualizador', 'pdb_diario', '*sentir*.epub'))
    if epy:
        EY = elyo.leer(epy[0]); log('Él y yo: %d puntos (separados por capítulo)' % len(EY['p']))
    out = parchear(src, metas, medi, js, VAL, EY, ATL)
    log('index.html', 'actualizado' if write_if_changed(os.path.join(DST, 'index.html'), out) else 'sin cambios', '(%d KB)' % (len(out.encode()) // 1024))
    # 4. sw.js y manifest
    C = json.loads(re.search(r'const CAT=(\{.*?\});\nconst MEDI=', out, re.S).group(1))
    sw = parchear_sw(open(os.path.join(DIA, 'sw.js'), encoding='utf-8').read(), metas, C['docs'])
    write_if_changed(os.path.join(DST, 'sw.js'), sw)
    man = json.load(open(os.path.join(DIA, 'manifest.webmanifest'), encoding='utf-8'))
    man.update(name='Diario', short_name='Diario')
    write_if_changed(os.path.join(DST, 'manifest.webmanifest'), json.dumps(man, ensure_ascii=False))
    log('Listo.')

if __name__ == '__main__':
    main()
