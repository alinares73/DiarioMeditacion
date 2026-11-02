/* ===== Atlas de los viajes de Jesús según María Valtorta: mapa, cronología y lugares ===== */
/* ATL = {L:{clave:[nombre,lat,lon,región]}, C:[[ciclo,periodo,G|J|C]], P:[[ciclo,clave,fecha,millas,capCEV,título,barca,off]], F:[[ciclo,antesDelPaso,fiesta,fecha]]} */
const ATLX=(()=>{if(typeof ATL==='undefined'||!ATL)return null;
  const vis={},byC=ATL.C.map(()=>[]);ATL.P.forEach((p,i)=>{(vis[p[1]]=vis[p[1]]||[]).push(i);byC[p[0]].push(i)});
  const fest={};ATL.F.forEach(f=>{(fest[f[1]]=fest[f[1]]||[]).push(f)});
  const km=byC.map(l=>Math.round(l.reduce((s,i)=>s+ATL.P[i][3],0)*1.609));
  return {vis,byC,fest,km}})();
function atlStep(i){if(!ATLX||i==null||i<0||!ATL.P[i])return null;const p=ATL.P[i];return {i,cyc:p[0],key:p[1],name:ATL.L[p[1]][0],date:p[2],title:p[5],off:p[7]}}
const ATL_SHORT=['Comienzo','1.º Galilea','1.º Judea','2.º Galilea','2.º Judea','3.º Galilea','3.º Judea','4.º Galilea','4.º Judea','5.º Galilea','5.º Judea','6.º Galilea','6.º Judea y Pasión'];
function atlCname(c){return ATL.C[c][0].split(' · ')[0]}
function atlKm(mi){return Math.round(mi*1.609)}
function atlRead(p){return p[7]?`<a class="cm" href="#/d/Valtorta/${p[7]}">Leer en Valtorta →</a>`:''}

/* ---------- proyección y geografía (dibujada a mano, aproximada) ---------- */
const AX=lon=>(lon-34.25)*0.848*400,AY=lat=>(33.72-lat)*400,AW=800,AH=990;
const SYR={antioch:[742,40],seleucia:[690,52],antigonea:[716,26]};
function axy(k){if(SYR[k])return SYR[k];const l=ATL.L[k];return [AX(l[2]),AY(l[1])]}
const GEO={
 coast:[[33.72,35.47],[33.56,35.37],[33.45,35.30],[33.27,35.19],[33.17,35.16],[33.09,35.10],[33.00,35.09],[32.92,35.07],[32.86,35.08],[32.82,35.03],[32.83,34.96],[32.75,34.95],[32.65,34.92],[32.50,34.89],[32.33,34.85],[32.17,34.80],[32.05,34.75],[31.95,34.70],[31.80,34.63],[31.67,34.55],[31.52,34.44],[31.40,34.33],[31.24,34.21]],
 galilee:[[32.882,35.574],[32.888,35.6],[32.886,35.626],[32.862,35.645],[32.82,35.652],[32.783,35.641],[32.74,35.637],[32.715,35.622],[32.705,35.59],[32.712,35.571],[32.75,35.552],[32.792,35.543],[32.81,35.524],[32.825,35.519],[32.85,35.53],[32.873,35.548],[32.88,35.563]],
 dead:[[31.77,35.50],[31.76,35.56],[31.70,35.585],[31.55,35.58],[31.45,35.565],[31.35,35.55],[31.24,35.53],[31.24,35.40],[31.35,35.39],[31.45,35.40],[31.55,35.44],[31.65,35.46],[31.73,35.48]],
 huleh:[[33.10,35.61],[33.09,35.63],[33.06,35.63],[33.05,35.61],[33.07,35.60]],
 rivers:[
  [[33.25,35.65],[33.15,35.625],[33.10,35.615],[33.05,35.617],[32.97,35.622],[32.92,35.60],[32.885,35.59]],
  [[32.705,35.575],[32.63,35.57],[32.55,35.565],[32.45,35.56],[32.35,35.545],[32.25,35.535],[32.15,35.53],[32.05,35.53],[31.95,35.535],[31.86,35.545],[31.77,35.535]],
  [[32.64,35.57],[32.68,35.65],[32.71,35.75],[32.72,35.85],[32.70,35.95],[32.66,36.05]],
  [[32.10,35.53],[32.15,35.62],[32.20,35.72],[32.25,35.82],[32.22,35.95],[32.10,36.03]],
  [[32.81,35.04],[32.73,35.12],[32.65,35.20],[32.58,35.30]],
  [[31.47,35.56],[31.47,35.70],[31.45,35.85]]],
 reg:[[33.38,35.27,'FENICIA'],[32.95,35.30,'GALILEA'],[32.27,35.12,'SAMARIA'],[31.60,34.98,'JUDEA'],[31.98,35.74,'PEREA'],[32.45,35.98,'DECÁPOLIS'],[33.02,35.85,'GAULANÍTIDE'],[33.30,36.20,'ITUREA'],[31.33,34.78,'IDUMEA'],[32.80,36.35,'AURANÍTIDE']],
 mt:[[33.416,35.857,'Hermón'],[32.687,35.390,''],[32.735,35.045,''],[32.200,35.270,'Garizim'],[31.768,35.725,''],[31.779,35.245,'']]
};
function apath(pts,close){return pts.map((p,i)=>(i?'L':'M')+AX(p[1]).toFixed(1)+' '+AY(p[0]).toFixed(1)).join('')+(close?'Z':'')}
function atlBase(){
  const sea=apath(GEO.coast)+`L${AX(33.0)} ${AY(31.24)}L-200 ${AY(31.24)}L-200 -200L${AX(35.47)} -200Z`;
  let s=`<rect x="-400" y="-400" width="1600" height="1800" class="aland"/>${ATL_REL?`<image href="${ATL_REL}" x="-100" y="-60" width="1000" height="1110" preserveAspectRatio="none"/>`:''}<path class="asea" d="${sea}"/><path class="acoast" d="${apath(GEO.coast)}"/>`;
  s+=GEO.rivers.map(r=>`<path class="ariv" d="${apath(r)}"/>`).join('');
  s+=`<path class="alake" d="${apath(GEO.galilee,1)}"/><path class="alake" d="${apath(GEO.dead,1)}"/><path class="alake" d="${apath(GEO.huleh,1)}"/>`;
  s+=`<g class="areg">`+GEO.reg.map(r=>`<text x="${AX(r[1])}" y="${AY(r[0])}">${r[2]}</text>`).join('')+`</g>`;
  s+=`<g class="amt">`+GEO.mt.map(m=>`<path d="M${AX(m[1])-7} ${AY(m[0])+5}l7-12 7 12z"/>`+(m[2]?`<text x="${AX(m[1])+10}" y="${AY(m[0])+4}">${m[2]}</text>`:'')).join('')+`</g>`;
  s+=`<g class="awat"><text x="${AX(34.42)}" y="${AY(32.35)}" transform="rotate(-72 ${AX(34.42)} ${AY(32.35)})">Mar Mediterráneo</text><text x="${AX(35.62)}" y="${AY(31.66)}" transform="rotate(90 ${AX(35.62)} ${AY(31.66)})">Mar Muerto</text><text x="${AX(35.66)}" y="${AY(32.53)}" transform="rotate(84 ${AX(35.66)} ${AY(32.53)})">Jordán</text></g>`;
  s+=`<g class="asyr"><rect x="660" y="6" width="130" height="66" rx="8"/><text x="725" y="66">Siria · fuera de escala ↑</text><text x="26" y="24" class="anor">N ↑</text></g>`;
  s+=`<g class="ascale"><path d="M24 ${AH-34}h72"/><path d="M24 ${AH-40}v12M96 ${AH-40}v12M60 ${AH-37}v6"/><text x="24" y="${AH-46}">0</text><text x="88" y="${AH-46}">20 km</text></g>`;
  return s;
}

/* ---------- mapa ---------- */
let AM=null;const ATL_REL='__RELIEVE__';
function renderMapa(a,b){
  if(!ATLX)return notFound();
  setHead('Mapa de los viajes','#/docs','doc');$('#fab').style.display='none';
  let mode='all',cyc=-1,step=-1,place=null;
  if(a==='c'&&ATL.C[+b]){mode='cyc';cyc=+b;step=0}
  else if(a==='p'&&ATL.P[+b]){mode='cyc';step=+b;cyc=ATL.P[step][0];step=ATLX.byC[cyc].indexOf(step)}
  else if(a==='l'&&ATL.L[b]){mode='place';place=b}
  const chips=`<a class="chip${mode==='all'||mode==='place'?' on':''}" data-c="-1">Todos</a>`+ATL.C.map((c,i)=>`<a class="chip t${c[2]}${i===cyc?' on':''}" data-c="${i}">${ATL_SHORT[i]}</a>`).join('');
  $('#main').innerHTML=`<div class="atl"><div class="achips" id="achips">${chips}</div><div class="mapw" id="mapw"><svg id="amap" viewBox="0 0 ${AW} ${AH}" preserveAspectRatio="xMidYMid meet"><g id="ag">${atlBase()}<g id="aroutes"></g><g id="apts"></g><g id="alab"></g><g id="acur"></g></g></svg><div class="mz"><button class="btn" data-z="1.6" aria-label="Acercar">+</button><button class="btn" data-z="0.625" aria-label="Alejar">−</button><button class="btn" data-z="0" aria-label="Ver todo">⤢</button></div></div><div class="card mapc" id="mapc"></div></div>`;
  atlStop();AM={mode,cyc,step,place,vb:[0,0,AW,AH],play:null};
  const svg=$('#amap');
  $('#achips').onclick=e=>{const c=e.target.closest('.chip');if(!c)return;const n=+c.dataset.c;history.replaceState(null,'',n<0?'#/mapa':'#/mapa/c/'+n);atlSet(n<0?{mode:'all',cyc:-1,step:-1,place:null}:{mode:'cyc',cyc:n,step:0,place:null},true)};
  $('#mapw .mz').onclick=e=>{const z=e.target.closest('[data-z]');if(!z)return;const f=+z.dataset.z;if(!f)return atlFit(atlBBox(),true);const [x,y,w,h]=AM.vb;atlZoomTo(x+w/2,y+h/2,1/f,true)};
  atlPointer(svg);
  window.removeEventListener('resize',atlLabels);window.addEventListener('resize',atlLabels);
  atlSet(AM,false,true);
  const c=$('#achips .chip.on');c&&c.scrollIntoView({inline:'center',block:'nearest'});
}
function atlSet(o,anim,first){
  Object.assign(AM,o);if(AM.play){clearInterval(AM.play);AM.play=null}
  document.querySelectorAll('#achips .chip').forEach(c=>c.classList.toggle('on',+c.dataset.c===(AM.mode==='cyc'?AM.cyc:-1)));
  atlDraw();atlCard();
  if(AM.mode==='place'){const [x,y]=axy(AM.place);atlFit([x-60,y-60,x+60,y+60],anim&&!first)}
  else if(AM.mode==='cyc'&&first&&AM.step>0){const [x,y]=axy(ATL.P[ATLX.byC[AM.cyc][AM.step]][1]);atlFit([x-170,y-170,x+170,y+170],false)}
  else atlFit(atlBBox(),anim&&!first);
}
function atlBBox(){
  const ids=AM.mode==='cyc'?ATLX.byC[AM.cyc]:null;if(!ids)return [-20,20,AW+20,AH-10];
  let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;ids.forEach(i=>{const [x,y]=axy(ATL.P[i][1]);x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y)});
  return [x0-40,y0-40,x1+40,y1+40];
}
function atlDraw(){
  const R=$('#aroutes'),Pt=$('#apts');let rs='',ps='';
  const counts={};
  if(AM.mode==='cyc'){
    const ids=ATLX.byC[AM.cyc],cur=AM.step;
    for(let n=1;n<ids.length;n++){const p0=ATL.P[ids[n-1]],p1=ATL.P[ids[n]];if(p0[1]===p1[1])continue;const [x0,y0]=axy(p0[1]),[x1,y1]=axy(p1[1]);
      const mx=(x0+x1)/2-(y1-y0)*.12,my=(y0+y1)/2+(x1-x0)*.12;
      rs+=`<path class="aseg${n<=cur?' done':''}${p1[6]?' boat':''}${n===cur?' last':''}" d="M${x0.toFixed(1)} ${y0.toFixed(1)}Q${mx.toFixed(1)} ${my.toFixed(1)} ${x1.toFixed(1)} ${y1.toFixed(1)}"/>`}
    ids.forEach((i,n)=>{const k=ATL.P[i][1];counts[k]=counts[k]||{n:0,done:false};counts[k].n++;if(n<=cur)counts[k].done=true});
  }else{
    for(const c of ATLX.byC){for(let n=1;n<c.length;n++){const a=ATL.P[c[n-1]][1],b=ATL.P[c[n]][1];if(a===b)continue;const [x0,y0]=axy(a),[x1,y1]=axy(b);rs+=`<path class="aseg all" d="M${x0.toFixed(1)} ${y0.toFixed(1)}L${x1.toFixed(1)} ${y1.toFixed(1)}"/>`}}
    for(const k in ATLX.vis)counts[k]={n:ATLX.vis[k].length,done:true};
  }
  for(const k in counts){const [x,y]=axy(k);ps+=`<circle class="apt${counts[k].done?' done':''}${AM.place===k?' sel':''}" data-k="${k}" data-n="${counts[k].n}" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="4"/>`}
  R.innerHTML=rs;Pt.innerHTML=ps;AM.counts=counts;
  const last=R.querySelector('.last');if(last){const L=last.getTotalLength();last.style.strokeDasharray=L;last.style.strokeDashoffset=L;last.getBoundingClientRect();last.style.transition='stroke-dashoffset .6s ease-out';last.style.strokeDashoffset=0}
  atlCur();atlScale();
}
function atlCur(){
  const G=$('#acur');if(AM.mode!=='cyc'){G.innerHTML=AM.mode==='place'?(()=>{const [x,y]=axy(AM.place);return `<circle class="apulse" cx="${x}" cy="${y}" r="9"/>`})():'';return}
  const p=ATL.P[ATLX.byC[AM.cyc][AM.step]],[x,y]=axy(p[1]);G.innerHTML=`<circle class="apulse" cx="${x}" cy="${y}" r="9"/><circle class="acurd" cx="${x}" cy="${y}" r="6"/>`;
}
function atlScale(){
  const svg=$('#amap');if(!svg)return;const k=svg.clientWidth/AM.vb[2]||1,s=1/k;
  svg.style.setProperty('--s',s);
  svg.querySelectorAll('.apt').forEach(c=>c.setAttribute('r',((AM.mode==='cyc'?3.2:2.2)+Math.min(5,Math.sqrt(+c.dataset.n)*(AM.mode==='cyc'?1:.9)))*s));
  svg.querySelectorAll('#acur circle').forEach(c=>c.setAttribute('r',(c.classList.contains('acurd')?7:12)*s));
  $('#ag').style.fontSize=(12*s)+'px';
  atlLabels();
}
function atlLabels(){
  const svg=$('#amap');if(!svg||!AM)return;const k=svg.clientWidth/AM.vb[2]||1,s=1/k,fs=12.5*s;
  const keys=Object.keys(AM.counts||{});
  const cur=AM.mode==='cyc'?ATL.P[ATLX.byC[AM.cyc][AM.step]][1]:AM.place;
  keys.sort((a,b)=>(b===cur)-(a===cur)||AM.counts[b].n-AM.counts[a].n);
  const boxes=[],[vx,vy,vw,vh]=AM.vb;let out='';
  for(const key of keys){const [x,y]=axy(key);if(x<vx||x>vx+vw||y<vy||y>vy+vh)continue;
    const nm=ATL.L[key][0],w=nm.length*fs*.56,h=fs*1.15;
    const cands=[[x+6*s,y+fs*.35],[x-6*s-w,y+fs*.35],[x-w/2,y-7*s],[x-w/2,y+fs+6*s]];
    let ok=null;for(const [lx,ly] of cands){const b=[lx-2*s,ly-h+2*s,lx+w+2*s,ly+3*s];if(!boxes.some(o=>b[0]<o[2]&&b[2]>o[0]&&b[1]<o[3]&&b[3]>o[1])){ok=[lx,ly,b];break}}
    if(!ok){if(key!==cur)continue;ok=[x+6*s,y+fs*.35,[0,0,0,0]]}
    boxes.push(ok[2]);out+=`<text class="alb${key===cur?' cur':''}${AM.counts[key].done?'':' fut'}" x="${ok[0].toFixed(1)}" y="${ok[1].toFixed(1)}" font-size="${fs.toFixed(2)}" data-k="${key}">${esc(nm)}</text>`;
    if(boxes.length>70)break}
  $('#alab').innerHTML=out;
}
function atlApplyVB(){const v=AM.vb;$('#amap').setAttribute('viewBox',v.map(n=>n.toFixed(1)).join(' '));atlScale()}
function atlFit(b,anim){
  const svg=$('#amap');const ar=svg.clientHeight/svg.clientWidth||1.2;let w=Math.max(b[2]-b[0],160),h=Math.max(b[3]-b[1],160);
  if(h/w>ar)w=h/ar;else h=w*ar;const cx=(b[0]+b[2])/2,cy=(b[1]+b[3])/2;atlAnim([cx-w/2,cy-h/2,w,h],anim)
}
function atlZoomTo(px,py,f,anim){const [x,y,w,h]=AM.vb;let nw=Math.min(Math.max(w*f,60),AW*1.6);const r=nw/w;atlAnim([px-(px-x)*r,py-(py-y)*r,nw,h*r],anim)}
function atlAnim(to,anim){
  if(AM.raf)cancelAnimationFrame(AM.raf);
  if(!anim){AM.vb=to;return atlApplyVB()}
  const fr=AM.vb.slice(),t0=performance.now(),D=380;
  const tick=t=>{const u=Math.min(1,(t-t0)/D),e=1-Math.pow(1-u,3);AM.vb=fr.map((v,i)=>v+(to[i]-v)*e);atlApplyVB();if(u<1)AM.raf=requestAnimationFrame(tick)};AM.raf=requestAnimationFrame(tick);
}
function atlPointer(svg){
  const pts=new Map();let start=null,moved=false,pinch=null;
  const toU=(cx,cy)=>{const r=svg.getBoundingClientRect(),[x,y,w,h]=AM.vb,k=Math.min(r.width/w,r.height/h),ox=(r.width-w*k)/2,oy=(r.height-h*k)/2;return [x+(cx-r.left-ox)/k,y+(cy-r.top-oy)/k,k]};
  svg.addEventListener('pointerdown',e=>{svg.setPointerCapture(e.pointerId);pts.set(e.pointerId,[e.clientX,e.clientY]);if(pts.size===1){start={x:e.clientX,y:e.clientY,vb:AM.vb.slice(),t:e.target};moved=false}else if(pts.size===2){const [a,b]=[...pts.values()];pinch={d:Math.hypot(a[0]-b[0],a[1]-b[1]),vb:AM.vb.slice(),m:toU((a[0]+b[0])/2,(a[1]+b[1])/2)};moved=true}});
  svg.addEventListener('pointermove',e=>{if(!pts.has(e.pointerId))return;pts.set(e.pointerId,[e.clientX,e.clientY]);
    if(pts.size===2&&pinch){const [a,b]=[...pts.values()],d=Math.hypot(a[0]-b[0],a[1]-b[1]);const f=pinch.d/d;const [x,y,w,h]=pinch.vb;let nw=Math.min(Math.max(w*f,60),AW*1.6);const r=nw/w,[mx,my]=pinch.m;
      const r2=svg.getBoundingClientRect(),k=Math.min(r2.width/nw,r2.height/(h*r));const cx=(a[0]+b[0])/2-r2.left,cy=(a[1]+b[1])/2-r2.top;
      const ox=(r2.width-nw*k)/2,oy=(r2.height-h*r*k)/2;AM.vb=[mx-(cx-ox)/k,my-(cy-oy)/k,nw,h*r];atlApplyVB()}
    else if(pts.size===1&&start){const dx=e.clientX-start.x,dy=e.clientY-start.y;if(Math.abs(dx)+Math.abs(dy)>6)moved=true;if(moved){const r=svg.getBoundingClientRect(),k=Math.min(r.width/start.vb[2],r.height/start.vb[3]);AM.vb=[start.vb[0]-dx/k,start.vb[1]-dy/k,start.vb[2],start.vb[3]];atlApplyVB()}}});
  const up=e=>{if(!pts.has(e.pointerId))return;pts.delete(e.pointerId);if(pts.size<2)pinch=null;
    if(pts.size===0&&start&&!moved){const [ux,uy,k]=toU(e.clientX,e.clientY);let best=null,bd=22/k;for(const key in AM.counts){const [x,y]=axy(key),d=Math.hypot(x-ux,y-uy);if(d<bd){bd=d;best=key}}
      if(best){history.replaceState(null,'','#/mapa/l/'+best);atlSet({mode:'place',place:best,cyc:-1,step:-1},true)}}
    if(pts.size===0)start=null;if(pts.size===1){const [p]=[...pts.values()];start={x:p[0],y:p[1],vb:AM.vb.slice()};moved=true}};
  svg.addEventListener('pointerup',up);svg.addEventListener('pointercancel',up);
  svg.addEventListener('wheel',e=>{e.preventDefault();const [ux,uy]=toU(e.clientX,e.clientY);atlZoomTo(ux,uy,e.deltaY>0?1.2:1/1.2,false)},{passive:false});
  svg.addEventListener('dblclick',e=>{const [ux,uy]=toU(e.clientX,e.clientY);atlZoomTo(ux,uy,.5,true)});
}
function atlCard(){
  const C=$('#mapc');if(!C)return;
  if(AM.mode==='all'){
    const tot=ATLX.km.reduce((a,b)=>a+b,0);
    C.innerHTML=`<h3 class="sh">Los caminos de Jesús</h3><p class="cap">Según las visiones de María Valtorta: ${ATL.P.length} etapas, ${Object.keys(ATL.L).length} lugares y unos ${tot.toLocaleString('es')} km a pie (y algunos en barca) en algo más de tres años.</p><p class="cap">Elige arriba un periodo para seguir el viaje paso a paso, o toca un punto del mapa para ver qué pasó allí. Pellizca o usa + y − para acercarte.</p><div class="row"><a class="btn" href="#/viajes">📜 Cronología</a><a class="btn" href="#/lugares">📍 Lugares</a></div>`;return}
  if(AM.mode==='place'){C.innerHTML=atlPlaceHtml(AM.place,true);return}
  const ids=ATLX.byC[AM.cyc],i=ids[AM.step],p=ATL.P[i],c=ATL.C[AM.cyc];
  const prev=AM.step>0?ATL.P[ids[AM.step-1]]:null;
  const from=prev&&prev[1]!==p[1]?`<span class="cap">desde ${esc(ATL.L[prev[1]][0])}${p[3]?' · ≈ '+atlKm(p[3])+' km':''}${p[6]?' · en barca':''}</span>`:'';
  const fe=(ATLX.fest[i]||[]).map(f=>`<span class="tag f">✦ ${esc(f[2])}</span>`).join('');
  C.innerHTML=`<div class="mbh"><h3 class="sh">${esc(c[0])}</h3><span class="cap">${esc(c[1])} · ${ATLX.km[AM.cyc]} km</span></div>
  <div class="astep"><button class="btn" id="aprev" aria-label="Paso anterior" ${AM.step?'':'disabled'}>‹</button><button class="btn" id="aplay" aria-label="Reproducir">${AM.play?'❚❚':'▶'}</button><span class="anum">${AM.step+1} / ${ids.length}</span><button class="btn" id="anext" aria-label="Paso siguiente" ${AM.step<ids.length-1?'':'disabled'}>›</button></div>
  <div class="aplace"><b>📍 ${esc(ATL.L[p[1]][0])}</b>${from}</div>${p[2]?`<p class="cap" style="margin:2px 0 6px">${esc(p[2])}</p>`:''}${fe?`<div class="tags">${fe}</div>`:''}
  ${p[5]?`<p class="atit">${esc(p[5])}</p>`:'<p class="cap">De camino.</p>'}${atlRead(p)}`;
  const go=d=>{const n=Math.max(0,Math.min(ids.length-1,AM.step+d));if(n===AM.step)return false;AM.step=n;history.replaceState(null,'','#/mapa/p/'+ids[n]);atlDraw();atlCard();atlFollow();return true};
  $('#aprev').onclick=()=>{atlStop();go(-1)};$('#anext').onclick=()=>{atlStop();go(1)};
  $('#aplay').onclick=()=>{if(AM.play){atlStop();atlCard();return}if(AM.step>=ids.length-1){AM.step=-1}const me=AM;AM.play=setInterval(()=>{if(AM!==me||AM.mode!=='cyc'||!location.hash.startsWith('#/mapa')){clearInterval(me.play);me.play=null;return}if(!go(1)){atlStop();atlCard()}},1500);go(1)||atlCard()};
}
function atlStop(){if(AM&&AM.play){clearInterval(AM.play);AM.play=null}}
function atlFollow(){const p=ATL.P[ATLX.byC[AM.cyc][AM.step]],[x,y]=axy(p[1]),[vx,vy,vw,vh]=AM.vb,m=.15;if(x<vx+vw*m||x>vx+vw*(1-m)||y<vy+vh*m||y>vy+vh*(1-m))atlAnim([x-vw/2,y-vh/2,vw,vh],true)}
function atlPlaceHtml(key,inMap){
  const L=ATL.L[key],ids=ATLX.vis[key]||[];let h=`<div class="mbh"><h3 class="sh">📍 ${esc(L[0])}</h3><span class="cap">${esc(L[3])}</span></div><p class="cap">${ids.length} ${ids.length===1?'etapa':'etapas'} en el itinerario según María Valtorta.</p>`;
  let lc=-1;
  for(const i of ids){const p=ATL.P[i];if(p[0]!==lc){lc=p[0];h+=`<h4 class="ach">${esc(atlCname(lc))}</h4>`}
    h+=`<a class="rd ard" href="${p[7]?'#/d/Valtorta/'+p[7]:'#/mapa/p/'+i}"><b>${esc(p[2]||'')}</b><span>${esc(p[5]||'De camino')}</span></a>`}
  h+=`<div class="row" style="margin-top:12px">${inMap?`<a class="btn" href="#/lugar/${key}">Ficha del lugar</a>`:`<a class="btn" href="#/mapa/l/${key}">🗺 Ver en el mapa</a>`}<a class="btn" href="#/lugares">📍 Todos los lugares</a></div>`;
  return h;
}

/* ---------- cronología ---------- */
function renderViajes(c){
  if(!ATLX)return notFound();
  setHead('Cronología de los viajes','#/docs','doc');
  const tot=ATL.P.length;
  let h=`<h2 class="t">Los viajes de Jesús</h2><p class="mut">Según María Valtorta. Fechas y distancias aproximadas del atlas de J. Webster; cada etapa enlaza con su capítulo.</p>`;
  h+=`<div class="aribbon">`+ATL.C.map((c,i)=>`<a href="#/viajes/${i}" class="t${c[2]}" style="flex:${ATLX.byC[i].length}" title="${esc(c[0])}"><span>${i?i:'·'}</span></a>`).join('')+`</div><div class="aleg"><span class="tG">Galilea</span><span class="tJ">Judea</span><span class="tC">Comienzo</span></div>`;
  ATL.C.forEach((cy,ci)=>{const ids=ATLX.byC[ci],pl=new Set(ids.map(i=>ATL.P[i][1]));
    h+=`<section class="card acy t${cy[2]}" id="cy${ci}"><div class="mbh"><h3 class="sh">${esc(cy[0])}</h3><span class="cap">${esc(cy[1])}</span></div><p class="cap">${ids.length} etapas · ${pl.size} lugares · ≈ ${ATLX.km[ci]} km</p><div class="row"><a class="btn" href="#/mapa/c/${ci}">🗺 Seguir en el mapa</a></div><details${+c===ci?' open':''}><summary>Ver las etapas</summary>`;
    ids.forEach(i=>{const p=ATL.P[i];(ATLX.fest[i]||[]).forEach(f=>h+=`<div class="afest">✦ ${esc(f[2])}${f[3]?' · '+esc(f[3].toLowerCase()):''}</div>`);
      h+=`<div class="arow"><a class="apl" href="#/mapa/p/${i}">${esc(ATL.L[p[1]][0])}</a><small>${esc(p[2]||'')}</small>${p[5]?(p[7]?`<a class="atl2" href="#/d/Valtorta/${p[7]}">${esc(p[5])}</a>`:`<span class="atl2">${esc(p[5])}</span>`):''}</div>`});
    h+=`</details></section>`});
  $('#main').innerHTML=h;
  if(c!==undefined&&$('#cy'+c))$('#cy'+c).scrollIntoView({block:'start'});
}

/* ---------- lugares ---------- */
function renderLugares(){
  if(!ATLX)return notFound();
  setHead('Lugares','#/docs','doc');
  const keys=Object.keys(ATL.L).sort((a,b)=>ATL.L[a][0].localeCompare(ATL.L[b][0],'es'));
  const regs=[...new Set(keys.map(k=>ATL.L[k][3]))].sort((a,b)=>(ATLX&&0)||a.localeCompare(b,'es'));
  let h=`<h2 class="t">Lugares</h2><p class="mut">${keys.length} lugares por donde pasó Jesús según María Valtorta.</p><input id="lq" class="si" type="search" placeholder="Buscar un lugar…" autocomplete="off"><div id="ll">`;
  for(const r of regs){h+=`<h3 class="thm areg2">${esc(r)}</h3>`;for(const k of keys.filter(k=>ATL.L[k][3]===r)){const n=(ATLX.vis[k]||[]).length;h+=`<a class="rd alug" href="#/lugar/${k}" data-n="${esc(norm(ATL.L[k][0]))}"><span>${esc(ATL.L[k][0])}</span><b>${n}</b></a>`}}
  h+=`</div>`;$('#main').innerHTML=h;
  $('#lq').oninput=e=>{const q=norm(e.target.value.trim());document.querySelectorAll('#ll .alug').forEach(a=>a.style.display=!q||a.dataset.n.includes(q)?'':'none');document.querySelectorAll('#ll .areg2').forEach(t=>{let n=t.nextElementSibling,any=false;while(n&&n.classList.contains('alug')){if(n.style.display!=='none')any=true;n=n.nextElementSibling}t.style.display=any?'':'none'})};
}
function renderLugar(k){
  if(!ATLX||!ATL.L[k])return notFound();
  setHead(ATL.L[k][0],'#/lugares','doc');
  $('#main').innerHTML=`<section class="card">${atlPlaceHtml(k,false)}</section>`;
}
