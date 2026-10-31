"""Índice de las meditaciones del «Hablar con Dios» que ya trae la app Diario (docs/HCD)."""
import re, html, os, json
from classify import classify

FIX = [(r'ESTRELLA DE LA MAÑANA', '30 de noviembre. 1º día de la Novena de la Inmaculada', 'F11-30'),
       (r'CASA DE ORO', '1 de diciembre. 2º día de la Novena de la Inmaculada', 'F12-01'),
       (r'CAUSA DE NUESTRA ALEGR', '3 de diciembre. 4º día de la Novena de la Inmaculada', 'F12-03'),
       (r'REFUGIO DE LOS PECADORES', '6 de diciembre. 7º día de la Novena de la Inmaculada', 'F12-06'),
       (r'NUESTRA FILIACIÓN DIVINA', 'Segundo domingo después de Navidad', 'NAV2')]

def entradas_hcd(dia_dir):
    D = os.path.join(dia_dir, 'docs', 'HCD'); out = []
    k = 0
    while os.path.exists(os.path.join(D, '%d.html' % k)):
        t = open(os.path.join(D, '%d.html' % k), encoding='utf-8').read()
        ps = list(re.finditer(r'<p\b([^>]*)>(.*?)</p>', t, re.S))
        for i, m in enumerate(ps):
            tx = html.unescape(re.sub(r'<[^>]+>', '', m.group(2))).strip()
            if not (re.match(r'^\d{1,3}\.\s+\S', tx) and 'center' in m.group(1) and tx.upper() == tx): continue
            j = i - 1
            while j >= 0 and not re.sub(r'<[^>]+>', '', ps[j].group(2)).strip(): j -= 1
            if j < 0: continue
            h = html.unescape(re.sub(r'<[^>]+>', '', ps[j].group(2))).replace('\xa0', ' ').strip()
            if len(h) > 90:   # el título quedó pegado al final de la nota anterior
                mm = re.search(r'(\d{1,2} de [a-záéíóú]+(?: \([IVX]+\))?)\s*$', h)
                h = mm.group(1) if mm else tx
            o = re.search(r'data-o="(\d+)"', m.group(1))
            if not o: continue
            keys, cyc = classify(h, [], 'tiempo ordinario')
            for rx, lab, kk in FIX:
                if re.search(rx, tx): h, keys = lab, [kk]
            hn = h.lower()
            if not keys and 'sagrada eucarist' in hn:
                mm = re.search(r'\(([IVX]+)\)', h); n = {'I':1,'II':2,'III':3,'IV':4,'V':5,'VI':6,'VII':7}.get(mm.group(1)) if mm else None
                if n: keys = ['CORPUS+%d' % n]
            if not keys and 'sábado posterior al 2º domingo después de pentecost' in hn: keys = ['ICM']
            if not keys and hn.startswith('domingo después de pentecost'): keys = ['TRIN']
            if not keys and 'octavario' in hn and re.match(r'^\d+ de enero', hn): keys = ['F01-%02d' % int(re.match(r'^(\d+)', hn).group(1))]
            keys = ['BAU' if k == 'EPI-0' else k for k in keys]
            tema = re.sub(r'^\d{1,3}\.\s+', '', tx).replace('(*)', '').strip().capitalize()
            out.append([int(o.group(1)), h + ' · ' + tema, keys, cyc])
        k += 1
    return out
