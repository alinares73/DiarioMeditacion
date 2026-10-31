/* ===== Resaltados de texto en los libros ===== */
const UHB='#dx p,#dx h1,#dx h2,#dx h3,#dx h4,#dx h5,#dx h6';
let uhCur=null; /* {doc,k} del libro abierto */
const uhAll=()=>LS.get('uhl',[]),uhSave=l=>LS.set('uhl',l);
function uhOff(el,node,off){const r=document.createRange();r.setStart(el,0);try{r.setEnd(node,off)}catch(e){return 0}return r.toString().length}
function uhWrap(el,s,e,id){
  const w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT),nodes=[];while(w.nextNode())nodes.push(w.currentNode);
  let pos=0;for(const nd of nodes){const a=pos,b=pos+nd.nodeValue.length;pos=b;if(b<=s||a>=e)continue;
    let t=nd;const from=Math.max(s,a)-a,to=Math.min(e,b)-a;if(to<=from)continue;
    if(from>0)t=t.splitText(from);if(to-from<t.nodeValue.length)t.splitText(to-from);
    if(!t.nodeValue.trim())continue;
    const m=document.createElement('mark');m.className='uh';m.dataset.h=id;t.replaceWith(m);m.append(t)}
}
function uhApply(doc,k){
  uhCur={doc,k};const els=[...document.querySelectorAll(UHB)];
  for(const r of uhAll()){if(r.d!==doc||r.k!==k)continue;let el=els[r.p];
    if(!el||el.textContent.slice(r.s,r.e)!==r.t){const i=els.findIndex(x=>x.textContent.includes(r.t));if(i<0)continue;el=els[i];const s=el.textContent.indexOf(r.t);r.p=i;r.s=s;r.e=s+r.t.length}
    uhWrap(el,r.s,r.e,r.id)}
}
function uhHeading(el){let n=el;while(n){if(n.tagName==='H2'&&n.closest('#dx'))return n.textContent.trim();n=n.previousElementSibling}return ''}
function uhFromSel(){
  const sel=window.getSelection();if(!sel||sel.isCollapsed||!sel.rangeCount)return false;
  const rg=sel.getRangeAt(0),dx=$('#dx');if(!dx||!uhCur||!dx.contains(rg.commonAncestorContainer))return false;
  const els=[...document.querySelectorAll(UHB)],id=Date.now().toString(36)+Math.random().toString(36).slice(2,6),segs=[];
  els.forEach((el,i)=>{if(!rg.intersectsNode(el))return;const L=el.textContent.length;
    let s=el.contains(rg.startContainer)||el===rg.startContainer?uhOff(el,rg.startContainer,rg.startOffset):0;
    let e=el.contains(rg.endContainer)||el===rg.endContainer?uhOff(el,rg.endContainer,rg.endOffset):L;
    const t0=el.textContent.slice(s,e);const lt=t0.length-t0.trimStart().length,rt=t0.length-t0.trimEnd().length;s+=lt;e-=rt;
    if(e>s)segs.push({id,d:uhCur.doc,k:uhCur.k,p:i,s,e,t:el.textContent.slice(s,e),h:uhHeading(el),ts:Date.now()})});
  if(!segs.length)return false;
  const l=uhAll();l.push(...segs);uhSave(l);segs.forEach(r=>uhWrap(els[r.p],r.s,r.e,id));sel.removeAllRanges();return true
}
function uhRemove(id){uhSave(uhAll().filter(r=>r.id!==id));document.querySelectorAll('mark.uh[data-h="'+id+'"]').forEach(m=>{m.replaceWith(...m.childNodes)});const dx=$('#dx');if(dx)dx.normalize()}
/* barra flotante al seleccionar */
let uhT=0;
document.addEventListener('selectionchange',()=>{clearTimeout(uhT);uhT=setTimeout(()=>{const sel=window.getSelection(),dx=$('#dx');const on=!!(sel&&!sel.isCollapsed&&dx&&uhCur&&sel.rangeCount&&dx.contains(sel.getRangeAt(0).commonAncestorContainer)&&sel.toString().trim());$('#hlb').classList.toggle('on',on)},120)});
$('#hlb-do').addEventListener('mousedown',e=>e.preventDefault());
$('#hlb-do').onclick=()=>{if(uhFromSel())toast('Resaltado');$('#hlb').classList.remove('on')};
$('#hlb-cp').addEventListener('mousedown',e=>e.preventDefault());
$('#hlb-cp').onclick=async()=>{const t=String(window.getSelection()||'').trim();if(t){await copyText(t);toast('Copiado')}$('#hlb').classList.remove('on')};
/* tocar un resaltado o una nota */
function popMenu(html){const p=$('#pop');p.innerHTML=html+'<button class="x" id="popx" aria-label="Cerrar">✕</button>';p.classList.add('on');$('#popx').onclick=()=>p.classList.remove('on')}
document.addEventListener('click',e=>{
  const f=e.target.closest&&e.target.closest('a.fn');
  if(f){e.preventDefault();const n=document.getElementById('n'+f.dataset.f);popMenu(`<div class="pnote">${n?n.innerHTML:'Nota no encontrada.'}</div>`);return}
  const m=e.target.closest&&e.target.closest('mark.uh');
  if(m&&String(window.getSelection()||'')===''){const id=m.dataset.h;popMenu(`<div class="pact"><button class="btn" id="uhdel">Quitar resaltado</button><a class="btn" href="#/resaltados">Ver mis resaltados</a></div>`);$('#uhdel').onclick=()=>{uhRemove(id);$('#pop').classList.remove('on');toast('Resaltado quitado')};return}
  if(!e.target.closest('#pop'))$('#pop').classList.remove('on');
});
/* pantalla de resaltados */
function uhGroups(){const g=new Map();for(const r of uhAll()){if(!g.has(r.id))g.set(r.id,[]);g.get(r.id).push(r)}return [...g.values()].map(l=>l.sort((a,b)=>a.k-b.k||a.p-b.p))}
function uhByBook(){const by=new Map();for(const l of uhGroups()){const d=l[0].d;if(!DOCS[d])continue;if(!by.has(d))by.set(d,[]);by.get(d).push(l)}
  for(const l of by.values())l.sort((a,b)=>a[0].k-b[0].k||a[0].p-b[0].p||a[0].s-b[0].s);
  const ord=Object.keys(DOCS);return [...by.entries()].sort((a,b)=>ord.indexOf(a[0])-ord.indexOf(b[0]))}
function uhMD(B){let o='# Mis resaltados\n\n';for(const [d,G] of B){o+='## '+dTitle(d)+'\n\n';for(const l of G){if(l[0].h)o+='**'+l[0].h+'**\n\n';o+='> '+l.map(r=>r.t).join(' […] ')+'\n\n'}}return o}
function renderUH(){
  setHead('Mis resaltados','#/docs','doc');const M=$('#main'),B=uhByBook(),n=B.reduce((a,[,G])=>a+G.length,0);
  if(!n){M.innerHTML='<h2 class="t">Mis resaltados</h2><p class="mut">Todavía no has resaltado nada. Abre cualquier libro, selecciona un texto con el dedo o el ratón y pulsa <b>🖍 Resaltar</b>.</p><div class="row"><a class="btn" href="#/docs">📚 Ir a los libros</a></div>';return}
  let h=`<h2 class="t" style="margin-bottom:4px">Mis resaltados</h2><p class="mut" style="margin:0 0 12px">${n} resaltado${n>1?'s':''} en ${B.length} libro${B.length>1?'s':''}</p><div class="row"><button class="btn" id="uxmd">⬇ .md</button><button class="btn" id="uxcp">📋 Copiar todo</button></div><div class="chips uhf"><button class="btn on" data-d="">Todos</button>${B.map(([d])=>`<button class="btn" data-d="${d}">${esc(dTitle(d))}</button>`).join('')}</div>`;
  for(const [d,G] of B){h+=`<section data-book="${d}"><h3 class="thm">${esc(dTitle(d))} <small class="mut">· ${G.length}</small></h3>`;
    for(const l of G){const r=l[0],dt=new Date(r.ts);h+=`<div class="uhi"><button class="x" data-id="${r.id}" aria-label="Quitar">✕</button><a href="#/dq/${d}/${r.k}/${r.p}/"><b>${esc(r.h||('Parte '+(r.k+1)))}</b><span class="uht">${l.map(x=>esc(x.t)).join(' <span class="mut">[…]</span> ')}</span><small class="mut">${dt.getDate()} ${MESES[dt.getMonth()]} ${dt.getFullYear()}</small></a></div>`}
    h+='</section>'}
  M.innerHTML=h;
  M.querySelectorAll('.uhi .x').forEach(b=>b.onclick=()=>{uhRemove(b.dataset.id);renderUH()});
  M.querySelectorAll('.uhf .btn').forEach(b=>b.onclick=()=>{M.querySelectorAll('.uhf .btn').forEach(x=>x.classList.toggle('on',x===b));M.querySelectorAll('section[data-book]').forEach(s=>s.style.display=!b.dataset.d||s.dataset.book===b.dataset.d?'':'none')});
  const hoy=isoOf(new Date());$('#uxmd').onclick=()=>dlFile('Resaltados_'+hoy+'.md','text/markdown;charset=utf-8',uhMD(uhByBook()));
  $('#uxcp').onclick=async()=>{const b=$('#uxcp'),ok=await copyText(uhMD(uhByBook()));b.textContent=ok?'✓ Copiado':'No se pudo copiar';setTimeout(()=>b.textContent='📋 Copiar todo',1800)};
}
