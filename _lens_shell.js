
/* ==========================================================================
   光学 3D 场景外壳 · 共用运行时
   --------------------------------------------------------------------------
   职责：渲染器/相机/控制器/灯光/循环、3D 坐标 → 屏幕标签投影、读数卡、
        底部控件、加载态与失败兜底，以及与父页面（光学交互实验室）的消息协议。
   三个场景各自内嵌一份本文件，互不依赖。

   与父页协议（postMessage，双向；离线 file:// 下 origin 为 null，故不做 origin 校验，
   只严格校验消息形状与数值范围）：
     父 → 子  {t:'s3d:init',  params:{...}}        进 3D 时同步一次当前参数
              {t:'s3d:param', name, value}         父页滑块变化
              {t:'s3d:active', on}                 父页切走 / 切回（暂停渲染省电）
              {t:'s3d:reset'}
     子 → 父  {t:'s3d:ready', key}                 场景就绪（也被"上下文已恢复"复用）
              {t:'s3d:state', key, params:{...}}   场景内控件变化（父页据此回写滑块）
              {t:'s3d:lost',  key}                 渲染上下文丢失（父页重置挂载，便于重新进入）
              {t:'s3d:error', key, msg}            初始化失败（父页可提示降级用 2D）
   ========================================================================== */
(function (global) {
  'use strict';
  var THREE = global.THREE;
  if (!THREE) { fail('三维库未加载'); return; }

  var OPT = null, KEY = '';
  var scene, camera, renderer, controls, clock;
  var running = false, raf = 0, t0 = 0;
  var labels = [], roRows = {}, toolBtns = {}, roEls = {};
  var params = {};
  /* V6.2.1：初始化/上下文状态。booted 用来判断"是否已有结论"，
     不再依赖 #boot 的 done 类（那个类会被 fail() 摘掉，从而让超时定时器误判补刀）。 */
  var booted = false, bootTimer = 0, _ctxLost = false;

  /* ---------------- 基础工具 ---------------- */
  function $(id) { return document.getElementById(id); }
  function px(v, a, b) { return Math.max(a, Math.min(b, v)); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function post(m) { try { (window.parent || window).postMessage(m, '*'); } catch (e) {} }

  /* V6.2.1：失败即"已有结论"，立刻取消 8 秒超时判定。
     旧版这里把 #boot 的 done 类摘掉，而超时定时器正是靠 done 类判断是否初始化成功，
     于是"先失败过一次"= "永远没成功"：8 秒后必然再报一次「初始化超时」，
     父页收到第二次 error 又把人踢回 2D —— 表现就是点 3D 反复被弹出去。 */
  function fail(msg) {
    booted = true;
    if (bootTimer) { clearTimeout(bootTimer); bootTimer = 0; }
    var b = $('boot');
    if (b) {
      b.classList.remove('done');
      b.innerHTML = '<div class="in"><p class="err">' + esc(msg) +
        '</p><p class="err" style="opacity:.7">可先切回 2D 视图继续做实验</p></div>';
    }
    post({ t: 's3d:error', key: KEY, msg: String(msg) });
  }
  /* 非致命提示：覆盖在加载层上显示，但不改变"已完成"状态、不通报错误 */
  function showNote(msg) {
    var b = $('boot');
    if (!b) return;
    b.innerHTML = '<div class="in"><p class="err">' + esc(msg) + '</p></div>';
    b.classList.remove('done');
  }
  function hideNote() {
    var b = $('boot');
    if (!b) return;
    b.innerHTML = '';
    b.classList.add('done');
    b.style.display = 'none';
  }

  /* ---------------- 材质 / 图元helper ---------------- */
  var MAT = {
    glass: function () {
      return new THREE.MeshPhongMaterial({
        color: 0xd2e9ff, transparent: true, opacity: 0.42, shininess: 180, emissive: 0x0d2436,
        specular: 0xffffff, side: THREE.DoubleSide, depthWrite: false
      });
    },
    board: function (c) {
      return new THREE.MeshLambertMaterial({ color: c === undefined ? 0xe6dfcc : c, side: THREE.DoubleSide });
    },
    metal: function (c) {
      return new THREE.MeshPhongMaterial({ color: c === undefined ? 0x9fb6d8 : c, shininess: 210, specular: 0xffffff });
    },
    matte: function (c) {
      return new THREE.MeshLambertMaterial({ color: c === undefined ? 0xdfe6f2 : c });
    },
    emissive: function (c, i) {
      return new THREE.MeshBasicMaterial({ color: c, transparent: true, opacity: i === undefined ? 1 : i });
    }
  };

  /* ---------------- 共享资源池（V6.2.1 性能修复）----------------
     旧实现每帧 new CylinderGeometry + new Material 重建整条光路：实测自动扫描时
     每秒新建 1400+ 个对象，其中【每秒 360 次是显存缓冲的创建/销毁】。弱 GPU
     （手机、教室一体机集显）上这种持续抖动是 WebGL 上下文丢失的头号诱因，
     而上下文一丢画面就静止不动 —— 也就是用户说的"用一段时间就卡死"。
     现在改成四件套，让每帧的显存分配降到 0：
       · 单位圆柱只建一次，光束用 scale 表达长度与粗细；
       · 材质按「类型 + 颜色」缓存，不再每帧新建；
       · 光束的 Group/Mesh 走对象池，clearGroup 时归还复用；
       · 折线（角度弧、虚线）按顶点数做几何体池，清空时归还而不是销毁。
     clearGroup 认识 s3dShared / s3dPool / s3dBeam 三种标记：不销毁，只归还。 */
  var _UP = new THREE.Vector3(0, 1, 0);
  var _tmpA = new THREE.Vector3(), _tmpB = new THREE.Vector3();
  var _share = { cyl: null, mat: {}, line: {} };
  var _beamPool = [];

  function unitCyl() {
    if (!_share.cyl) {
      _share.cyl = new THREE.CylinderGeometry(1, 1, 1, 10, 1, true);
      _share.cyl.userData.s3dShared = true;
      _share.cyl.computeBoundingSphere();
    }
    return _share.cyl;
  }
  /* 材质缓存：kind = core(光束实体) / glow(光束外发光) / line(角度弧) / dash(虚线) */
  function sharedMat(kind, color) {
    var k = kind + ':' + color;
    if (_share.mat[k]) return _share.mat[k];
    var m;
    if (kind === 'core') m = MAT.emissive(color);
    else if (kind === 'glow') m = new THREE.MeshBasicMaterial({
      color: color, transparent: true, opacity: 0.16, blending: THREE.AdditiveBlending, depthWrite: false });
    else if (kind === 'line') m = new THREE.LineBasicMaterial({ color: color });
    else m = new THREE.LineDashedMaterial({ color: color, dashSize: 0.085, gapSize: 0.055 });
    m.userData.s3dShared = true;
    _share.mat[k] = m;
    return m;
  }
  function makeBeamShell() {
    var m = new THREE.Mesh(unitCyl(), sharedMat('core', 0xffffff));
    var glow = new THREE.Mesh(unitCyl(), sharedMat('glow', 0xffffff));
    var wrap = new THREE.Group();
    wrap.add(m); wrap.add(glow);
    m.userData.s3dShared = true; glow.userData.s3dShared = true;
    wrap.userData.s3dBeam = { m: m, glow: glow };
    return wrap;
  }

  function beam(a, b, color, r) {
    r = r || 0.016;
    _tmpA.subVectors(b, a);
    var len = _tmpA.length();
    var wrap = _beamPool.length ? _beamPool.pop() : makeBeamShell();
    if (len < 1e-6) { wrap.visible = false; return wrap; }
    wrap.visible = true;
    var sh = wrap.userData.s3dBeam, m = sh.m, glow = sh.glow;
    m.material = sharedMat('core', color);
    glow.material = sharedMat('glow', color);
    _tmpB.copy(_tmpA).normalize();
    m.position.copy(a).addScaledVector(_tmpA, 0.5);
    m.quaternion.setFromUnitVectors(_UP, _tmpB);
    m.scale.set(r, len, r);
    glow.position.copy(m.position);
    glow.quaternion.copy(m.quaternion);
    glow.scale.set(r * 2.7, len, r * 2.7);
    return wrap;
  }

  /* 折线几何体池：按顶点数分组，clearGroup 归还、不销毁 */
  function pooledLine(n) {
    var k = 'L' + n, arr = _share.line[k] || (_share.line[k] = []);
    var g = arr.pop();
    if (!g) {
      g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(n * 3), 3));
      g.userData.s3dPool = k;
      g.userData.s3dShared = true;
    }
    return g;
  }
  function putLine(g) {
    var k = g && g.userData && g.userData.s3dPool;
    if (!k) { if (g && g.dispose) g.dispose(); return; }
    var arr = _share.line[k] || (_share.line[k] = []);
    if (arr.length < 32) arr.push(g); else if (g.dispose) g.dispose();
  }
  /* 一条折线：顶点数固定 → 零分配（替代 new BufferGeometry().setFromPoints(...)） */
  function polyLine(pts, color, dashed) {
    var n = pts.length, g = pooledLine(n), at = g.attributes.position;
    for (var i = 0; i < n; i++) at.setXYZ(i, pts[i].x, pts[i].y, pts[i].z);
    at.needsUpdate = true;
    g.setDrawRange(0, n);
    g.computeBoundingSphere();
    var l = new THREE.Line(g, sharedMat(dashed ? 'dash' : 'line', color));
    if (dashed) l.computeLineDistances();
    return l;
  }

  function dashLine(a, b, color) {
    return polyLine([a, b], color === undefined ? 0x8ea6d8 : color, true);
  }

  function grid(size, div, c1, c2) {
    return new THREE.GridHelper(size, div, c1, c2);
  }

  /* 清空一个分组：光束归还对象池；池化折线几何体归还几何体池；其余几何体 dispose；
     材质只释放本框架 new 且非共享的（避免误伤共享材质）。 */
  function clearGroup(g) {
    if (!g || !g.children) return;
    for (var i = g.children.length - 1; i >= 0; i--) {
      var c = g.children[i];
      if (c.userData && c.userData.s3dBeam) {
        g.remove(c);
        if (_beamPool.length < 96) _beamPool.push(c);
        continue;
      }
      try {
        c.traverse(function (o) {
          var geo = o.geometry, mat = o.material;
          if (geo) {
            if (geo.userData && geo.userData.s3dPool) putLine(geo);
            else if (geo.dispose && !(geo.userData && geo.userData.s3dShared)) geo.dispose();
          }
          if (mat && o.userData.s3dOwnMat && mat.dispose && !(mat.userData && mat.userData.s3dShared)) mat.dispose();
        });
      } catch (e) {}
      g.remove(c);
    }
  }

  /* ---------------- 场景搭建 ---------------- */
  function init(opt) {
    OPT = opt; KEY = opt.key || '';
    var cv = $('gl');
    try {
      renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: true, alpha: true });
    } catch (e) { fail('当前浏览器/设备不支持 WebGL，无法显示三维光路'); return; }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(window.innerWidth, window.innerHeight, false);
    if ('outputEncoding' in renderer) renderer.outputEncoding = THREE.sRGBEncoding;

    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(42, window.innerWidth / window.innerHeight, 0.05, 120);
    var c = opt.cam || {};
    camera.position.fromArray(c.pos || [2.8, 2.1, 3.4]);
    var target = new THREE.Vector3().fromArray(c.target || [0, 0.5, 0]);

    controls = new THREE.OrbitControls(camera, cv);
    controls.target.copy(target);
    controls.enableDamping = true;
    controls.dampingFactor = 0.075;
    controls.rotateSpeed = 0.85;
    controls.zoomSpeed = 0.9;
    controls.panSpeed = 0.7;
    controls.minDistance = c.minDist || 1.2;
    controls.maxDistance = c.maxDist || 16;
    controls.maxPolarAngle = c.maxPolar || Math.PI * 0.52;
    controls.autoRotateSpeed = 0.9;
    controls.update();

    scene.add(new THREE.AmbientLight(0xb9cdf0, 0.42));
    var d1 = new THREE.DirectionalLight(0xffffff, 0.58); d1.position.set(4, 7, 5); scene.add(d1);
    var d2 = new THREE.DirectionalLight(0x8fb0ff, 0.24); d2.position.set(-5, 3, -4); scene.add(d2);

    // 参数初值（必须在 buildFooter 之前，否则底部滑块的显示值会是 undefined）
    params = {};
    if (opt.params) for (var k in opt.params) params[k] = opt.params[k];

    // 标题 / 副标题 / 读数卡 / 底部控件
    if ($('chip')) $('chip').textContent = opt.chip || '光现象 · 3D 立体模型';
    if ($('ttl')) $('ttl').innerHTML = opt.title || '3D 立体模型';
    if ($('sub')) $('sub').innerHTML = opt.sub || '';
    cv.setAttribute('aria-label', opt.aria || (String(opt.title || '三维光路图').replace(/<[^>]*>/g, '')));

    buildRO(opt.readouts || []);
    buildTools(opt);
    buildFooter(opt.footer || []);

    if (global.document && document.getElementById('bootTxt') && opt.bootText) {
      $('bootTxt').textContent = opt.bootText;
    }

    clock = new THREE.Clock();
    window.addEventListener('resize', onResize);
    /* ★ V6.2.1：上下文丢失不再走"报错即死亡"那条路。
       旧实现只报错、没有任何恢复路径，而父页挂载是一次性的（srcdoc 只注入一次），
       于是上下文一丢，3D 就永久静止、再点 3D 也进不去 —— 用户感受就是"卡死"。
       现在两条路都留：能恢复就恢复；恢复不了则通报父页（父页会重置挂载，
       用户下次点 3D 就是一次全新的初始化）。 */
    cv.addEventListener('webglcontextlost', function (e) {
      e.preventDefault();
      running = false; _ctxLost = true;
      showNote('三维渲染中断（可能是系统显存不足），正在尝试恢复…');
      post({ t: 's3d:lost', key: KEY });
    });
    cv.addEventListener('webglcontextrestored', function () {
      _ctxLost = false;
      booted = true;
      if (bootTimer) { clearTimeout(bootTimer); bootTimer = 0; }
      /* three.js 的 WebGLRenderer 会在 contextrestored 时重建内部 GL 上下文，
         显存对象按需重传，这里只需把循环重新挂起来。 */
      try { renderer.info.autoReset = true; } catch (err) {}
      hideNote();
      updateLabels(); paint(); setActive(true);
      toast('三维场景已恢复', 2200);
      post({ t: 's3d:ready', key: KEY });
    });

    if (opt.build) {
      try { opt.build(API); } catch (e) { fail('三维场景构建失败：' + (e && e.message)); return; }
    }
    updateLabels();
    paint();

    bootDone();
    setActive(true);
    post({ t: 's3d:ready', key: KEY });
    if (opt.onParam) for (var k2 in params) { try { opt.onParam(k2, params[k2]); } catch (e) {} }
  }

  function bootDone() {
    booted = true;
    if (bootTimer) { clearTimeout(bootTimer); bootTimer = 0; }
    var b = $('boot');
    if (b) { b.classList.add('done'); setTimeout(function () { if (b.parentNode) b.style.display = 'none'; }, 600); }
  }

  function onResize() {
    if (!renderer) return;
    var w = window.innerWidth, h = window.innerHeight;
    camera.aspect = w / h; camera.updateProjectionMatrix();
    renderer.setSize(w, h, false);
    layoutLabels();
  }

  /* ---------------- 读数卡 ---------------- */
  function buildRO(list) {
    var box = $('ro'), body = $('roBody');
    if (!box || !body) return;
    if (!list.length) { box.hidden = true; return; }
    box.hidden = false;
    body.innerHTML = list.map(function (r) {
      roRows[r.k] = 1;
      return '<div class="row" id="ro-' + r.k + '"><span>' + esc(r.label) + '</span><b>—</b></div>';
    }).join('');
    if ($('roTitle') && OPT && OPT.roTitle) $('roTitle').textContent = OPT.roTitle;
  }
  /* V6.2.1：缓存 <b> 引用与上一次的值/样式，值没变就不碰 DOM。
     旧实现每帧对 6 行读数做一次 innerHTML 赋值（= 每帧 6 次 HTML 解析 + 样式重算），
     自动扫描时是纯粹的浪费。 */
  function setRO(k, val, cls) {
    var e = roEls[k];
    if (!e) {
      var el = $('ro-' + k);
      if (!el) return;
      e = roEls[k] = { row: el, b: el.querySelector('b'), v: null, c: null };
      if (!e.b) return;
    }
    var t = val == null ? '—' : String(val);
    if (e.v !== t) { e.b.textContent = t; e.v = t; }
    var c = cls || '';
    if (e.c !== c) { e.row.className = 'row' + (c ? ' ' + c : ''); e.c = c; }
  }
  function clearRO() { for (var k in roRows) setRO(k, '—', ''); }

  /* ---------------- 左侧工具按钮 ---------------- */
  var ICON = {
    reset: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v5h5"/></svg>',
    orbit: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><ellipse cx="12" cy="12" rx="9" ry="4.2"/><circle cx="12" cy="12" r="2.6"/></svg>',
    side: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M3 12h18"/><circle cx="7" cy="12" r="2"/><circle cx="13" cy="12" r="1.4"/><circle cx="18.5" cy="12" r="2.6"/></svg>'
  };
  function buildTools(opt) {
    var box = $('tools');
    if (!box) return;
    var defs = [
      { k: 'orbit', t: '自动环绕', on: false, fn: function (b) { controls.autoRotate = !controls.autoRotate; b.setAttribute('aria-pressed', controls.autoRotate ? 'true' : 'false'); } },
      { k: 'reset', t: '重置视角', fn: function () { API.view(opt.cam); if (controls.autoRotate) { controls.autoRotate = false; toolBtns.orbit.setAttribute('aria-pressed', 'false'); } } }
    ];
    if (opt.side) defs.splice(2, 0, { k: 'side', t: '正侧视', fn: function () { API.view(opt.side); } });
    box.innerHTML = defs.map(function (d) {
      return '<button type="button" id="tl-' + d.k + '" title="' + esc(d.t) + '" aria-label="' + esc(d.t) + '" aria-pressed="false">' + ICON[d.k] + '</button>';
    }).join('');
    defs.forEach(function (d) {
      var b = $('tl-' + d.k); toolBtns[d.k] = b;
      b.addEventListener('click', function () { try { d.fn(b); } catch (e) {} });
    });
  }

  /* ---------------- 底部控件 ---------------- */
  function buildFooter(list) {
    var box = $('ctlBody');
    if (!box) return;
    if (!list.length) { $('ctl').hidden = true; return; }
    $('ctl').hidden = false;
    box.innerHTML = list.map(function (f) {
      if (f.type === 'range') {
        return '<div class="f"><span>' + esc(f.label) + '</span>' +
          '<input type="range" id="fc-' + f.name + '" min="' + f.min + '" max="' + f.max + '" step="' + f.step +
          '" value="' + (params[f.name] === undefined ? f.value : params[f.name]) + '" aria-label="' + esc(f.label) + '">' +
          '<b id="fv-' + f.name + '">—</b></div>';
      }
      if (f.type === 'out') {
        return '<div class="f"><span>' + esc(f.label) + '</span><b id="fv-' + f.name + '">—</b></div>';
      }
      if (f.type === 'toggle') {
        return '<button type="button" class="tog" id="fc-' + f.name + '" aria-pressed="' + (f.value ? 'true' : 'false') + '">' + esc(f.label) + '</button>';
      }
      if (f.type === 'play') {
        return '<button type="button" class="play" id="fc-' + f.name + '">' + esc(f.label) + '</button>';
      }
      return '';
    }).join('');
    list.forEach(function (f) {
      var el = $('fc-' + f.name);
      if (!el) return;
      if (f.type === 'range') {
        el.addEventListener('input', function () {
          var v = parseFloat(el.value);
          params[f.name] = v;
          setVal(f.name, f.unit ? fmt(v, f.dp) + f.unit : String(v));
          fire(f.name, v);
        });
        setVal(f.name, f.unit ? fmt(params[f.name], f.dp) + f.unit : String(params[f.name]));
      } else if (f.type === 'out') {
        setVal(f.name, f.value === undefined ? '—' : f.value);
      } else if (f.type === 'toggle') {
        el.addEventListener('click', function () {
          var on = el.getAttribute('aria-pressed') !== 'true';
          el.setAttribute('aria-pressed', on ? 'true' : 'false');
          fire(f.name, on);
        });
      } else if (f.type === 'play') {
        el.addEventListener('click', function () { if (f.fn) f.fn(); });
      }
    });
  }
  function setVal(name, text) { var b = $('fv-' + name); if (b) b.textContent = text; }
  function fmt(v, dp) { return Number(v).toFixed(dp === undefined ? 1 : dp); }
  function setRange(name, v) {
    var el = $('fc-' + name);
    if (el && el.type === 'range') { el.value = v; }
    params[name] = v;
  }

  /* ---------------- 参数入口（父页与本地控件共用一条） ---------------- */
  function fire(name, v) {
    if (OPT && OPT.onParam) { try { OPT.onParam(name, v); } catch (e) { console.warn('[3D] onParam 失败:', name, e && e.message); } }
    post({ t: 's3d:state', key: KEY, params: snapshot() });
    paint();
  }
  function snapshot() { var o = {}; for (var k in params) o[k] = params[k]; return o; }

  /* ---------------- 标签投影 ---------------- */
  function label(text, v3, cls) {
    var box = $('labels'); if (!box) return null;
    var el = document.createElement('span');
    el.className = 'lb' + (cls ? ' ' + cls : '');
    el.innerHTML = text;
    box.appendChild(el);
    var item = { el: el, v: new THREE.Vector3().fromArray(v3), vis: true, _vis: null, _tf: '' };
    labels.push(item);
    return item;
  }
  function labelAt(item, v3) { if (item) item.v.fromArray(v3); }
  function labelVis(item, on) { if (item) item.vis = !!on; }
  function clearLabels() {
    var box = $('labels');
    if (box) box.innerHTML = '';
    labels = [];
  }
  /* V6.2.1：复用投影向量；值没变不写 style。
     旧实现每个标签每帧 clone 一个 Vector3、并且每帧无条件写 transform +
     display —— 每帧都要强制样式重算。 */
  var _lblP = new THREE.Vector3();
  function updateLabels() {
    if (!camera) return;
    var w = window.innerWidth, h = window.innerHeight;
    for (var i = 0; i < labels.length; i++) {
      var it = labels[i];
      var p = _lblP.copy(it.v).project(camera);
      var vis = it.vis !== false && p.z < 1 && Math.abs(p.x) < 1.35 && Math.abs(p.y) < 1.35;
      if (it._vis !== vis) { it.el.style.display = vis ? '' : 'none'; it._vis = vis; }
      if (!vis) continue;
      var tf = 'translate(-50%,-50%) translate(' + ((p.x * 0.5 + 0.5) * w).toFixed(1) + 'px,' +
               ((-p.y * 0.5 + 0.5) * h).toFixed(1) + 'px)';
      if (it._tf !== tf) { it.el.style.transform = tf; it._tf = tf; }
    }
  }
  function layoutLabels() { updateLabels(); }

  /* ---------------- 3D 内直接拖动对象 ----------------
     用 Raycaster 命中后，把指针投到水平面上取交点交给回调。
     命中时 stopPropagation，避免 OrbitControls 同时转视角。 */
  var _ray = new THREE.Raycaster(), _ndc = new THREE.Vector2(), _drag = null;
  var _dragPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0), _hitPt = new THREE.Vector3();
  var _dragList = [];
  function draggable(obj, o) {
    o = o || {};
    obj.userData.s3dDrag = { planeY: (o.planeY === undefined ? 0.2 : o.planeY), onDrag: o.onDrag, onStart: o.onStart, onEnd: o.onEnd, hint: o.hint };
    _dragList.push(obj);
    return obj;
  }
  function _ptFromEvent(e) {
    var cv = $('gl'); if (!cv || !camera) return null;
    var r = cv.getBoundingClientRect();
    _ndc.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    _ray.setFromCamera(_ndc, camera);
    return _ndc;
  }
  function _onDown(e) {
    if (_drag || !_dragList.length || !camera) return;
    _ptFromEvent(e);
    var hits = _ray.intersectObjects(_dragList, true);
    for (var i = 0; i < hits.length; i++) {
      var o = hits[i].object;
      while (o && !(o.userData && o.userData.s3dDrag)) o = o.parent;
      if (o) {
        _drag = { obj: o, cfg: o.userData.s3dDrag };
        if (controls) controls.enabled = false;
        if (_drag.cfg.onStart) { try { _drag.cfg.onStart(o); } catch (err) {} }
        if (_drag.cfg.hint) toast(_drag.cfg.hint, 2000);
        e.stopPropagation();
        return;
      }
    }
  }
  function _onMove(e) {
    if (!_drag) return;
    _ptFromEvent(e);
    _dragPlane.constant = -_drag.cfg.planeY;
    if (_ray.ray.intersectPlane(_dragPlane, _hitPt)) {
      try { _drag.cfg.onDrag && _drag.cfg.onDrag(_hitPt, _drag.obj); } catch (err) {}
    }
    e.stopPropagation();
  }
  function _onUp() {
    if (!_drag) return;
    var cfg = _drag.cfg;
    _drag = null;
    if (controls) controls.enabled = true;
    try { cfg.onEnd && cfg.onEnd(); } catch (e) {}
  }
  window.addEventListener('pointerdown', _onDown, true);
  window.addEventListener('pointermove', _onMove, true);
  window.addEventListener('pointerup', _onUp, true);

  /* ---------------- 循环 ---------------- */
  function setActive(on) {
    on = !!on;
    if (on === running) return;
    running = on;
    if (on) { clock.getDelta(); tick(); } else { cancelAnimationFrame(raf); raf = 0; }
  }
  function tick() {
    if (!running) return;
    raf = requestAnimationFrame(tick);
    var dt = Math.min(clock.getDelta(), 0.05), t = clock.elapsedTime;
    stepAnim(dt);
    if (controls) controls.update();
    if (OPT && OPT.onFrame) { try { OPT.onFrame(t, dt, API); } catch (e) {} }
    updateLabels();
    if (renderer && scene && camera) renderer.render(scene, camera);
  }
  function paint() { if (renderer && scene && camera) renderer.render(scene, camera); }

  /* ---------------- 视角 ---------------- */
  var anim = null;
  function view(cfg) {
    if (!cfg) return;
    var p = new THREE.Vector3().fromArray(cfg.pos || [2.8, 2.1, 3.4]);
    var q = new THREE.Vector3().fromArray(cfg.target || [0, 0.5, 0]);
    anim = { p0: camera.position.clone(), q0: controls.target.clone(), p1: p, q1: q, k: 0 };
  }
  function stepAnim(dt) {
    if (!anim) return;
    anim.k = Math.min(1, anim.k + dt * 1.6);
    var e = 1 - Math.pow(1 - anim.k, 3);
    camera.position.lerpVectors(anim.p0, anim.p1, e);
    controls.target.lerpVectors(anim.q0, anim.q1, e);
    if (anim.k >= 1) anim = null;
  }

  /* ---------------- 提示条 ---------------- */
  var toastTimer = 0;
  function toast(html, ms) {
    var el = $('toast'); if (!el) return;
    el.innerHTML = html;
    el.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { el.classList.remove('show'); }, ms || 3200);
  }

  /* ---------------- 父页消息 ---------------- */
  var ALLOWED = /^[a-zA-Z][a-zA-Z0-9_]{0,15}$/;
  window.addEventListener('message', function (e) {
    var m = e && e.data;
    if (!m || typeof m !== 'object' || typeof m.t !== 'string') return;
    if (m.t === 's3d:param') {
      if (typeof m.name !== 'string' || !ALLOWED.test(m.name)) return;
      if (typeof m.value !== 'number' || !isFinite(m.value)) return;
      params[m.name] = m.value;
      setRange(m.name, m.value);
      var f = (OPT && OPT.footer || []).filter(function (x) { return x.name === m.name; })[0];
      if (f && f.type === 'range') setVal(m.name, f.unit ? fmt(m.value, f.dp) + f.unit : String(m.value));
      if (OPT && OPT.onParam) { try { OPT.onParam(m.name, m.value); } catch (err) {} }
      paint();
    } else if (m.t === 's3d:init') {
      if (m.params && typeof m.params === 'object') {
        for (var k in m.params) {
          if (!ALLOWED.test(k)) continue;
          var v = m.params[k];
          if (typeof v !== 'number' || !isFinite(v)) continue;
          params[k] = v; setRange(k, v);
          var f2 = (OPT && OPT.footer || []).filter(function (x) { return x.name === k; })[0];
          if (f2 && f2.type === 'range') setVal(k, f2.unit ? fmt(v, f2.dp) + f2.unit : String(v));
          if (OPT && OPT.onParam) { try { OPT.onParam(k, v); } catch (err) {} }
        }
        paint();
      }
    } else if (m.t === 's3d:active') {
      setActive(m.on !== false);
    } else if (m.t === 's3d:reset') {
      API.view(OPT && OPT.cam);
      if (OPT && OPT.onReset) { try { OPT.onReset(); } catch (err) {} }
    }
  });

  /* ---------------- 对外 API ---------------- */
  var API = {
    THREE: THREE,
    key: KEY,
    init: init,
    get scene() { return scene; },
    get camera() { return camera; },
    get renderer() { return renderer; },
    get controls() { return controls; },
    get params() { return params; },
    MAT: MAT, beam: beam, dashLine: dashLine, polyLine: polyLine, grid: grid,
    clearGroup: clearGroup, draggable: draggable,
    add: function (o) { scene.add(o); return o; },
    label: label, labelAt: labelAt, labelVis: labelVis, clearLabels: clearLabels,
    setRO: setRO, clearRO: clearRO,
    setVal: setVal, fmt: fmt, px: px,
    params_get: function (k) { return params[k]; },
    setParam: function (k, v) { params[k] = v; setRange(k, v); },
    fire: fire,
    view: view,
    stepAnim: stepAnim,
    toast: toast,
    fail: fail,
    post: post,
    snapshot: snapshot
  };
  global.S3D = API;

  /* 兜底：8 秒仍未就绪 → 给出可读的失败提示（不静默白屏）。
     V6.2.1：判定改用独立布尔量 booted，只在"确实还没出结论"时才报。 */
  bootTimer = setTimeout(function () {
    bootTimer = 0;
    if (!booted) fail('三维场景初始化超时（8 秒），可先切回 2D 视图继续做实验');
  }, 8000);
})(window);

