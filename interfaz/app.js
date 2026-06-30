const fileInput=document.getElementById('fileInput');
const gallery=document.getElementById('gallery');
const mainImage=document.getElementById('mainImage');
const emptyViewer=document.getElementById('emptyViewer');
const viewer=document.getElementById('viewer');
const zoomLabel=document.getElementById('zoomLabel');
const countImages=document.getElementById('countImages');
const totalPercent=document.getElementById('totalPercent');
const freePercent=document.getElementById('freePercent');
const usedImages=document.getElementById('usedImages');
const totalBox=document.getElementById('totalBox');
const createBtn=document.getElementById('createBtn');
const statusEl=document.getElementById('status');
const pName=document.getElementById('pName');
const pRes=document.getElementById('pRes');
const pSize=document.getElementById('pSize');
const pType=document.getElementById('pType');
const pPercent=document.getElementById('pPercent');

let images=[];
let selectedId=null;
let scale=1,minScale=1,x=0,y=0,drag=false,lastX=0,lastY=0;

function fmtSize(bytes){
  if(bytes<1024)return bytes+' B';
  if(bytes<1024*1024)return (bytes/1024).toFixed(1)+' KB';
  return (bytes/(1024*1024)).toFixed(2)+' MB';
}
function uid(){return crypto.randomUUID ? crypto.randomUUID() : String(Date.now()+Math.random());}

fileInput.addEventListener('change',()=>{
  const files=[...fileInput.files];
  files.forEach(file=>{
    const url=URL.createObjectURL(file);
    const img=new Image();
    const item={id:uid(),file,url,name:file.name,size:file.size,type:file.type||'imagen',w:0,h:0,percent:0};
    img.onload=()=>{
      item.w=img.naturalWidth; item.h=img.naturalHeight;
      render();
      if(!selectedId) selectImage(item.id);
    };
    img.src=url;
    images.push(item);
  });
  fileInput.value='';
  render();
});

function totalExcept(id){return images.reduce((sum,img)=>sum+(img.id===id?0:Number(img.percent||0)),0);}
function total(){return images.reduce((sum,img)=>sum+Number(img.percent||0),0);}
function setPercent(id,value){
  const img=images.find(i=>i.id===id);
  if(!img)return;
  let val=parseInt(value,10);
  if(isNaN(val)) val=0;
  val=Math.max(0,Math.min(100,val));
  const available=100-totalExcept(id);
  if(val>available) val=available;
  img.percent=val;
  render();
  if(selectedId===id) showProps(img);
}
function deleteImage(id){
  const idx=images.findIndex(i=>i.id===id);
  if(idx<0)return;
  URL.revokeObjectURL(images[idx].url);
  images.splice(idx,1);
  if(selectedId===id) selectedId=images[0]?.id||null;
  render();
  if(selectedId) selectImage(selectedId); else clearViewer();
}
function render(){
  gallery.innerHTML='';
  images.forEach(img=>{
    const row=document.createElement('div');
    row.className='image-row'+(img.id===selectedId?' active':'');
    row.addEventListener('click',e=>{
      if(e.target.tagName==='INPUT'||e.target.tagName==='BUTTON')return;
      selectImage(img.id);
    });
    const thumb=document.createElement('div');
    thumb.className='thumb';
    const im=document.createElement('img');
    im.src=img.url;
    thumb.appendChild(im);
    const info=document.createElement('div');
    const name=document.createElement('div');
    name.className='name'; name.textContent=img.name;
    const meta=document.createElement('div');
    meta.className='meta'; meta.textContent=(img.w&&img.h?`${img.w} × ${img.h}`:'Cargando...')+' · '+fmtSize(img.size);
    info.appendChild(name); info.appendChild(meta);
    const pbox=document.createElement('div');
    pbox.className='percent-box';
    const input=document.createElement('input');
    input.type='number'; input.min='0'; input.max='100'; input.step='1'; input.value=img.percent;
    input.addEventListener('input',()=>setPercent(img.id,input.value));
    input.addEventListener('change',()=>setPercent(img.id,input.value));
    const ps=document.createElement('span'); ps.textContent='%';
    pbox.appendChild(input); pbox.appendChild(ps);
    const del=document.createElement('button');
    del.className='delete'; del.textContent='×'; del.title='Eliminar imagen';
    del.addEventListener('click',()=>deleteImage(img.id));
    row.appendChild(thumb); row.appendChild(info); row.appendChild(pbox); row.appendChild(del);
    gallery.appendChild(row);
  });
  const t=total();
  countImages.textContent=images.length;
  totalPercent.textContent=t+'%';
  freePercent.textContent=(100-t)+'%';
  usedImages.textContent=images.filter(i=>i.percent>0).length;
  totalBox.className=t===100?'total-ok':'total-warn';
  createBtn.disabled=t!==100 || images.length===0;
  statusEl.textContent=t===100?'Listo. Pulsa Validar imágenes para comprobarlo en el servidor.':'Para continuar, el total de porcentajes debe ser exactamente 100%.';
  statusEl.className='status '+(t===100?'ok':'');
}
function selectImage(id){
  const img=images.find(i=>i.id===id);
  if(!img)return;
  selectedId=id;
  mainImage.src=img.url;
  mainImage.style.display='block';
  emptyViewer.style.display='none';
  mainImage.onload=()=>fitImage();
  showProps(img);
  render();
}
function showProps(img){
  pName.textContent=img.name;
  pRes.textContent=img.w&&img.h?`${img.w} × ${img.h}`:'—';
  pSize.textContent=fmtSize(img.size);
  pType.textContent=img.type;
  pPercent.textContent=img.percent+'%';
}
function clearViewer(){
  mainImage.removeAttribute('src');
  mainImage.style.display='none';
  emptyViewer.style.display='flex';
  pName.textContent=pRes.textContent=pSize.textContent=pType.textContent=pPercent.textContent='—';
}
function fitImage(){
  const img=images.find(i=>i.id===selectedId);
  if(!img||!img.w||!img.h)return;
  const r=viewer.getBoundingClientRect();
  minScale=Math.min((r.width-40)/img.w,(r.height-40)/img.h);
  scale=minScale;
  x=(r.width-img.w*scale)/2;
  y=(r.height-img.h*scale)/2;
  applyTransform();
}
function applyTransform(){
  mainImage.style.transform=`translate(${x}px, ${y}px) scale(${scale})`;
  zoomLabel.textContent='Zoom '+Math.round((scale/minScale)*100)+'%';
}
viewer.addEventListener('wheel',e=>{
  if(!mainImage.src)return;
  e.preventDefault();
  const rect=viewer.getBoundingClientRect();
  const mx=e.clientX-rect.left, my=e.clientY-rect.top;
  const old=scale;
  const factor=e.deltaY<0?1.14:1/1.14;
  scale=Math.max(minScale,Math.min(20*minScale,scale*factor));
  x=mx-(mx-x)*(scale/old);
  y=my-(my-y)*(scale/old);
  applyTransform();
},{passive:false});
viewer.addEventListener('contextmenu',e=>e.preventDefault());
viewer.addEventListener('mousedown',e=>{
  if(e.button!==2||!mainImage.src)return;
  drag=true; lastX=e.clientX; lastY=e.clientY;
});
window.addEventListener('mousemove',e=>{
  if(!drag)return;
  x+=e.clientX-lastX; y+=e.clientY-lastY;
  lastX=e.clientX; lastY=e.clientY;
  applyTransform();
});
window.addEventListener('mouseup',()=>drag=false);
viewer.addEventListener('dblclick',fitImage);

createBtn.addEventListener('click',async()=>{
  if(total()!==100 || images.length===0)return;
  createBtn.disabled=true;
  statusEl.textContent='Validando imágenes en el servidor...';
  const form=new FormData();
  images.forEach(img=>form.append('imagenes', img.file, img.name));
  form.append('porcentajes_json', JSON.stringify(images.map(img=>img.percent)));
  try{
    const res=await fetch('/api/validar-imagenes',{method:'POST',body:form});
    const data=await res.json();
    if(!res.ok)throw new Error(data.detail||'Error de validación');
    statusEl.textContent='Servidor correcto: imágenes y porcentajes validados. Siguiente módulo: motor IA.';
    statusEl.className='status ok';
  }catch(err){
    statusEl.textContent='Error: '+err.message;
    statusEl.className='status bad';
  }finally{
    render();
  }
});
