# -*- coding: utf-8 -*-
"""V6.4.9 补丁
① 「直线传播」页（影子形成 / 小孔成像）的调节栏从右栏搬到画布下方，与前几个 2D 实验一致。
② 「物体颜色」：修掉 obj 控件被嵌进 rgb 控件导致整组不可见的结构 bug；
   新增「物体本色」选择，并把「看到的颜色」按物理规则（反射本色 ∩ 照射光）真实算出来。
"""
import os, re

BASE = r"C:/Users/Administrator/Desktop/AI光学参赛"
SRC = os.path.join(BASE, "光学交互实验室_AI_v6.4.8.html")
DST = os.path.join(BASE, "光学交互实验室_AI_v6.4.9.html")
LOG = []


def rep(s, old, new, n=1, label=""):
    c = s.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    LOG.append("OK  %-52s x%d" % (label, c))
    return s.replace(old, new)


s = open(SRC, "r", encoding="utf-8", newline="").read()
n0 = os.path.getsize(SRC)
closes0 = len(re.findall(r"</script(?=[\s>/])", s))
opens0 = len(re.findall(r"<script(?=[\s>/])", s))
V648_BEFORE = s.count("V6.4.8")

# ============================================================
# ① 直线传播页：把 .ctrl 从右栏搬到画布下方（.left 内）
# ============================================================
A = '\n    <div class="ctrl">\n      <span class="clabel" data-i18n="line.mode">'
B = '\n        <div class="data-panel">'
i0 = s.index(A)
i1 = s.index(B, i0)
block = s[i0 + 1:i1]                      # 不含前导 \n，末尾即 "    </div>"
assert block.startswith('    <div class="ctrl">'), "[FAIL] 直线传播调节栏起点不对"
assert block.rstrip().endswith('</div>'), "[FAIL] 直线传播调节栏终点不对"
assert 'line-uSlider' in block and 'line-holeSlider' in block and 'line-reset' in block, \
    "[FAIL] 直线传播调节栏内容不完整"
LOG.append("OK  %-52s %s" % ("直线传播调节栏定位（行块）", "%d 字符" % len(block)))
# 从 .right 里摘掉
s = s[:i0] + s[i1:]

# 缩进 +4 后插进 .left（放在日食 3D 宿主之后、.left 闭合之前）
block_ind = "\n".join(("    " + ln) if ln.strip() else ln for ln in block.split("\n"))
anchor = '\n      </div>\n      <div class="right">\n    <div class="verdict" id="verdict-line"></div>'
s = rep(s, anchor,
        "\n" + block_ind + "\n      </div>\n      <div class=\"right\">\n    <div class=\"verdict\" id=\"verdict-line\"></div>",
        1, "① 调节栏移到 .left（画布下方）")

# ============================================================
# ② 物体颜色：修嵌套 bug + 新增「物体本色」
# ============================================================
s = rep(
    s,
    '      <label style="margin-left:8px;"><span data-i18n="disp.rgb.mix">混合结果：</span><b id="disp-rgb-out">白光</b></label>\n'
    '    <div class="ctrl" id="disp-obj-ctrl" style="display:none;">\n'
    '      <span class="clabel" data-i18n="disp.light">照射「红苹果」的光：</span>\n'
    '      <div class="seg" id="disp-light">\n'
    '        <button class="sec active" data-l="white" data-i18n="disp.l.white">白光</button>\n'
    '        <button class="sec" data-l="red" data-i18n="disp.l.red">红光</button>\n'
    '        <button class="sec" data-l="green" data-i18n="disp.l.green">绿光</button>\n'
    '        <button class="sec" data-l="blue" data-i18n="disp.l.blue">蓝光</button>\n'
    '      </div>\n'
    '    </div>\n',

    '      <label style="margin-left:8px;"><span data-i18n="disp.rgb.mix">混合结果：</span><b id="disp-rgb-out">白光</b></label>\n'
    '    </div>\n'
    '    <!-- V6.4.9：原来 #disp-obj-ctrl 被写在 #disp-rgb-ctrl 的「收尾标签之前」，\n'
    '         于是整组被嵌在 rgb 组里面；而切到「物体颜色」时 rgb 组是 display:none\n'
    '         → 祖先隐藏连坐整棵子树，看起来「完全没有任何可操作内容」。\n'
    '         修法是把那个收尾标签【挪】到 rgb 组末尾（不是"加"——页面标记总数必须不变，\n'
    '         直接加会让 .right 提前闭合、后续 6 个面板掉出 .wrap），并补上「物体本色」选择。 -->\n'
    '    <div class="ctrl" id="disp-obj-ctrl" style="display:none;">\n'
    '      <span class="clabel" data-i18n="disp.objct">物体本色：</span>\n'
    '      <div class="seg" id="disp-obj-color">\n'
    '        <button class="sec active" data-oc="red" data-i18n="disp.oc.red">红</button>\n'
    '        <button class="sec" data-oc="green" data-i18n="disp.oc.green">绿</button>\n'
    '        <button class="sec" data-oc="blue" data-i18n="disp.oc.blue">蓝</button>\n'
    '        <button class="sec" data-oc="yellow" data-i18n="disp.oc.yellow">黄</button>\n'
    '        <button class="sec" data-oc="white" data-i18n="disp.oc.white">白</button>\n'
    '      </div>\n'
    '      <span class="clabel" data-i18n="disp.light">照射光：</span>\n'
    '      <div class="seg" id="disp-light">\n'
    '        <button class="sec active" data-l="white" data-i18n="disp.l.white">白光</button>\n'
    '        <button class="sec" data-l="red" data-i18n="disp.l.red">红光</button>\n'
    '        <button class="sec" data-l="green" data-i18n="disp.l.green">绿光</button>\n'
    '        <button class="sec" data-l="blue" data-i18n="disp.l.blue">蓝光</button>\n'
    '      </div>\n'
    '    </div>\n',
    1, "② 修嵌套 bug + 新增「物体本色」选择")

# ---- ②b 关键：补的那个收尾标签必须从尾部【搬】走一个，而不是净增一个 ----
# 原页面标记总数本来就是平衡的，只是那个 </div> 的位置错了（写在 obj 组之后）。
# 把 </div> 挪到 rgb 组末尾后，尾部就必须少一个，否则 .right 会提前闭合。
s = rep(s,
        '        <button class="sec" data-l="blue" data-i18n="disp.l.blue">蓝光</button>\n'
        '      </div>\n'
        '    </div>\n'
        '    </div>\n'
        '    </div>\n'
        '        <div class="data-panel">',
        '        <button class="sec" data-l="blue" data-i18n="disp.l.blue">蓝光</button>\n'
        '      </div>\n'
        '    </div>\n'
        '    </div>\n'
        '        <div class="data-panel">',
        1, "②b 尾部收尾 </div> 由 3 个减为 2 个（挪而非加）")

# ---- i18n：照射光标签改文案 ----
s = rep(s,
        "'disp.light':     {zh:'照射「红苹果」的光：', zht:'照射「紅蘋果」的光：', en:'Light on the \"red apple\":'},",
        "'disp.light':     {zh:'照射光：', zht:'照射光：', en:'Light:'},",
        1, "i18n：disp.light 改为「照射光：」")

# ---- i18n：4 条 disp.note.* 换成新的结果/原因/本色词条 ----
NEW_I18N = """'disp.objct':     {zh:'物体本色：', zht:'物體本色：', en:'Object color:'},
'disp.oc.red':    {zh:'红', zht:'紅', en:'Red'},
'disp.oc.green':  {zh:'绿', zht:'綠', en:'Green'},
'disp.oc.blue':   {zh:'蓝', zht:'藍', en:'Blue'},
'disp.oc.yellow': {zh:'黄', zht:'黃', en:'Yellow'},
'disp.oc.white':  {zh:'白', zht:'白', en:'White'},
'disp.pc.black':  {zh:'看到的颜色：<b>黑色</b>', zht:'看到的顏色：<b>黑色</b>', en:'You see: <b>black</b>'},
'disp.pc.red':    {zh:'看到的颜色：<b>红</b>色', zht:'看到的顏色：<b>紅</b>色', en:'You see: <b>red</b>'},
'disp.pc.green':  {zh:'看到的颜色：<b>绿</b>色', zht:'看到的顏色：<b>綠</b>色', en:'You see: <b>green</b>'},
'disp.pc.blue':   {zh:'看到的颜色：<b>蓝</b>色', zht:'看到的顏色：<b>藍</b>色', en:'You see: <b>blue</b>'},
'disp.pc.yellow': {zh:'看到的颜色：<b>黄</b>色', zht:'看到的顏色：<b>黃</b>色', en:'You see: <b>yellow</b>'},
'disp.pc.white':  {zh:'看到的颜色：<b>白</b>色', zht:'看到的顏色：<b>白</b>色', en:'You see: <b>white</b>'},
'disp.why.white': {zh:'白光里含各种色光，物体把<b>本色光</b>反射进眼睛、其余全部吸收 → 看到的正是它的本色。', zht:'白光裡含各種色光，物體把<b>本色光</b>反射進眼睛、其餘全部吸收 → 看到的正是它的本色。', en:'White light contains every color; the object reflects its <b>own</b> colors and absorbs the rest → you see its own color.'},
'disp.why.mono':  {zh:'照射光里<b>含有</b>物体能反射的色光 → 这部分光被反射进眼睛，看到的颜色是<b>两者共有的色光</b>。', zht:'照射光裡<b>含有</b>物體能反射的色光 → 這部分光被反射進眼睛，看到的顏色是<b>兩者共有的色光</b>。', en:'The light <b>does</b> contain colors the object reflects → those reach your eye; you see the <b>colors they share</b>.'},
'disp.why.black': {zh:'照射光里<b>没有</b>物体能反射的色光 → 光被全部吸收，没有光进入眼睛，看起来就是<b>黑的</b>。', zht:'照射光裡<b>沒有</b>物體能反射的色光 → 光被全部吸收，沒有光進入眼睛，看起來就是<b>黑的</b>。', en:'The light contains <b>none</b> of the colors the object reflects → everything is absorbed, no light reaches your eye, so it looks <b>black</b>.'},"""
OLD_I18N = """'disp.note.white':{zh:'白光下：苹果反射红光 → 显示红色', zht:'白光下：蘋果反射紅光 → 顯示紅色', en:'White light: the apple reflects red → looks red'},
'disp.note.red':  {zh:'红光下：苹果反射红光 → 依然红色（更暗些）', zht:'紅光下：蘋果反射紅光 → 依然紅色（更暗些）', en:'Red light: it still reflects red → red (slightly darker)'},
'disp.note.green':{zh:'绿光下：绿光不含红光，苹果无红光可反射 → 看起来发黑', zht:'綠光下：綠光不含紅光，蘋果無紅光可反射 → 看起來發黑', en:'Green light has no red component; nothing to reflect → looks black'},
'disp.note.blue': {zh:'蓝光下：蓝光不含红光，苹果无红光可反射 → 看起来发黑', zht:'藍光下：藍光不含紅光，蘋果無紅光可反射 → 看起來發黑', en:'Blue light has no red component; nothing to reflect → looks black'},"""
s = rep(s, OLD_I18N, NEW_I18N, 1, "i18n：新增本色/结果/原因共 16 条词条")

# ---- JS：新增物体本色状态 + 颜色物理 ----
s = rep(s,
        "  let rOn = true, gOn = true, bOn = true;\n  let light = 'white';\n",
        "  let rOn = true, gOn = true, bOn = true;\n  let light = 'white';\n"
        "  /* V6.4.9：物体颜色 —— 物体本色（objC）与照射光（light）都可调，\n"
        "     「看到的颜色」按物理算：不透明物体只反射【本色所含】的色光，\n"
        "     照射光里没有的那部分就无从反射 → 取两者的交集，空集即黑色。 */\n"
        "  let objC = 'red';\n"
        "  const OC_RGB  = { red:[1,0,0], green:[0,1,0], blue:[0,0,1], yellow:[1,1,0], white:[1,1,1] };\n"
        "  const L_RGB   = { white:[1,1,1], red:[1,0,0], green:[0,1,0], blue:[0,0,1] };\n"
        "  const OC_NAME = { red:'红', green:'绿', blue:'蓝', yellow:'黄', white:'白' };\n"
        "  const L_NAME  = { white:'白光', red:'红光', green:'绿光', blue:'蓝光' };\n"
        "  const L_GLOW  = { white:'rgba(255,255,255,0.25)', red:'rgba(255,80,80,0.5)',\n"
        "                    green:'rgba(80,255,80,0.35)', blue:'rgba(80,80,255,0.35)' };\n"
        "  const OC_HEX  = { red:'#e53935', green:'#43a047', blue:'#1e88e5', yellow:'#fdd835', white:'#f2f2f2' };\n"
        "  const SEEN_ZH = { '000':'黑', '100':'红', '010':'绿', '001':'蓝',\n"
        "                    '110':'黄', '101':'紫', '011':'青', '111':'白' };\n"
        "  function seenColor(){\n"
        "    const o = OC_RGB[objC] || OC_RGB.red, L = L_RGB[light] || L_RGB.white;\n"
        "    const key = '' + (o[0] && L[0] ? 1 : 0) + (o[1] && L[1] ? 1 : 0) + (o[2] && L[2] ? 1 : 0);\n"
        "    return { key: key, zh: SEEN_ZH[key] || '黑' };\n"
        "  }\n"
        "  function seenHex(){ const k = seenColor().key;\n"
        "    return { '000':'#141414', '100':'#e53935', '010':'#43a047', '001':'#1e88e5',\n"
        "             '110':'#fdd835', '101':'#ab47bc', '011':'#26c6da', '111':'#f2f2f2' }[k]; }\n",
        1, "JS：新增 objC 状态与颜色物理")

# ---- JS：重写 drawObj ----
OLD_DRAWOBJ = """  function drawObj(){
    const ax = W / 2, ay = H / 2;
    // 光从左侧来
    let apple, stem, glow, noteKey;
    if(light === 'white'){ apple = '#e53935'; stem = '#5d4037'; noteKey = 'disp.note.white'; glow = 'rgba(255,255,255,0.25)'; }
    else if(light === 'red'){ apple = '#e53935'; stem = '#5d4037'; noteKey = 'disp.note.red'; glow = 'rgba(255,80,80,0.5)'; }
    else if(light === 'green'){ apple = '#4a2c28'; stem = '#3d2b20'; noteKey = 'disp.note.green'; glow = 'rgba(80,255,80,0.35)'; }
    else { apple = '#35262e'; stem = '#3d2b20'; noteKey = 'disp.note.blue'; glow = 'rgba(80,80,255,0.35)'; }
    // 环境光
    ctx.save();
    const g = ctx.createRadialGradient(80, ay, 10, 80, ay, 400);
    g.addColorStop(0, glow); g.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    ctx.restore();
    drawApple(ax, ay, 72, apple, stem);
    labelAt(ctx, ax - 20, ay + 108, '红苹果', P.mark, 14);
    labelAt(ctx, 24, 26, '光源：' + ({ white:'白光', red:'红光', green:'绿光', blue:'蓝光' }[light]), P.fdot, 14);
    $('verdict-disp').innerHTML =
      '<span class="tag" style="background:#ff7043;color:#06202b">' + T('v.disp.obj.tag') + '</span><br>' +
      T(noteKey) + '。<br>' +
      T('v.disp.obj.body');
  }"""
NEW_DRAWOBJ = """  function drawObj(){
    const ax = W / 2, ay = H / 2;
    const seen = seenColor();
    const fill  = seenHex();
    const stem  = (seen.key === '000') ? '#241b16' : '#5d4037';
    const glow  = L_GLOW[light] || L_GLOW.white;
    // 环境光（从左侧照来）
    ctx.save();
    const g = ctx.createRadialGradient(80, ay, 10, 80, ay, 400);
    g.addColorStop(0, glow); g.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    ctx.restore();
    drawApple(ax, ay, 72, fill, stem);
    labelAt(ctx, 24, 26, '照射光：' + (L_NAME[light] || '白光'), P.fdot, 14);
    // 左下：本色色块 + 两行说明
    ctx.save();
    ctx.fillStyle = OC_HEX[objC] || OC_HEX.red;
    ctx.strokeStyle = P.axis; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.rect(ax - 168, ay + 86, 22, 16); ctx.fill(); ctx.stroke();
    ctx.restore();
    labelAt(ctx, ax - 138, ay + 99, '物体本色：' + (OC_NAME[objC] || '红'), P.mark, 14);
    labelAt(ctx, ax - 168, ay + 126, '看到的颜色：' + seen.zh, P.mark, 14);
    const why = (seen.key === '000') ? 'disp.why.black'
              : (light === 'white' ? 'disp.why.white' : 'disp.why.mono');
    const KEY2EN = { '000':'black', '100':'red', '010':'green', '001':'blue',
                     '110':'yellow', '101':'magenta', '011':'cyan', '111':'white' };
    $('verdict-disp').innerHTML =
      '<span class="tag" style="background:#ff7043;color:#06202b">' + T('v.disp.obj.tag') + '</span><br>' +
      T('disp.pc.' + (KEY2EN[seen.key] || 'black')) + '<br>' +
      T(why) + '<br>' +
      T('v.disp.obj.body');
  }"""
assert OLD_DRAWOBJ in s, "[FAIL] 未能定位原 drawObj"
s = rep(s, OLD_DRAWOBJ, NEW_DRAWOBJ, 1, "JS：重写 drawObj（本色+照射光→看到的颜色）")

# ---- JS：本体色按钮监听 ----
s = rep(s,
        "  document.querySelectorAll('#disp-light .sec').forEach(b => b.addEventListener('click', () => {",
        "  /* V6.4.9：「物体本色」选择 */\n"
        "  document.querySelectorAll('#disp-obj-color .sec').forEach(b => b.addEventListener('click', () => {\n"
        "    document.querySelectorAll('#disp-obj-color .sec').forEach(x => x.classList.remove('active'));\n"
        "    b.classList.add('active');\n"
        "    objC = b.dataset.oc;\n"
        "    render();\n"
        "  }));\n"
        "  document.querySelectorAll('#disp-light .sec').forEach(b => b.addEventListener('click', () => {",
        1, "JS：新增「物体本色」按钮监听")

# ---- JS：数据记录（物体颜色行） ----
s = rep(s,
        "      const LM = { white: '白光', red: '红光', green: '绿光', blue: '蓝光' };\n"
        "      return ['物体颜色', '照射「红苹果」：' + (LM[light] || light),\n"
        "              light === 'red' ? '呈红色（红色光被反射进入眼睛）' : '呈黑色（红色光被物体吸收，无光进入眼睛）'];",
        "      const LM = { white: '白光', red: '红光', green: '绿光', blue: '蓝光' };\n"
        "      const oc = OC_NAME[objC] || '红';\n"
        "      return ['物体颜色', '物体本色：' + oc + '；照射光：' + (LM[light] || light),\n"
        "              '看到的颜色：' + seenColor().zh +\n"
        "              (seenColor().key === '000' ? '（本色光被全部吸收，无光进入眼睛）'\n"
        "                                         : '（本色光被反射进入眼睛）')];",
        1, "JS：数据记录改为「本色 / 照射光 / 看到的颜色」")

# ============================================================
# ③ 版本号四处同步 + 更新日志
# ============================================================
s = rep(s, "var BUILD = 'v6.4.8'", "var BUILD = 'v6.4.9'", 1, "版本：BUILD")
s = rep(s, "    return 'v6.4.8';", "    return 'v6.4.9';", 1, "版本：报告兜底 RPT_BUILD")
s = rep(s,
        '<div class="ver-badge" title="光学交互实验室 V6.4.8 · 顶栏设置紧贴按钮簇，修掉右上角空白。">v6.4.8</div>',
        '<div class="ver-badge" title="光学交互实验室 V6.4.9 · 直线传播调节栏移到画布下，物体颜色可调。">v6.4.9</div>',
        1, "版本：右下角角标（title + 文本）")
s = rep(s,
        '      <div class="log-item cur">\n'
        '        <div class="log-head"><span class="log-ver">V6.4.8</span><span class="log-date">2026-09-18</span></div>\n'
        '        <p>修顶栏设置按钮与按钮簇间的空白。</p>\n'
        '      </div>',
        '      <div class="log-item cur">\n'
        '        <div class="log-head"><span class="log-ver">V6.4.9</span><span class="log-date">2026-09-18</span></div>\n'
        '        <p>直线传播调节栏移下，物体颜色可调。</p>\n'
        '      </div>\n'
        '      <div class="log-item">\n'
        '        <div class="log-head"><span class="log-ver">V6.4.8</span><span class="log-date">2026-09-18</span></div>\n'
        '        <p>修顶栏设置按钮与按钮簇间的空白。</p>\n'
        '      </div>',
        1, "更新日志：插入 V6.4.9 首条")

# ============================================================
# 硬校验
# ============================================================
closes1 = len(re.findall(r"</script(?=[\s>/])", s))
opens1 = len(re.findall(r"<script(?=[\s>/])", s))
assert closes1 == closes0, "[FAIL] 脚本收尾标签字面量数变了: %d -> %d" % (closes0, closes1)
assert opens1 == opens0, "[FAIL] 脚本开标签数变了: %d -> %d" % (opens0, opens1)
assert s.count("disp.note.") == 0, "[FAIL] 旧 disp.note.* 仍有残留"
# 注：知识图谱正文里「红苹果」是教学内容（例题/易错点），必须保留；只清掉界面与画布上的旧写法
assert s.count('照射「红苹果」') == 0, "[FAIL] 旧的照射光标签仍有残留"
assert s.count("'红苹果', P.mark") == 0, "[FAIL] 画布上的旧物体标签仍有残留"
assert s.count("'红苹果") == 3, "[FAIL] 知识图谱里 3 处「红苹果」应原样保留，实际 %d" % s.count("'红苹果")
assert s.count("disp-obj-color") == 3, "[FAIL] disp-obj-color 应为 3 处（1 DOM + 2 JS 选择器），实际 %d" % s.count("disp-obj-color")
assert s.count("v6.4.8") == 0, "[FAIL] 小写 v6.4.8 残留: %d" % s.count("v6.4.8")
assert s.count("v6.4.9") == 3, "[FAIL] 小写 v6.4.9 应为 3 处，实际 %d" % s.count("v6.4.9")
assert s.count("V6.4.9") == 5, "[FAIL] 大写 V6.4.9 应为 5 处（3 注释 + 更新日志 + 角标 title），实际 %d" % s.count("V6.4.9")
assert s.count("V6.4.8") == V648_BEFORE - 1, "[FAIL] V6.4.8 注释数异常: %d -> %d" % (V648_BEFORE, s.count("V6.4.8"))
assert s.count('id="line-mode"') == 1 and s.count('id="line-reset"') == 1, "[FAIL] 直线传播控件 id 异常"

# ---- DOM 嵌套体检（★ 上一轮就是漏了这一步：多加一个 </div> 把 .right 顶出 .stage） ----
import importlib.util, sys as _sys
_spec = importlib.util.spec_from_file_location("v649s", os.path.join(BASE, "v649_structure.py"))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
_t = _mod.Tree()
_t.feed(s[:s.find('window.__S3D_LENS__')])
_bad = [(p, par) for p, par in _t.section_parents if par != ".wrap"]
assert len(_t.section_parents) == 12, "[FAIL] .panel 数量应为 12，实际 %d" % len(_t.section_parents)
assert not _bad, "[FAIL] 有面板掉出 .wrap：%s" % _bad
assert _t.parent.get("disp-rgb-ctrl") == ".ctrl", \
    "[FAIL] #disp-rgb-ctrl 父级应为 .ctrl，实际 %s" % _t.parent.get("disp-rgb-ctrl")
assert _t.parent.get("disp-obj-ctrl") == ".ctrl", \
    "[FAIL] #disp-obj-ctrl 父级应为 .ctrl，实际 %s" % _t.parent.get("disp-obj-ctrl")
assert _t.parent.get("disp-light") == "#disp-obj-ctrl", \
    "[FAIL] #disp-light 应仍在 #disp-obj-ctrl 内，实际 %s" % _t.parent.get("disp-light")
assert not _t.errors, "[FAIL] 未匹配收尾标签：%s" % _t.errors[:5]
LOG.append("OK  %-52s %s" % ("DOM 嵌套体检", "12 个面板父级均为 .wrap；obj/rgb 组均为 .ctrl 子级"))

open(DST, "w", encoding="utf-8", newline="").write(s)
n1 = os.path.getsize(DST)

print("\n".join(LOG))
print("-" * 66)
print("脚本标签：opens %d -> %d, closes %d -> %d" % (opens0, opens1, closes0, closes1))
print("源 %s (%d B) -> 产物 %s (%d B, %+d B)" % (os.path.basename(SRC), n0, os.path.basename(DST), n1, n1 - n0))
