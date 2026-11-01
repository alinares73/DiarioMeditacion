/* ===== Valtorta: puntos naranjas en la Biblia y en las lecturas del día ===== */
let valOn=false;
function valFind(b,c,v1,v2){const L=VAL&&VAL[b]&&VAL[b][c];if(!L)return null;const m=L.filter(x=>x[0]<=v2&&x[1]>=v1);if(!m.length)return null;return (m.find(x=>!x[3])||m[0])}
function rdHtml(r){
  if(!r[0])return `<div class="rd"><span>${esc(r[1])}</span></div>`;
  let dot='';const m=/^#\/r\/(\d+)\/(\d+)\/(\d+)/.exec(r[0]);
  if(m&&+m[1]>=46&&+m[1]<=49){const v1=+m[3];let v2=v1;const t=String(r[2]||'');if(/[,:]/.test(t))v2=999;else{const ns=(t.match(/\d+/g)||[]).map(Number);if(ns.length)v2=Math.max(v1,...ns)}
    const f=valFind(m[1],m[2],v1,v2);if(f)dot=`<a class="vhd" href="#/d/Valtorta/${f[2]}" title="María Valtorta" aria-label="Ver en María Valtorta"></a>`}
  return `<div class="rdw"><a class="rd" href="${r[0]}"><b>${esc(r[1])}${esc(r[2])}</b><span>${esc(r[3])}</span></a>${dot}</div>`
}
function valDots(b,c){
  const L=VAL&&VAL[b]&&VAL[b][c],tx=$('#txt');if(!L||!tx)return;
  const h=tx.querySelector('h2');if(!h)return;
  const bt=document.createElement('button');bt.type='button';bt.className='vbtn';bt.title='Pasajes en María Valtorta';bt.setAttribute('aria-label','Mostrar u ocultar los pasajes de María Valtorta');
  h.insertBefore(bt,h.firstChild);
  const by=new Map();L.forEach(x=>{if(!by.has(x[0]))by.set(x[0],[]);const a=by.get(x[0]);if(!a.some(y=>y[2]===x[2]))a.push(x)});
  for(const [v,xs] of by){const vs=tx.querySelector('.vs[data-v="'+v+'"]');if(!vs)continue;const p=vs.querySelector('p')||vs;
    xs.slice(0,3).reverse().forEach(x=>{const a=document.createElement('a');a.className='vdot'+(x[3]?' al':'');a.href='#/d/Valtorta/'+x[2];a.title='María Valtorta: '+BK[b].ab+' '+(c*1+1)+','+x[0]+(x[1]>x[0]?'-'+x[1]:'')+(x[3]?' (alusión)':'');p.insertBefore(a,p.firstChild)})}
  const set=on=>{valOn=on;tx.classList.toggle('von',on);bt.classList.toggle('on',on)};set(valOn);
  bt.onclick=e=>{e.stopPropagation();set(!valOn);if(valOn){const d=tx.querySelector('.vdot');d&&d.closest('.vs').scrollIntoView({block:'center',behavior:'smooth'})}};
}
