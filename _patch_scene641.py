# -*- coding: utf-8 -*-
"""V6.4.1 场景脚本改造：从大文件提取的 _lens_scene.js → _lens_scene_new.js
物体三维全方向移动（oy 上下 / oz 左右），像与光线按近轴薄透镜规律联动。
每处替换断言命中数，任一处不符立即中止。"""
import re, sys

BASE = r"C:\Users\Administrator\Desktop\AI光学参赛"
SRC = BASE + r"\_lens_scene.js"
DST = BASE + r"\_lens_scene_new.js"
LOG = []

s = open(SRC, encoding="utf-8").read().replace("\r\n", "\n")

def rep(old, new, n=1, label=""):
    global s
    c = s.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    s = s.replace(old, new)
    LOG.append("OK  %s  x%d" % (label, c))

# ---------- R1 头注释补 V6.4.1 说明 ----------
rep("""   物理：薄透镜公式 1/u + 1/v = 1/f（初中口径），放大率 m = v/u，实像倒立；
        |u − f| < 0.6 cm 视为不成像（出射光平行）。""",
"""   物理：薄透镜公式 1/u + 1/v = 1/f（初中口径），放大率 m = v/u，实像倒立；
        |u − f| < 0.6 cm 视为不成像（出射光平行）。
        V6.4.1：物体三维全方向移动 —— 物点离轴后像点仍在原像平面内，横向坐标
        取 -m 倍（上下颠倒、左右相反）；像距与放大率只由 u、f 决定，与离轴无关。""",
    1, "R1 头注释")

# ---------- R2 状态变量 ----------
rep("  var u = 42, f = 11, coneOn = true, specialOn = true;",
    "  var u = 42, f = 11, oy = 0, oz = 0, coneOn = true, specialOn = true;",
    1, "R2 状态变量加 oy/oz")

# ---------- R3 声明区加 postG ----------
rep("  var lens, screenG, imgPlane, matReal, matVirt, coneG, rayG, objG;",
    "  var lens, screenG, imgPlane, matReal, matVirt, coneG, rayG, objG, postG;",
    1, "R3 声明 postG")

# ---------- R4 build 立柱提升为 postG ----------
rep("""    var post = new T.Mesh(new T.BoxGeometry(0.07, AY, 0.07), S.MAT.metal(0x5d6b84));
    /* 注意：这支立柱刻意挂在 objG（烛台）上而不是 screenG —— 光屏本身就高到台面，
       立在屏里的柱子会被屏面挡住；挂在物上正好当烛台，物体移动时支架跟着走。 */
    post.position.set(0, -AY / 2, 0); objG.add(post);""",
"""    /* 这支立柱刻意挂在 objG（烛台）上而不是 screenG —— 光屏本身就高到台面，
       立在屏里的柱子会被屏面挡住；挂在物上正好当烛台，物体移动时支架跟着走。
       V6.4.1：物体上下移动时立柱跟着伸缩（scale.y），底端始终立到台面。 */
    postG = new T.Mesh(new T.BoxGeometry(0.07, AY, 0.07), S.MAT.metal(0x5d6b84));
    postG.position.set(0, -AY / 2, 0); objG.add(postG);""",
    1, "R4 立柱 postG")

# ---------- R5 redraw 物坐标段（三维位置 + 立柱伸缩） ----------
rep("""    var xObj = sxf(-u), yTip = syf(OBJ_H);
    objG.position.set(xObj, AY, 0);
    S.labelAt(lb.obj, [xObj, AY + yTip + 0.3, 0]);""",
"""    /* V6.4.1：物体三维全方向移动 —— 沿轴 u（原有滑块）+ 离轴 oy（上下）+ 侧偏 oz（左右）。
       近轴薄透镜的平移不变性：像距 v 与放大率 m 只由 u、f 决定，与离轴量无关；
       像点的横向坐标 = 物点横向坐标的 -m 倍（上下颠倒、左右也颠倒，实像倒立）。
       z 与 y 同用 KY 比例，保证透镜圆面在 (y,z) 平面是真正的圆。 */
    var xObj = sxf(-u), yTip = syf(OBJ_H + oy), zTip = syf(oz), yBase = syf(oy);
    objG.position.set(xObj, AY + yBase, zTip);
    var postH = AY + yBase;                        // 烛台底到台面的高度跟着变
    if (postG) { postG.scale.y = postH / AY; postG.position.y = -postH / 2; }
    S.labelAt(lb.obj, [xObj, AY + yTip + 0.3, zTip]);""",
    1, "R5 物坐标三维化")

# ---------- R6 光屏跟随像侧移 ----------
rep("""    /* 光屏 */
    var xScr = real ? sxf(vShow) : RAIL_R;
    screenG.visible = real;
    screenG.position.set(xScr, AY, 0);
    S.labelVis(lb.scr, real);
    S.labelAt(lb.scr, [xScr + 0.12, AY + 1.62, 0]);""",
"""    /* 光屏：物侧偏后像也侧偏（z 向 -m 倍），把光屏沿 z 平移到像所在的平面才能接到像
       —— 真实光具座上就是"把屏挪到像的位置"；上下方向像若超出屏面则提示屏太小。 */
    var xScr = real ? sxf(vShow) : RAIL_R;
    var zScr = real ? -m * zTip : 0;
    screenG.visible = real;
    screenG.position.set(xScr, AY, zScr);
    S.labelVis(lb.scr, real);
    S.labelAt(lb.scr, [xScr + 0.12, AY + 1.62, zScr]);""",
    1, "R6 光屏侧移")

# ---------- R7 像段三维化 ----------
rep("""    /* 像（实像贴在屏上；虚像画在物侧，正立） */
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
    var pImgY = real ? -ih : ih;""",
"""    /* 像（实像贴在屏上；虚像画在物侧，正立）。V6.4.1：像整体随物偏移反向平移 ——
       像底端横向偏移 -m·oy、侧向 -m·oz；像高仍是 |m|·物高。 */
    var ih = Math.max(0.08, Math.abs(syf(OBJ_H) * m));
    var yImgBase = noImg ? 0 : -m * yBase;         // 像底端的横向偏移（实像倒立向下）
    var zImg = noImg ? 0 : -m * zTip;              // 像的侧向偏移
    imgPlane.visible = !noImg && (real ? !over : true);
    if (imgPlane.visible) {
      imgPlane.scale.set(1, ih, 1);
      if (real) {
        imgPlane.material = matReal;
        imgPlane.position.set(xScr - 0.04, AY + yImgBase - ih / 2, zImg);
        S.labelVis(lb.img, true); S.labelAt(lb.img, [xScr + 0.12, AY + yImgBase - ih - 0.14, zImg]);
      } else {
        imgPlane.material = matVirt;
        imgPlane.position.set(sxf(v) + 0.03, AY + yImgBase + ih / 2, zImg);
        S.labelVis(lb.img, true); S.labelAt(lb.img, [sxf(v) + 0.12, AY + yImgBase + ih + 0.16, zImg]);
      }
    } else S.labelVis(lb.img, false);
    if (lb.img.el) lb.img.el.className = 'lb ' + (real ? 'k-e' : 'k-n');

    /* 像点（光锥与三条光线都交于此）：像顶端，横向坐标 = -m × 物顶端横向坐标 */
    var pImgX = real ? sxf(vShow) : sxf(v);
    var pImgY = noImg ? 0 : -m * yTip;
    var pImgZ = noImg ? 0 : -m * zTip;""",
    1, "R7 像三维化")

# ---------- R8 光锥：tip / 出射方向 / 过光心那条 ----------
rep("""      var RINGS = [[0.42, 8], [0.72, 12], [0.97, 16]];
      var tip = new V(xObj, yTip, 0), a, b, d, len, yl, zl, ang, rt, k, sp;""",
"""      var RINGS = [[0.42, 8], [0.72, 12], [0.97, 16]];
      var tip = new V(xObj, yTip, zTip), a, b, d, len, yl, zl, ang, rt, k, sp;""",
    1, "R8a 光锥 tip")
rep("          d = new V(pImgX - 0, pImgY - yl, 0 - zl).normalize();",
    "          d = new V(pImgX - 0, pImgY - yl, pImgZ - zl).normalize();",
    1, "R8b 出射方向含 pImgZ")
rep("""      /* 轴上那条 */
      coneG.add(S.beam(tip, new V(0, 0, 0), 0xff7043, 0.006));
      coneG.add(S.beam(new V(0, 0, 0), new V(real ? pImgX : RAIL_R, 0, 0), 0xffd54f, 0.006));""",
"""      /* 过光心那条：物离轴后它不再是水平线 —— 实像时出射沿过光心直线直达像点，
         虚像时实际出射光是发散的，沿同一直线朝 +x 画（反向延长才过像点）。 */
      coneG.add(S.beam(tip, new V(0, 0, 0), 0xff7043, 0.006));
      if (real) coneG.add(S.beam(new V(0, 0, 0), new V(pImgX, pImgY, pImgZ), 0xffd54f, 0.006));
      else {
        var dcC = -xObj;
        coneG.add(S.beam(new V(0, 0, 0),
          new V(RAIL_R, -yTip * RAIL_R / dcC, -zTip * RAIL_R / dcC), 0xffd54f, 0.006));
      }""",
    1, "R8c 过光心线")

# ---------- R9 特殊光线三维追迹 + 口径截断 ----------
rep("""    /* ---- 三条特殊光线 ---- */
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
    }""",
"""    /* ---- 三条特殊光线 ----
       V6.4.1：物离轴后按三维近轴追迹 —— 旋转对称透镜对 y、z 两个横向分量
       按同一规律独立折射，故每条光线在透镜处的交点与出射方向都把 z 一并算上。
       科学性兜底：若某条光线在透镜处的交点落在玻璃圆面之外（r > LENS_R），
       那条光实际不会以理想折射参与成像，出射段不再硬画。 */
    S.clearGroup(rayG);
    if (specialOn && !noImg) {
      var xFp = sxf(f);
      var inLens = function (yy, zz) { return yy * yy + zz * zz <= LENS_R * LENS_R; };
      /* ① 平行主光轴 → 过 F′ */
      var c1 = inLens(yTip, zTip);
      rayG.add(S.beam(new V(xObj, yTip, zTip), new V(0, yTip, zTip), 0xff5252, 0.013));
      if (c1) {
        if (real) rayG.add(S.beam(new V(0, yTip, zTip),
          new V(xScr, yTip * (1 - vShow / f), zTip * (1 - vShow / f)), 0xff5252, 0.013));
        else {
          rayG.add(S.beam(new V(0, yTip, zTip),
            new V(RAIL_R, yTip * (1 - RAIL_R / xFp), zTip * (1 - RAIL_R / xFp)), 0xff5252, 0.013));
          rayG.add(S.dashLine(new V(0, yTip, zTip), new V(pImgX, pImgY, pImgZ), 0xff9e9e));
        }
      }
      /* ② 过光心，方向不变（必在口径内） */
      rayG.add(S.beam(new V(xObj, yTip, zTip), new V(0, 0, 0), 0x4fc3f7, 0.013));
      var dc = new V(-xObj, -yTip, -zTip).normalize();
      var ex = real ? xScr : RAIL_R;
      rayG.add(S.beam(new V(0, 0, 0), new V(ex, dc.y * (ex / dc.x), dc.z * (ex / dc.x)), 0x4fc3f7, 0.013));
      if (virt) rayG.add(S.dashLine(new V(0, 0, 0), new V(pImgX, pImgY, pImgZ), 0x9fd8ff));
      /* ③ 过焦点 F → 出射平行主光轴 */
      var y3 = yTip * f / (f - u), z3 = zTip * f / (f - u);
      var c3 = inLens(y3, z3);
      rayG.add(S.beam(new V(xObj, yTip, zTip), new V(0, y3, z3), 0x66bb6a, 0.013));
      if (c3) rayG.add(S.beam(new V(0, y3, z3), new V(real ? xScr : RAIL_R, y3, z3), 0x66bb6a, 0.013));
    }""",
    1, "R9 特殊光线三维化")

# ---------- R10 读数：scr 行重排 + off 行 ----------
rep("""    S.setRO('scr', noImg ? '接不到像' : (v > 0 ? (over ? '像距超出导轨末端' : '屏上有清晰的像') : '光屏接不到虚像'),
      (noImg || v < 0 || over) ? 'no' : 'ok');
    S.setRO('use', noImg ? '—' : (u > 2 * f + 0.6 ? '照相机' : (Math.abs(u - 2 * f) < 0.6 ? '—（u = 2f，等大）' : (u > f ? '投影仪' : '放大镜'))));""",
"""    S.setRO('use', noImg ? '—' : (u > 2 * f + 0.6 ? '照相机' : (Math.abs(u - 2 * f) < 0.6 ? '—（u = 2f，等大）' : (u > f ? '投影仪' : '放大镜'))));
    /* V6.4.1：物偏移读数 + 像是否完整落在屏面内（屏半高 1.5 场景单位 ≈ 7.9 cm，
       z 向因光屏已平移到像平面、恒在屏内，只判上下） */
    S.setRO('off', (oy === 0 && oz === 0) ? '在光轴上'
      : '上' + (oy > 0 ? '+' : '') + oy.toFixed(1) + ' · 侧' + (oz > 0 ? '+' : '') + oz.toFixed(1) + ' cm',
      (oy !== 0 || oz !== 0) ? 'hi' : '');
    var scrTxt, scrCls;
    if (noImg) { scrTxt = '接不到像'; scrCls = 'no'; }
    else if (v < 0) { scrTxt = '光屏接不到虚像'; scrCls = 'no'; }
    else if (over) { scrTxt = '像距超出导轨末端'; scrCls = 'no'; }
    else {
      var topY = yImgBase - ih;                    // 实像的像顶（最低点）
      var tooTall = (yImgBase > 1.5 || topY < -1.5);
      scrTxt = tooTall ? '像超出光屏（屏太小）' : '屏上有清晰的像';
      scrCls = tooTall ? 'no' : 'ok';
    }
    S.setRO('scr', scrTxt, scrCls);""",
    1, "R10 读数 off/scr")

# ---------- R11 apply 分支 ----------
rep("""    if (name === 'u') u = S.px(v, 4, 42);
    else if (name === 'f') f = S.px(Math.round(v), 4, 20);
    else if (name === 'cone') coneOn = !!v;""",
"""    if (name === 'u') u = S.px(v, 4, 42);
    else if (name === 'f') f = S.px(Math.round(v), 4, 20);
    else if (name === 'oy') oy = S.px(v, -4, 4);
    else if (name === 'oz') oz = S.px(v, -4, 4);
    else if (name === 'cone') coneOn = !!v;""",
    1, "R11 apply oy/oz")

# ---------- R12 onReset ----------
rep("""  function onReset() {
    playing = false; dir = -1;
    S.setParam('u', 42); S.setParam('f', 11);
    u = 42; f = 11;
    redraw();
  }""",
"""  function onReset() {
    playing = false; dir = -1;
    S.setParam('u', 42); S.setParam('f', 11);
    S.setParam('oy', 0); S.setParam('oz', 0);
    u = 42; f = 11; oy = 0; oz = 0;
    redraw();
  }""",
    1, "R12 onReset")

# ---------- R13 init 配置：sub / params / readouts / footer ----------
rep("""    sub: '从烛焰顶端发出的光经凸透镜后会聚到一点，光屏放到那个位置就出现<b>倒立的实像</b>。' +
         '转动视角看整束光锥怎样穿过这枚<b>立体的双凸透镜</b>。',""",
"""    sub: '从烛焰顶端发出的光经凸透镜后会聚到一点，光屏放到那个位置就出现<b>倒立的实像</b>。' +
         '拖动「物体上下 / 左右」把蜡烛移离主光轴 —— 像会向<b>相反方向</b>移动，像距不变。' +
         '转动视角看整束光锥怎样穿过这枚<b>立体的双凸透镜</b>。',""",
    1, "R13a sub 文案")
rep("    params: { u: 42, f: 11, cone: true, special: true },",
    "    params: { u: 42, f: 11, oy: 0, oz: 0, cone: true, special: true },",
    1, "R13b params")
rep("""      { k: 'scr', label: '光屏' },
      { k: 'use', label: '应用' }""",
"""      { k: 'scr', label: '光屏' },
      { k: 'use', label: '应用' },
      { k: 'off', label: '物偏移' }""",
    1, "R13c readouts")
rep("""      { type: 'range', name: 'u', label: '物距 u', min: 4, max: 42, step: 0.5, unit: ' cm', dp: 1 },
      { type: 'range', name: 'f', label: '焦距 f', min: 4, max: 20, step: 1, unit: ' cm', dp: 0 },
      { type: 'toggle', name: 'cone', label: '立体光锥', value: true },""",
"""      { type: 'range', name: 'u', label: '物距 u', min: 4, max: 42, step: 0.5, unit: ' cm', dp: 1 },
      { type: 'range', name: 'f', label: '焦距 f', min: 4, max: 20, step: 1, unit: ' cm', dp: 0 },
      { type: 'range', name: 'oy', label: '物体上下', min: -4, max: 4, step: 0.5, unit: ' cm', dp: 1 },
      { type: 'range', name: 'oz', label: '物体左右', min: -4, max: 4, step: 0.5, unit: ' cm', dp: 1 },
      { type: 'toggle', name: 'cone', label: '立体光锥', value: true },""",
    1, "R13d footer 滑块")

open(DST, "w", encoding="utf-8", newline="\n").write(s)
print("\n".join(LOG))
print("场景改造完成 -> %s (%d chars)" % (DST, len(s)))
