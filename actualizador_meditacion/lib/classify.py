import re
from epublib import nrm, find_dow, find_date, find_week, cycle, ROM

def roman_suffix(t):
    m = re.search(r'\(([ivx]+)\)\s*$', t) or re.search(r'\(([ivx]+)\)', t)
    return ROM.get(m.group(1)) if m else None

def classify(label, parents, hint=''):
    """Devuelve (claves, ciclo).  Claves: Fmm-dd, A/C/P/T{sem}-{dow}, C0-d, SS-d, EPI-d, y fiestas móviles."""
    if not label: return [], ''
    try:
        return _classify(label, parents, hint)
    except TypeError:
        return [], ''

def _classify(label, parents, hint):
    t = nrm(label); ctx = nrm(' '.join(parents) + ' ' + hint)
    t = t.replace('“', '').replace('"', '')
    keys = []; cyc = cycle(t)
    d = find_date(t)
    # ---- fiestas móviles / especiales
    if 'sumo y eterno sacerdote' in t: keys.append('SUMOSAC')
    elif 'sagrado corazon' in t: keys.append('ICM' if 'despues del sagrado corazon' in t else 'SCJ')
    elif re.search(r'inmaculado corazon|corazon inmaculado', t): keys.append('ICM')
    elif re.search(r'(viernes|sabado|domingo|lunes|martes|miercoles|jueves) despues de(l)? corpus', t):
        keys.append('CORPUS+%d' % {5: 1, 6: 2, 0: 3, 1: 4, 2: 5, 3: 6, 4: 7}[find_dow(t)])
    elif re.search(r'corpus christi|cuerpo y sangre', t): keys.append('CORPUS')
    elif re.search(r'meditacion sagrada eucaristia', t):
        n = roman_suffix(t)
        if n: keys.append('CORPUS+%d' % n)
    elif 'santisima trinidad' in t: keys.append('TRIN')
    elif 'sagrada familia' in t: keys.append('SF')
    elif 'bautismo' in t: keys.append('BAU')
    elif 'ascension' in t:
        keys.append('ASC')
        if 'domingo vii de pascua' in t: keys.append('P7-0')
    elif 'vispera de pentecostes' in t: keys.append('P7-6')
    elif 'pentecostes' in t and 'semana' not in t and 'despues' not in t: keys.append('PENT')
    elif re.search(r'cristo,? rey|rey del universo', t): keys.append('CR')
    elif re.search(r'domingos? de (s\.?|san) jose', t):
        n = roman_suffix(t)
        if not n:
            m = re.match(r'^(\d)\s*[ºo]', t); n = int(m.group(1)) if m else None
        if n: keys.append('SJ7-%d' % n)
    elif 'octavario por la unidad' in t:
        n = roman_suffix(t)
        if n: keys.append('F01-%02d' % (17 + n))
    elif 'eleccion del papa' in t or 'eleccion del romano pontifice' in t: keys.append('F05-08')   # León XIV, 8-V-2025
    elif d: keys.append(d)
    elif 'ceniza' in t:
        w = find_dow(t); keys.append('C0-%d' % w)
    elif 'ramos' in t: keys.append('SS-0')
    elif re.search(r'\b(lunes|martes|miercoles|jueves|viernes|sabado) santo\b', t): keys.append('SS-%d' % find_dow(t))
    elif re.search(r'resurreccion|^domingo de pascua', t): keys.append('P1-0')
    elif 'octava de pascua' in t: keys.append('P1-%d' % find_dow(t))
    elif 'despues de epifania' in t: keys.append('EPI-%d' % find_dow(t))
    elif re.search(r'segundo domingo del tiempo de navidad|ii domingo de navidad|^domingo ii$', t): keys.append('NAV2')
    elif re.search(r'^epifania', t): keys.append('F01-06')
    else:
        w = find_dow(t); n = find_week(t)
        season = None
        for s, rx in (('A', 'adviento'), ('C', 'cuaresma'), ('P', 'pascua'), ('T', r'tiempo ordinario|\bto\b')):
            if re.search(rx, t): season = s; break
        if not season:
            for s, rx in (('A', 'adviento'), ('C', 'cuaresma'), ('P', 'pascua'), ('T', r'tiempo ordinario|\bto\b')):
                if re.search(rx, ctx): season = s; break
        if season and w is not None and n:
            if season == 'P' and n == 1: pass
            keys.append('%s%d-%d' % (season, n, w))
    # extras: fechas que llevan además el día después de Epifanía ("7 DE ENERO O LUNES DESPUÉS DE EPIFANÍA")
    if d and 'despues de epifania' in t and find_dow(t) is not None: keys.append('EPI-%d' % find_dow(t))
    if 'CR' in keys: keys.append('T34-0')
    # ferias de Navidad del 7 al 12 de enero: solo valen antes del Bautismo del Señor
    if re.search(r'epifan|navidad', t + ' ' + ctx):
        keys = ['N' + k[1:] if re.match(r'^F01-(0[7-9]|1[0-3])$', k) else k for k in keys]
    return keys, cyc
