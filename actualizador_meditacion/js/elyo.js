/* Él y yo: botón ◀ para volver a leer los puntos de días anteriores */
function eyPrevInit(st){
  const b=$('#eyprev');if(!b)return;let back=st.start;b.disabled=back<=0;
  b.onclick=()=>{if(back<=0)return;const from=Math.max(0,back-6),L=$('#eyl');
    let sep=L.querySelector('.eysep.old');
    if(!sep){const hoy=document.createElement('p');hoy.className='mut eysep';hoy.textContent='Hoy';L.prepend(hoy);sep=document.createElement('p');sep.className='mut eysep old';sep.textContent='Puntos de días anteriores';L.prepend(sep)}
    const box=document.createElement('div');box.innerHTML=eyCards(st,from,back-from);const first=box.firstElementChild;sep.after(...box.children);back=from;b.disabled=back<=0;
    if(first){first.scrollIntoView({block:'start',behavior:'smooth'});setTimeout(()=>window.scrollBy(0,-70),350)}}
}
