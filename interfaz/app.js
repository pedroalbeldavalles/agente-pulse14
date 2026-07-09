const input = document.getElementById('imagenes');
const lista = document.getElementById('listaImagenes');
const btnAnalizar = document.getElementById('analizar');
const complejidad = document.getElementById('complejidad');
const resumen = document.getElementById('resumen');
const fase2 = document.getElementById('fase2');
const fase3 = document.getElementById('fase3');
const fase4 = document.getElementById('fase4');
const biblioteca = document.getElementById('biblioteca');
const buscar = document.getElementById('buscar');
const filtroImagen = document.getElementById('filtroImagen');
const filtroComplejidad = document.getElementById('filtroComplejidad');
const estadoBiblioteca = document.getElementById('estadoBiblioteca');
const boceto = document.getElementById('boceto');
let archivos = [];
let motivos = [];
let analisisId = '';
let ultimoSvg = '';
let tipoActivo = 'todos';

input.addEventListener('change', () => {
  archivos = Array.from(input.files || []);
  repartirPorcentajes();
  renderImagenes();
});

function repartirPorcentajes(){
  const n = archivos.length || 1;
  archivos.forEach((f,i)=>{ f._pct = Math.floor(100/n); });
  let total = archivos.reduce((a,f)=>a+f._pct,0);
  if(archivos.length) archivos[0]._pct += 100-total;
}
function renderImagenes(){
  lista.innerHTML = '';
  archivos.forEach((f,i)=>{
    const url = URL.createObjectURL(f);
    const div = document.createElement('div'); div.className='img-card';
    div.innerHTML = `<img src="${url}"><div><b>${f.name}</b><span class="muted">${(f.size/1024).toFixed(1)} KB</span></div><input class="pct" type="number" min="0" max="100" value="${f._pct}"><b>%</b>`;
    div.querySelector('.pct').addEventListener('input',e=>{f._pct=Number(e.target.value||0)});
    lista.appendChild(div);
  });
}
btnAnalizar.addEventListener('click', async()=>{
  if(!archivos.length){ alert('Selecciona al menos una imagen.'); return; }
  const total = archivos.reduce((a,f)=>a+Number(f._pct||0),0);
  if(Math.round(total)!==100){ alert('Los porcentajes deben sumar 100%. Ahora suman '+total); return; }
  btnAnalizar.disabled=true; btnAnalizar.textContent='Analizando imágenes reales...';
  const fd = new FormData();
  archivos.forEach(f=>fd.append('imagenes', f));
  fd.append('porcentajes', archivos.map(f=>f._pct).join(','));
  fd.append('complejidad', complejidad.value);
  try{
    const r = await fetch('/api/analizar-biblioteca-real',{method:'POST',body:fd});
    const data = await r.json();
    if(!r.ok) throw new Error(data.detail||'Error');
    analisisId = data.analisis_id; motivos = data.motivos || [];
    renderResumen(data.resumen||[]); renderFiltrosImagen(data.resumen||[]); renderBiblioteca();
    fase2.classList.remove('oculto'); fase3.classList.remove('oculto'); fase2.scrollIntoView({behavior:'smooth'});
  }catch(e){ alert(e.message); }
  finally{btnAnalizar.disabled=false; btnAnalizar.textContent='Analizar y crear biblioteca visual real';}
});
function renderResumen(items){
  resumen.innerHTML = items.map(it=>`<div class="res-card"><h3>Imagen ${it.imagen}</h3><p><b>${it.nombre}</b></p><p>Aportación: ${it.aportacion}%</p><p>Resolución: ${it.resolucion}</p><p>Motivos reales detectados: <b>${it.motivos_detectados}</b></p><p>Flores: ${it.flores} · Hojas: ${it.hojas} · Tallos: ${it.tallos} · Volutas: ${it.volutas} · Ornamentos: ${it.ornamentos}</p></div>`).join('');
}
function renderFiltrosImagen(items){
  filtroImagen.innerHTML='<option value="todas">Todas las imágenes</option>'+items.map(it=>`<option value="${it.imagen}">Imagen ${it.imagen}</option>`).join('');
}
document.querySelectorAll('.pill[data-tipo]').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.pill').forEach(x=>x.classList.remove('active'));b.classList.add('active');tipoActivo=b.dataset.tipo;renderBiblioteca();}));
[buscar,filtroImagen,filtroComplejidad].forEach(el=>el.addEventListener('input', renderBiblioteca));
function renderBiblioteca(){
  const q=(buscar.value||'').toLowerCase();
  const fi=filtroImagen.value; const fc=filtroComplejidad.value;
  const vis = motivos.filter(m => (tipoActivo==='todos'||m.tipo===tipoActivo) && (fi==='todas'||String(m.imagen)===fi) && (fc==='todas'||m.complejidad===fc) && (`${m.titulo} ${m.descripcion} ${m.tipo}`.toLowerCase().includes(q)));
  biblioteca.innerHTML = vis.map(m=>`<div class="motivo ${m.seleccionado?'':'no'}" data-id="${m.id}">
    <div class="motivo-top"><input class="check" type="checkbox" ${m.seleccionado?'checked':''}><div class="thumb"><img src="${m.svg_data}"/></div></div>
    <div class="motivo-body"><h3>${m.titulo}</h3><div class="muted">${m.descripcion}</div><div class="tags"><span class="tag">${m.tipo}</span><span class="tag">${m.complejidad}</span><span class="tag">${m.regiones} regiones</span><span class="tag">Imagen ${m.imagen}</span></div></div>
    <div class="motivo-actions"><button class="mod">Modificar</button><button class="danger del">🗑 Eliminar</button></div>
  </div>`).join('');
  estadoBiblioteca.textContent = `${motivos.filter(m=>m.seleccionado).length} seleccionados · ${motivos.length} motivos reales en biblioteca temporal`;
  biblioteca.querySelectorAll('.motivo').forEach(card=>{
    const id=card.dataset.id; const m=motivos.find(x=>x.id===id);
    card.querySelector('.check').addEventListener('change',e=>{m.seleccionado=e.target.checked;renderBiblioteca();});
    card.querySelector('.del').addEventListener('click',()=>{m.seleccionado=false;renderBiblioteca();});
    card.querySelector('.mod').addEventListener('click',()=>{const txt=prompt('Instrucción para modificar este motivo. Ejemplo: simplificar contornos, aumentar detalle, usarlo solo como flor secundaria.', m.instrucciones||''); if(txt!==null){m.instrucciones=txt;m.descripcion='Modificado por instrucción: '+txt;renderBiblioteca();}});
  });
}
document.getElementById('crearBoceto').addEventListener('click', async()=>{
  const ids = motivos.filter(m=>m.seleccionado).map(m=>m.id);
  if(!ids.length){alert('Selecciona al menos un motivo.');return;}
  const r = await fetch('/api/crear-boceto-real',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({analisis_id:analisisId,ids})});
  const data = await r.json(); if(!r.ok){alert(data.detail||'Error');return;}
  ultimoSvg = data.svg; boceto.src=data.svg_data; fase4.classList.remove('oculto'); fase4.scrollIntoView({behavior:'smooth'});
});
document.getElementById('descargarSvg').addEventListener('click',()=>{ if(!ultimoSvg) return; const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([ultimoSvg],{type:'image/svg+xml'})); a.download='boceto_contornos_reales.svg'; a.click(); });
document.getElementById('volverBiblioteca').addEventListener('click',()=>fase3.scrollIntoView({behavior:'smooth'}));
document.getElementById('volverCargar').addEventListener('click',()=>document.getElementById('fase1').scrollIntoView({behavior:'smooth'}));
