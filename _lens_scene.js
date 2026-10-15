
/* ==========================================================================
   3D 场景② · 凸透镜成像
   --------------------------------------------------------------------------
   与 2D 的不同：这里能把「光锥」画出来 —— 从烛焰顶端发出的一束光经透镜后
   真正会聚到一点，光屏放在那一点上就出现清晰的倒立实像。转动视角能看出
   像"在空间里的某个位置"，而不是画在纸面上的两条线。
   物理：薄透镜公式 1/u + 1/v = 1/f（初中口径），放大率 m = v/u，实像倒立；
        |u − f| < 0.6 cm 视为不成像（出射光平行）。
   坐标：光轴 = X 轴，透镜在 x=0，物在 −u，光屏在 +v。
        轴向与横向用不同比例（KX=0.042、KY=0.13 单位/cm）—— 教材示意图的惯用
        夸张：仿射缩放保直线仍是直线、成像关系不变，但看起来清楚得多。
   ========================================================================== */
(function () {
  var S = window.S3D, T = S.THREE;
  var V = T.Vector3;
  var KX = 0.05, KY = 0.19;
  var OBJ_H = 7;                        // 物高（cm），与 2D 画布同口径（70px ÷ 10px/cm）
  var RAIL_L = -2.6, RAIL_R = 2.6;
  var LENS_R = 1.45;
  var AY = 1.45;                       // 光轴离台面（导轨）的高度：让整束光都走在台面之上

  var u = 42, f = 11, coneOn = true, specialOn = true;
  var lens, screenG, imgPlane, matReal, matVirt, coneG, rayG, objG;
  var lb = {};
  var playing = false, dir = -1;

  function sxf(cm) { return KX * cm; }
  function syf(cm) { return KY * cm; }
  function vOf(uu, ff) { return uu * ff / (uu - ff); }

  /* ---------- 零件：真正立体的【双凸】透镜 ----------
     剖面是一条绕光轴旋转的【闭合】曲线：后表面 → 镜缘（一圈薄边）→ 前表面。
     由「中心厚度 Tc / 镜缘厚度 Te」反解球面曲率半径 Rc，保证中间最厚、向镜缘
     平滑收薄 —— 这样侧看、斜看才有"凸"的轮廓，而不是一个圈。
     ⚠️ 旧版写法有两个错：① LatheGeometry 的 point.x 是【回转半径】，却给它塞了
        负半径（想表达"后表面"），负半径会把曲面折进轴里；② 半径最大只到 0.235，
        而镜箍半径是 1.45 —— 于是整个玻璃体缩成贴着光轴的一根细刺，画面上只剩
        镜箍那一个环，"凸透镜"看起来就是一个圆环。 */
  function makeLens(R) {
    var Tc = 0.70, Te = 0.12;                       // 中心厚度 / 镜缘厚度（场景单位）
    var Rc = (R * R + (Tc - Te) * (Tc - Te) / 4) / (Tc - Te);   // 由 Tc、Te 反解曲率半径
    function surf(r) {                              // 单侧表面沿光轴的偏移
      var d = Math.max(0, Rc * Rc - r * r);
      return Tc / 2 - Rc + Math.sqrt(d);            // r=0 → Tc/2；r=R → Te/2
    }
    var N = 36, k, r, pts = [];
    for (k = 0; k <= N; k++) { r = R * (k / N); pts.push(new T.Vector2(r, -surf(r))); }  // 后表面
    for (k = N; k >= 0; k--) { r = R * (k / N); pts.push(new T.Vector2(r, surf(r))); }   // 前表面

    var g = new T.Group();
    var body = new T.Mesh(new T.LatheGeometry(pts, 56), new T.MeshPhongMaterial({
      color: 0xc7e6ff, transparent: true, opacity: 0.38, shininess: 240,
      specular: 0xffffff, emissive: 0x11324c, side: T.DoubleSide, depthWrite: false
    }));
    body.rotation.z = -Math.PI / 2;                 // 回转轴 → 世界 X（光轴）
    g.add(body);

    /* 镜箍：一圈细金属环箍住镜缘，顺势把"边缘薄"衬托出来 */
    var rim = new T.Mesh(new T.TorusGeometry(R, Te / 2 + 0.008, 10, 56), S.MAT.metal(0x9fc0e8));
    rim.rotation.y = Math.PI / 2;
    g.add(rim);
    return g;
  }

  function makeCandle(h) {
    var g = new T.Group(), hb = h * 0.72, hf = h * 0.28;
    var body = new T.Mesh(new T.CylinderGeometry(h * 0.12, h * 0.13, hb, 18), S.MAT.matte(0xf2e4c8));
    body.position.y = hb / 2; g.add(body);
    var flame = new T.Mesh(new T.ConeGeometry(h * 0.075, hf, 16), S.MAT.emissive(0xffb347));
    flame.position.y = hb + hf / 2; g.add(flame);
    var core = new T.Mesh(new T.ConeGeometry(h * 0.032, hf * 0.5, 12), S.MAT.emissive(0xfff0c0));
    core.position.y = hb + hf * 0.32; g.add(core);
    var glow = new T.Mesh(new T.SphereGeometry(h * 0.26, 16, 12),
      new T.MeshBasicMaterial({ color: 0xffc46b, transparent: true, opacity: 0.14, blending: T.AdditiveBlending, depthWrite: false }));
    glow.position.y = hb + hf * 0.45; g.add(glow);
    return g;
  }

  /* 光屏上那张"像"：把蜡烛画进画布纹理，倒立版把画布上下镜像 */
  function candleTexture(flip) {
    var c = document.createElement('canvas');
    c.width = 120; c.height = 240;
    var x = c.getContext('2d');
    x.save();
    if (flip) { x.translate(0, 240); x.scale(1, -1); }
    x.fillStyle = '#ffe9c0'; x.fillRect(42, 70, 36, 160);
    x.fillStyle = '#ffb347';
    x.beginPath(); x.moveTo(60, 18); x.quadraticCurveTo(81, 56, 60, 72); x.quadraticCurveTo(39, 56, 60, 18); x.fill();
    x.fillStyle = '#fff3cf';
    x.beginPath(); x.moveTo(60, 34); x.quadraticCurveTo(71, 56, 60, 68); x.quadraticCurveTo(49, 56, 60, 34); x.fill();
    x.restore();
    var t = new T.CanvasTexture(c);
    if ('encoding' in t) t.encoding = T.sRGBEncoding;
    return t;
  }

  /* ---------- 构建 ---------- */
  function build() {
    u = S.params.u === undefined ? 42 : S.params.u;
    f = S.params.f === undefined ? 11 : S.params.f;

    /* 导轨 + 刻度 */
    var rail = new T.Mesh(new T.BoxGeometry(RAIL_R - RAIL_L, 0.05, 0.3), S.MAT.metal(0x2c405f));
    rail.position.set((RAIL_L + RAIL_R) / 2, -0.025, 0);
    S.add(rail);
    for (var cm = -52; cm <= 52; cm += 5) {
      var x0 = sxf(cm);
      if (x0 < RAIL_L || x0 > RAIL_R) continue;
      var lng = (cm % 10 === 0);
      var tk = new T.Mesh(new T.BoxGeometry(0.014, 0.012, lng ? 0.34 : 0.18),
        S.MAT.emissive(lng ? 0x6f8cb8 : 0x3d5678));
      tk.position.set(x0, 0.006, 0.14);
      S.add(tk);
    }
    /* 主光轴（虚线） */
    var ax = S.dashLine(new V(RAIL_L + 0.05, AY, 0), new V(RAIL_R - 0.05, AY, 0), 0x5f87c8);
    ax.material.transparent = true; ax.material.opacity = 0.75;
    S.add(ax);
    lb.axis = S.label('主光轴', [RAIL_L + 0.42, AY + 0.16, 0], 'k-p');

    lb.F = S.label('F', [0, 0, 0], 'k-n');
    lb.F2 = S.label('2F', [0, 0, 0], 'k-p');
    lb.Fp = S.label("F′", [0, 0, 0], 'k-n');
    lb.F2p = S.label("2F′", [0, 0, 0], 'k-p');

    /* 透镜 */
    lens = makeLens(LENS_R);
    lens.position.set(0, AY, 0);
    S.add(lens);
    S.label('凸透镜', [0, AY + LENS_R + 0.26, 0], 'k-n');

    /* 物体 */
    objG = makeCandle(syf(OBJ_H));
    S.add(objG);
    lb.obj = S.label('烛焰（物）', [0, 0, 0], 'k-p');

    /* 光屏（含边框与支架），中心在光轴上 */
    screenG = new T.Group();
    var sc = new T.Mesh(new T.PlaneGeometry(1.7, 3.0), S.MAT.matte(0xc4ccdb));
    sc.rotation.y = -Math.PI / 2;
    screenG.add(sc);
    [-0.88, 0.88].forEach(function (z) {
      var fr = new T.Mesh(new T.BoxGeometry(0.03, 3.06, 0.05), S.MAT.metal(0x7c8ba5));
      fr.position.set(0, 0, z); screenG.add(fr);
    });
    var post = new T.Mesh(new T.BoxGeometry(0.07, AY, 0.07), S.MAT.metal(0x5d6b84));
    /* 注意：这支立柱刻意挂在 objG（烛台）上而不是 screenG —— 光屏本身就高到台面，
       立在屏里的柱子会被屏面挡住；挂在物上正好当烛台，物体移动时支架跟着走。 */
    post.position.set(0, -AY / 2, 0); objG.add(post);
    S.add(screenG);
    lb.scr = S.label('光屏', [0, 0, 0], 'k-n');

    /* 屏上的像（倒立）与虚像（正立）两套材质 */
    matReal = new T.MeshBasicMaterial({ map: candleTexture(true), transparent: true, depthWrite: false, side: T.DoubleSide });
    matVirt = new T.MeshBasicMaterial({ map: candleTexture(false), transparent: true, opacity: 0.55, depthWrite: false, side: T.DoubleSide });
    imgPlane = new T.Mesh(new T.PlaneGeometry(1, 1), matReal);
    imgPlane.rotation.y = -Math.PI / 2;
    S.add(imgPlane);
    lb.img = S.label('实像', [0, 0, 0], 'k-e');

    coneG = new T.Group(); rayG = new T.Group();
    coneG.position.y = AY; rayG.position.y = AY;
    S.add(coneG); S.add(rayG);

    apply('u', u);
    apply('f', f);
  }

  /* ---------- 光路重绘 ---------- */
  function redraw() {
    var noImg = Math.abs(u - f) < 0.6;
    var v = noImg ? NaN : vOf(u, f);
    var m = noImg ? NaN : v / u;
    var real = !noImg && v > 0;
    var virt = !noImg && v < 0;
    var vCap = RAIL_R / KX;                       // 导轨末端对应的像距（cm）
    var over = real && v > vCap;
    var vShow = real ? Math.min(v, vCap) : v;

    var xObj = sxf(-u), yTip = syf(OBJ_H);
    objG.position.set(xObj, AY, 0);
    S.labelAt(lb.obj, [xObj, AY + yTip + 0.3, 0]);

    /* 焦点标注：只画落在导轨范围内的 */
    var fits = function (cm) { var x = sxf(cm); return x > RAIL_L + 0.05 && x < RAIL_R - 0.05; };
    S.labelAt(lb.F, [sxf(-f), AY + 0.08, 0.17]); S.labelVis(lb.F, fits(-f));
    S.labelAt(lb.F2, [sxf(-2 * f), AY + 0.08, 0.17]); S.labelVis(lb.F2, fits(-2 * f));
    S.labelAt(lb.Fp, [sxf(f), AY + 0.08, 0.17]); S.labelVis(lb.Fp, fits(f));
    S.labelAt(lb.F2p, [sxf(2 * f), AY + 0.08, 0.17]); S.labelVis(lb.F2p, fits(2 * f));

    /* 光屏 */
    var xScr = real ? sxf(vShow) : RAIL_R;
    screenG.visible = real;
    screenG.position.set(xScr, AY, 0);
    S.labelVis(lb.scr, real);
    S.labelAt(lb.scr, [xScr + 0.12, AY + 1.62, 0]);

    /* 像（实像贴在屏上；虚像画在物侧，正立） */
    var hImg = noImg ? 0 : -syf(OBJ_H) * m;       // 实像为负（倒立）；虚像为正（正立）
    var ih = Math.max(0.08, Math.abs(hImg));
    imgPlane.visible = !noImg && (real ? !over : true);
    if (imgPlane.visible) {
      imgPlane.scale.set(1, ih, 1);
      if (real) {
        imgPlane.material = matReal;
        imgPlane.position.set(xScr - 0.04, AY - ih / 2, 0);
        S.labelVis(lb.img, true); S.labelAt(lb.img, [xScr + 0.12, AY - ih - 0.14, 0]);
      } else {
        imgPlane.material = matVirt;
        imgPlane.position.set(sxf(v) + 0.03, AY + ih / 2, 0);
        S.labelVis(lb.img, true); S.labelAt(lb.img, [sxf(v) + 0.12, AY + ih + 0.16, 0]);
      }
    } else S.labelVis(lb.img, false);
    if (lb.img.el) lb.img.el.className = 'lb ' + (real ? 'k-e' : 'k-n');

    /* 像点（光锥与三条光线都交于此） */
    var pImgX = real ? sxf(vShow) : sxf(v);
    var pImgY = real ? -ih : ih;

    /* ---- 立体光锥 ---- */
    S.clearGroup(coneG);
    if (coneOn && !noImg) {
      /* 关键：取样点要铺满透镜【整个圆面】（y 与 z 都取），否则画出来只是
         同一个竖直平面里的一个扇面，看着不像光锥。 */
      var RINGS = [[0.42, 8], [0.72, 12], [0.97, 16]];
      var tip = new V(xObj, yTip, 0), a, b, d, len, yl, zl, ang, rt, k, sp;
      for (k = 0; k < RINGS.length; k++) {
        rt = LENS_R * RINGS[k][0];
        sp = RINGS[k][1];
        for (var j = 0; j < sp; j++) {
          ang = (j / sp) * Math.PI * 2 + k * 0.22;
          yl = rt * Math.cos(ang); zl = rt * Math.sin(ang);
          a = tip; b = new V(0, yl, zl);
          coneG.add(S.beam(a, b, 0xff7043, 0.0055));
          d = new V(pImgX - 0, pImgY - yl, 0 - zl).normalize();
          if (d.x < 0) d.multiplyScalar(-1);        // 出射光一律朝 +x（虚像靠反向延长线成像）
          len = real ? Math.abs(pImgX) : RAIL_R;
          coneG.add(S.beam(b, new V(0, yl, zl).addScaledVector(d, len), 0xffd54f, 0.0055));
        }
      }
      /* 轴上那条 */
      coneG.add(S.beam(tip, new V(0, 0, 0), 0xff7043, 0.006));
      coneG.add(S.beam(new V(0, 0, 0), new V(real ? pImgX : RAIL_R, 0, 0), 0xffd54f, 0.006));
    }

    /* ---- 三条特殊光线 ---- */
    S.clearGroup(rayG);
    if (specialOn && !noImg) {
      var xFp = sxf(f);
      /* ① 平行主光轴 → 过 F′ */
      rayG.add(S.beam(new V(xObj, yTip, 0), new V(0, yTip, 0), 0xff5252, 0.013));
      if (real) rayG.add(S.beam(new V(0, yTip, 0), new V(xScr, yTip * (1 - vShow / f), 0), 0xff5252, 0.013));
      else {
        rayG.add(S.beam(new V(0, yTip, 0), new V(RAIL_R, yTip * (1 - RAIL_R / xFp), 0), 0xff5252, 0.013));
        rayG.add(S.dashLine(new V(0, yTip, 0), new V(pImgX, pImgY, 0), 0xff9e9e));
      }
      /* ② 过光心，方向不变 */
      rayG.add(S.beam(new V(xObj, yTip, 0), new V(0, 0, 0), 0x4fc3f7, 0.013));
      var dc = new V(-xObj, -yTip, 0).normalize();
      var ex = real ? xScr : RAIL_R;
      rayG.add(S.beam(new V(0, 0, 0), new V(ex, dc.y * (ex / dc.x), 0), 0x4fc3f7, 0.013));
      if (virt) rayG.add(S.dashLine(new V(0, 0, 0), new V(pImgX, pImgY, 0), 0x9fd8ff));
      /* ③ 过焦点 F → 出射平行主光轴 */
      var y3 = yTip * f / (f - u);
      rayG.add(S.beam(new V(xObj, yTip, 0), new V(0, y3, 0), 0x66bb6a, 0.013));
      rayG.add(S.beam(new V(0, y3, 0), new V(real ? xScr : RAIL_R, y3, 0), 0x66bb6a, 0.013));
    }

    /* ---------- 读数 ---------- */
    S.setRO('u', u.toFixed(1) + ' cm');
    S.setRO('f', f.toFixed(0) + ' cm');
    S.setRO('v', noImg ? '∞' : (v > 0 ? v.toFixed(1) + ' cm' : Math.abs(v).toFixed(1) + ' cm（虚像侧）'), noImg ? 'no' : '');
    S.setRO('m', noImg ? '—' : Math.abs(m).toFixed(2) + ' 倍');
    var nat = noImg ? '不成像（出射光平行）'
      : (v > 0 ? (Math.abs(Math.abs(m) - 1) < 0.05 ? '倒立 · 等大 · 实像'
        : (Math.abs(m) > 1 ? '倒立 · 放大 · 实像' : '倒立 · 缩小 · 实像')) : '正立 · 放大 · 虚像');
    S.setRO('nat', nat, noImg ? 'no' : (v > 0 ? 'ok' : 'hi'));
    S.setRO('scr', noImg ? '接不到像' : (v > 0 ? (over ? '像距超出导轨末端' : '屏上有清晰的像') : '光屏接不到虚像'),
      (noImg || v < 0 || over) ? 'no' : 'ok');
    S.setRO('use', noImg ? '—' : (u > 2 * f + 0.6 ? '照相机' : (Math.abs(u - 2 * f) < 0.6 ? '—（u = 2f，等大）' : (u > f ? '投影仪' : '放大镜'))));
  }

  function apply(name, v) {
    if (name === 'u') u = S.px(v, 4, 42);
    else if (name === 'f') f = S.px(Math.round(v), 4, 20);
    else if (name === 'cone') coneOn = !!v;
    else if (name === 'special') specialOn = !!v;
    redraw();
  }

  function onReset() {
    playing = false; dir = -1;
    S.setParam('u', 42); S.setParam('f', 11);
    u = 42; f = 11;
    redraw();
  }

  /* 物距扫描时同样把 u 回推父页：2D 视图与数据记录要跟得上（限流 10 Hz）。
     停表时补推一次，父页不会停在中途的旧值上。 */
  var _postAcc = 0;
  function syncParentNow() { _postAcc = 0; S.post({ t: 's3d:state', key: 'lens', params: S.snapshot() }); }
  function syncParent(dt) { _postAcc += dt; if (_postAcc < 0.1) return; syncParentNow(); }

  function frame(t, dt) {
    if (!playing) return;
    u += dt * dir * 9;
    if (u <= 4.5) { u = 4.5; dir = 1; }
    if (u >= 42) { u = 42; dir = -1; }
    S.setParam('u', +u.toFixed(1));
    syncParent(dt);
    redraw();
  }

  function togglePlay() {
    playing = !playing;
    dir = (u >= 41.5) ? -1 : 1;
    if (!playing) syncParentNow();
    S.toast(playing ? '物距自动扫描中：留意 <b>u = 2f</b>（等大）与 <b>u = f</b>（不成像）两处突变'
      : '已暂停扫描', 2800);
  }

  S.init({
    key: 'lens',
    chip: '光的折射透镜 · 3.1 凸透镜成像的规律',
    title: '凸透镜成像 · <em>立体光锥</em>',
    sub: '从烛焰顶端发出的光经凸透镜后会聚到一点，光屏放到那个位置就出现<b>倒立的实像</b>。' +
         '转动视角看整束光锥怎样穿过这枚<b>立体的双凸透镜</b>。',
    aria: '三维凸透镜成像：蜡烛、凸透镜、光屏与立体光锥',
    bootText: '正在搭建光具座与透镜',
    roTitle: '实时读数',
    cam: { pos: [4.0, 3.6, 5.6], target: [0.3, 1.6, 0], minDist: 1.8, maxDist: 22, maxPolar: Math.PI * 0.6 },
    side: { pos: [0.3, 1.55, 7.6], target: [0.3, 1.5, 0] },
    params: { u: 42, f: 11, cone: true, special: true },
    readouts: [
      { k: 'u', label: '物距 u' },
      { k: 'f', label: '焦距 f' },
      { k: 'v', label: '像距 v' },
      { k: 'm', label: '放大率 m' },
      { k: 'nat', label: '像的性质' },
      { k: 'scr', label: '光屏' },
      { k: 'use', label: '应用' }
    ],
    footer: [
      /* V6.3.0：父页的 2D 控件在 3D 模式下是隐藏的，因此 3D 底栏必须自带
         u 与 f —— 否则在 3D 里连焦距都改不了，「成像规律」这条主线做不下去。 */
      { type: 'range', name: 'u', label: '物距 u', min: 4, max: 42, step: 0.5, unit: ' cm', dp: 1 },
      { type: 'range', name: 'f', label: '焦距 f', min: 4, max: 20, step: 1, unit: ' cm', dp: 0 },
      { type: 'toggle', name: 'cone', label: '立体光锥', value: true },
      { type: 'toggle', name: 'special', label: '三条特殊光线', value: true },
      { type: 'play', name: 'play', label: '▶ 物距扫描', fn: togglePlay }
    ],
    build: build,
    onParam: apply,
    onReset: onReset,
    onFrame: frame
  });
})();

