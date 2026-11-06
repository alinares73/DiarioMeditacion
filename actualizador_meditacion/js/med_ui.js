/* ===== Meditación diaria: pantalla ===== */
const MBOOKS=[['MedOD','Meditaciones','Libro de meditaciones · 7 tomos'],['MAL','Meditaciones del año litúrgico','VV. AA.'],['SCE','Siempre con Él','F. Espa y otros · 9 tomos'],['HCD','Hablar con Dios','F. Fernández-Carvajal']];
const MKEY=(()=>{const m=new Map();for(const [b] of MBOOKS)(MEDI[b]||[]).forEach((e,i)=>e[2].forEach(k=>{if(!m.has(k))m.set(k,[]);m.get(k).push([b,i])}));return m})();
const GRP={f:'Fiesta del día',t:'Tiempo litúrgico',x:'Devoción'};
function medFor(iso){
  const D=DAY[iso],E=EPA[iso],hint=(D?D.t:'')+' '+(E?E.cel:''),L=LIT.day(iso,hint.trim()),out={};
  for(const [b] of MBOOKS)out[b]=[];
  const seen=new Set();
  const order=[...L.keys.filter(k=>k[1]==='f'),...L.keys.filter(k=>k[1]==='t'),...L.keys.filter(k=>k[1]==='x')];
  for(const [k,g] of order){for(const [b,i] of (MKEY.get(k)||[])){const e=MEDI[b][i];if(e[3]&&e[3]!==L.cyc)continue;const id=b+':'+i;if(seen.has(id))continue;seen.add(id);out[b].push({b,o:e[0],t:e[1],g})}}
  return {L,out}
}
function renderMed(arg){
  const today=isoOf(new Date()),iso=/^\d{4}-\d\d-\d\d$/.test(arg||'')?arg:today;
  const [y,m,d]=iso.split('-').map(Number),dt=new Date(y,m-1,d),E=EPA[iso],D=DAY[iso];
  setHead('Meditación diaria',iso===today?'#/':'#/dia/'+iso);
  const {L,out}=medFor(iso);
  let h=`<div class="mtop"><div class="dhero"><div class="dnum">${d}</div><div class="dmon">${MESES[m-1]}</div><div class="dwk">${DIAS[dt.getDay()]} · ${y}</div></div></div>`;
  h+=`<div class="dnav"><a class="btn" href="#/med/${addDays(iso,-1)}" aria-label="Día anterior">‹</a><a class="btn" href="#/med">Hoy</a><a class="btn" href="#/med/${addDays(iso,1)}" aria-label="Día siguiente">›</a></div>`;
  const cel=E?E.cel.replace(/^PROPIO:\s*/,''):D?D.t.replace(/^\+\s*/,''):'';
  const dots=E&&E.c.length?`<span class="dots">${E.c.map(c=>`<span class="dot c-${c}" title="${esc(COLN[c]||c)}"></span>`).join('<span class="or">/</span>')}</span>`:'';
  h+=`<section class="card"><div class="lh">${dots}<h2>${esc(cel||L.name)}</h2></div>${cel&&norm(cel)!==norm(L.name)?`<p class="cap" style="margin:8px 0 0">${esc(L.name)}${/Domingo|Ramos|Resurrección|Pentecostés|Trinidad|Cuerpo|Ascensión|Rey del/.test(L.name)?' · ciclo '+L.cyc:''}</p>`:''}${E&&E.tp?`<div class="tags"><span class="tag f">Fiesta ${esc(E.tp)}</span>${E.cat?`<span class="tag">${esc(E.cat)}</span>`:''}</div>`:''}</section>`;
  for(const [b,tit,sub] of MBOOKS){
    const l=out[b];
    if(b==='MAL'&&(!l.length||!DOCS.MAL))continue;   // si no trae meditación para ese día, no se muestra
    h+=`<section class="card mbk"><div class="mbh"><h3 class="sh">${esc(tit)}</h3><span class="cap">${esc(sub)}</span></div>`;
    if(!l.length)h+=`<p class="cap" style="margin:6px 0 0">Este libro no trae una meditación propia para este día.</p>`;
    let lastG='';
    for(const e of l){h+=`<a class="rd mrd" href="#/d/${b}/${e.o}"><b>${e.g!==lastG?esc(GRP[e.g]):'&nbsp;'}</b><span>${esc(e.t)}</span></a>`;lastG=e.g}
    h+=`<a class="cm" href="#/dp/${b}/0">Índice del libro →</a></section>`;
  }
  h+=`<div class="row"><a class="btn" href="#/resaltados">🖍 Mis resaltados</a><a class="btn" href="#/docs">📚 Libros</a></div>`;
  $('#main').innerHTML=h;
}
