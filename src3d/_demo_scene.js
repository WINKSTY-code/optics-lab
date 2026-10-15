/* ============================================================================
   日食 · 月食 —— 光的直线传播 3D 演示
   Three.js r147 (UMD)  |  全程序化纹理，零外部资源，支持离线
   ============================================================================ */
(function () {
'use strict';

/* ---------- 0. 小工具 ---------- */
var $ = function (id) { return document.getElementById(id); };
var clamp = function (v, a, b) { return v < a ? a : v > b ? b : v; };
var lerp = function (a, b, t) { return a + (b - a) * t; };
var smoothstep = function (e0, e1, x) { var t = clamp((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t); };
var TAU = Math.PI * 2;
var RM_ = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

/* ---------- 1. 几何参数（教学示意比例，非真实尺度） ----------
   太阳位于 x = −50；日食：月球 0 → 地球 18
                     月食：地球 0 → 月球 18
   两种情形下，观测点到月球的距离都恰好是 15.9（地球半径 2.1）
---------------------------------------------------------------- */
var SUN_R = 3.6, SUN_X = -50, EARTH_R = 2.1, MOON_R = 1.0, GAP = 18;

var MODE = {
  sun:  { moonX: 0,   earthX: GAP, yAmp: 3.4, name: '日食',
          sub: '月球挡住了射向地球的太阳光，在地球上形成影子。' },
  moon: { moonX: GAP, earthX: 0,   yAmp: 6.5, name: '月食',
          sub: '地球挡住了射向月球的太阳光，在月球上形成影子。' }
};

/* 影锥：本影锥（外公切线收敛）/ 半影锥（内公切线发散） */
function coneGeom(occR, dist) {
  var su = (SUN_R - occR) / dist, sp = (SUN_R + occR) / dist;
  var tu = su / Math.sqrt(Math.max(1e-9, 1 - su * su));
  var tp = sp / Math.sqrt(Math.max(1e-9, 1 - sp * sp));
  return { tanU: tu, lenU: occR / tu, tanP: tp };
}
var CONE = { sun: coneGeom(MOON_R, 50), moon: coneGeom(EARTH_R, 50) };

/* 阶段滑块位置由真实几何反解 —— 刻度间距不均，正对应各阶段真实时长 */
var PHASES = {
  sun: [
    { n: '初亏',       d: '月球刚接触日面，太阳边缘出现极小的缺口', t: 0.22515 },
    { n: '部分食',     d: '月球继续移入，太阳被遮去一部分，形如月牙', t: 0.36765 },
    { n: '食甚·全食',  d: '月球完全挡住太阳，天色转暗，日冕浮现',     t: 0.5     },
    { n: '再次部分食', d: '月球继续移出，太阳边缘重新露出光芒',       t: 0.63235 },
    { n: '复圆',       d: '月球完全离开日面，太阳恢复圆满',           t: 0.77485 }
  ],
  moon: [
    { n: '半影食始', d: '月球开始进入地球半影区，月光略微变暗',     t: 0.10231 },
    { n: '初亏',     d: '月球边缘接触地球本影，月面出现第一个缺口', t: 0.30308 },
    { n: '食甚',     d: '月球完全进入本影区，呈现暗红的“血月”',    t: 0.5     },
    { n: '复圆',     d: '月球逐渐离开本影区，缺口另一侧开始退去',   t: 0.69692 },
    { n: '半影食终', d: '月球完全离开地球半影区，月食结束',         t: 0.89769 }
  ]
};

var yAt = function (m, t) { var A = MODE[m].yAmp; return A - 2 * A * t; };

/* 各模式的取景参数：相机注视点 x 与需要容纳的场景跨度 */
var TGT = { sun: -10, moon: -6 };
var SPAN = { sun: 104, moon: 120 };
var TY = 3.5;

/* ---------------------------------------------------------------------------
   2. 程序化纹理
--------------------------------------------------------------------------- */
function cv(w, h) { var c = document.createElement('canvas'); c.width = w; c.height = h; return c; }

/* 简易 value-noise 分形值场 */
function noiseField(w, h, oct, seed, wrap) {
  var out = new Float32Array(w * h), amp = 1, tot = 0;
  for (var o = 0; o < oct; o++) {
    var gw = Math.max(3, Math.round(4 * Math.pow(2, o))), gh = Math.max(2, Math.round(2 * Math.pow(2, o)));
    var g = new Float32Array(gw * gh), s = seed + o * 977;
    for (var i = 0; i < gw * gh; i++) { s = (s * 1103515245 + 12345) & 0x7fffffff; g[i] = (s % 10000) / 10000; }
    for (var y = 0; y < h; y++) {
      var fy = y / h * (gh - 1), y0 = Math.floor(fy), ty = fy - y0, y1 = Math.min(gh - 1, y0 + 1), wy = ty * ty * (3 - 2 * ty);
      for (var x = 0; x < w; x++) {
        var fx = x / w * (gw - 1), x0 = Math.floor(fx), tx = fx - x0,
            x1 = wrap ? (x0 + 1) % gw : Math.min(gw - 1, x0 + 1), wx = tx * tx * (3 - 2 * tx);
        out[y * w + x] += lerp(lerp(g[y0 * gw + x0], g[y0 * gw + x1], wx),
                               lerp(g[y1 * gw + x0], g[y1 * gw + x1], wx), wy) * amp;
      }
    }
    tot += amp; amp *= 0.52;
  }
  for (var k = 0; k < out.length; k++) out[k] /= tot;
  return out;
}

function sunTexture() {
  var W = 1024, H = 512, c = cv(W, H), x = c.getContext('2d');
  var f = noiseField(W / 2, H / 2, 5, 7, true);
  var im = x.createImageData(W, H), d = im.data;
  for (var j = 0; j < H; j++) for (var i = 0; i < W; i++) {
    var n = f[(j >> 1) * (W >> 1) + (i >> 1)], k = (j * W + i) * 4;
    d[k] = clamp(212 + n * 232, 0, 255); d[k + 1] = clamp(106 + n * 186, 0, 255); d[k + 2] = clamp(14 + n * 92, 0, 255); d[k + 3] = 255;
  }
  x.putImageData(im, 0, 0);
  for (var s = 0; s < 44; s++) {
    var px = Math.random() * W, py = Math.random() * H, r = 12 + Math.random() * 66;
    var g = x.createRadialGradient(px, py, 0, px, py, r);
    g.addColorStop(0, 'rgba(255,249,220,.70)'); g.addColorStop(1, 'rgba(255,200,90,0)');
    x.fillStyle = g; x.beginPath(); x.arc(px, py, r, 0, TAU); x.fill();
  }
  for (var s2 = 0; s2 < 24; s2++) {
    var qx = Math.random() * W, qy = Math.random() * H, rr = 20 + Math.random() * 88;
    var g2 = x.createRadialGradient(qx, qy, 0, qx, qy, rr);
    g2.addColorStop(0, 'rgba(150,52,0,.32)'); g2.addColorStop(1, 'rgba(150,52,0,0)');
    x.fillStyle = g2; x.beginPath(); x.arc(qx, qy, rr, 0, TAU); x.fill();
  }
  var t = new THREE.CanvasTexture(c); t.anisotropy = 4; return t;
}

/* 简化大陆轮廓（经度,纬度） */
var LAND = [
  [[-168,64],[-160,71],[-140,70],[-120,71],[-95,73],[-78,68],[-60,58],[-54,49],[-66,45],[-71,42],[-76,35],[-81,25],[-97,26],[-105,20],[-115,30],[-125,41],[-125,49],[-136,58],[-152,60]],
  [[-81,8],[-74,11],[-60,10],[-50,1],[-35,-6],[-38,-15],[-48,-25],[-58,-35],[-62,-42],[-68,-53],[-75,-50],[-72,-40],[-71,-20],[-78,-5]],
  [[-17,15],[-10,25],[0,35],[10,37],[25,32],[35,30],[43,12],[51,12],[42,-2],[40,-15],[35,-25],[20,-35],[18,-30],[12,-18],[9,-1],[5,5],[-8,5]],
  [[-10,36],[0,44],[5,52],[10,58],[25,70],[40,70],[60,72],[90,75],[130,72],[160,68],[179,66],[170,60],[140,45],[120,38],[122,30],[110,20],[100,10],[95,15],[80,8],[72,20],[60,25],[50,28],[43,12],[35,30],[28,36],[10,37],[0,35]],
  [[113,-22],[130,-12],[142,-10],[153,-27],[146,-38],[130,-32],[115,-34]],
  [[-45,60],[-20,70],[-20,82],[-45,84],[-60,80],[-58,68]],
  [[-180,-71],[180,-71],[180,-90],[-180,-90]]
];
function earthTexture() {
  var W = 1024, H = 512, c = cv(W, H), x = c.getContext('2d');
  var g = x.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, '#0b2242'); g.addColorStop(.5, '#103f77'); g.addColorStop(1, '#0b2242');
  x.fillStyle = g; x.fillRect(0, 0, W, H);
  for (var i = 0; i < 620; i++) {
    x.fillStyle = 'rgba(34,96,168,' + (0.02 + Math.random() * 0.05) + ')';
    x.beginPath(); x.arc(Math.random() * W, Math.random() * H, 8 + Math.random() * 46, 0, TAU); x.fill();
  }
  var X = function (lon) { return (lon + 180) / 360 * W; }, Y = function (lat) { return (90 - lat) / 180 * H; };
  LAND.forEach(function (poly, idx) {
    x.beginPath();
    poly.forEach(function (p, i) { var a = X(p[0]), b = Y(p[1]); i ? x.lineTo(a, b) : x.moveTo(a, b); });
    x.closePath(); x.save(); x.clip();
    var lg = x.createLinearGradient(0, 0, 0, H);
    if (idx === 6) { lg.addColorStop(0, '#eef5fa'); lg.addColorStop(.4, '#dfeaf2'); lg.addColorStop(1, '#c6d8e6'); }
    else {
      lg.addColorStop(0, '#8aa27c'); lg.addColorStop(.2, '#4e7c46'); lg.addColorStop(.46, '#3f7639');
      lg.addColorStop(.63, '#8d7d43'); lg.addColorStop(.82, '#5c6b38'); lg.addColorStop(1, '#3d6b3a');
    }
    x.fillStyle = lg; x.fillRect(0, 0, W, H);
    for (var k = 0; k < 120; k++) {
      x.fillStyle = 'rgba(' + (Math.random() > .5 ? '122,142,82,' : '58,48,28,') + (0.03 + Math.random() * 0.07) + ')';
      x.beginPath(); x.arc(Math.random() * W, Math.random() * H, 6 + Math.random() * 34, 0, TAU); x.fill();
    }
    x.restore();
  });
  [0, 1].forEach(function (i) {
    var gg = x.createLinearGradient(0, i ? H : 0, 0, i ? H * .845 : H * .155);
    gg.addColorStop(0, 'rgba(238,246,252,1)'); gg.addColorStop(1, 'rgba(238,246,252,0)');
    x.fillStyle = gg; x.fillRect(0, i ? H * .845 : 0, W, H * .155);
  });
  var t = new THREE.CanvasTexture(c); t.anisotropy = 4; return t;
}
function cloudTexture() {
  var W = 512, H = 256, c = cv(W, H), x = c.getContext('2d');
  var f = noiseField(W, H, 6, 4242, true), im = x.createImageData(W, H), d = im.data;
  for (var i = 0; i < W * H; i++) {
    d[i * 4] = 255; d[i * 4 + 1] = 255; d[i * 4 + 2] = 255;
    d[i * 4 + 3] = Math.round(smoothstep(0.55, 0.82, f[i]) * 185);
  }
  x.putImageData(im, 0, 0);
  var t = new THREE.CanvasTexture(c); return t;
}
function moonTexture() {
  var W = 1024, H = 512, c = cv(W, H), x = c.getContext('2d');
  var f = noiseField(W / 2, H / 2, 5, 9182, true), im = x.createImageData(W, H), d = im.data;
  for (var j = 0; j < H; j++) for (var i = 0; i < W; i++) {
    var n = f[(j >> 1) * (W >> 1) + (i >> 1)], k = (j * W + i) * 4;
    var b = 152 + (n - .5) * 86;
    d[k] = clamp(b + 8, 0, 255); d[k + 1] = clamp(b + 5, 0, 255); d[k + 2] = clamp(b - 5, 0, 255); d[k + 3] = 255;
  }
  x.putImageData(im, 0, 0);
  [[210,150,132],[300,205,96],[155,225,110],[540,180,88],[660,235,120],[430,120,72],[790,300,96]].forEach(function (m) {
    var g = x.createRadialGradient(m[0], m[1], 0, m[0], m[1], m[2]);
    g.addColorStop(0, 'rgba(96,98,104,.5)'); g.addColorStop(.65, 'rgba(110,112,116,.28)'); g.addColorStop(1, 'rgba(120,122,124,0)');
    x.fillStyle = g; x.beginPath(); x.arc(m[0], m[1], m[2], 0, TAU); x.fill();
  });
  for (var cr = 0; cr < 290; cr++) {
    var px = Math.random() * W, py = Math.random() * H, r = 2 + Math.pow(Math.random(), 2.4) * 30;
    x.beginPath(); x.arc(px, py, r, 0, TAU); x.fillStyle = 'rgba(126,127,132,' + (0.16 + Math.random() * 0.2) + ')'; x.fill();
    x.beginPath(); x.arc(px - r * .22, py - r * .22, r * .74, 0, TAU); x.fillStyle = 'rgba(198,199,200,' + (0.10 + Math.random() * 0.16) + ')'; x.fill();
    x.beginPath(); x.arc(px, py, r, 0, TAU); x.strokeStyle = 'rgba(228,229,228,' + (0.09 + Math.random() * 0.15) + ')'; x.lineWidth = Math.max(.6, r * .13); x.stroke();
  }
  for (var ry = 0; ry < 20; ry++) {
    var ox = Math.random() * W, oy = Math.random() * H, an = Math.random() * TAU, ln = 20 + Math.random() * 88;
    var rg = x.createLinearGradient(ox, oy, ox + Math.cos(an) * ln, oy + Math.sin(an) * ln);
    rg.addColorStop(0, 'rgba(232,232,230,.16)'); rg.addColorStop(1, 'rgba(232,232,230,0)');
    x.strokeStyle = rg; x.lineWidth = 1 + Math.random() * 2;
    x.beginPath(); x.moveTo(ox, oy); x.lineTo(ox + Math.cos(an) * ln, oy + Math.sin(an) * ln); x.stroke();
  }
  var t = new THREE.CanvasTexture(c); t.anisotropy = 4; return t;
}
function glowTexture(inner, mid) {
  var S = 512, c = cv(S, S), x = c.getContext('2d');
  var g = x.createRadialGradient(S / 2, S / 2, 0, S / 2, S / 2, S / 2);
  g.addColorStop(0, inner); g.addColorStop(.26, mid);
  g.addColorStop(.56, 'rgba(255,172,62,.12)'); g.addColorStop(1, 'rgba(255,140,30,0)');
  x.fillStyle = g; x.fillRect(0, 0, S, S);
  return new THREE.CanvasTexture(c);
}

/* ---------------------------------------------------------------------------
   3. 渲染器 / 场景 / 相机
--------------------------------------------------------------------------- */
var stage = $('stage'), gl = $('gl');
var renderer = new THREE.WebGLRenderer({ canvas: gl, antialias: true, alpha: true, powerPreference: 'high-performance' });
renderer.setClearColor(0x000000, 0);
if ('outputEncoding' in renderer) renderer.outputEncoding = THREE.sRGBEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.97;

var scene = new THREE.Scene();
var camera = new THREE.PerspectiveCamera(38, 1, 0.4, 3000);

var controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = 0.062;
controls.enablePan = false; controls.minDistance = 24; controls.maxDistance = 340;
controls.rotateSpeed = 0.6; controls.zoomSpeed = 0.78;
controls.autoRotate = !RM_; controls.autoRotateSpeed = 0.34;

/* ---------- 星空 ---------- */
var starGroup = new THREE.Group(); scene.add(starGroup);
(function () {
  var N = 1900, pos = new Float32Array(N * 3), col = new Float32Array(N * 3), c = new THREE.Color();
  for (var i = 0; i < N; i++) {
    var u = Math.random() * 2 - 1, th = Math.random() * TAU, s = Math.sqrt(1 - u * u), R = 620 + Math.random() * 260;
    pos[i * 3] = Math.cos(th) * s * R; pos[i * 3 + 1] = u * R; pos[i * 3 + 2] = Math.sin(th) * s * R;
    var b = 0.30 + Math.pow(Math.random(), 2.6) * 0.9, tt = Math.random();
    if (tt > .82) c.setRGB(b * .76, b * .85, b);
    else if (tt > .68) c.setRGB(b, b * .90, b * .76);
    else c.setRGB(b, b, b);
    col[i * 3] = c.r; col[i * 3 + 1] = c.g; col[i * 3 + 2] = c.b;
  }
  var g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  starGroup.add(new THREE.Points(g, new THREE.PointsMaterial({
    size: 3.1, sizeAttenuation: true, vertexColors: true, transparent: true,
    opacity: .92, depthWrite: false, blending: THREE.AdditiveBlending, map: glowTexture('rgba(255,255,255,1)', 'rgba(255,255,255,.45)')
  })));
})();

/* ---------- 太阳 ---------- */
var sunGroup = new THREE.Group(); sunGroup.position.x = SUN_X; scene.add(sunGroup);
var sunMesh = new THREE.Mesh(new THREE.SphereGeometry(SUN_R, 48, 34), new THREE.MeshBasicMaterial({ map: sunTexture() }));
sunGroup.add(sunMesh);
var gTex = glowTexture('rgba(255,252,232,1)', 'rgba(255,206,110,.70)');
[[SUN_R * 3.2, .52], [SUN_R * 6.0, .22], [SUN_R * 11.0, .09]].forEach(function (L, i) {
  var sp = new THREE.Sprite(new THREE.SpriteMaterial({
    map: gTex, color: i === 0 ? 0xfff2cf : 0xffb85a, transparent: true, opacity: L[1],
    blending: THREE.AdditiveBlending, depthWrite: false
  }));
  sp.scale.set(L[0] * 2, L[0] * 2, 1); sp.renderOrder = -10 + i; sunGroup.add(sp);
});
var sunLight = new THREE.PointLight(0xfff3d6, 1.85, 0, 0); sunLight.position.set(SUN_X, 0, 0); scene.add(sunLight);
scene.add(new THREE.AmbientLight(0x2b3d63, 0.50));
var fillLight = new THREE.DirectionalLight(0x9cbcff, 0.24); fillLight.position.set(6, 24, 44); scene.add(fillLight);

/* ---------- 地球 ---------- */
var earthGroup = new THREE.Group(); scene.add(earthGroup);
var earthMesh = new THREE.Mesh(new THREE.SphereGeometry(EARTH_R, 48, 34),
  new THREE.MeshPhongMaterial({ map: earthTexture(), shininess: 14, specular: 0x24384f }));
earthGroup.add(earthMesh);
var cloudMesh = new THREE.Mesh(new THREE.SphereGeometry(EARTH_R * 1.014, 40, 26),
  new THREE.MeshPhongMaterial({ map: cloudTexture(), transparent: true, opacity: .48, depthWrite: false }));
earthGroup.add(cloudMesh);
earthGroup.add(new THREE.Mesh(new THREE.SphereGeometry(EARTH_R * 1.11, 40, 26), new THREE.ShaderMaterial({
  transparent: true, side: THREE.BackSide, depthWrite: false, blending: THREE.AdditiveBlending,
  uniforms: { uColor: { value: new THREE.Color(0x5aa6ff) }, uPow: { value: 3.0 }, uInt: { value: .82 } },
  vertexShader: 'varying vec3 vN;varying vec3 vV;void main(){vec4 mv=modelViewMatrix*vec4(position,1.0);vN=normalize(normalMatrix*normal);vV=normalize(-mv.xyz);gl_Position=projectionMatrix*mv;}',
  fragmentShader: 'uniform vec3 uColor;uniform float uPow;uniform float uInt;varying vec3 vN;varying vec3 vV;void main(){float f=pow(clamp(1.0-abs(dot(normalize(vN),normalize(vV))),0.0,1.0),uPow);gl_FragColor=vec4(uColor,f*uInt);}'
})));

/* ---------- 月球 ---------- */
var moonMesh = new THREE.Mesh(new THREE.SphereGeometry(MOON_R, 44, 30),
  new THREE.MeshPhongMaterial({ map: moonTexture(), shininess: 2, specular: 0x101010 }));
scene.add(moonMesh);

/* ---------------------------------------------------------------------------
   4. 影锥（本影 / 半影）
--------------------------------------------------------------------------- */
function coneMat(color, edge, a0, a1, fres) {
  return new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, side: THREE.DoubleSide,
    uniforms: {
      uColor: { value: new THREE.Color(color) }, uEdge: { value: new THREE.Color(edge) },
      uA0: { value: a0 }, uA1: { value: a1 }, uF: { value: fres }
    },
    vertexShader: 'varying vec2 vUv;varying vec3 vN;varying vec3 vV;void main(){vUv=uv;vec4 mv=modelViewMatrix*vec4(position,1.0);vN=normalize(normalMatrix*normal);vV=normalize(-mv.xyz);gl_Position=projectionMatrix*mv;}',
    fragmentShader: [
      'uniform vec3 uColor;uniform vec3 uEdge;uniform float uA0;uniform float uA1;uniform float uF;',
      'varying vec2 vUv;varying vec3 vN;varying vec3 vV;',
      'void main(){',
      '  float t=clamp(vUv.y,0.0,1.0);',
      '  float a=mix(uA0,uA1,pow(t,0.7));',
      '  float fr=pow(clamp(1.0-abs(dot(normalize(vN),normalize(vV))),0.0,1.0),2.1);',
      '  vec3 col=mix(uColor,uEdge,clamp(fr*uF,0.0,1.0));',
      '  a*=(0.58+0.80*fr*uF);',
      '  gl_FragColor=vec4(col,clamp(a,0.0,1.0));',
      '}'
    ].join('\n')
  });
}
var umbraGroup = new THREE.Group(), penGroup = new THREE.Group();
scene.add(umbraGroup); scene.add(penGroup);

function rebuildCones(mode) {
  [umbraGroup, penGroup].forEach(function (g) {
    while (g.children.length) { var o = g.children.pop(); o.geometry.dispose(); o.material.dispose(); }
  });
  var occR = mode === 'sun' ? MOON_R : EARTH_R, g = CONE[mode];
  var penLen = mode === 'sun' ? 27 : 36;

  var ug = new THREE.ConeGeometry(occR, g.lenU, 88, 1, true);
  ug.rotateZ(-Math.PI / 2); ug.translate(g.lenU / 2, 0, 0);
  var um = new THREE.Mesh(ug, coneMat(0x0c1a34, 0xa8c8ff, .78, .22, 1.5));
  um.renderOrder = 3; umbraGroup.add(um);

  var pg = new THREE.CylinderGeometry(occR + penLen * g.tanP, occR, penLen, 88, 1, true);
  pg.rotateZ(-Math.PI / 2); pg.translate(penLen / 2, 0, 0);
  var pm = new THREE.Mesh(pg, coneMat(0x3a5c92, 0xa8c8ff, .18, .02, 0.55));
  pm.renderOrder = 2; penGroup.add(pm);
}
rebuildCones('sun');

/* ---------- 切线光线：外公切线=本影边界，内公切线=半影边界 ---------- */
var rayMat = new THREE.LineDashedMaterial({ color: 0xffd76b, dashSize: 1.0, gapSize: .68, transparent: true, opacity: .60, depthWrite: false });
var rayGeo = new THREE.BufferGeometry();
rayGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(8 * 3), 3));
var rayLines = new THREE.LineSegments(rayGeo, rayMat);
rayLines.renderOrder = 4; rayLines.frustumCulled = false; scene.add(rayLines);

function tangentSegs(sunX, sunR, occX, occY, occR, endX) {
  var d = occX - sunX;
  return [[sunR, occR], [-sunR, -occR], [-sunR, occR], [sunR, -occR]].map(function (p) {
    var y0 = p[0], y1 = occY + p[1], sl = (y1 - y0) / d;
    return [sunX, y0, 0, endX, y1 + sl * (endX - occX), 0];
  });
}

/* ---------- 平行光束（体现光沿直线传播，被遮挡体截断） ---------- */
var BEAM_N = 34;
var beamGeo = new THREE.BufferGeometry();
beamGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(BEAM_N * 6), 3));
var beams = new THREE.LineSegments(beamGeo,
  new THREE.LineBasicMaterial({ color: 0xffd489, transparent: true, opacity: .105, depthWrite: false }));
beams.renderOrder = 1; beams.frustumCulled = false; scene.add(beams);
var beamOrigins = (function () {
  var a = [];
  for (var i = 0; i < BEAM_N; i++) {
    var th = i * 2.3999632, r = SUN_R * 0.94 * Math.sqrt((i + .4) / BEAM_N);
    a.push([Math.cos(th) * r, Math.sin(th) * r]);
  }
  return a;
})();

/* ---------------------------------------------------------------------------
   5. 标签层
--------------------------------------------------------------------------- */
var labelBox = $('labels'), LBL = {}, stageW = 1, stageH = 1;
[['sun', '太阳', 'is-sun', ''], ['moon', '月球', 'is-key', ''], ['earth', '地球', 'is-key', ''],
 ['umbra', '本影区', 'is-umbra', 'u'], ['pen', '半影区', 'is-pen', 'd']].forEach(function (d) {
  var e = document.createElement('div');
  e.className = 'lbl ' + d[2] + (d[3] ? ' ' + d[3] : '');
  e.textContent = d[1]; e.style.opacity = '0';
  e._dy = d[3] === 'u' ? -46 : d[3] === 'd' ? 34 : 0;
  e._off = d[3] === 'u' ? ' translateY(-100%)' : d[3] === 'd' ? ' translateY(0)' : '';
  e._o = '0';
  labelBox.appendChild(e); LBL[d[0]] = e;
});
var _v = new THREE.Vector3();
function placeLabel(el, x, y, z) {
  _v.set(x, y, z).project(camera);
  if (_v.z > 1) { if (el._o !== '0') { el.style.opacity = '0'; el._o = '0'; } return; }
  var sx = (_v.x * .5 + .5) * stageW, sy = (-_v.y * .5 + .5) * stageH;
  var op = (sx < -30 || sx > stageW + 30) ? '0' : '1';
  var px = Math.round(sx * 2) / 2, py = Math.round((sy + el._dy) * 2) / 2;
  if (el._px !== px || el._py !== py) {
    el._px = px; el._py = py;
    el.style.transform = 'translate(-50%,-50%) translate(' + px + 'px,' + py + 'px)' + el._off;
  }
  if (el._o !== op) { el.style.opacity = op; el._o = op; }
}

/* ---------------------------------------------------------------------------
   6. 观测窗（PiP）
--------------------------------------------------------------------------- */
var pipcv = $('pipcv'), px = pipcv.getContext('2d');
var PC = 224, CX = PC, CY = PC;
var SUN_PX_R = 60;
var MOON_PX_R_S = SUN_PX_R * (MOON_R / 15.9) / (SUN_R / 65.9);   // ≈ 69.1
var MOON_PX_R_L = 56, VIEW_R = 210;

function overlapFrac(d, r1, r2) {
  if (d >= r1 + r2) return 0;
  if (d <= Math.abs(r1 - r2)) { var rm = Math.min(r1, r2); return rm * rm / (r1 * r1); }
  var a1 = Math.acos(clamp((d * d + r1 * r1 - r2 * r2) / (2 * d * r1), -1, 1));
  var a2 = Math.acos(clamp((d * d + r2 * r2 - r1 * r1) / (2 * d * r2), -1, 1));
  var s = (-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2);
  return (r1 * r1 * a1 + r2 * r2 * a2 - .5 * Math.sqrt(Math.max(0, s))) / (Math.PI * r1 * r1);
}

function drawSolarPip() {
  var dy = MOON_PX_R_S * moonMesh.position.y, d = Math.abs(dy);
  var RS = SUN_PX_R, RM = MOON_PX_R_S, frac = overlapFrac(d, RS, RM);
  if (d < RM - RS) {                                    /* 全食：日冕 */
    var k = smoothstep(0, 1, 1 - d / Math.max(1e-3, RM - RS));
    var cg = px.createRadialGradient(CX, CY, RS * .9, CX, CY, RS * 2.35);
    cg.addColorStop(0, 'rgba(255,255,255,' + (.88 * k) + ')');
    cg.addColorStop(.15, 'rgba(240,247,255,' + (.48 * k) + ')');
    cg.addColorStop(.42, 'rgba(178,206,255,' + (.19 * k) + ')');
    cg.addColorStop(1, 'rgba(140,180,255,0)');
    px.fillStyle = cg; px.beginPath(); px.arc(CX, CY, RS * 2.4, 0, TAU); px.fill();
  } else {                                              /* 部分食：柔光 */
    var hg = px.createRadialGradient(CX, CY, RS * .78, CX, CY, RS * 1.95);
    hg.addColorStop(0, 'rgba(255,214,130,.30)'); hg.addColorStop(1, 'rgba(255,170,60,0)');
    px.fillStyle = hg; px.beginPath(); px.arc(CX, CY, RS * 2, 0, TAU); px.fill();
  }
  var g = px.createRadialGradient(CX - RS * .17, CY - RS * .17, RS * .08, CX, CY, RS);
  g.addColorStop(0, '#fffdf4'); g.addColorStop(.42, '#ffe7a4');
  g.addColorStop(.74, '#ffc75e'); g.addColorStop(.93, '#ff9c2d'); g.addColorStop(1, '#f47a15');
  px.fillStyle = g; px.beginPath(); px.arc(CX, CY, RS, 0, TAU); px.fill();
  for (var i = 0; i < 62; i++) {
    var aa = i * 2.3999632, rr = RS * .82 * Math.sqrt((i + .5) / 62);
    px.fillStyle = 'rgba(' + (i % 3 ? '255,246,206,' : '226,120,26,') + '0.13)';
    px.beginPath(); px.arc(CX + Math.cos(aa) * rr, CY + Math.sin(aa) * rr, 3.2 + (i % 5) * 1.9, 0, TAU); px.fill();
  }
  var my = CY + dy;
  var mg = px.createRadialGradient(CX - RM * .3, my - RM * .3, RM * .1, CX, my, RM);
  mg.addColorStop(0, '#151a24'); mg.addColorStop(.78, '#080b12'); mg.addColorStop(1, '#05070d');
  px.fillStyle = mg; px.beginPath(); px.arc(CX, my, RM, 0, TAU); px.fill();
  px.beginPath(); px.arc(CX, my, RM - .8, 0, TAU);
  px.strokeStyle = 'rgba(140,164,210,.28)'; px.lineWidth = 1.4; px.stroke();
  return frac;
}

function drawLunarPip() {
  var RM = MOON_PX_R_L, k = RM / (MOON_R / 15.9);
  var dy = k * (moonMesh.position.y / 15.9);
  var dist = Math.abs(MODE.moon.moonX - MODE.moon.earthX);
  var uR = EARTH_R - dist * CONE.moon.tanU, pR = EARTH_R + dist * CONE.moon.tanP;
  var uPx = k * (uR / 15.9), pPx = k * (pR / 15.9);
  var mx = CX, my = CY + dy;

  px.save(); px.beginPath(); px.arc(mx, my, RM, 0, TAU); px.clip();
  var pg = px.createRadialGradient(CX, CY, uPx * .9, CX, CY, pPx);
  pg.addColorStop(0, 'rgba(0,0,0,0)'); pg.addColorStop(1, 'rgba(0,0,0,.36)');
  px.fillStyle = pg; px.fillRect(0, 0, PC * 2, PC * 2);

  var g = px.createRadialGradient(mx - RM * .32, my - RM * .32, RM * .08, mx, my, RM);
  g.addColorStop(0, '#f4f5f0'); g.addColorStop(.55, '#d1d2cc'); g.addColorStop(.88, '#a0a4a0'); g.addColorStop(1, '#7d827f');
  px.fillStyle = g; px.beginPath(); px.arc(mx, my, RM, 0, TAU); px.fill();

  for (var i = 0; i < 54; i++) {
    var aa = i * 2.3999632, rr = RM * .88 * Math.sqrt((i + .5) / 54);
    var cx2 = mx + Math.cos(aa) * rr, cy2 = my + Math.sin(aa) * rr, cr = 1.6 + (i % 6) * 1.5;
    px.beginPath(); px.arc(cx2, cy2, cr, 0, TAU); px.fillStyle = 'rgba(130,134,130,.26)'; px.fill();
    px.beginPath(); px.arc(cx2 - cr * .2, cy2 - cr * .2, cr * .72, 0, TAU); px.fillStyle = 'rgba(244,245,240,.20)'; px.fill();
  }
  [[-.34, -.18, .34], [.26, .10, .26], [-.06, .42, .22]].forEach(function (m) {
    var gx = mx + m[0] * RM, gy = my + m[1] * RM;
    var mg2 = px.createRadialGradient(gx, gy, 0, gx, gy, m[2] * RM);
    mg2.addColorStop(0, 'rgba(122,126,124,.42)'); mg2.addColorStop(1, 'rgba(122,126,124,0)');
    px.fillStyle = mg2; px.beginPath(); px.arc(gx, gy, m[2] * RM, 0, TAU); px.fill();
  });

  var ug = px.createRadialGradient(CX, CY, 0, CX, CY, uPx);
  ug.addColorStop(0, 'rgba(92,24,12,.96)'); ug.addColorStop(.6, 'rgba(122,40,20,.94)');
  ug.addColorStop(.9, 'rgba(142,60,32,.78)'); ug.addColorStop(1, 'rgba(152,72,40,.32)');
  px.fillStyle = ug; px.beginPath(); px.arc(CX, CY, uPx, 0, TAU); px.fill();
  var rg = px.createRadialGradient(CX, CY, uPx * .35, CX, CY, uPx);
  rg.addColorStop(0, 'rgba(202,78,36,.24)'); rg.addColorStop(1, 'rgba(202,78,36,0)');
  px.fillStyle = rg; px.beginPath(); px.arc(CX, CY, uPx, 0, TAU); px.fill();
  px.restore();

  px.beginPath(); px.arc(CX, CY, uPx, 0, TAU);
  px.strokeStyle = 'rgba(204,124,90,.34)'; px.lineWidth = 1.4; px.setLineDash([5, 5]); px.stroke(); px.setLineDash([]);
  px.beginPath(); px.arc(mx, my, RM, 0, TAU);
  px.strokeStyle = 'rgba(226,236,255,.15)'; px.lineWidth = 1.2; px.stroke();
  return overlapFrac(Math.abs(dy), RM, uPx);
}

function drawPip() {
  px.setTransform(1, 0, 0, 1, 0, 0);
  px.clearRect(0, 0, PC * 2, PC * 2);
  var bg = px.createRadialGradient(CX, CY, 0, CX, CY, PC * 1.45);
  bg.addColorStop(0, '#080d1a'); bg.addColorStop(1, '#02040a');
  px.fillStyle = bg; px.fillRect(0, 0, PC * 2, PC * 2);
  px.save();
  px.beginPath(); px.arc(CX, CY, VIEW_R - 2, 0, TAU); px.clip();
  px.fillStyle = '#040711'; px.fillRect(0, 0, PC * 2, PC * 2);
  for (var i = 0; i < 58; i++) {
    var a = (i * 2.3999632) % TAU, rr = 12 + ((i * 37) % (VIEW_R - 18));
    px.fillStyle = 'rgba(210,226,255,' + (0.09 + ((i * 53) % 30) / 300) + ')';
    px.fillRect(CX + Math.cos(a) * rr, CY + Math.sin(a) * rr, 1.6, 1.6);
  }
  var frac = mode === 'sun' ? drawSolarPip() : drawLunarPip();
  px.restore();
  px.beginPath(); px.arc(CX, CY, VIEW_R - 2, 0, TAU);
  px.strokeStyle = 'rgba(122,156,220,.26)'; px.lineWidth = 1.6; px.stroke();
  px.beginPath(); px.arc(CX, CY, VIEW_R - 10, 0, TAU);
  px.strokeStyle = 'rgba(122,156,220,.09)'; px.lineWidth = 1; px.stroke();
  return frac;
}

var lastPipKey = '';
function updatePip(force) {
  var key = mode + '|' + moonMesh.position.y.toFixed(4);
  if (!force && key === lastPipKey) return;
  lastPipKey = key;
  var pct = Math.round(drawPip() * 100);
  var el = $('pip-pct');
  if (el.textContent !== pct + '%') el.textContent = pct + '%';
  el.style.color = pct > 45 ? '#ffc98a' : '#93a7ca';
}

/* ---------------------------------------------------------------------------
   7. 状态与 UI
--------------------------------------------------------------------------- */
var mode = 'sun', t = PHASES.sun[0].t, playing = false, sideView = false, camAnim = null, camFit = 96, narrowNow = false;
var basePos = new THREE.Vector3(9, 31, 84);
var lastStepKey = '';

function buildSteps() {
  var box = $('steps'); box.innerHTML = '';
  PHASES[mode].forEach(function (p, i) {
    var b = document.createElement('button');
    b.className = 'step'; b.setAttribute('role', 'tab');
    b.innerHTML = '<span class="no">0' + (i + 1) + '</span><span class="nm">' + p.n + '</span>';
    b.title = p.d;
    b.addEventListener('click', function () { setT(p.t, true); });
    box.appendChild(b);
  });
  var tk = $('ticks'); tk.innerHTML = '';
  PHASES[mode].forEach(function (p) { var i = document.createElement('i'); i.style.left = (p.t * 100) + '%'; tk.appendChild(i); });
  lastStepKey = '';
}
function syncSteps() {
  var arr = $('steps').children, ph = PHASES[mode], best = 0, bd = 9;
  for (var i = 0; i < ph.length; i++) { var d = Math.abs(ph[i].t - t); if (d < bd) { bd = d; best = i; } }
  var hit = bd < .055;
  var key = mode + '|' + (hit ? best : 'x' + best);
  if (key === lastStepKey) return;
  lastStepKey = key;
  for (var j = 0; j < arr.length; j++) arr[j].setAttribute('aria-current', (hit && j === best) ? 'true' : 'false');
  $('blurb-name').textContent = ph[best].n;
  $('blurb-text').textContent = ph[best].d;
  $('phase-blurb').classList.toggle('dim', !hit);
}
function setT(v, pause) {
  t = clamp(v, 0, 1);
  if (pause) { playing = false; setPlayIcon(); }
  $('slider').setAttribute('aria-valuenow', Math.round(t * 100));
  $('fill').style.width = (t * 100) + '%';
  $('knob').style.left = (t * 100) + '%';
}
function setPlayIcon() {
  $('ic-play').style.display = playing ? 'none' : 'block';
  $('ic-pause').style.display = playing ? 'block' : 'none';
  $('play').setAttribute('aria-label', playing ? '暂停' : '播放');
}
function toast(msg) {
  var el = $('toast'); el.textContent = msg; el.classList.add('on');
  clearTimeout(toast._t); toast._t = setTimeout(function () { el.classList.remove('on'); }, 2600);
}
function switchMode(m) {
  if (m === mode) return;
  mode = m;
  $('modes').dataset.mode = m;
  $('tab-sun').setAttribute('aria-selected', m === 'sun');
  $('tab-moon').setAttribute('aria-selected', m === 'moon');
  $('ttl').innerHTML = MODE[m].name.charAt(0) + '<em>' + MODE[m].name.slice(1) + '</em>';
  $('sb').innerHTML = MODE[m].sub + '<i class="note">示意图，天体大小与距离非真实比例</i>';
  rebuildCones(m);
  buildSteps();
  resize();
  setT(0.5, true);
  var to = new THREE.Vector3(camX(m), TY, 0);
  var sc = camFit / basePos.length();
  camAnim = {
    k: 0, dur: 1.0,
    from: camera.position.clone(), to: to.clone().add(basePos.clone().multiplyScalar(sc)),
    fromT: controls.target.clone(), toT: to
  };
  toast(m === 'sun' ? '月球移至日地之间 · 月球的影锥投向地球' : '地球移至日月之间 · 月球进入地球影锥');
  updatePip(true);
}

/* 滑块 */
(function () {
  var sl = $('slider'), dragging = false;
  function fromEvt(e) {
    var r = sl.getBoundingClientRect();
    var cx = (e.touches ? e.touches[0].clientX : e.clientX) - r.left;
    setT(cx / r.width, true);
  }
  sl.addEventListener('pointerdown', function (e) { dragging = true; sl.classList.add('dragging'); try { sl.setPointerCapture(e.pointerId); } catch (x) {} fromEvt(e); });
  sl.addEventListener('pointermove', function (e) { if (dragging) fromEvt(e); });
  sl.addEventListener('pointerup', function () { dragging = false; sl.classList.remove('dragging'); });
  sl.addEventListener('pointercancel', function () { dragging = false; sl.classList.remove('dragging'); });
  sl.addEventListener('keydown', function (e) {
    if (e.key === 'Home') { setT(0, true); e.preventDefault(); return; }
    if (e.key === 'End') { setT(1, true); e.preventDefault(); return; }
    var d = (e.key === 'ArrowRight' || e.key === 'ArrowUp') ? .012 : (e.key === 'ArrowLeft' || e.key === 'ArrowDown') ? -.012 : 0;
    if (d) { setT(t + d, true); e.preventDefault(); }
  });
})();

$('play').addEventListener('click', function () { playing = !playing; if (playing && t >= .999) setT(0); setPlayIcon(); });
$('tab-sun').addEventListener('click', function () { switchMode('sun'); });
$('tab-moon').addEventListener('click', function () { switchMode('moon'); });
$('tool-orbit').addEventListener('click', function () {
  controls.autoRotate = !controls.autoRotate;
  this.setAttribute('aria-pressed', controls.autoRotate);
  toast(controls.autoRotate ? '自动环绕已开启' : '自动环绕已暂停，可自由拖拽观察');
});
$('tool-reset').addEventListener('click', function () { resetCam(); toast('视角已重置'); });
$('tool-side').addEventListener('click', function () {
  sideView = !sideView;
  this.setAttribute('aria-pressed', sideView);
  if (sideView) {
    controls.autoRotate = false; $('tool-orbit').setAttribute('aria-pressed', 'false');
    var tg = controls.target.clone();
    camAnim = { k: 0, dur: .85, from: camera.position.clone(), to: new THREE.Vector3(tg.x + 1.5, 5, camFit * 1.02), fromT: tg, toT: tg };
    toast('正侧视 · 光线与影锥的几何关系最清晰');
  } else { resetCam(); toast('已回到立体视角'); }
});
window.addEventListener('keydown', function (e) {
  if (e.code === 'Space' && document.activeElement !== $('slider')) { e.preventDefault(); $('play').click(); }
  if (e.key === '1') switchMode('sun');
  if (e.key === '2') switchMode('moon');
});

function resetCam() {
  sideView = false; $('tool-side').setAttribute('aria-pressed', 'false');
  controls.autoRotate = !RM_; $('tool-orbit').setAttribute('aria-pressed', String(controls.autoRotate));
  camAnim = null;
  var tg = new THREE.Vector3(camX(mode), TY, 0);
  var sc = camFit / basePos.length();
  controls.target.copy(tg);
  camera.position.copy(tg).add(basePos.clone().multiplyScalar(sc));
  controls.update();
}

/* ---------------------------------------------------------------------------
   8. 自适应
--------------------------------------------------------------------------- */
function resize() {
  stageW = stage.clientWidth; stageH = stage.clientHeight;
  applyPQ();
  renderer.setSize(stageW, stageH, false);
  camera.aspect = stageW / Math.max(1, stageH);
  /* 竖屏（手机）横向空间紧张：收紧取景跨度并把注视点左移，
     让「月球—地球」放大呈现，太阳仍留在画面内 */
  narrowNow = camera.aspect < 0.92;
  var spanX = SPAN[mode] * (narrowNow ? 0.845 : 1);
  var halfH = Math.tan(camera.fov * Math.PI / 360);
  camFit = Math.max((spanX * .5) / (halfH * camera.aspect), 74);
  camera.updateProjectionMatrix();
}
function camX(m) { return TGT[m] + (narrowNow ? -3.2 : 0); }

/* 自适应画质：若持续掉帧，逐步下调渲染分辨率，保证拖拽/旋转跟手 */
var PQ = 1, pqCool = 0, fpsAcc = 0, fpsFrames = 0;
function applyPQ() {
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75) * PQ);
}
function tickQuality(dt) {
  if (document.hidden || dt <= 0) return;
  fpsAcc += dt; fpsFrames++;
  if (fpsAcc < 1.3) return;
  var f = fpsFrames / fpsAcc;
  fpsAcc = 0; fpsFrames = 0;
  var now = (window.performance && performance.now) ? performance.now() : Date.now();
  if (f < 26 && PQ > 0.62 && now > pqCool) {
    PQ = Math.max(0.6, PQ - 0.2);
    pqCool = now + 4000;
    applyPQ();
    renderer.setSize(stageW, stageH, false);
  }
}
window.addEventListener('resize', resize);
window.addEventListener('orientationchange', function () { setTimeout(resize, 260); });

/* ---------------------------------------------------------------------------
   9. 主循环
--------------------------------------------------------------------------- */
var clock = new THREE.Clock();
function frame() {
  requestAnimationFrame(frame);
  var dt = Math.min(clock.getDelta(), 0.05);
  tickQuality(dt);

  if (playing) {
    t += dt / (mode === 'sun' ? 15 : 19);
    if (t > 1) t = 0;
    setT(t, false);
  }

  var m = MODE[mode], y = yAt(mode, t);
  moonMesh.position.set(m.moonX, y, 0);
  earthGroup.position.set(m.earthX, 0, 0);

  var occX = mode === 'sun' ? m.moonX : m.earthX;
  var occY = mode === 'sun' ? y : 0;
  var occR = mode === 'sun' ? MOON_R : EARTH_R;
  /* 影锥轴线始终沿「太阳中心 → 遮挡体中心」的连线，
     因此月球偏离轴线时影锥会随之倾斜，本影斑才会真正扫过地球 */
  var tilt = Math.atan2(occY, occX - SUN_X);
  umbraGroup.position.set(occX, occY, 0); umbraGroup.rotation.z = tilt;
  penGroup.position.set(occX, occY, 0); penGroup.rotation.z = tilt;

  /* 切线光线 */
  var segs = tangentSegs(SUN_X, SUN_R, occX, occY, occR, mode === 'sun' ? 31 : 46);
  var arr = rayGeo.attributes.position.array;
  for (var i = 0; i < segs.length; i++) for (var j = 0; j < 6; j++) arr[i * 6 + j] = segs[i][j];
  rayGeo.attributes.position.needsUpdate = true;
  rayLines.computeLineDistances();

  /* 平行光束：被月球与地球共同截断（地球上背光侧同样无阳光） */
  var bp = beamGeo.attributes.position.array;
  var farX = mode === 'sun' ? 31 : 46;
  var bodies = [[m.moonX, y, MOON_R], [m.earthX, 0, EARTH_R]];
  for (var b = 0; b < BEAM_N; b++) {
    var by = beamOrigins[b][0], bz = beamOrigins[b][1];
    var sx = SUN_X + Math.sqrt(Math.max(0, SUN_R * SUN_R - by * by - bz * bz));
    var ex = farX;
    for (var q = 0; q < 2; q++) {
      var bx = bodies[q][0], cy = by - bodies[q][1], cz = bz, dd = cy * cy + cz * cz;
      if (dd < bodies[q][2] * bodies[q][2]) {
        var hit = bx - Math.sqrt(bodies[q][2] * bodies[q][2] - dd);
        if (hit > sx && hit < ex) ex = hit;
      }
    }
    bp[b * 6] = sx; bp[b * 6 + 1] = by; bp[b * 6 + 2] = bz;
    bp[b * 6 + 3] = ex; bp[b * 6 + 4] = by; bp[b * 6 + 5] = bz;
  }
  beamGeo.attributes.position.needsUpdate = true;

  if (!RM_) {
    moonMesh.rotation.y += dt * 0.07;
    earthMesh.rotation.y += dt * 0.028;
    cloudMesh.rotation.y += dt * 0.040;
    sunMesh.rotation.y += dt * 0.011;
    starGroup.rotation.y += dt * 0.0021;
  }

  /* 相机 */
  var tgx = camX(mode);
  if (camAnim) {
    camAnim.k += dt / camAnim.dur;
    var kk = smoothstep(0, 1, Math.min(1, camAnim.k));
    camera.position.lerpVectors(camAnim.from, camAnim.to, kk);
    controls.target.lerpVectors(camAnim.fromT, camAnim.toT, kk);
    if (camAnim.k >= 1) camAnim = null;
  } else {
    controls.target.x += (tgx - controls.target.x) * Math.min(1, dt * 2.2);
    controls.target.y += (TY - controls.target.y) * Math.min(1, dt * 2.2);
  }
  controls.update();
  renderer.render(scene, camera);

  /* 标签：沿影锥自身坐标系定位，锥体倾斜时标签同步跟随 */
  var cp = function (dist, off) {
    return [occX + Math.cos(tilt) * dist - Math.sin(tilt) * off,
            occY + Math.sin(tilt) * dist + Math.cos(tilt) * off];
  };
  placeLabel(LBL.sun, SUN_X, SUN_R + 1.1, 0);
  placeLabel(LBL.moon, m.moonX, y + MOON_R + 1.1, 0);
  placeLabel(LBL.earth, m.earthX, EARTH_R + 1.3, 0);
  var u1 = cp(mode === 'sun' ? 6 : 13, mode === 'sun' ? 0.15 : -1.1);
  var p1 = cp(mode === 'sun' ? 11 : 9, mode === 'sun' ? 1.6 : 2.4);
  placeLabel(LBL.umbra, u1[0], u1[1], 0);
  placeLabel(LBL.pen, p1[0], p1[1], 0);

  $('roff').textContent = (y >= 0 ? '+' : '−') + Math.abs(y).toFixed(2);
  syncSteps();
  updatePip(false);
}

/* ---------------------------------------------------------------------------
   10. 启动
--------------------------------------------------------------------------- */
function boot() {
  resize();
  resetCam();
  buildSteps();
  setT(PHASES.sun[0].t, true);
  setPlayIcon();
  updatePip(true);
  frame();
  setTimeout(function () { $('boot').classList.add('gone'); }, 300);
  setTimeout(function () {
    toast('拖拽可旋转视角 · 滚轮/双指缩放 · 点阶段卡片看全过程');
  }, 1350);
}
try { boot(); }
catch (err) {
  var bt = $('boot-txt');
  bt.className = 'err';
  bt.textContent = '3D 初始化失败：' + (err && err.message ? err.message : String(err)) + '　请用新版 Chrome / Edge 打开。';
  $('boot').classList.remove('gone');
  if (window.console) console.error(err);
}

})();
