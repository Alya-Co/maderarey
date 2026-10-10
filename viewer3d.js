/*
 * viewer3d.js — 3D-просмотр дома на странице house.html (MaderaRey).
 *
 * Как работает:
 *  - Берёт id дома из адреса (?casa=...), проверяет, есть ли houses/<id>/model3d.json.
 *  - Если модель есть — добавляет на главное фото кнопку «Ver en 3D».
 *  - По нажатию открывает окно с 3D: вращение, без крыши, план, вид изнутри.
 *  - Библиотека three.js загружается только при открытии окна (страница не тяжелеет).
 *  - Нет model3d.json — ничего не появляется, страница работает как раньше.
 * Создаёт model3d.json скрипт build_3d_models.py.
 */
(function () {
  'use strict';
  var THREE_URL = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
  var ORBIT_URL = 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js';

  function houseId() {
    var p = new URLSearchParams(location.search).get('casa');
    if (p) return p;
    var m = location.pathname.match(/houses\/([^/]+)\//);
    return m ? decodeURIComponent(m[1]) : null;
  }
  var id = houseId();
  if (!id) return;
  var modelUrl = 'houses/' + encodeURIComponent(id) + '/model3d.json';
  var model = null;

  function loadScript(src) {
    return new Promise(function (res, rej) {
      var s = document.createElement('script'); s.src = src; s.onload = res; s.onerror = rej; document.head.appendChild(s);
    });
  }
  function libs() {
    if (window.THREE && THREE.OrbitControls) return Promise.resolve();
    return (window.THREE ? Promise.resolve() : loadScript(THREE_URL)).then(function () { return loadScript(ORBIT_URL); });
  }

  // ---------- styles ----------
  var css = '' +
    '.v3d-btn{position:absolute;left:12px;bottom:12px;z-index:3;display:inline-flex;align-items:center;gap:8px;' +
    'background:rgba(255,255,255,.95);color:#1B5E20;border:2px solid #2E7D32;border-radius:999px;padding:9px 16px;' +
    'font:700 14px/1 "Segoe UI",system-ui,-apple-system,sans-serif;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,.15)}' +
    '.v3d-btn:hover{background:#2E7D32;color:#fff}' +
    '.v3d-btn svg{width:18px;height:18px}' +
    '.v3d-modal{position:fixed;inset:0;z-index:2147483000;background:rgba(20,26,22,.72);display:flex;align-items:center;justify-content:center;padding:16px}' +
    '.v3d-box{position:relative;width:min(1200px,100%);height:min(780px,100%);background:#eef1ec;border-radius:12px;overflow:hidden;' +
    'font-family:"Segoe UI",system-ui,-apple-system,sans-serif;color:#1A1A1A}' +
    '.v3d-box canvas{display:block;width:100%;height:100%;touch-action:none}' +
    '.v3d-top{position:absolute;left:12px;top:12px;right:60px;display:flex;flex-wrap:wrap;gap:6px}' +
    '.v3d-top button,.v3d-tg label{font:600 13px/1 inherit;font-family:inherit;color:#1A1A1A;background:#fff;border:1px solid #d6dbd3;border-radius:999px;padding:9px 14px;cursor:pointer}' +
    '.v3d-top button[aria-pressed="true"]{background:#2E7D32;border-color:#2E7D32;color:#fff}' +
    '.v3d-x{position:absolute;right:12px;top:12px;width:38px;height:38px;border-radius:50%;border:1px solid #d6dbd3;background:#fff;font-size:22px;line-height:1;cursor:pointer}' +
    '.v3d-tg{position:absolute;left:12px;bottom:12px;display:flex;gap:6px;flex-wrap:wrap}' +
    '.v3d-tg label{display:inline-flex;align-items:center;gap:8px}.v3d-tg input{accent-color:#2E7D32;margin:0}' +
    '.v3d-cta{position:absolute;right:12px;bottom:12px;background:#25D366;color:#fff;border:0;border-radius:8px;padding:12px 16px;font:700 14px/1 inherit;font-family:inherit;cursor:pointer}' +
    '.v3d-cta:hover{background:#1da851}' +
    '.v3d-note{position:absolute;right:12px;bottom:58px;font-size:11px;color:#555;background:rgba(255,255,255,.8);padding:3px 8px;border-radius:4px}' +
    '.v3d-dim{position:absolute;transform:translate(-50%,-50%);font:600 12px/1 ui-monospace,Menlo,Consolas,monospace;background:#fff;border:1px solid #d6dbd3;border-radius:4px;padding:3px 6px;pointer-events:none;white-space:nowrap}' +
    '.v3d-load{position:absolute;inset:0;display:grid;place-items:center;color:#555;font-size:14px}' +
    '.v3d-box button:focus-visible,.v3d-btn:focus-visible{outline:2px solid #2E7D32;outline-offset:2px}' +
    '@media(max-width:640px){.v3d-modal{padding:0}.v3d-box{height:100%;border-radius:0}.v3d-note{display:none}.v3d-cta{left:auto}.v3d-tg{bottom:60px}}';
  var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);

  // ---------- button on the gallery (only if model exists) ----------
  function addButton() {
    var host = document.getElementById('gallery-main');
    if (!host || host.querySelector('.v3d-btn')) return;
    if (getComputedStyle(host).position === 'static') host.style.position = 'relative';
    var b = document.createElement('button');
    b.type = 'button'; b.className = 'v3d-btn';
    b.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M12 2 3 7v10l9 5 9-5V7z"/><path d="M3 7l9 5 9-5M12 12v10"/></svg>Ver en 3D';
    b.addEventListener('click', function (e) { e.stopPropagation(); open(); });
    host.appendChild(b);
  }
  fetch(modelUrl, { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (m) {
    if (!m || !m.items) return;
    model = m;
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', addButton); else addButton();
  }).catch(function () {});

  var modal = null;
  function close() {
    if (!modal) return;
    modal.cleanup && modal.cleanup();
    modal.remove(); modal = null; document.body.style.overflow = '';
    document.removeEventListener('keydown', onKey);
  }
  function onKey(e) { if (e.key === 'Escape') close(); }

  function open() {
    if (modal) return;
    modal = document.createElement('div'); modal.className = 'v3d-modal';
    modal.setAttribute('role', 'dialog'); modal.setAttribute('aria-modal', 'true'); modal.setAttribute('aria-label', 'Vista 3D de la casa');
    modal.innerHTML = '<div class="v3d-box"><canvas></canvas><div class="v3d-load">Cargando 3D…</div>' +
      '<div class="v3d-top" role="group" aria-label="Vistas">' +
      '<button type="button" data-v="ext" aria-pressed="true">Exterior</button>' +
      '<button type="button" data-v="open" aria-pressed="false">Sin tejado</button>' +
      '<button type="button" data-v="plan" aria-pressed="false">Planta</button>' +
      '<button type="button" data-v="int" aria-pressed="false">Interior</button></div>' +
      '<button type="button" class="v3d-x" aria-label="Cerrar">×</button>' +
      '<div class="v3d-tg"><label><input type="checkbox" class="v3d-roof" checked>Tejado</label><label><input type="checkbox" class="v3d-dims" checked>Medidas</label></div>' +
      '<div class="v3d-note">Recreación 3D orientativa · mobiliario no incluido</div>' +
      '<button type="button" class="v3d-cta">Pedir precio por WhatsApp</button></div>';
    document.body.appendChild(modal); document.body.style.overflow = 'hidden';
    modal.addEventListener('click', function (e) { if (e.target === modal) close(); });
    modal.querySelector('.v3d-x').addEventListener('click', close);
    document.addEventListener('keydown', onKey);
    modal.querySelector('.v3d-cta').addEventListener('click', function () {
      var wa = document.getElementById('btn-wa-main');
      close();
      if (wa) wa.click();
    });
    libs().then(function () { if (modal) build(modal.querySelector('.v3d-box')); })
      .catch(function () { var l = modal && modal.querySelector('.v3d-load'); if (l) l.textContent = 'No se pudo cargar la vista 3D. Revisa la conexión.'; });
  }

  // ---------- 3D scene ----------
  var texCache = null;
  function build(box) {
    var canvas = box.querySelector('canvas');
    var items = model.items;
    var mn=[1e9,1e9,1e9], mx=[-1e9,-1e9,-1e9];
    items.forEach(function(it){it.f.forEach(function(f){f.forEach(function(p){for(var d=0;d<3;d++){mn[d]=Math.min(mn[d],p[d]);mx[d]=Math.max(mx[d],p[d])}})})});
    var cx=(mn[0]+mx[0])/2, cy=(mn[1]+mx[1])/2;
    var V=function(p){return new THREE.Vector3(p[0]-cx,p[2],-(p[1]-cy))};
    var span=Math.max(mx[0]-mn[0],mx[1]-mn[1]);

    var renderer=new THREE.WebGLRenderer({canvas:canvas,antialias:true,alpha:true});
    renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
    renderer.shadowMap.enabled=true; renderer.shadowMap.type=THREE.PCFSoftShadowMap;
    renderer.outputEncoding=THREE.sRGBEncoding;
    var scene=new THREE.Scene();
    var camera=new THREE.PerspectiveCamera(42,1,0.05,300);
    var controls=new THREE.OrbitControls(camera,canvas);
    controls.enableDamping=true; controls.dampingFactor=0.08; controls.maxPolarAngle=Math.PI*0.495;
    scene.add(new THREE.HemisphereLight(0xfff4e0,0x8a7558,0.9));
    var sun=new THREE.DirectionalLight(0xfff1dc,0.9);
    sun.position.set(span*0.8,span*1.2,span*0.6); sun.castShadow=true; sun.shadow.mapSize.set(2048,2048);
    var sc=span*0.9; Object.assign(sun.shadow.camera,{left:-sc,right:sc,top:sc,bottom:-sc,near:0.5,far:span*4}); sun.shadow.bias=-0.0006;
    scene.add(sun);

    var built = (function(){
// ---- procedural wood textures (canvas), 1 texture tile = TILE metres ----
function rng(seed){return()=>{seed=(seed*16807)%2147483647;return(seed-1)/2147483646}}
function grain(ctx,x,y,w,h,base,r,dir){
  // base fill + long fibres + occasional knot
  ctx.fillStyle=base;ctx.fillRect(x,y,w,h);
  const L=dir==='h'?w:h, S=dir==='h'?h:w;
  for(let i=0;i<S*0.9;i++){
    const o=r()*S, a=0.04+r()*0.08, amp=1+r()*3, f=0.004+r()*0.01, ph=r()*6;
    ctx.strokeStyle=r()<0.5?`rgba(90,52,22,${a})`:`rgba(255,236,200,${a*0.8})`;
    ctx.lineWidth=0.6+r()*1.2;ctx.beginPath();
    for(let t=0;t<=L;t+=6){const d=o+Math.sin(t*f+ph)*amp;dir==='h'?ctx.lineTo(x+t,y+d):ctx.lineTo(x+d,y+t)}
    ctx.stroke();
  }
  if(r()<0.35){const kx=x+(dir==='h'?r()*w:w/2), ky=y+(dir==='h'?h/2:r()*h), kr=S*0.18;
    const g=ctx.createRadialGradient(kx,ky,0,kx,ky,kr);g.addColorStop(0,'rgba(80,45,18,.75)');g.addColorStop(1,'rgba(80,45,18,0)');
    ctx.fillStyle=g;ctx.beginPath();ctx.ellipse(kx,ky,dir==='h'?kr*1.8:kr,dir==='h'?kr:kr*1.8,0,0,Math.PI*2);ctx.fill()}
}
function boards(opts){
  // opts: px, count (boards per tile), dir 'h' (boards run horizontally) | 'v', tones, seams (staggered butt joints), groove
  const c=document.createElement('canvas');c.width=c.height=opts.px;const ctx=c.getContext('2d');const r=rng(opts.seed);
  const n=opts.count, step=opts.px/n;
  for(let i=0;i<n;i++){
    const tone=opts.tones[Math.floor(r()*opts.tones.length)];
    const segs=opts.seams?[[0,0.35+r()*0.3],[null,1]]:[[0,1]];
    let start=0;
    const cuts=opts.seams?[0,0.3+r()*0.4,1]:[0,1];
    for(let j=0;j<cuts.length-1;j++){
      const t0=cuts[j]*opts.px,t1=cuts[j+1]*opts.px, tn=j?opts.tones[Math.floor(r()*opts.tones.length)]:tone;
      if(opts.dir==='h')grain(ctx,t0,i*step,t1-t0,step,tn,r,'h');else grain(ctx,i*step,t0,step,t1-t0,tn,r,'v');
      if(opts.seams&&j){ctx.fillStyle='rgba(60,34,14,.55)';opts.dir==='h'?ctx.fillRect(t0-1,i*step,2,step):ctx.fillRect(i*step,t0-1,step,2)}
    }
    if(opts.dir==='h'&&opts.figure){
      const y0=i*step;
      for(let k=0;k<opts.figure.knots;k++){const kx=r()*opts.px,ky=y0+step*(0.2+r()*0.6),kr=1.5+r()*2.5;
        ctx.fillStyle=`rgba(70,48,28,${0.55+r()*0.3})`;ctx.beginPath();ctx.ellipse(kx,ky,kr*1.4,kr,0,0,Math.PI*2);ctx.fill();
        ctx.strokeStyle='rgba(90,62,36,.25)';ctx.lineWidth=1;ctx.beginPath();ctx.ellipse(kx,ky,kr*3.2,kr*1.8,0,0,Math.PI*2);ctx.stroke()}
      for(let k=0;k<opts.figure.arcs;k++){const ax=r()*opts.px,ay=y0+step*(0.3+r()*0.4),len=30+r()*70;
        for(let q=0;q<4;q++){const d=q*4+2;ctx.strokeStyle=`rgba(110,78,46,${0.22-q*0.04})`;ctx.lineWidth=1;ctx.beginPath();
          ctx.moveTo(ax+len,ay-d*0.9);ctx.quadraticCurveTo(ax-d,ay,ax+len,ay+d*0.9);ctx.stroke()}}
    }
    if(opts.dir==='v'&&opts.gap){ctx.fillStyle='rgba(30,22,16,.85)';ctx.fillRect(i*step,0,opts.gap,opts.px)}
    // groove + rounded-log shading between boards
    const g=opts.dir==='h'?ctx.createLinearGradient(0,i*step,0,(i+1)*step):ctx.createLinearGradient(i*step,0,(i+1)*step,0);
    g.addColorStop(0,`rgba(255,240,215,${opts.round*0.5})`);g.addColorStop(0.5,'rgba(0,0,0,0)');g.addColorStop(1,`rgba(50,28,10,${opts.round})`);
    ctx.fillStyle=g;opts.dir==='h'?ctx.fillRect(0,i*step,opts.px,step):ctx.fillRect(i*step,0,step,opts.px);
    ctx.fillStyle='rgba(45,25,8,.8)';opts.dir==='h'?ctx.fillRect(0,(i+1)*step-opts.groove,opts.px,opts.groove):ctx.fillRect((i+1)*step-opts.groove,0,opts.groove,opts.px);
  }
  return c;
}
const maxAniso=renderer.capabilities.getMaxAnisotropy();
function tex(canvas,tile){const t=new THREE.CanvasTexture(canvas);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.encoding=THREE.sRGBEncoding;t.anisotropy=maxAniso;t.tileM=tile;return t}
const warm=['#ead6a6','#e5cf9c','#eddbb0','#e2ca96','#e8d3a3'];
const T={
  wall: tex(boards({px:1024,count:9,dir:'h',tones:warm,seams:false,groove:2,round:.14,seed:11,figure:{knots:2,arcs:1}}),1.0),
  floor:tex(boards({px:1024,count:8,dir:'v',tones:['#8a6e52','#816649','#91755a','#7a6045','#866a4f'],seams:true,groove:1,round:.06,gap:5,seed:23}),1.0),
  beam: tex(boards({px:512,count:2,dir:'h',tones:['#e6cf9e','#e0c894'],seams:false,groove:1,round:.08,seed:5,figure:{knots:1,arcs:1}}),0.5),
  frame:tex(boards({px:512,count:3,dir:'h',tones:['#eedcb2','#e9d5a8'],seams:false,groove:1,round:.06,seed:9}),0.5),
  door: tex(boards({px:512,count:5,dir:'v',tones:['#e2ca98','#dcc390','#e6cf9f'],seams:false,groove:2,round:.12,seed:31}),0.8),
  roof: tex(boards({px:1024,count:10,dir:'v',tones:['#b0926d','#aa8c67','#b59873','#a58864'],seams:true,groove:2,round:.1,seed:41}),1.0)
};
const M=(map,extra)=>new THREE.MeshStandardMaterial(Object.assign({map,roughness:.82,side:THREE.DoubleSide,bumpMap:map,bumpScale:0.015},extra));
const mats={
  wall:M(T.wall), gable:M(T.wall), floor:M(T.floor), beam:M(T.beam), joist:M(T.beam),
  roof:M(T.roof,{roughness:.95,bumpScale:0.006}), door:M(T.door),
  window:M(T.frame),
  glass:new THREE.MeshStandardMaterial({color:0x9fc3d6,roughness:.08,metalness:.1,transparent:true,opacity:.32,side:THREE.DoubleSide,depthWrite:false})
};

      return {T:T,mats:mats};
    })();
    var mats=built.mats;
    function tileOf(k){var m=mats[k]||mats.wall;return m.map?m.map.tileM:1}
    function polyTris(poly,pos,uv,tile){
      var n=[0,0,0];
      for(var i=0;i<poly.length;i++){var a=poly[i],b=poly[(i+1)%poly.length];
        n[0]+=(a[1]-b[1])*(a[2]+b[2]); n[1]+=(a[2]-b[2])*(a[0]+b[0]); n[2]+=(a[0]-b[0])*(a[1]+b[1]);}
      var ax=n.map(Math.abs), drop=ax.indexOf(Math.max.apply(null,ax));
      var u=drop===0?1:0, v=drop===2?1:2;
      var c2=poly.map(function(p){return new THREE.Vector2(p[u],p[v])});
      THREE.ShapeUtils.triangulateShape(c2,[]).forEach(function(t){t.forEach(function(i){var p=poly[i],w=V(p);pos.push(w.x,w.y,w.z);uv.push(p[u]/tile,p[v]/tile)})});
    }
    var groups={}, buckets={};
    items.forEach(function(it){var b=(buckets[it.k]=buckets[it.k]||{p:[],u:[]});var tl=tileOf(it.k);it.f.forEach(function(f){polyTris(f,b.p,b.u,tl)})});
    Object.keys(buckets).forEach(function(k){var b=buckets[k];
      var g=new THREE.BufferGeometry(); g.setAttribute('position',new THREE.Float32BufferAttribute(b.p,3)); g.setAttribute('uv',new THREE.Float32BufferAttribute(b.u,2)); g.computeVertexNormals();
      var m=new THREE.Mesh(g,mats[k]||mats.wall); m.castShadow=true; m.receiveShadow=true; groups[k]=m; scene.add(m);
    });
    items.filter(function(it){return it.k==='window'}).forEach(function(it){
      var b=new THREE.Box3(); it.f.forEach(function(f){f.forEach(function(p){b.expandByPoint(V(p))})});
      var s=new THREE.Vector3(), c=new THREE.Vector3(); b.getSize(s); b.getCenter(c);
      var thin=s.x<s.z?'x':'z';
      var m=new THREE.Mesh(new THREE.PlaneGeometry(thin==='x'?s.z:s.x,s.y),mats.glass); m.position.copy(c); if(thin==='x')m.rotation.y=Math.PI/2; scene.add(m);
    });
    var ground=new THREE.Mesh(new THREE.CircleGeometry(span*3,64),new THREE.MeshStandardMaterial({color:0xb2baa8,roughness:1}));
    ground.rotation.x=-Math.PI/2; ground.position.y=Math.min(-0.2,mn[2]-0.02); ground.receiveShadow=true; scene.add(ground);

    // dimensions from the wall outline
    var wb=new THREE.Box3(); items.filter(function(it){return it.k==='wall'}).forEach(function(it){it.f.forEach(function(f){f.forEach(function(p){wb.expandByPoint(V(p))})})});
    if(wb.isEmpty()) wb.setFromObject(scene);
    var ws=new THREE.Vector3(); wb.getSize(ws);
    var fmt=function(n){return n.toLocaleString('es-ES',{minimumFractionDigits:1,maximumFractionDigits:1})+' m'};
    var dims=[{t:fmt(ws.z),p:new THREE.Vector3(wb.max.x+0.6,0.05,(wb.min.z+wb.max.z)/2)},{t:fmt(ws.x),p:new THREE.Vector3((wb.min.x+wb.max.x)/2,0.05,wb.max.z+0.6)}]
      .map(function(d){var el=document.createElement('div');el.className='v3d-dim';el.textContent=d.t;box.appendChild(el);d.el=el;return d});
    var dimLines=new THREE.Group();
    [[[wb.max.x+0.6,wb.min.z],[wb.max.x+0.6,wb.max.z]],[[wb.min.x,wb.max.z+0.6],[wb.max.x,wb.max.z+0.6]]].forEach(function(s){
      var g=new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(s[0][0],0.02,s[0][1]),new THREE.Vector3(s[1][0],0.02,s[1][1])]);
      dimLines.add(new THREE.Line(g,new THREE.LineBasicMaterial({color:0x555555})));
    });
    scene.add(dimLines);

    var roofCb=box.querySelector('.v3d-roof'), dimCb=box.querySelector('.v3d-dims');
    function setRoof(on){['roof','beam','gable'].forEach(function(k){if(groups[k])groups[k].visible=on});roofCb.checked=on}
    var reduce=matchMedia('(prefers-reduced-motion: reduce)').matches, anim=null;
    function fly(pos,target){
      var p0=camera.position.clone(), t0=controls.target.clone(), start=performance.now(), dur=reduce?0:900;
      anim=function(now){var k=dur?Math.min(1,(now-start)/dur):1, e=k<.5?2*k*k:1-Math.pow(-2*k+2,2)/2;
        camera.position.lerpVectors(p0,pos,e); controls.target.lerpVectors(t0,target,e); if(k>=1)anim=null;};
    }
    var H=mx[2]-mn[2];
    var fit=function(){var a=box.clientWidth/Math.max(1,box.clientHeight);return Math.max(1,1.0/a)};
    var extPos=function(){var f=fit();return new THREE.Vector3(span*1.05*f,H+span*0.35*f,span*1.15*f)};
    var views={
      ext:function(){setRoof(true);controls.minDistance=2;controls.maxPolarAngle=Math.PI*0.495;fly(extPos(),new THREE.Vector3(0,H*0.4,0))},
      open:function(){setRoof(false);controls.minDistance=2;controls.maxPolarAngle=Math.PI*0.495;var f=fit();fly(new THREE.Vector3(span*0.75*f,span*f,span*0.9*f),new THREE.Vector3(0,0.6,0))},
      plan:function(){setRoof(false);controls.minDistance=2;controls.maxPolarAngle=Math.PI*0.495;fly(new THREE.Vector3(0.01,span*1.75*fit(),0.6),new THREE.Vector3(0,0,0))},
      int:function(){setRoof(true);controls.minDistance=0.01;controls.maxPolarAngle=Math.PI*0.9;
        var c=new THREE.Vector3(); wb.getCenter(c);
        var eye=new THREE.Vector3(c.x+ws.x*0.12,1.6,c.z+ws.z*0.12), look=new THREE.Vector3(wb.min.x+0.3,1.3,wb.min.z+0.3);
        fly(eye,eye.clone().lerp(look,0.04))}
    };
    var vbtns=box.querySelectorAll('[data-v]');
    vbtns.forEach(function(b){b.addEventListener('click',function(){vbtns.forEach(function(x){x.setAttribute('aria-pressed',String(x===b))});views[b.dataset.v]()})});
    roofCb.addEventListener('change',function(){setRoof(roofCb.checked)});
    dimCb.addEventListener('change',function(){dimLines.visible=dimCb.checked});

    resize(); camera.position.copy(extPos()); controls.target.set(0,H*0.4,0);
    var idle=true; controls.addEventListener('start',function(){idle=false});
    function resize(){var w=box.clientWidth,h=box.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix()}
    var ro=new ResizeObserver(resize); ro.observe(box); resize();
    var tmp=new THREE.Vector3(), raf=0, alive=true;
    function loop(now){
      if(!alive)return;
      if(anim)anim(now);
      else if(idle&&!reduce&&vbtns[0].getAttribute('aria-pressed')==='true'){var r=camera.position.clone().sub(controls.target);r.applyAxisAngle(new THREE.Vector3(0,1,0),0.0015);camera.position.copy(controls.target).add(r)}
      controls.update(); renderer.render(scene,camera);
      var w=box.clientWidth,h=box.clientHeight;
      dims.forEach(function(d){tmp.copy(d.p).project(camera);var vis=dimCb.checked&&tmp.z<1&&Math.abs(tmp.x)<1.1&&Math.abs(tmp.y)<1.1;
        d.el.hidden=!vis; if(vis){d.el.style.left=((tmp.x+1)/2*w)+'px';d.el.style.top=((1-tmp.y)/2*h)+'px'}});
      raf=requestAnimationFrame(loop);
    }
    var l=box.querySelector('.v3d-load'); if(l)l.remove();
    raf=requestAnimationFrame(loop);
    modal.cleanup=function(){alive=false;cancelAnimationFrame(raf);ro.disconnect();controls.dispose();
      scene.traverse(function(o){if(o.geometry)o.geometry.dispose()});
      Object.keys(mats).forEach(function(k){if(mats[k].map)mats[k].map.dispose();mats[k].dispose()});
      renderer.dispose();};
  }
})();
