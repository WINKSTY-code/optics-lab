/* ==========================================================================
   3D 场景① · 光的反射 —— 苏科版「可折转纸板」实验
   --------------------------------------------------------------------------
   装置：平面镜平放（y=0），两块白色硬纸板 E、F 竖直立在镜面上。
         E 板固定，F 板可绕法线 ON 折转（铰链就在 ON 上）。
   光路：激光沿 E 板射向镜面上的 O 点，反射光线射向 F 板方向。
   关键：折转 F 板后，F 板上再也接不到反射光线 —— 说明反射光线、入射光线
         和法线在同一平面内（该平面始终是 E 板所在的平面）。
   坐标：镜面 = XZ 平面，法线 ON = +Y，入射面 = XY 平面。
   ========================================================================== */
(function () {
  var S = window.S3D, T = S.THREE, DEG = Math.PI / 180;
  var V = T.Vector3;

  var BW = 2.2, BH = 2.0, RAY_LEN = 1.95;    // 纸板半宽 / 纸板高 / 光线长度
  var gE, gF, fPivot, boardF, rayIn, rayOut, spot, spotO, hint, arcB, laser, ghost;
  var lbF, lbB, lbSpot, lbHint;
  var iDeg = 40, betaDeg = 0;
  var demo = { on: false, k: 0, dir: 1 };

  function build() {
    iDeg = S.params.i; betaDeg = S.params.beta;

    /* ---------- 平面镜（暗镜面 + 冷色网格，别做成"白地板"） ---------- */
    var MW = BW * 2 + 0.2, MD = BW * 1.15;
    var mir = new T.Mesh(new T.BoxGeometry(MW, 0.07, MD), S.MAT.metal(0x2c405f));
    mir.position.y = -0.035;
    S.add(mir);
    var face = new T.Mesh(new T.PlaneGeometry(MW, MD),
      new T.MeshPhongMaterial({ color: 0x16243c, shininess: 250, specular: 0xffffff }));
    face.rotation.x = -Math.PI / 2; face.position.y = 0.002;
    S.add(face);
    var gr = S.grid(MW, 18, 0x4a72a8, 0x2b4368);
    gr.position.y = 0.004;
    S.add(gr);
    S.label('平面镜', [-BW + 0.3, 0.1, MD * 0.42], 'k-p');

    /* ---------- 纸板 E（固定，与入射面共面） ---------- */
    gE = new T.Group();
    var e = new T.Mesh(new T.PlaneGeometry(BW, BH), S.MAT.board(0xcbc4b0));
    e.position.set(-BW / 2, BH / 2, 0);
    gE.add(e);
    gE.add(new T.LineSegments(new T.EdgesGeometry(new T.PlaneGeometry(BW, BH)),
      new T.LineBasicMaterial({ color: 0x8d97ab })).translateX(-BW / 2).translateY(BH / 2));
    S.add(gE);

    /* ---------- 纸板 F（可绕 ON 折转） ---------- */
    fPivot = new T.Group();
    boardF = new T.Group();
    var f = new T.Mesh(new T.PlaneGeometry(BW, BH), S.MAT.board(0xd8d2c0));
    f.position.set(BW / 2, BH / 2, 0);
    boardF.add(f);
    boardF.add(new T.LineSegments(new T.EdgesGeometry(new T.PlaneGeometry(BW, BH)),
      new T.LineBasicMaterial({ color: 0x8d97ab })).translateX(BW / 2).translateY(BH / 2));
    fPivot.add(boardF);
    S.add(fPivot);

    /* ---------- F 板原位虚线框（折转后仍在原处，说明"光还在这儿"） ---------- */
    ghost = new T.LineSegments(new T.EdgesGeometry(new T.PlaneGeometry(BW, BH)),
      new T.LineDashedMaterial({ color: 0x5f7ba8, dashSize: 0.09, gapSize: 0.07 }))
      .translateX(BW / 2).translateY(BH / 2);
    if (ghost.computeLineDistances) ghost.computeLineDistances();
    ghost.geometry.computeBoundingSphere && ghost.geometry.computeBoundingSphere();
    ghost.visible = false;
    S.add(ghost);

    /* ---------- 法线 ON ---------- */
    S.add(S.dashLine(new V(0, 0, 0), new V(0, BH + 0.45, 0), 0x8ea6d8));
    S.label('<span>O</span> 入射点', [0.0, -0.16, 0.16], 'k-p');
    S.label('<span>N</span> 法线', [0, BH + 0.66, 0], 'k-n');

    /* ---------- 入射/反射光线 ---------- */
    rayIn = new T.Group(); rayOut = new T.Group();
    S.add(rayIn); S.add(rayOut);

    /* 激光笔 */
    laser = new T.Group();
    var body = new T.Mesh(new T.CylinderGeometry(0.062, 0.062, 0.3, 14), S.MAT.metal(0x39445c));
    laser.add(body);
    laser.add(new T.Mesh(new T.CylinderGeometry(0.03, 0.03, 0.05, 12),
      S.MAT.emissive(0xff5a46)).translateY(0.17));
    S.add(laser);

    /* ---------- F 板上的光斑（始终朝向相机的小光点） ---------- */
    spot = new T.Mesh(new T.CircleGeometry(0.085, 22),
      new T.MeshBasicMaterial({ color: 0xffe6a0, transparent: true, opacity: 0.95, blending: T.AdditiveBlending, depthWrite: false }));
    S.add(spot);
    var halo = new T.Mesh(new T.CircleGeometry(0.2, 22),
      new T.MeshBasicMaterial({ color: 0xffb347, transparent: true, opacity: 0.22, blending: T.AdditiveBlending, depthWrite: false }));
    spot.add(halo);
    /* 入射点 O 上的亮点 */
    spotO = new T.Mesh(new T.CircleGeometry(0.075, 20),
      new T.MeshBasicMaterial({ color: 0xffd0b0, transparent: true, opacity: 0.9, blending: T.AdditiveBlending, depthWrite: false }));
    spotO.position.set(0, 0.01, 0);
    S.add(spotO);

    /* ---------- 「入射光线与法线决定的平面」提示面 ---------- */
    var hg = new T.PlaneGeometry(BW * 2, BH);
    hint = new T.Group();
    hint.add(new T.Mesh(hg, new T.MeshBasicMaterial({
      color: 0x4fc3f7, transparent: true, opacity: 0.10, side: T.DoubleSide, depthWrite: false
    })).translateY(BH / 2).translateZ(-0.006));
    hint.add(new T.LineSegments(new T.EdgesGeometry(hg),
      new T.LineBasicMaterial({ color: 0x4fc3f7, transparent: true, opacity: 0.55 }))
      .translateY(BH / 2).translateZ(-0.006));
    hint.visible = false;
    S.add(hint);
    lbHint = S.label('入射光线与法线决定的平面', [BW * 1.1, BH * 0.55, 0], 'k-n');

    /* ---------- 角度弧 ---------- */
    arcB = new T.Group(); S.add(arcB);
    S.label('入射光线', [-1.5, 1.62, 0], 'k-p');
    S.label('反射光线', [1.05, 1.72, 0], 'k-p');
    lbF = S.label('纸板 F', [BW * 0.72, BH + 0.24, 0], 'k-n');
    lbB = S.label('β', [0.55, 0.2, 0], 'k-on');
    lbSpot = S.label('光斑', [1.0, 1.0, 0.1], 'k-on');

    apply('i', iDeg);
    apply('beta', betaDeg);
  }

  function onReset() {
    demo.on = false;
    betaDeg = 0; fPivot.rotation.y = 0;
    S.setParam('beta', 0); S.setVal('beta', '0°');
    rebuildBetaArc(); redraw();
  }

  /* ---------- 参数应用（父页滑块与本地控件共用这一条入口） ---------- */
  function apply(name, v) {
    if (name === 'i') {
      iDeg = S.px(v, 0, 88);
    } else if (name === 'beta') {
      betaDeg = S.px(v, 0, 90);
      fPivot.rotation.y = betaDeg * DEG;
      rebuildBetaArc();
    }
    redraw();
  }

  function rebuildBetaArc() {
    S.clearGroup(arcB);
    if (betaDeg > 1) {
      var r = 0.42, pts = [];
      for (var k = 0; k <= 24; k++) {
        var a = betaDeg * DEG * (k / 24);
        pts.push(new V(r * Math.cos(a), 0.14, -r * Math.sin(a)));
      }
      arcB.add(new T.Line(new T.BufferGeometry().setFromPoints(pts), new T.LineBasicMaterial({ color: 0x4fc3f7 })));
    }
  }

  /* ---------- 重画光路（每次参数变化 / 自动演示每帧） ---------- */
  function redraw() {
    var a = iDeg * DEG;
    var A = new V(-RAY_LEN * Math.sin(a), RAY_LEN * Math.cos(a), 0);
    var O = new V(0, 0, 0);
    var B = new V(RAY_LEN * Math.sin(a), RAY_LEN * Math.cos(a), 0);

    S.clearGroup(rayIn); rayIn.add(S.beam(A, O, 0xff7043, 0.015));
    S.clearGroup(rayOut); rayOut.add(S.beam(O, B, 0xffd54f, 0.015));

    /* 激光笔：贴在入射光线起点外侧，指向 O */
    laser.position.copy(A).addScaledVector(new V(Math.sin(a), -Math.cos(a), 0), -0.17);
    laser.quaternion.setFromUnitVectors(new V(0, 1, 0), new V(Math.sin(a), -Math.cos(a), 0));

    /* 入射角 / 反射角小弧（仅正侧视时看得最清楚，保留作教学标注） */
    var ri = 0.34;
    var pi = [], pr = [];
    for (var k = 0; k <= 18; k++) {
      var t = a * (k / 18);
      pi.push(new V(-ri * Math.sin(t), ri * Math.cos(t), 0));
      pr.push(new V(ri * Math.sin(t), ri * Math.cos(t), 0));
    }
    rayIn.add(new T.Line(new T.BufferGeometry().setFromPoints(pi), new T.LineBasicMaterial({ color: 0xff8a70 })));
    rayOut.add(new T.Line(new T.BufferGeometry().setFromPoints(pr), new T.LineBasicMaterial({ color: 0xffd76b })));

    /* 光斑：β 很小时才落在 F 板上（F 板一旦折转，反射光线就不再与它相交） */
    var onBoard = betaDeg < 2.5 && B.x <= BW + 0.02 && B.y <= BH + 0.02;
    spot.visible = onBoard;
    spot.position.copy(B);
    S.labelVis(lbSpot, onBoard);
    S.labelAt(lbSpot, [B.x + 0.12, B.y + 0.16, B.z]);

    hint.visible = betaDeg > 2.5;
    S.labelVis(lbHint, betaDeg > 2.5);
    ghost.visible = betaDeg > 5;
    S.labelVis(lbB, betaDeg > 1);

    /* ---------- 读数 ---------- */
    S.setRO('i', iDeg.toFixed(0) + '°');
    S.setRO('r', iDeg.toFixed(0) + '°');
    S.setRO('beta', betaDeg.toFixed(0) + '°');
    S.setRO('hit', onBoard ? '有光斑' : '看不到光斑', onBoard ? 'ok' : 'no');
    S.setRO('cop', '成立（同一平面内）', 'ok');
    if (S.params.beta !== undefined) S.params.beta = betaDeg;
    if (S.params.i !== undefined) S.params.i = iDeg;
  }

  /* ---------- 自动演示：折转 F 板看光斑消失 ---------- */
  function toggleDemo() {
    demo.on = !demo.on;
    if (demo.on) { S.setParam('beta', 0); betaDeg = 0; fPivot.rotation.y = 0; S.setVal('beta', '0°'); S.toast('F 板与 E 板在<b>同一平面</b>内：F 板上能看到反射光线', 2600); }
    else { S.toast('已停止演示，可手动拖动 β 滑块', 1800); }
    redraw();
  }

  function frame(t, dt) {
    if (demo.on) {
      demo.k += dt * demo.dir * 26;
      if (demo.k >= 62) { demo.k = 62; demo.dir = -1; S.toast('把 F 板<b>折转</b>后，F 板上再也接不到反射光线 —— 说明反射光线、入射光线与法线在<b>同一平面</b>内', 3800); }
      if (demo.k <= 0) { demo.k = 0; demo.dir = 1; S.toast('F 板转回原平面：反射光线又出现在 F 板上', 2600); }
      betaDeg = demo.k;
      S.setParam('beta', betaDeg);
      S.setVal('beta', betaDeg.toFixed(0) + '°');
      fPivot.rotation.y = betaDeg * DEG;
      rebuildBetaArc();
      redraw();
    }
    /* 光斑始终朝向相机 */
    if (spot.visible && S.camera) spot.quaternion.copy(S.camera.quaternion);
    if (S.camera) spotO.quaternion.copy(S.camera.quaternion);
    /* F 板标签跟随折转 */
    if (lbF) S.labelAt(lbF, new V(BW * 0.74, BH + 0.26, 0).applyMatrix4(fPivot.matrixWorld));
    if (betaDeg > 1 && lbB) S.labelAt(lbB, new V(0.5, 0.3, -0.34 * Math.sin(betaDeg * DEG * 0.5)));
  }

  S.init({
    key: 'refl',
    chip: '光现象 · 2.2 光的直线传播 / 3.3 光的反射',
    title: '光的反射 · <em>可折转纸板</em>',
    sub: '两块纸板 E、F 立在平面镜上，F 可绕法线 ON 折转。<b>折转后 F 板上接不到反射光线</b>，说明三线共面。拖动画面可换视角。',
    aria: '三维反射实验：入射光线、反射光线与法线、可绕法线折转的纸板',
    bootText: '正在搭建镜面与纸板',
    roTitle: '实时读数',
    cam: { pos: [3.35, 2.6, 4.3], target: [0, 0.85, 0], minDist: 1.6, maxDist: 14, maxPolar: Math.PI * 0.52 },
    side: { pos: [0.02, 0.95, 5.0], target: [0, 0.95, 0] },
    params: { i: 40, beta: 0 },
    readouts: [
      { k: 'i', label: '入射角 i' },
      { k: 'r', label: '反射角 r' },
      { k: 'beta', label: '纸板 F 折转角 β' },
      { k: 'hit', label: 'F 板上光斑' },
      { k: 'cop', label: '三线共面' }
    ],
    footer: [
      { type: 'range', name: 'i', label: '入射角 i', min: 0, max: 85, step: 0.5, unit: '°', dp: 1 },
      { type: 'range', name: 'beta', label: '纸板 F 折转角 β', min: 0, max: 90, step: 1, unit: '°', dp: 0 },
      { type: 'play', name: 'demo', label: '▶ 折转演示', fn: toggleDemo }
    ],
    build: build,
    onParam: apply,
    onReset: onReset,
    onFrame: frame
  });
})();
