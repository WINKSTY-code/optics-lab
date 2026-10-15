/* ==========================================================================
   3D 场景③ · 平面镜成像 —— 苏科版「棋子与玻璃板」实验
   --------------------------------------------------------------------------
   教材装置：一块玻璃板竖直架在白纸上，板前放棋子 A，板后放棋子 B。
            从板前看过去，移动 B 直到它与 A 的像完全重合 —— B 所在的位置
            就是像的位置，量一量就知道像距是否等于物距。
   3D 的价值：正对板面看过去，"B 与像重合"这件事只有真的立起来才看得见；
             玻璃板后面的"像"到底在哪里、物与像关于板面怎样对称，一目了然。
   坐标：玻璃板所在平面 = YZ 平面（x=0）；桌面 = y=0；板前为 −x，板后为 +x。
   ========================================================================== */
(function () {
  var S = window.S3D, T = S.THREE;
  var V = T.Vector3;
  var K = 0.06;                        // 单位 / 厘米（沿 x 的距离）
  var HI = 0.028;                      // 棋子高度 = h × HI（单位 / 厘米）
  var TABLE_Z = 1.35;                  // 白纸的半宽（z 方向）

  var uCm = 14, hCm = 17, bCm = 14;
  var zA = 0;                          // 棋子的左右位置（单位，绕板面法向前后为 x，左右为 z）
  var pieceA, pieceB, ghost, glassG, tblG, sightG, hitB, lb = {};
  var okTol = 0.4;                     // 判"重合"的容差（cm）
  var seenBehind = false;
  var planeY = 0.16;

  /* 棋子：车削一件圆润的棋子（底盘 + 束腰 + 圆顶），剖面上半部分由点集决定 */
  function makePiece(h, color) {
    var R = h * 0.62;
    var pts = [
      new T.Vector2(0, 0), new T.Vector2(R * 0.92, 0), new T.Vector2(R * 0.94, h * 0.06),
      new T.Vector2(R * 0.80, h * 0.14), new T.Vector2(R * 0.72, h * 0.42),
      new T.Vector2(R * 0.66, h * 0.62), new T.Vector2(R * 0.52, h * 0.80),
      new T.Vector2(R * 0.30, h * 0.93), new T.Vector2(0, h * 0.96)
    ];
    var m = new T.Mesh(new T.LatheGeometry(pts, 30), S.MAT.metal(color));
    m.castShadow = false;
    return m;
  }

  function build() {
    uCm = S.params.u === undefined ? 14 : S.params.u;
    zA = S.params.z === undefined ? 0 : S.params.z * K;
    hCm = S.params.h === undefined ? 17 : S.params.h;
    bCm = S.params.b === undefined ? 14 : S.params.b;

    /* ---------- 白纸桌面 + 刻度 ---------- */
    tblG = new T.Group();
    var pc = document.createElement('canvas');
    pc.width = pc.height = 256;
    var px = pc.getContext('2d');
    px.fillStyle = '#cdc9bb'; px.fillRect(0, 0, 256, 256);
    px.strokeStyle = '#a9a496'; px.lineWidth = 1.5;
    for (var q = 0; q <= 4; q++) {
      var v4 = q * 64 + 0.5;
      px.beginPath(); px.moveTo(v4, 0); px.lineTo(v4, 256); px.stroke();
      px.beginPath(); px.moveTo(0, v4); px.lineTo(256, v4); px.stroke();
    }
    var pt = new T.CanvasTexture(pc);
    pt.wrapS = pt.wrapT = T.RepeatWrapping;
    pt.repeat.set(3.6, TABLE_Z * 2 / 0.6);
    if ('encoding' in pt) pt.encoding = T.sRGBEncoding;
    var paper = new T.Mesh(new T.PlaneGeometry(7.2, TABLE_Z * 2),
      new T.MeshLambertMaterial({ map: pt, color: 0xffffff }));
    paper.rotation.x = -Math.PI / 2;
    tblG.add(paper);
    /* 板面的投影线（像与物到它的距离要相等） */
    var axis = S.dashLine(new V(0, 0.004, -TABLE_Z), new V(0, 0.004, TABLE_Z), 0x4fa3e8);
    tblG.add(axis);
    S.add(tblG);
    S.label('白纸', [-2.6, 0.02, -1.05], 'k-p');
    S.label('玻璃板位置', [0, 0.02, TABLE_Z + 0.12], 'k-n');

    /* ---------- 玻璃板 ---------- */
    glassG = new T.Group();
    /* 茶色玻璃板（苏科版器材）：茶色让反射光足够强，虚像才看得清；
       同时又半透，能透过它看到板后的棋子 B —— 这两件事缺一不可。 */
    var glassM = new T.MeshPhongMaterial({
      color: 0x8f5a24, transparent: true, opacity: 0.34, shininess: 26,
      specular: 0x5a4423, emissive: 0x2b1808, side: T.DoubleSide, depthWrite: false
    });
    var gp = new T.Mesh(new T.BoxGeometry(0.035, 1.5, 1.3), glassM);
    gp.position.y = 0.75;
    glassG.add(gp);
    var edge = new T.LineSegments(new T.EdgesGeometry(new T.BoxGeometry(0.035, 1.5, 1.3)),
      new T.LineBasicMaterial({ color: 0xe0b073, transparent: true, opacity: 0.95 })).translateY(0.75);
    glassG.add(edge);
    S.add(glassG);
    S.label('茶色玻璃板', [0, 1.64, 0], 'k-n');
    lb.hint = S.label('只有透过玻璃板才看得到虚像', [0, 1.36, -0.78], 'k-on');

    /* ---------- 棋子 A（板前）／B（板后）／像 ---------- */
    pieceA = makePiece(1, 0xc98a3c);
    pieceB = makePiece(1, 0xc98a3c);
    ghost = makePiece(1, 0x6fd0f0);
    ghost.material = new T.MeshPhongMaterial({
      color: 0x86d8f7, transparent: true, opacity: 0.62, shininess: 70, emissive: 0x0d3245
    });
    S.add(pieceA); S.add(pieceB); S.add(ghost);
    /* 直接在 3D 里拖：A 的前后 → 物距（并回写父页滑块），左右 → z；虚像全程跟着镜像移动 */
    S.draggable(pieceA, {
      planeY: 0.2, hint: '拖动棋子 A：像会跟着一起动',
      onDrag: function (pt) {
        var cm = Math.round((Math.abs(pt.x) / K) * 10) / 10;
        if (cm < 3) cm = 3; if (cm > 28) cm = 28;
        var z = Math.round((pt.z / K) * 10) / 10;
        if (z < -9) z = -9; if (z > 9) z = 9;
        if (Math.abs(cm - uCm) > 0.05) { uCm = cm; S.setParam('u', cm); S.setVal('u', cm.toFixed(1) + ' cm'); }
        if (Math.abs(z - zA / K) > 0.05) { zA = z * K; S.setParam('z', z); S.setVal('z', z.toFixed(1) + ' cm'); }
        apply('drag', 0);
      }
    });
    S.draggable(pieceB, {
      planeY: 0.2, hint: '拖动棋子 B：与玻璃板里的像重合',
      onDrag: function (pt) {
        var cm = Math.round((pt.x / K) * 10) / 10;
        if (cm < 0.5) cm = 0.5; if (cm > 28) cm = 28;
        if (Math.abs(cm - bCm) > 0.05) { bCm = cm; S.setParam('b', cm); S.setVal('b', cm.toFixed(1) + ' cm'); apply('drag', 0); }
      }
    });
    lb.A = S.label('棋子 A（物）', [0, 0, 0], 'k-p');
    lb.B = S.label('棋子 B', [0, 0, 0], 'k-p');
    lb.g = S.label('像（虚像）', [0, 0, 0], 'k-n');
    lb.dis = S.label('', [0, 0, 0], 'k-on');
    lb.du = S.label('', [0, 0, 0], 'k-p');
    lb.dv = S.label('', [0, 0, 0], 'k-p');

    /* ---------- 观察者的眼睛 + 视线 ---------- */
    var eyeG = new T.Group();
    var eyeb = new T.Mesh(new T.SphereGeometry(0.07, 16, 12), S.MAT.emissive(0xdfe9ff));
    eyeG.add(eyeb);
    var iris = new T.Mesh(new T.CircleGeometry(0.035, 16), S.MAT.emissive(0x2a4a7a));
    iris.position.z = 0.071; eyeG.add(iris);
    eyeG.position.set(-2.9, 0.26, 0);
    S.add(eyeG);
    S.label('眼睛', [-2.9, 0.48, 0], 'k-p');
    sightG = new T.Group();
    S.add(sightG);

    apply('u', uCm); apply('h', hCm); apply('b', bCm);
  }

  /* ---------- 重绘 ---------- */
  function redraw() {
    var xA = -K * uCm, xB = K * bCm, xG = K * uCm;      // 像与物关于板面对称
    var z = zA;                                          // 左右位置：物、像、B 三者相同
    var hh = HI * hCm;

    /* 棋子 A */
    pieceA.scale.setScalar(hh);
    pieceA.position.set(xA, 0, z);
    pieceB.scale.setScalar(hh);
    pieceB.position.set(xB, 0, z);
    ghost.scale.setScalar(hh);
    ghost.position.set(xG, 0, z);

    S.labelAt(lb.A, [xA, hh * 1.05 + 0.24, z]);
    S.labelAt(lb.B, [xB, hh * 1.05 + 0.24, z]);
    S.labelAt(lb.g, [xG, hh * 1.05 + 0.24, z]);

    /* 视线：眼睛 → 板后（像与 B 各一条，重合时会并成一条） */
    S.clearGroup(sightG);
    var eye = new V(-2.9, 0.26, z * 0.5);
    var pG = new V(xG, hh * 0.5, z), pB = new V(xB, hh * 0.5, z);
    sightG.add(S.beam(eye, pG, 0x8fd8f5, 0.004));
    sightG.add(S.beam(eye, pB, 0xffd54f, 0.0035));
    S.labelAt(lb.du, [xA / 2, 0.05, z - 0.62]);
    S.labelAt(lb.dv, [xG / 2, 0.05, z + 0.62]);
    lb.du.el.innerHTML = 'u = <i>' + uCm.toFixed(1) + '</i> cm';
    lb.dv.el.innerHTML = 'v = <i>' + uCm.toFixed(1) + '</i> cm';

    /* 重合判定 */
    var diff = bCm - uCm;
    var same = Math.abs(diff) < okTol;
    lb.dis.el.className = 'lb ' + (same ? 'k-e' : 'k-on');
    S.labelVis(lb.dis, !same);
    S.labelAt(lb.dis, [(xB + xG) / 2, hh * 1.05 + 0.62, z]);
    lb.dis.el.innerHTML = same ? '' : ('还差 <i>' + Math.abs(diff).toFixed(1) + '</i> cm');

    /* ---------- 读数 ---------- */
    S.setRO('u', uCm.toFixed(1) + ' cm');
    S.setRO('z', (zA / K).toFixed(1) + ' cm', Math.abs(zA) > 0.01 ? 'hi' : '');
    S.setRO('b', bCm.toFixed(1) + ' cm');
    S.setRO('v', uCm.toFixed(1) + ' cm（像距 = 物距）');
    S.setRO('fit', same ? '完全重合' : '还差 ' + Math.abs(diff).toFixed(1) + ' cm', same ? 'ok' : 'no');
    S.setRO('h', hCm.toFixed(1) + ' cm');
    S.setRO('virt', '没有 · 只能透过玻璃板看到', 'hi');
    S.setRO('nat', '虚像 · 正立 · 与物等大 · 左右相反', 'hi');

    return same;
  }

  var lastSame = null;
  function apply(name, v) {
    if (name === 'u') uCm = S.px(v, 3, 28);
    else if (name === 'z') zA = S.px(v, -9, 9) * K;
    else if (name === 'h') hCm = S.px(v, 5, 22);
    else if (name === 'b') bCm = S.px(v, 0.5, 28);
    var same = redraw();
    if (same !== lastSame) {
      if (same) lb.dis.el.innerHTML = '';
      if (same) S.toast('<b>B 与 A 的像完全重合</b>：B 所在的位置就是像的位置 —— 像距 = 物距 = <b>' +
        uCm.toFixed(1) + ' cm</b>，像与物等大', 4200);
      lastSame = same;
    }
  }

  /* 虚像只在"站在板前、透过玻璃板看"时才存在 —— 交互式证据：把镜头绕到板后，
     虚像立刻消失（板后其实什么都没有）。逐帧判定，因为换视角不一定伴随参数变化。 */
  function frame() {
    if (!S.camera) return;
    var fromFront = S.camera.position.x < -0.05;
    if (ghost.visible !== fromFront) {
      ghost.visible = fromFront;
      S.labelVis(lb.g, fromFront);
      if (!fromFront && !seenBehind) {
        seenBehind = true;
        S.toast('绕到板后：<b>什么也没有</b> —— 虚像不是板后的实物，它只能透过茶色玻璃板看到', 4200);
      } else if (fromFront) seenBehind = false;
    }
    lb.hint.el.innerHTML = fromFront
      ? '透过玻璃板看：A 的虚像在板后 <i>' + uCm.toFixed(1) + '</i> cm 处'
      : '板后没有实物（虚像只能在玻璃板里看到）';
    lb.hint.el.className = 'lb ' + (fromFront ? 'k-on' : 'k-n');
  }

  function onReset() {
    S.setParam('u', 14); S.setParam('h', 17); S.setParam('b', 14); S.setParam('z', 0);
    uCm = 14; hCm = 17; bCm = 14; zA = 0;
    lastSame = null;
    redraw();
  }

  /* ---------- 直接在 3D 里拖棋子 B（真实的"移动棋子找像"） ---------- */
  S.init({
    key: 'mirror',
    chip: '光现象 · 3.4 平面镜成像',
    title: '平面镜成像 · <em>玻璃板里找像</em>',
    sub: '站在板前<b>透过茶色玻璃板</b>看棋子 A 的虚像。棋子可<b>直接在 3D 里拖动</b>：左右移动时像跟着一起动；把 B 移到板后与像完全重合，B 的位置就是像的位置。',
    aria: '三维平面镜成像实验：玻璃板、棋子 A 与 B、虚像与对称关系',
    bootText: '正在架起茶色玻璃板',
    roTitle: '实时读数',
    cam: { pos: [-3.3, 2.3, 3.2], target: [0.1, 0.35, 0], minDist: 1.6, maxDist: 16, maxPolar: Math.PI * 0.52 },
    side: { pos: [-4.9, 0.26, 0.002], target: [1.0, 0.26, 0] },
    params: { u: 14, h: 17, b: 14, z: 0 },
    readouts: [
      { k: 'u', label: '物距 u（A→板）' },
      { k: 'z', label: '棋子左右位置' },
      { k: 'b', label: 'B→板' },
      { k: 'v', label: '像距 v' },
      { k: 'fit', label: 'B 与像' },
      { k: 'h', label: '物高 h（= 像高）' },
      { k: 'virt', label: '板后是否有实物' },
      { k: 'nat', label: '像的性质' }
    ],
    footer: [
      { type: 'range', name: 'z', label: '棋子左右移动', min: -9, max: 9, step: 0.5, unit: ' cm', dp: 1 },
      { type: 'range', name: 'b', label: '棋子 B 位置', min: 0.5, max: 28, step: 0.1, unit: ' cm', dp: 1 },
      { type: 'play', name: 'auto', label: '▶ 自动重合', fn: function () {
          bCm = uCm;
          S.setParam('b', bCm); S.setVal('b', bCm.toFixed(1) + ' cm');
          apply('b', bCm);
        } }
    ],
    build: build,
    onParam: apply,
    onReset: onReset,
    onFrame: frame
  });
})();
