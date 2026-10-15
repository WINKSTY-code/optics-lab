
/* ==========================================================================
   路灯下的影子间距 · 3D 交互演示
   物理内核：点光源投影 —— 地面点 X = x · H/(H − h)，两位同学同速同向移动
   ========================================================================== */
(function(){
'use strict';

/* ---------------- 0.5 嵌入协议（与主作品 s3d:* 同口径） ----------------
   父 → 子  {t:'s3d:init', params}   进 3D 时同步一次（本场景参数独立，仅回执）
            {t:'s3d:active', on}     父页切走 / 切回 —— 真正停掉 rAF 省电
   子 → 父  {t:'s3d:ready', key}     场景就绪 / 上下文已恢复
            {t:'s3d:lost',  key}      渲染上下文丢失（父页会重置挂载）
            {t:'s3d:error', key, msg} 出错（父页会退回 2D）
            {t:'s3d:state', key, params}
   离线 file:// 下 origin 为 null，故不做 origin 校验，只严格校验消息形状。 */
var S3D_KEY = 'shadow';
function post(m){ try { (window.parent || window).postMessage(m, '*'); } catch(e){} }

/* ---------------- 0. 错误可视化（便于排查） ---------------- */
window.addEventListener('error', function(e){
  var d = document.getElementById('err'); d.style.display='block';
  d.textContent = 'ERROR: ' + (e.message||'') + '\n' + (e.filename||'') + ':' + (e.lineno||'');
  post({ t:'s3d:error', key:S3D_KEY, msg:String(e.message||'') });
});

/* ---------------- 1. 参数与物理 ---------------- */
var WALK = 5.4;          // B 在一段演示中走过的总路程（m）
var XA_START = 0.30;     // A 的起始位置（距 O′，m）
var V_BASE = 0.85;       // 基准行走速度（m/s）

var S = {
  H:3.2, hA:1.7, hB:1.1, gap:1.0,
  p:0, playing:true, speed:0.5,
  rays:true, cone:true, grid:true, ruler:false, follow:true
};

var KA=0, KB=0, XB0=0, XEND=0;
function derive(){
  if (S.hB > S.hA - 0.15) S.hB = S.hA - 0.15;   // 保证 A 一定比 B 高
  KA = S.H / (S.H - S.hA);
  KB = S.H / (S.H - S.hB);
  XB0 = XA_START + S.gap;
  XEND = XB0 + WALK;
}
function xAat(p){ return XA_START + WALK*p; }
function xBat(p){ return XB0 + WALK*p; }
function calc(p){
  var xA = xAat(p), xB = xBat(p);
  var tipA = xA*KA, tipB = xB*KB;
  return { xA:xA, xB:xB, tipA:tipA, tipB:tipB, lenA:tipA-xA, lenB:tipB-xB,
           s: tipA-tipB, d: Math.abs(tipA-tipB) };
}
function dAt(p){ var c = calc(p); return c.d; }
function critXB(){ return -KA*(XA_START - XB0) / (KA - KB); }  // 括号内为 0 时 B 的位置

/* ---------------- 2. 渲染器 / 场景 ---------------- */
if (THREE.ColorManagement) THREE.ColorManagement.enabled = true;
var canvas = document.getElementById('gl');
var renderer = new THREE.WebGLRenderer({ canvas:canvas, antialias:true, powerPreference:'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio||1, 2));
if (THREE.sRGBEncoding !== undefined) renderer.outputEncoding = THREE.sRGBEncoding;

/* 上下文丢失：先自愈，同时通报父页（父页会重置挂载，便于重新进入） */
canvas.addEventListener('webglcontextlost', function(e){
  e.preventDefault(); setRunning(false);
  post({ t:'s3d:lost', key:S3D_KEY });
});
canvas.addEventListener('webglcontextrestored', function(){
  setRunning(true); post({ t:'s3d:ready', key:S3D_KEY });
});

var scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x050810, 13, 42);

var camera = new THREE.PerspectiveCamera(42, 1, 0.05, 260);

/* 天空渐变球 */
var skyMat = new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite:false, fog:false,
  uniforms:{ cTop:{value:new THREE.Color(0x0d1c3c)}, cBot:{value:new THREE.Color(0x03050c)} },
  vertexShader:'varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0);}',
  fragmentShader:'varying vec3 vP; uniform vec3 cTop; uniform vec3 cBot;'+
                 'void main(){ float h = clamp(vP.y/60.0*0.5+0.5, 0.0, 1.0);'+
                 'gl_FragColor = vec4(mix(cBot, cTop, pow(h,1.15)), 1.0);}'
});
scene.add(new THREE.Mesh(new THREE.SphereGeometry(90,32,20), skyMat));

/* 星点 */
(function(){
  var n=420, pos=new Float32Array(n*3);
  for(var i=0;i<n;i++){
    var a=Math.random()*Math.PI*2, u=Math.random()*0.85+0.06, r=74;
    pos[i*3]=Math.cos(a)*r*Math.sin(u*Math.PI/2+0.3);
    pos[i*3+1]=r*Math.cos(u*Math.PI/2+0.3)*0.9+6;
    pos[i*3+2]=Math.sin(a)*r*Math.sin(u*Math.PI/2+0.3);
  }
  var g=new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos,3));
  scene.add(new THREE.Points(g, new THREE.PointsMaterial({color:0xaecbff,size:1.5,sizeAttenuation:false,transparent:true,opacity:.75,fog:false})));
})();

/* ---------------- 3. 灯光 ---------------- */
/* 灯光（已按实测标定：legacy 渲染路径下 point light 必须给 distance 才会衰减） */
scene.add(new THREE.AmbientLight(0x9fb4d8, 1.5));
scene.add(new THREE.HemisphereLight(0xa8c8ff, 0x0d1526, 0.55));
var lampLight = new THREE.PointLight(0xffdcae, 6, 16, 2);
lampLight.position.set(0, S.H, 0);
scene.add(lampLight);

/* ---------------- 4. 地面（铺装广场 + 网格） ---------------- */
var groundTex = (function(){
  var c=document.createElement('canvas'); c.width=c.height=256;
  var x=c.getContext('2d');
  x.fillStyle='#77879d'; x.fillRect(0,0,256,256);
  var g=x.createLinearGradient(0,0,256,256);
  g.addColorStop(0,'rgba(255,255,255,.035)'); g.addColorStop(1,'rgba(0,0,0,.05)');
  x.fillStyle=g; x.fillRect(0,0,256,256);
  x.strokeStyle='rgba(28,40,64,.22)'; x.lineWidth=2;
  x.strokeRect(0,0,256,256);
  x.strokeStyle='rgba(28,40,64,.10)'; x.lineWidth=1;
  for(var i=1;i<4;i++){ x.beginPath(); x.moveTo(i*64,0); x.lineTo(i*64,256); x.stroke();
                        x.beginPath(); x.moveTo(0,i*64); x.lineTo(256,i*64); x.stroke(); }
  var t=new THREE.CanvasTexture(c);
  t.wrapS=t.wrapT=THREE.RepeatWrapping; t.repeat.set(16,12);
  t.anisotropy=8;
  return t;
})();
var ground = new THREE.Mesh(
  new THREE.PlaneGeometry(64,48),
  new THREE.MeshStandardMaterial({ map:groundTex, color:0x8b9cbb, roughness:0.98, metalness:0.0 })
);
ground.rotation.x = -Math.PI/2;
ground.position.set(3,0,0);
scene.add(ground);

var grid = new THREE.GridHelper(64, 64, 0x86a6dd, 0x3b537c);
grid.position.set(3,0.004,0);
grid.material.transparent=true; grid.material.opacity=0.22; grid.material.depthWrite=false;
scene.add(grid);

/* 标尺（沿 z=+2.6 的刻度） */
var rulerG = new THREE.Group(); scene.add(rulerG);
(function(){
  var verts=[], i;
  for(i=0;i<=16;i++){
    var x=i, L=(i%5===0)?0.42:0.22;
    verts.push(x,0.012,2.6, x,0.012,2.6+L);
  }
  verts.push(0,0.012,2.6, 16,0.012,2.6);
  var g=new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(verts,3));
  rulerG.add(new THREE.LineSegments(g, new THREE.LineBasicMaterial({color:0x9db8e8,transparent:true,opacity:.75})));
})();
rulerG.visible = S.ruler;

/* ---------------- 5. 路灯（光源严格位于 O′ 正上方 h = H 处，保证光沿直线传播） ---------------- */
var POLE_DROP = 0.30;       // 杆顶比光源低多少（灯泡坐在杆上）
var lampGrp = new THREE.Group(); scene.add(lampGrp);
var poleMat = new THREE.MeshStandardMaterial({color:0x2c3a52, roughness:0.5, metalness:0.65});
var pole = new THREE.Mesh(new THREE.CylinderGeometry(0.045,0.062,1,18), poleMat);
lampGrp.add(pole);
var base = new THREE.Mesh(new THREE.CylinderGeometry(0.18,0.24,0.09,20), poleMat);
base.position.set(0,0.045,0); lampGrp.add(base);
var collar = new THREE.Mesh(new THREE.CylinderGeometry(0.095,0.07,0.28,16), poleMat);
lampGrp.add(collar);
var bulbMat = new THREE.MeshStandardMaterial({color:0xfff0cf, emissive:0xffd489, emissiveIntensity:2.6, roughness:0.3});
var bulb = new THREE.Mesh(new THREE.SphereGeometry(0.115,22,16), bulbMat);
lampGrp.add(bulb);

/* 光源位置 = 灯泡球心 = (0, H, 0)，O′ 即灯杆脚下 (0,0,0) */
var LAMP = new THREE.Vector3(0, S.H, 0);
lampLight.position.copy(LAMP);

/* 灯泡光晕 sprite */
var glowSprite = (function(){
  var c=document.createElement('canvas'); c.width=c.height=128;
  var x=c.getContext('2d'); var g=x.createRadialGradient(64,64,0,64,64,64);
  g.addColorStop(0,'rgba(255,240,205,1)'); g.addColorStop(.25,'rgba(255,205,120,.62)');
  g.addColorStop(.6,'rgba(255,170,70,.16)'); g.addColorStop(1,'rgba(255,160,60,0)');
  x.fillStyle=g; x.fillRect(0,0,128,128);
  var t=new THREE.CanvasTexture(c);
  var sp=new THREE.Sprite(new THREE.SpriteMaterial({map:t, blending:THREE.AdditiveBlending, depthWrite:false, transparent:true, fog:false}));
  sp.scale.set(1.9,1.9,1); scene.add(sp);
  return sp;
})();

/* 光锥（锥顶即光源） */
var coneMat = new THREE.ShaderMaterial({
    transparent:true, depthWrite:false, side:THREE.DoubleSide, blending:THREE.AdditiveBlending, fog:false,
    uniforms:{ hgt:{value:S.H} },
    vertexShader:'varying float vY; varying float vR; void main(){ vY=position.y; vR=length(position.xz);'+
                 ' gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',
    fragmentShader:'varying float vY; varying float vR; uniform float hgt;'+
      'void main(){ float t=(vY+hgt*0.5)/hgt;'+
      ' float a=0.018+0.078*pow(t,1.6);'+
      ' float r=smoothstep(1.0,0.12,abs(vR)/3.6);'+
      ' gl_FragColor=vec4(1.0,0.82,0.52,a*(0.30+0.70*r));}'
});
var cone = new THREE.Mesh(new THREE.ConeGeometry(3.6, S.H, 40, 1, true), coneMat);
scene.add(cone);

/* 灯高变化时重建灯与被照几何 */
function rebuildLamp(){
  var poleH = Math.max(0.5, S.H - POLE_DROP);
  pole.geometry.dispose(); pole.geometry = new THREE.CylinderGeometry(0.045,0.062,poleH,18);
  pole.position.set(0, poleH/2, 0);
  collar.position.set(0, poleH + 0.08, 0);
  bulb.position.set(0, S.H, 0);
  LAMP.set(0, S.H, 0);
  lampLight.position.copy(LAMP);
  glowSprite.position.copy(LAMP);
  cone.geometry.dispose(); cone.geometry = new THREE.ConeGeometry(3.6, S.H, 40, 1, true);
  cone.position.set(0, S.H/2, 0);
  coneMat.uniforms.hgt.value = S.H;
  SHADOW_M = makeShadowMatrix();
}
rebuildLamp();

/* ---------------- 6. 人物模型 ---------------- */
var people = [],
    shadowMeshes = [],
    shadowGroup = new THREE.Group(), shadowMatrix = new THREE.Matrix4();

/* 点光源投影矩阵：地面点 = (H·x, 0, H·z)/(H − y)，再整体抬高 0.010 避免与地面 z-fighting */
function makeShadowMatrix(){
  var m = new THREE.Matrix4();
  m.set( S.H, 0, 0, 0,
         0,   0, 0, 0,
         0,   0, S.H, 0,
         0,  -1, 0, S.H );
  var lift = new THREE.Matrix4().makeTranslation(0, 0.010, 0);
  return lift.multiply(m);
}
var SHADOW_M = makeShadowMatrix();
var shadowMat = new THREE.MeshBasicMaterial({ color:0x0a1120, side:THREE.DoubleSide, fog:true });

function clearPeople(){
  people.forEach(function(o){
    scene.remove(o.root);
    o.root.traverse(function(c){ if(c.geometry) c.geometry.dispose(); });
    if (o.shadowGroup) scene.remove(o.shadowGroup);
  });
  shadowGroups.forEach(function(g){
    g.children.forEach(function(c){ if(c.geometry) c.geometry.dispose(); });
    scene.remove(g);
  });
  shadowGroups = [];
  people = []; shadowMeshes = []; shadowMeshesA = []; shadowMeshesB = [];
}
var shadowGroups = [];

/* 生成一位同学：身高 h，颜色 color，站位 x0 */
function makePerson(h, color, sign){
  var root = new THREE.Group();
  var mat = new THREE.MeshStandardMaterial({ color:color, roughness:0.42, metalness:0.12 });
  var skin = new THREE.MeshStandardMaterial({ color:0xd6a884, roughness:0.75, metalness:0.0 });
  var parts = [];

  var rHead = 0.078*h, yHead = h - rHead;
  var head = new THREE.Mesh(new THREE.SphereGeometry(rHead, 22, 16), skin);
  head.position.set(0, yHead, 0); root.add(head); parts.push(head);

  var torsoLen = 0.30*h;
  var torso = new THREE.Mesh(new THREE.CapsuleGeometry(0.088*h, torsoLen, 6, 18), mat);
  torso.position.set(0, 0.66*h, 0); root.add(torso); parts.push(torso);

  var hipY = 0.50*h, legLen = 0.42*h;
  var legs = [];
  [-1,1].forEach(function(sd){
    var g = new THREE.Group(); g.position.set(0, hipY, sd*0.052*h); root.add(g);
    var m = new THREE.Mesh(new THREE.CapsuleGeometry(0.056*h, legLen, 5, 14), mat);
    m.position.set(0, -legLen/2 - 0.02*h, 0); g.add(m); parts.push(m);
    var foot = new THREE.Mesh(new THREE.BoxGeometry(0.11*h, 0.045*h, 0.075*h), mat);
    foot.position.set(0.012*h, -legLen - 0.03*h, 0); g.add(foot); parts.push(foot);
    legs.push(g);
  });

  var shY = 0.855*h, armLen = 0.26*h;
  var arms = [];
  [-1,1].forEach(function(sd){
    var g = new THREE.Group(); g.position.set(0, shY, sd*0.105*h); root.add(g);
    var m = new THREE.Mesh(new THREE.CapsuleGeometry(0.036*h, armLen, 5, 12), mat);
    m.position.set(0, -armLen/2-0.01*h, 0); g.add(m); parts.push(m);
    arms.push(g);
  });

  scene.add(root);
  return { root:root, parts:parts, legs:legs, arms:arms, h:h, sign:sign, mat:mat };
}

/* 为每位同学建立“投影影子”：影子网格直接复用部件几何体，
   每帧用 SHADOW_M × 部件的 matrixWorld 做一次点光源投影（不可再烘焙本地矩阵） */
function buildShadowFor(person){
  var grp = new THREE.Group();
  grp.matrixAutoUpdate = false;
  person.parts.forEach(function(pt){
    var g = pt.geometry.clone();
    var m = new THREE.Mesh(g, shadowMat);
    m.matrixAutoUpdate = false;
    shadowMeshes.push({ mesh:m, part:pt });
    grp.add(m);
  });
  scene.add(grp);
  shadowGroups.push(grp);
  person.shadowGroup = grp;
}

function buildPeople(){
  clearPeople();
  var A = makePerson(S.hA, 0x7fb6ff, 'A');
  var B = makePerson(S.hB, 0xffb347, 'B');
  people.push(A, B);
  buildShadowFor(A);
  shadowMeshesA = shadowMeshes.slice();
  shadowMeshes = [];
  buildShadowFor(B);
  shadowMeshesB = shadowMeshes.slice();
  shadowMeshes = shadowMeshesA.concat(shadowMeshesB);
}
var shadowMeshesA=[], shadowMeshesB=[];

/* ---------------- 7. 头影标记 / 光路 / 测量线 ---------------- */
function ring(color){
  var g = new THREE.Group();
  var t = new THREE.Mesh(new THREE.TorusGeometry(0.085,0.016,8,26),
          new THREE.MeshBasicMaterial({color:color, transparent:true, opacity:.95}));
  t.rotation.x = -Math.PI/2; g.add(t);
  var s = new THREE.Mesh(new THREE.SphereGeometry(0.038,14,10), new THREE.MeshBasicMaterial({color:color}));
  s.position.y = 0.03; g.add(s);
  g.position.y = 0.014;
  return g;
}
var markA = ring(0x7fb6ff), markB = ring(0xffb347);
scene.add(markA, markB);

/* 光路：O → 头顶 → 头影 */
function rayLine(color){
  var g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(9),3));
  var l = new THREE.Line(g, new THREE.LineBasicMaterial({color:color, transparent:true, opacity:.85, fog:false}));
  scene.add(l); return l;
}
var rayA = rayLine(0xffe6a6), rayB = rayLine(0xffd07a);

/* 测量线 */
var measGeo = new THREE.BufferGeometry();
measGeo.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(6),3));
var measLine = new THREE.Line(measGeo, new THREE.LineBasicMaterial({color:0xffffff, transparent:true, opacity:.9}));
scene.add(measLine);

/* ---------------- 8. HTML 标签 ---------------- */
var labelBox = document.getElementById('labels');
function mkLabel(text, cls){
  var el = document.createElement('div');
  el.className = 'lab ' + (cls||'');
  el.innerHTML = text;
  labelBox.appendChild(el);
  return el;
}
var LB = {
  O:  mkLabel('O · 光源','pill'),
  Op: mkLabel('O′','pill'),
  A:  mkLabel('A','pill'),
  B:  mkLabel('B','pill'),
  Ap: mkLabel('A′','pill'),
  Bp: mkLabel('B′','pill'),
  d:  mkLabel('d','dval')
};
LB.O.style.color = '#ffe0a0';
LB.Op.style.color = '#cfe0ff';
LB.A.style.color = '#a8cdff';
LB.B.style.color = '#ffca7a';
LB.Ap.style.color = '#a8cdff';
LB.Bp.style.color = '#ffca7a';
LB.d.style.color = '#ffffff';

var v3 = new THREE.Vector3();
function placeLabel(el, x, y, z, hide){
  if (hide){ el.style.display='none'; return; }
  v3.set(x,y,z).project(camera);
  var w = window.innerWidth, hh = window.innerHeight;
  if (v3.z > 1){ el.style.display='none'; return; }
  var px = (v3.x*0.5+0.5)*w, py = (-v3.y*0.5+0.5)*hh;
  var m = 46;                                    // 贴边时把标签拉回屏内，避免被裁掉
  px = Math.max(m, Math.min(w-m, px));
  py = Math.max(18, Math.min(hh-18, py));
  el.style.display = '';
  el.style.transform = 'translate(-50%,-50%) translate(' + px.toFixed(1) + 'px,' + py.toFixed(1) + 'px)';
}

/* ---------------- 9. 相机控制（自研 orbit） ---------------- */
var cam = {
  az:0.46, pol:1.315, dist:14.0, fov:42,
  target:new THREE.Vector3(4.9, 0.95, 0)
};
var PRESET = {
  iso:  {az:0.46, pol:1.315, dist:14.0, fov:42, target:[4.9,0.95,0]},
  side: {az:0.02, pol:1.478, dist:17.2, fov:34,  target:[4.6,1.35,0]},
  top:  {az:0.46, pol:0.10,  dist:13.0, fov:42,  target:[4.7,0,0]}
};
var tween = null;
function applyCam(){
  var sp = Math.sin(cam.pol), cp = Math.cos(cam.pol);
  camera.position.set(
    cam.target.x + cam.dist*sp*Math.sin(cam.az),
    cam.target.y + cam.dist*cp,
    cam.target.z + cam.dist*sp*Math.cos(cam.az)
  );
  camera.lookAt(cam.target);
  if (camera.fov !== cam.fov){ camera.fov = cam.fov; camera.updateProjectionMatrix(); }
}
function gotoView(name){
  var pr = name === 'reset' ? PRESET.iso : PRESET[name];
  if (!pr) return;
  tween = {
    t0: performance.now(), dur: 720,
    from: {az:cam.az, pol:cam.pol, dist:cam.dist, fov:cam.fov,
           target:cam.target.clone()},
    to:   {az:pr.az, pol:pr.pol, dist:pr.dist, fov:pr.fov,
           target:new THREE.Vector3(pr.target[0],pr.target[1],pr.target[2])}
  };
}
function easeIO(t){ return t<0.5 ? 4*t*t*t : 1-Math.pow(-2*t+2,3)/2; }

/* 鼠标 / 触摸 */
(function(){
  var dragging = false, lx = 0, ly = 0, pinch = 0;
  canvas.addEventListener('pointerdown', function(e){
    dragging = true; tween = null; lx = e.clientX; ly = e.clientY;
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener('pointermove', function(e){
    if (!dragging) return;
    var dx = e.clientX - lx, dy = e.clientY - ly; lx = e.clientX; ly = e.clientY;
    cam.az -= dx*0.0062;
    cam.pol = Math.max(0.08, Math.min(1.50, cam.pol - dy*0.0052));
  });
  canvas.addEventListener('pointerup', function(e){ dragging = false; });
  canvas.addEventListener('pointercancel', function(){ dragging = false; });
  canvas.addEventListener('wheel', function(e){
    e.preventDefault(); tween = null;
    cam.dist = Math.max(3.2, Math.min(34, cam.dist * (1 + Math.sign(e.deltaY)*0.09)));
  }, {passive:false});
  canvas.addEventListener('touchmove', function(e){
    if (e.touches.length === 2){
      e.preventDefault(); tween = null;
      var a = e.touches[0], b = e.touches[1];
      var d = Math.hypot(a.clientX-b.clientX, a.clientY-b.clientY);
      if (pinch) cam.dist = Math.max(3.2, Math.min(34, cam.dist * (pinch/d)));
      pinch = d;
    }
  }, {passive:false});
  canvas.addEventListener('touchend', function(){ pinch = 0; });
})();

/* ---------------- 9.5 取景：跟随实验 + 居中在空白处 ---------------- */
/* 跟随：把「灯—两人—两个头影」整体当作实验范围，镜头始终追随它的中心 */
var follow = { cx:4.9, dist:11, on:true, autoDist:true, inited:false, dInited:false, fitMin:9.6, fitMax:15.6 };
function actionBox(p){
  var c = calc(p);
  var lo = Math.min(0, c.xA, c.tipA, c.xB, c.tipB);      // 灯杆底(0)始终留在画面里
  var hi = Math.max(0, c.xA, c.tipA, c.xB, c.tipB);
  return [lo, hi];
}
/* 空白区域中心（把四个面板遮住的格子挖掉，取剩余区域质心） */
function freeCenter(){
  var W = window.innerWidth, H = window.innerHeight, NX = 36, NY = 22;
  var occ = new Uint8Array(NX*NY), i;
  var ids = ['topbar','hud','chartCard','dock','drawer'];
  var boxes = [];
  for (i=0;i<ids.length;i++){
    var el = document.getElementById(ids[i]); if (!el) continue;
    var r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    boxes.push(r);
  }
  /* 嵌入模式：父页的「2D / 3D案例」切换条悬浮在右下角，取景时一并避开 */
  if (document.body.classList.contains('embed'))
    boxes.push({left:W-196, top:H-62, right:W, bottom:H});
  for (i=0;i<boxes.length;i++){
    var r2 = boxes[i];
    var x0 = Math.max(0, Math.floor(r2.left/W*NX)), x1 = Math.min(NX, Math.ceil(r2.right/W*NX));
    var y0 = Math.max(0, Math.floor(r2.top/H*NY)),  y1 = Math.min(NY, Math.ceil(r2.bottom/H*NY));
    for (var y=y0;y<y1;y++) for (var x=x0;x<x1;x++) occ[y*NX+x] = 1;
  }
  var sx=0, sy=0, n=0;
  for (var y2=0;y2<NY;y2++) for (var x2=0;x2<NX;x2++){
    if (occ[y2*NX+x2]) continue;
    sx += (x2+0.5)/NX; sy += (y2+0.5)/NY; n++;
  }
  if (!n) return [0.5,0.5];
  return [sx/n, sy/n];
}
var viewOff = {x:0,y:0}, viewWant = {x:0,y:0};
function updateViewWant(){
  var W = window.innerWidth, H = window.innerHeight, c = freeCenter();
  /* 想让实验中心落在空白区中心 → 画面整体位移 */
  viewWant.x = W/2 - c[0]*W;
  viewWant.y = H/2 - c[1]*H;
}
function applyViewOff(){
  if (Math.abs(viewOff.x - viewWant.x) < 0.15 && Math.abs(viewOff.y - viewWant.y) < 0.15){
    viewOff.x = viewWant.x; viewOff.y = viewWant.y;
  } else {
    viewOff.x += (viewWant.x - viewOff.x)*0.18;
    viewOff.y += (viewWant.y - viewOff.y)*0.18;
  }
  camera.setViewOffset(window.innerWidth, window.innerHeight, viewOff.x, viewOff.y,
                       window.innerWidth, window.innerHeight);
}
function setFollow(on){
  follow.on = on; S.follow = on;
  var chip = document.querySelector('[data-tg="follow"]');
  if (chip) chip.classList.toggle('on', on);
  if (on){ follow.cx = cam.target.x; follow.autoDist = true; }
}

/* ---------------- 10. 图表 ---------------- */
var chartEl = document.getElementById('chart');
var cctx = chartEl.getContext('2d');
function drawChart(){
  var W = chartEl.clientWidth, Hh = chartEl.clientHeight;
  var dpr = Math.min(window.devicePixelRatio||1, 2);
  if (chartEl.width !== Math.round(W*dpr) || chartEl.height !== Math.round(Hh*dpr)){
    chartEl.width = Math.round(W*dpr); chartEl.height = Math.round(Hh*dpr);
  }
  cctx.setTransform(dpr,0,0,dpr,0,0);
  cctx.clearRect(0,0,W,Hh);

  var padL = 34, padR = 10, padT = 8, padB = 18;
  var gw = W-padL-padR, gh = Hh-padT-padB;
  var N = 180, i, pts = [], maxD = 0;
  for (i=0;i<=N;i++){
    var p = i/N, d = dAt(p);
    pts.push({p:p, d:d});
    if (d > maxD) maxD = d;
  }
  var dCrit = critXB();
  maxD = Math.max(maxD, 0.4) * 1.16;

  function X(p){ return padL + gw*p; }
  function Y(d){ return padT + gh*(1 - d/maxD); }

  /* 网格 & 轴 */
  cctx.strokeStyle='rgba(122,156,220,.15)'; cctx.lineWidth=1;
  for (i=0;i<=3;i++){
    var yy = padT + gh*i/3;
    cctx.beginPath(); cctx.moveTo(padL, yy); cctx.lineTo(padL+gw, yy); cctx.stroke();
  }
  cctx.strokeStyle='rgba(122,156,220,.42)';
  cctx.beginPath(); cctx.moveTo(padL,padT); cctx.lineTo(padL,padT+gh); cctx.lineTo(padL+gw,padT+gh); cctx.stroke();

  /* 曲线下方填充 */
  var grad = cctx.createLinearGradient(0,padT,0,padT+gh);
  grad.addColorStop(0,'rgba(127,182,255,.22)'); grad.addColorStop(1,'rgba(127,182,255,0)');
  cctx.beginPath(); cctx.moveTo(X(0), Y(pts[0].d));
  for (i=1;i<=N;i++) cctx.lineTo(X(pts[i].p), Y(pts[i].d));
  cctx.lineTo(X(1), padT+gh); cctx.lineTo(X(0), padT+gh); cctx.closePath();
  cctx.fillStyle = grad; cctx.fill();

  /* 曲线：分“减小 / 增大”两段着色 */
  function seg(from, to, color){
    cctx.beginPath();
    var first = true;
    for (var k=from;k<=to;k++){
      var x = X(pts[k].p), y = Y(pts[k].d);
      if (first){ cctx.moveTo(x,y); first=false; } else cctx.lineTo(x,y);
    }
    cctx.strokeStyle = color; cctx.lineWidth = 2.1; cctx.lineJoin='round';
    cctx.shadowColor = color; cctx.shadowBlur = 7; cctx.stroke(); cctx.shadowBlur = 0;
  }
  /* 找最小点索引 */
  var iMin = 0; for (i=1;i<=N;i++) if (pts[i].d < pts[iMin].d) iMin = i;
  var hasMin = (pts[iMin].d < pts[0].d - 1e-6) && (iMin < N);
  seg(0, hasMin?iMin:N, '#6ef0c0');
  if (hasMin) seg(iMin, N, '#ffb347');

  if (hasMin){
    cctx.setLineDash([3,3]); cctx.strokeStyle='rgba(255,255,255,.45)'; cctx.lineWidth=1;
    cctx.beginPath(); cctx.moveTo(X(pts[iMin].p), Y(pts[iMin].d)); cctx.lineTo(X(pts[iMin].p), padT+gh); cctx.stroke();
    cctx.setLineDash([]);
  }

  /* 轴文字 */
  cctx.fillStyle='rgba(147,167,202,.85)'; cctx.font='9.5px ' + getComputedStyle(document.body).fontFamily;
  cctx.textAlign='right'; cctx.textBaseline='middle';
  cctx.fillText(maxD.toFixed(1), padL-5, padT+3);
  cctx.fillText('0', padL-5, padT+gh);
  cctx.textAlign='center'; cctx.textBaseline='top';
  cctx.fillText('0', padL, padT+gh+4);
  cctx.fillText('x_B / m', padL+gw*0.52, padT+gh+4);
  cctx.save(); cctx.translate(9, padT+gh*0.5); cctx.rotate(-Math.PI/2);
  cctx.textAlign='center'; cctx.textBaseline='top'; cctx.fillText('d / m', 0, 0); cctx.restore();

  /* 当前点 */
  var c = calc(S.p);
  var cxp = padL + gw*S.p, cyp = Y(c.d);
  cctx.beginPath(); cctx.arc(cxp, cyp, 8, 0, 6.29);
  cctx.fillStyle = 'rgba(255,255,255,.14)'; cctx.fill();
  cctx.beginPath(); cctx.arc(cxp, cyp, 3.4, 0, 6.29);
  cctx.fillStyle = '#fff'; cctx.fill();

  /* 图例 */
  cctx.textAlign='left'; cctx.textBaseline='middle';
  cctx.fillStyle='#6ef0c0'; cctx.fillText('减小', padL+6, padT+8);
  cctx.fillStyle='#ffb347'; cctx.textAlign='right'; cctx.fillText('增大', padL+gw-2, padT+8);
  if (hasMin){
    cctx.fillStyle='rgba(255,255,255,.75)'; cctx.textAlign='center';
    cctx.fillText('d 最小', X(pts[iMin].p), padT+gh-9);
  }
  return { iMin:iMin, hasMin:hasMin };
}

/* ---------------- 11. UI 绑定 ---------------- */
var $ = function(id){ return document.getElementById(id); };
var elD = $('dVal'), elTrend = $('trendTag'), elProg = $('progTxt'), elTime = $('time'), elPlay = $('play');
var tipEl = $('tip'), tipTimer = null;
function toast(msg, ms){
  tipEl.textContent = msg; tipEl.classList.add('on');
  clearTimeout(tipTimer); tipTimer = setTimeout(function(){ tipEl.classList.remove('on'); }, ms||1900);
}

var loops = 0;
elPlay.addEventListener('click', function(){
  S.playing = !S.playing;
  elPlay.textContent = S.playing ? '❚❚' : '▶';
  if (!S.playing) holdPend = false;
});
elTime.addEventListener('input', function(){
  S.p = (+elTime.value)/1000; S.playing = false; holdPend = false;
  elPlay.textContent = '▶';
});
$('spd').addEventListener('change', function(){ S.speed = +this.value; });
document.querySelectorAll('[data-view]').forEach(function(b){
  b.addEventListener('click', function(){
    var v = b.getAttribute('data-view');
    gotoView(v);
    if (v === 'iso' || v === 'reset') setFollow(true);
    else if (follow.on) setFollow(false);           // 侧视/俯视：交还手动控制
  });
});
document.querySelectorAll('[data-tg]').forEach(function(b){
  b.addEventListener('click', function(){
    var k = b.getAttribute('data-tg');
    S[k] = !S[k];
    b.classList.toggle('on', S[k]);
    if (k === 'rays'){ rayA.visible = rayB.visible = S.rays; }
    if (k === 'cone'){ cone.visible = S.cone; glowSprite.visible = S.cone; }
    if (k === 'grid'){ grid.visible = S.grid; }
    if (k === 'ruler'){ rulerG.visible = S.ruler; }
    if (k === 'follow'){ setFollow(S.follow); }
  });
});
/* 全屏 */
var fsBtn = $('btnFull');
function fsEl(){ return document.fullscreenElement || document.webkitFullscreenElement; }
function syncFs(){ if (fsBtn) fsBtn.textContent = fsEl() ? '退出' : '全屏'; }
if (!(document.documentElement.requestFullscreen || document.documentElement.webkitRequestFullscreen)){
  fsBtn.style.display = 'none';
} else {
  fsBtn.addEventListener('click', function(){
    try{
      if (!fsEl()){
        var el = document.documentElement;
        var p = (el.requestFullscreen || el.webkitRequestFullscreen).call(el);
        if (p && p.catch) p.catch(function(){});
      } else {
        var q = (document.exitFullscreen || document.webkitExitFullscreen).call(document);
        if (q && q.catch) q.catch(function(){});
      }
    }catch(e){}
  });
  document.addEventListener('fullscreenchange', syncFs);
  document.addEventListener('webkitfullscreenchange', syncFs);
}
document.querySelectorAll('.fold').forEach(function(f){
  f.addEventListener('click', function(){
    var box = $('fold-' + f.getAttribute('data-fold'));
    var open = box.style.display !== 'none';
    box.style.display = open ? 'none' : 'block';
    f.classList.toggle('open', !open);
    setTimeout(updateViewWant, 30);
  });
});
$('btnDrawer').addEventListener('click', function(){
  $('drawer').classList.add('open'); $('mask').classList.add('on');
  setTimeout(updateViewWant, 60);
});
function closeDrawer(){
  $('drawer').classList.remove('open'); $('mask').classList.remove('on');
  setTimeout(updateViewWant, 60);
}
$('btnClose').addEventListener('click', closeDrawer);
$('mask').addEventListener('click', closeDrawer);
window.addEventListener('keydown', function(e){
  if (e.code === 'Space'){ e.preventDefault(); elPlay.click(); }
  if (e.key === 'Escape') closeDrawer();
});

/* 参数滑块 */
function bindSlider(id, out, key, fmt){
  var el = $(id), o = $(out);
  el.addEventListener('input', function(){
    S[key] = +el.value;
    if (key === 'hB' && S.hB > S.hA - 0.15){ S.hB = S.hA - 0.15; el.value = S.hB; }
    if (key === 'hA' && S.hA < S.hB + 0.15){ S.hA = S.hB + 0.15; el.value = S.hA; }
    o.textContent = fmt(S[key]);
    derive();
    if (key === 'H' || key === 'gap') rebuildLamp();
    buildPeople(); refreshStatic(); drawChart(); updateScene(performance.now());
  });
}
bindSlider('sH','oH','H',  function(v){ return v.toFixed(1)+' m'; });
bindSlider('sA','oA','hA', function(v){ return v.toFixed(2)+' m'; });
bindSlider('sB','oB','hB', function(v){ return v.toFixed(2)+' m'; });
bindSlider('sG','oG','gap',function(v){ return v.toFixed(2)+' m'; });

function refreshStatic(){
  $('vRatio').textContent = S.hA.toFixed(2) + ' / ' + S.hB.toFixed(2);
  var xc = critXB(), inRange = (xc > XB0 - 0.01) && (xc < XEND);
  $('vCrit').textContent = xc.toFixed(2) + ' m';
  $('vCrit').style.color = inRange ? '' : 'var(--solar)';
  var note = $('critNote');
  if (inRange){ note.style.display = 'none'; }
  else {
    note.style.display = 'block';
    note.innerHTML = '⚠ 当前参数下最小点超出演示范围：全程 d 都在减小。<br>把灯调低、或让 A、B 身高差更大，最小点就会重新出现。';
  }
  $('oH').textContent = S.H.toFixed(1)+' m';
  $('oA').textContent = S.hA.toFixed(2)+' m';
  $('oB').textContent = S.hB.toFixed(2)+' m';
  $('oG').textContent = S.gap.toFixed(2)+' m';
  $('sH').value = S.H; $('sA').value = S.hA; $('sB').value = S.hB; $('sG').value = S.gap;
}

/* ---------------- 12. 每帧更新 ---------------- */
function updateScene(now){
  var c = calc(S.p);

  /* 站位 + 走路动作（步幅约 0.62 m，与位移同步） */
  var phase = (WALK*S.p) / 0.62 * Math.PI;
  people.forEach(function(o, i){
    var x = (i === 0) ? c.xA : c.xB;
    o.root.position.set(x, 0, 0);
    var sw = Math.sin(phase) * 0.20;
    var am = Math.sin(phase) * 0.24;
    o.legs[0].rotation.z =  sw; o.legs[1].rotation.z = -sw;
    o.arms[0].rotation.z = -am; o.arms[1].rotation.z =  am;
    o.root.updateMatrixWorld(true);
  });

  /* 影子：把人体各部件沿光源方向投影到地面（点光源精确投影） */
  function proj(list){
    list.forEach(function(o){
      o.mesh.matrix.multiplyMatrices(SHADOW_M, o.part.matrixWorld);
      o.mesh.matrixWorldNeedsUpdate = true;
    });
  }
  proj(shadowMeshesA); proj(shadowMeshesB);

  /* 头影标记 */
  markA.position.x = c.tipA; markB.position.x = c.tipB;

  /* 光路 O → 头顶 → 头影：三点严格共线（末端抬高只是抬离地面，仍落在同一直线上） */
  function setRay(line, xP, hP, tip){
    var yEnd = 0.014, xEnd = tip * (1 - yEnd/S.H);
    var pos = line.geometry.attributes.position;
    pos.setXYZ(0, LAMP.x, LAMP.y, LAMP.z);
    pos.setXYZ(1, xP, hP, 0);
    pos.setXYZ(2, xEnd, yEnd, 0);
    pos.needsUpdate = true;
    line.geometry.computeBoundingSphere();
  }
  setRay(rayA, c.xA, S.hA, c.tipA);
  setRay(rayB, c.xB, S.hB, c.tipB);
  rayA.visible = rayB.visible = S.rays;

  /* 测量线 */
  var mp = measLine.geometry.attributes.position;
  mp.setXYZ(0, c.tipA, 0.02, 0); mp.setXYZ(1, c.tipB, 0.02, 0); mp.needsUpdate = true;
  measLine.geometry.computeBoundingSphere();

  /* 标签 */
  placeLabel(LB.O,  LAMP.x, LAMP.y + 0.34, 0);
  placeLabel(LB.Op, 0, 0.02, 0);
  placeLabel(LB.A,  c.xA, S.hA + 0.30, 0);
  placeLabel(LB.B,  c.xB, S.hB + 0.30, 0);
  placeLabel(LB.Ap, c.tipA, 0.02, 0.52);
  placeLabel(LB.Bp, c.tipB, 0.02, -0.52);
  placeLabel(LB.d,  (c.tipA + c.tipB)/2, 0.62, 0.0, c.d < 0.32);
  LB.d.textContent = 'd = ' + c.d.toFixed(2) + ' m';

  /* 数据面板 */
  elD.textContent = c.d.toFixed(2);
  $('vXA').textContent = c.xA.toFixed(2) + ' m';
  $('vXB').textContent = c.xB.toFixed(2) + ' m';
  $('vLA').textContent = c.lenA.toFixed(2) + ' m';
  $('vLB').textContent = c.lenB.toFixed(2) + ' m';
  $('vTA').textContent = c.tipA.toFixed(2) + ' m';
  $('vTB').textContent = c.tipB.toFixed(2) + ' m';
  elProg.textContent = Math.round(S.p*100) + '%';

  var trend = c.s > 0.03 ? 'up' : (c.s < -0.03 ? 'down' : 'zero');
  if (elTrend.dataset.k !== trend){
    elTrend.dataset.k = trend;
    elTrend.className = trend;
    elTrend.textContent = trend === 'down' ? '● d 正在减小' :
                          trend === 'up'   ? '● d 正在增大' : '● 两影尖端重合 d ≈ 0';
  }
  if (!elTime.dataset.drag && document.activeElement !== elTime) elTime.value = Math.round(S.p*1000);
}

/* ---------------- 13. 主循环 ---------------- */
var last = performance.now(), chartTick = 0, viewTick = 0, holdPend = false, holdUntil = 0;

/* ★ 嵌入协议：父页切走时真正停掉 rAF。
   同源 srcdoc 的 iframe 不在浏览器「隐藏 iframe 节流」范围内，
   只把容器藏起来的话，切走后仍在满速渲染。 */
var RUN = { on: true, raf: 0 };
function setRunning(on){
  on = !!on;
  if (on === RUN.on) return;
  RUN.on = on;
  if (on){ last = performance.now(); if (!RUN.raf) RUN.raf = requestAnimationFrame(loop); }
  else { if (RUN.raf) cancelAnimationFrame(RUN.raf); RUN.raf = 0; }
}

function loop(now){
  if (!RUN.on){ RUN.raf = 0; return; }
  RUN.raf = requestAnimationFrame(loop);
  var dtRaw = (now - last)/1000; last = now;
  var dt = Math.min(0.05, dtRaw);              // 物理推进：限幅防跳
  var dts = Math.min(0.25, dtRaw);             // 镜头平滑：低帧率下也要跟得上

  if (tween){
    var t = Math.min(1, (now - tween.t0)/tween.dur), e = easeIO(t);
    cam.az = tween.from.az + (tween.to.az - tween.from.az)*e;
    cam.pol = tween.from.pol + (tween.to.pol - tween.from.pol)*e;
    cam.dist = tween.from.dist + (tween.to.dist - tween.from.dist)*e;
    cam.fov = tween.from.fov + (tween.to.fov - tween.from.fov)*e;
    cam.target.lerpVectors(tween.from.target, tween.to.target, e);
    if (t >= 1) tween = null;
  }

  /* 跟随实验：镜头中心追着「灯—两人—两头影」跑，并自动调焦，让实验占满画面 */
  if (follow.on){
    var box = actionBox(S.p), wantCx = (box[0] + box[1])/2;
    if (!follow.inited){ follow.cx = wantCx; follow.inited = true; }
    follow.cx += (wantCx - follow.cx) * (1 - Math.exp(-dts*5.0));
    cam.target.x = follow.cx;
    if (follow.autoDist){
      var need = (box[1] - box[0]) + 2.4;
      var dFit = (need/2) / (Math.tan(cam.fov*Math.PI/360) * Math.max(0.42, camera.aspect));
      var wantD = Math.max(follow.fitMin, Math.min(follow.fitMax, dFit));
      if (!follow.dInited){ cam.dist = wantD; follow.dInited = true; }
      cam.dist += (wantD - cam.dist) * (1 - Math.exp(-dts*2.6));
    }
  } else { follow.inited = false; follow.dInited = false; follow.cx = cam.target.x; }

  applyCam();
  if (++viewTick % 16 === 0) updateViewWant();
  applyViewOff();

  if (S.playing){
    if (holdPend){                       // 终点略停一下，让人看清最后的状态
      if (now >= holdUntil){ S.p = 0; holdPend = false; last = now; }
    } else {
      S.p += dt * (V_BASE * S.speed) / WALK;
      if (S.p >= 1){                     // 循环播放：不停止就一直循环演示
        S.p = 1; holdPend = true; holdUntil = now + 750; loops++;
        if (loops === 1) toast('循环播放中 · 点暂停或拖动时间轴可停止', 2600);
      }
    }
  }
  updateScene(now);

  chartTick++;
  if (chartTick % 2 === 0) drawChart();

  renderer.render(scene, camera);
}

/* ---------------- 14. 尺寸 & 启动 ---------------- */
function resize(){
  var w = window.innerWidth, h = window.innerHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w/h;
  camera.updateProjectionMatrix();
  $('btnDrawer').textContent = (w < 900) ? '题目' : '题目与解析';
  $('ttlMain').textContent = (w < 900) ? '路灯影子间距' : '路灯下的影子间距';
  updateViewWant(); viewOff.x = viewWant.x; viewOff.y = viewWant.y;   // 尺寸变了立即对齐，避免拖影
  applyViewOff();
  drawChart();
}
window.addEventListener('resize', resize);

derive();
buildPeople();
refreshStatic();
resize();
RUN.raf = requestAnimationFrame(loop);

/* 供自动化测试调用 */
window.__demo = {
  seek:function(p){ S.p = Math.max(0, Math.min(1, p)); S.playing = false; holdPend = false; elPlay.textContent='▶'; updateScene(performance.now()); drawChart(); },
  run:function(){ return RUN.on; },
  state:function(){ return { p:S.p, calc:calc(S.p), KA:KA, KB:KB, XB0:XB0, XEND:XEND, crit:critXB() }; }
};
window.__dbg = { scene:scene, camera:camera, renderer:renderer, ground:ground, THREE:THREE,
                 lamps:{ambient:null,hemi:null,pt:lampLight},
                 freeCenter:freeCenter, actionBox:actionBox, viewOff:viewOff, cam:cam, follow:follow };

/* ---------------- 15. 与父页的消息协议 ---------------- */
window.addEventListener('message', function(e){
  var m = e && e.data;
  if (!m || typeof m !== 'object' || typeof m.t !== 'string') return;
  if (m.t === 's3d:active'){ setRunning(m.on !== false); return; }
  if (m.t === 's3d:init'){
    /* 本场景的参数（灯高 / 两人身高 / 间距）与父页 2D「影子形成」的
       （物距 / 物体位置）不是同一套，故不做参数同步，只回执一次状态。 */
    post({ t:'s3d:state', key:S3D_KEY, params:{} });
  }
});
post({ t:'s3d:ready', key:S3D_KEY });
})();
