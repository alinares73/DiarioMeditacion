/* ===== Meditación diaria: calendario litúrgico (rito romano, España) ===== */
const LIT=(()=>{
  const D=(y,m,d)=>new Date(y,m-1,d),dd=(a,b)=>Math.round((a-b)/864e5),plus=(dt,n)=>new Date(dt.getFullYear(),dt.getMonth(),dt.getDate()+n);
  const p2=n=>String(n).padStart(2,'0'),iso=dt=>dt.getFullYear()+'-'+p2(dt.getMonth()+1)+'-'+p2(dt.getDate());
  function easter(y){const a=y%19,b=Math.floor(y/100),c=y%100,d=Math.floor(b/4),e=b%4,f=Math.floor((b+8)/25),g=Math.floor((b-f+1)/3),h=(19*a+b-d-g+15)%30,i=Math.floor(c/4),k=c%4,l=(32+2*e+2*i-h-k)%7,m=Math.floor((a+11*h+22*l)/451),mo=Math.floor((h+l-7*m+114)/31),da=((h+l-7*m+114)%31)+1;return D(y,mo,da)}
  const adv1=y=>{const x=D(y,12,25);return plus(x,-((x.getDay()+6)%7+1)-21)}   /* 4.º domingo antes de Navidad */
  const ROMAN=['','I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII','XIII','XIV','XV','XVI','XVII','XVIII','XIX','XX','XXI','XXII','XXIII','XXIV','XXV','XXVI','XXVII','XXVIII','XXIX','XXX','XXXI','XXXII','XXXIII','XXXIV'];
  const DN=['Domingo','Lunes','Martes','Miércoles','Jueves','Viernes','Sábado'];
  const cache=new Map();
  function year(y){ /* datos del año civil y */
    if(cache.has(y))return cache.get(y);
    const E=easter(y),A1=adv1(y),j6=D(y,1,6),bau=plus(j6,7-j6.getDay()); /* domingo después del 6 de enero */
    let sj=[];{let s=D(y,3,19);s=plus(s,-(s.getDay()||7));for(let i=0;i<7;i++)sj.unshift(plus(s,-7*i))} /* 7 domingos antes del 19 de marzo */
    const o={E,A1,bau,ash:plus(E,-46),pent:plus(E,49),sj};cache.set(y,o);return o}
  function cycleOf(dt){const y=dt>=adv1(dt.getFullYear())?dt.getFullYear()+1:dt.getFullYear();return ['C','A','B'][y%3]}
  /* Devuelve {keys:[[clave,grupo]], name, cyc} ; grupo: f (fiesta), t (tiempo), x (devoción) */
  function day(isoS,hint){
    const [y,m,d]=isoS.split('-').map(Number),dt=D(y,m,d),w=dt.getDay(),Y=year(y),K=[];let name='';
    const add=(k,g)=>{if(!K.some(x=>x[0]===k))K.push([k,g])};
    const md=p2(m)+'-'+p2(d),tE=dd(dt,Y.E);
    const H=(hint||'').toUpperCase();
    /* ---- tiempo */
    if(dt>=Y.A1){ /* Adviento y Navidad (diciembre) */
      if(m===12&&d>=25){name=d===25?'Natividad del Señor':'Octava de Navidad'}
      else{const wk=Math.floor(dd(dt,Y.A1)/7)+1;name=(w?DN[w]+' de la '+wk+'.ª semana':ROMAN[wk]+' Domingo')+' de Adviento';
        if(!(m===12&&d>=17&&w))add('A'+wk+'-'+w,'t');if(m===12&&d>=17)add('F'+md,'t')}
    }else if(dt<=Y.bau&&m===1){
      if(dt.getTime()===Y.bau.getTime()){add('BAU','f');name='Bautismo del Señor'}
      else if(d===1)name='Santa María, Madre de Dios';else if(d===6)name='Epifanía del Señor';
      else if(d<6){name='Tiempo de Navidad';if(w===0){add('NAV2','t');name='II Domingo de Navidad'}}
      else{name=DN[w]+' después de Epifanía';add('N'+md,'t');add('EPI-'+w,'t')}
    }else if(dt<Y.ash){const wk=Math.floor(dd(dt,Y.bau)/7)+1;add('T'+wk+'-'+w,'t');name=w?DN[w]+' de la '+wk+'.ª semana del Tiempo Ordinario':ROMAN[wk]+' Domingo del Tiempo Ordinario'}
    else if(tE<-42){add('C0-'+w,'t');name=w===3?'Miércoles de Ceniza':DN[w]+' después de Ceniza'}
    else if(tE<-7){const wk=Math.floor((tE+42)/7)+1;add('C'+wk+'-'+w,'t');name=w?DN[w]+' de la '+wk+'.ª semana de Cuaresma':ROMAN[wk]+' Domingo de Cuaresma'}
    else if(tE<0){add('SS-'+w,'t');name=w?DN[w]+' Santo':'Domingo de Ramos'}
    else if(tE<49){const wk=Math.floor(tE/7)+1;add('P'+wk+'-'+w,'t');name=tE===0?'Domingo de Resurrección':wk===1?DN[w]+' de la Octava de Pascua':w?DN[w]+' de la '+wk+'.ª semana de Pascua':ROMAN[wk]+' Domingo de Pascua'}
    else if(tE===49){add('PENT','f');name='Pentecostés'}
    else{const wk2=34-Math.floor((dd(Y.A1,dt)-1)/7);add('T'+wk2+'-'+w,'t');name=w?DN[w]+' de la '+wk2+'.ª semana del Tiempo Ordinario':ROMAN[wk2]+' Domingo del Tiempo Ordinario';if(wk2===34&&!w){add('CR','f');name='Jesucristo, Rey del Universo'}}
    /* ---- Navidad (fechas) */
    if(m===12&&d>=25||m===1&&d<=6)add('F'+md,'t');
    if(m===12&&d>=26&&d<=31&&(w===0||(d===30&&D(y,12,25).getDay()===0))){add('SF','f');name='Sagrada Familia'}
    /* ---- fiestas móviles */
    if(tE===53){add('SUMOSAC','f');name+=' · Jesucristo, Sumo y Eterno Sacerdote'}
    if(tE===56){add('TRIN','f');name='Santísima Trinidad'}
    if(tE===63){add('CORPUS','f');name='Santísimo Cuerpo y Sangre de Cristo'}
    if(tE>=61&&tE<=67)add('CORPUS+'+(tE-60),'x');
    if(tE===68){add('SCJ','f');name='Sagrado Corazón de Jesús'}
    if(tE===69){add('ICM','f');name+=' · Inmaculado Corazón de María'}
    /* Ascensión: en España, VII domingo de Pascua (salvo que el Diario diga otra cosa) */
    const ascHint=/ASCENSI/.test(H);
    if((ascHint&&(tE===39||tE===42))||(!hint&&tE===42)){add('ASC','f');name='Ascensión del Señor'}
    else if(tE===39)add('ASC','t'); /* jueves de la Ascensión (donde no se traslada al domingo) */
    /* ---- santoral (fecha fija) con traslados */
    let fk='F'+md;
    const inHoly=t=>t>=-7&&t<=7;
    if(md==='03-19'&&(inHoly(tE)||w===0))fk=null;
    if(md==='03-25'&&(inHoly(tE)||w===0))fk=null;
    {const j=D(y,3,19),tj=dd(j,Y.E);if(inHoly(tj)&&tE===-8)add('F03-19','f');else if(j.getDay()===0&&tj<-7&&md==='03-20')add('F03-19','f')}
    {const a=D(y,3,25),ta=dd(a,Y.E);if(inHoly(ta)&&tE===8)add('F03-25','f');else if(a.getDay()===0&&ta<-7&&md==='03-26')add('F03-25','f')}
    if(fk&&!K.some(x=>x[0]===fk))add(fk,'f');
    /* ---- devociones */
    const sji=Y.sj.findIndex(s=>s.getTime()===dt.getTime());if(sji>=0)add('SJ7-'+(sji+1),'x');
    return {keys:K,name,cyc:cycleOf(dt)}
  }
  return {day,easter,iso}
})();
if(typeof module!=='undefined')module.exports=LIT;
