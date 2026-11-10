/* ===== Valtorta: puntos naranjas en la Biblia y en las lecturas del día ===== */
let valOn=false;
function valFind(b,c,v1,v2){const L=VAL&&VAL[b]&&VAL[b][c];if(!L)return null;const m=L.filter(x=>x[0]<=v2&&x[1]>=v1);if(!m.length)return null;return (m.find(x=>!x[3])||m[0])}
function rdHtml(r){
  if(!r[0])return `<div class="rd"><span>${esc(r[1])}</span></div>`;
  let dot='';const m=/^#\/r\/(\d+)\/(\d+)\/(\d+)/.exec(r[0]);
  if(m&&+m[1]>=46&&+m[1]<=49){const v1=+m[3];let v2=v1;const t=String(r[2]||'');if(/[,:]/.test(t))v2=999;else{const ns=(t.match(/\d+/g)||[]).map(Number);if(ns.length)v2=Math.max(v1,...ns)}
    const f=valFind(m[1],m[2],v1,v2);if(f){dot=`<a class="vhd" href="#/d/Valtorta/${f[2]}" title="María Valtorta" aria-label="Ver en María Valtorta"></a>`;const st=atlStep(f[4]);if(st)dot+=`<a class="vloc" href="#/mapa/p/${f[4]}">📍 Según M. Valtorta: ${esc(st.name)}${st.date?' · '+esc(st.date.toLowerCase()):''}</a>`}}
  return `<div class="rdw"><a class="rd" href="${r[0]}"><b>${esc(r[1])}${esc(r[2])}</b><span>${esc(r[3])}</span></a>${dot}</div>`
}
function valDots(b,c){
  const L=VAL&&VAL[b]&&VAL[b][c],tx=$('#txt');if(!L||!tx)return;
  const bt=$('#hval');if(!bt)return;bt.style.display='';
  const by=new Map();L.forEach(x=>{if(!by.has(x[0]))by.set(x[0],[]);const a=by.get(x[0]);if(!a.some(y=>y[2]===x[2]))a.push(x)});
  let lastSt=null;
  for(const [v,xs] of by){const vs=tx.querySelector('.vs[data-v="'+v+'"]');if(!vs)continue;const p=vs.querySelector('p')||vs;
    const sx=xs.find(x=>!x[3]&&x[4]>=0)||xs.find(x=>x[4]>=0),st=sx&&atlStep(sx[4]);
    if(st&&st.name!==lastSt){lastSt=st.name;const a=document.createElement('a');a.className='vpl';a.href='#/mapa/p/'+sx[4];a.textContent='📍 '+st.name+(st.date?' · '+st.date.toLowerCase():'');vs.parentNode.insertBefore(a,vs)}
    xs.slice(0,3).reverse().forEach(x=>{const a=document.createElement('a');a.className='vdot'+(x[3]?' al':'');a.href='#/d/Valtorta/'+x[2];a.title='María Valtorta: '+BK[b].ab+' '+(c*1+1)+','+x[0]+(x[1]>x[0]?'-'+x[1]:'')+(x[3]?' (alusión)':'');p.insertBefore(a,p.firstChild)})}
  const set=on=>{valOn=on;tx.classList.toggle('von',on);bt.classList.toggle('on',on)};set(valOn);
  bt.onclick=e=>{e.stopPropagation();if(!document.contains(tx))return;set(!valOn);if(valOn){const d=tx.querySelector('.vdot');d&&d.closest('.vs').scrollIntoView({block:'center',behavior:'smooth'})}};
}
/* Biblia: los trozos de versículo que quedan sueltos tras un título (p. ej. «Tomaron a Jesús,» en Jn 19)
   se envuelven como el versículo al que pertenecen, para poder seleccionarlos y copiarlos */
function vsWrap(M){const tx=M.querySelector('#txt');if(!tx)return;
  [...tx.querySelectorAll(':scope > p')].forEach(p=>{let v=null;for(let e=p.previousElementSibling;e;e=e.previousElementSibling)if(e.classList.contains('vs')){v=e.dataset.v;break}
    if(v===null)for(let e=p.nextElementSibling;e;e=e.nextElementSibling)if(e.classList.contains('vs')){v=e.dataset.v;break}
    if(v===null)return;const d=document.createElement('div');d.className='vs vsc';d.dataset.v=v;p.replaceWith(d);d.appendChild(p)})}
/* Libros: al tocar una cita de la Biblia dentro de un capítulo largo, se recuerda el párrafo para que «volver» regrese a él */
document.addEventListener('click',e=>{const a=e.target.closest&&e.target.closest('a[href^="#/r/"]');if(!a||!a.closest('.doc'))return;
  const m=location.hash.match(/^#\/(?:d|dp)\/([^/]+)/);if(!m)return;
  let el=a.closest('.vrf')?a.closest('.vrf').nextElementSibling:a.closest('[data-o]');
  if(el&&el.dataset&&el.dataset.o)history.replaceState(null,'','#/d/'+m[1]+'/'+el.dataset.o)},true);
