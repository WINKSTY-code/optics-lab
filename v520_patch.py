# -*- coding: utf-8 -*-
"""
V5.1.3 -> V5.2.0
「直线传播」实验新增第三个模式「日食与月食」，把独立的 3D 立体演示内嵌进来。

设计要点
--------
1. 内嵌方式：iframe + srcdoc。
   演示是自带一整套设计系统的单文件（内联 three.js，690KB）：它有
   html,body{overflow:hidden}、#stage{position:fixed;inset:0}、自己的
   :root 变量与 canvas 尺寸逻辑，直接内联会与本页的 :root / body / canvas
   规则正面冲突；iframe 自带文档边界，样式与脚本零污染。
   srcdoc 不依赖任何 URL，双击 file:// 打开也能正常显示。
2. 懒挂载：只有第一次切到「日食与月食」模式时才注入 690KB 源码，
   首屏速度与既有 10 个实验完全不受影响。
3. 数据记录：3D 演示是独立场景（跨文档取不到内部读数），
   本模式下 getRow() 返回 null → 不落表，避免把无关读数记进「直线传播」的数据表。
4. 全屏：原生 Fullscreen API（顶层渲染，不受祖先 transform/zoom 影响），
   不支持时降级为 position:fixed 覆盖层。

所有文本替换都断言命中次数，任一处不符立即中止，绝不静默产出半成品。
"""
import json
import os
import re
import shutil

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "光学交互实验室_AI_v5.1.3.html")
DST = os.path.join(BASE, "光学交互实验室_AI_v5.2.0.html")
DEMO = r"C:\Users\Administrator\Desktop\日食与月食 3D演示.html"

LOG = []


def rep(s, old, new, n=1, label=""):
    c = s.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    LOG.append("OK   %-42s x%d" % (label, c))
    return s.replace(old, new)


# ===========================================================================
# 0. 读取
# ===========================================================================
s = open(SRC, encoding="utf-8").read()
n0 = os.path.getsize(SRC)
demo = open(DEMO, encoding="utf-8").read()
demo_bytes = os.path.getsize(DEMO)
LOG.append("源 %s (%d B)" % (os.path.basename(SRC), n0))
LOG.append("演示 %s (%d B)" % (os.path.basename(DEMO), demo_bytes))

# 演示源码里不能出现这些序列，否则要么 HTML 脚本标签被提前闭合，
# 要么 JS 字符串字面量被破坏。
assert demo.count("</script") == 3, "演示里的 </script 数量异常"
assert "<!--" not in demo, "演示含 <!--（会触发 script data escaped 状态）"
assert "\u2028" not in demo and "\u2029" not in demo, "演示含 U+2028/2029"

# JSON 转义 = 合法的 JS 字符串字面量；再把 </script 拆开写
esc = json.dumps(demo, ensure_ascii=False).replace("</script", "<\\/script")
# round-trip 自证无损
assert json.loads(esc) == demo, "转义后无法无损还原演示源码"
LOG.append("OK   演示源码转义无损                       %d -> %d B" % (demo_bytes, len(esc.encode())))


# ===========================================================================
# 1. 版本号（角标 + BUILD 常量 + 报告模块自带常量，三处同步）
# ===========================================================================
s = rep(s,
        "var BUILD = 'v5.1.3', MAX_SHOW = 3",
        "var BUILD = 'v5.2.0', MAX_SHOW = 3",
        label="BUILD 常量")

s = rep(s,
        "    return 'v5.1.3';\n  })();",
        "    return 'v5.2.0';\n  })();",
        label="RPT_BUILD 兜底常量")

s = rep(s,
        '<div class="ver-badge" title="光学交互实验室 V5.1.3 · 数据记录行新增实验报告跳转按钮 · 导出按钮精简">v5.1.3</div>',
        '<div class="ver-badge" title="光学交互实验室 V5.2.0 · 直线传播新增「日食与月食」3D 立体演示（可全屏）">v5.2.0</div>',
        label="版本角标")


# ===========================================================================
# 2. 更新日志：新增 V5.2.0，并把 V5.1.3 的 cur 摘掉
# ===========================================================================
OLD_LOG_CUR = '      <div class="log-item cur">\n        <div class="log-head"><span class="log-ver">V5.1.3</span>'
NEW_LOG = (
    '      <div class="log-item cur">\n'
    '        <div class="log-head"><span class="log-ver">V5.2.0</span><span class="log-date">2026-09-16</span></div>\n'
    '        <p>「直线传播」实验新增第三个模式<strong>「日食与月食」</strong>：把一份独立的<strong>3D 立体演示</strong>'
    '（日地月系统 · 本影 / 半影光锥 · 食相时间轴 · 观测窗遮挡比例，内联 three.js、离线可用）以独立文档边界内嵌进本页，'
    '与「影子形成」「小孔成像」并列切换，支持<strong>全屏放大</strong>观察；3D 演示为自带场景，不参与数据记录。</p>\n'
    '      </div>\n'
    '      <div class="log-item">\n'
    '        <div class="log-head"><span class="log-ver">V5.1.3</span>'
)
s = rep(s, OLD_LOG_CUR, NEW_LOG, label="更新日志新增 V5.2.0")


# ===========================================================================
# 3. i18n 词条
# ===========================================================================
s = rep(s,
        "'line.m.pinhole': {zh:'小孔成像', zht:'小孔成像', en:'Pinhole Image'},",
        "'line.m.pinhole': {zh:'小孔成像', zht:'小孔成像', en:'Pinhole Image'},\n"
        "'line.m.eclipse': {zh:'日食与月食', zht:'日食與月食', en:'Eclipses'},",
        label="i18n line.m.eclipse")

ECL_KEYS = (
    "\n/* ---- V5.2.0 直线传播 · 日食与月食 3D 演示 ---- */\n"
    "'ecl.title':      {zh:'日食与月食 · 3D 立体演示', zht:'日食與月食 · 3D 立體演示', en:'Solar & Lunar Eclipses · 3D'},\n"
    "'ecl.badge':      {zh:'独立 3D 场景', zht:'獨立 3D 場景', en:'Standalone 3D view'},\n"
    "'ecl.fs':         {zh:'全屏演示', zht:'全螢幕演示', en:'Full screen'},\n"
    "'ecl.exit':       {zh:'← 退出全屏', zht:'← 退出全螢幕', en:'← Exit full screen'},\n"
    "'ecl.tip':        {zh:'拖动底部时间轴看日食 / 月食的全过程；可全屏放大观察', zht:'拖動底部時間軸看日食 / 月食的全過程；可全螢幕放大觀察', en:'Drag the timeline to watch the whole eclipse; use full screen to enlarge it.'},\n"
    "'ecl.tipFs':      {zh:'按 Esc 或点左侧按钮退出全屏', zht:'按 Esc 或點左側按鈕退出全螢幕', en:'Press Esc or the button on the left to exit full screen'},\n"
    "'ecl.note':       {zh:'3D 演示不参与数据记录', zht:'3D 演示不參與資料記錄', en:'3D demo is not recorded'},"
)
s = rep(s,
        "'line.hole.l':    {zh:'大', zht:'大', en:'Large'},",
        "'line.hole.l':    {zh:'大', zht:'大', en:'Large'}," + ECL_KEYS,
        label="i18n ecl.* 词条")

LINE_ECL_KEYS = (
    "'v.line.eclipse.tag': {zh:'日食与月食', zht:'日食與月食', en:'Eclipses'},\n"
    "'v.line.eclipse': {"
    "zh:'太阳的光沿<b>直线</b>传播，遇到不透明的天体就被挡住，在后方留下<b>影子</b>。<br>"
    "· <b>日食</b>：月球运行到太阳与地球<b>之间</b>，月球的影子落在地球上，处在影子区的人看到太阳被遮住"
    "（初亏 → 部分食 → 食甚·全食 → 再次部分食 → 复圆）。<br>"
    "· <b>月食</b>：地球运行到太阳与月球<b>之间</b>，射向月球的光被地球挡住，月球进入地球的影子"
    "（半影食始 → 初亏 → 食甚 → 复圆 → 半影食终）。<br>"
    "拖动下方时间轴，观察日、地、月三者的位置关系如何决定食相。', "
    "zht:'太陽的光沿<b>直線</b>傳播，遇到不透明的天體就被擋住，在後方留下<b>影子</b>。<br>"
    "· <b>日食</b>：月球運行到太陽與地球<b>之間</b>，月球的影子落在地球上，處在影子區的人看到太陽被遮住"
    "（初虧 → 部分食 → 食甚·全食 → 再次部分食 → 復圓）。<br>"
    "· <b>月食</b>：地球運行到太陽與月球<b>之間</b>，射向月球的光被地球擋住，月球進入地球的影子"
    "（半影食始 → 初虧 → 食甚 → 復圓 → 半影食終）。<br>"
    "拖動下方時間軸，觀察日、地、月三者的位置關係如何決定食相。', "
    "en:'Sunlight travels in <b>straight lines</b>; an opaque body blocks it and casts a <b>shadow</b> behind.<br>"
    "· <b>Solar eclipse</b>: the Moon moves <b>between</b> the Sun and the Earth, its shadow falls on the Earth, "
    "and people inside the shadow see the Sun blocked.<br>"
    "· <b>Lunar eclipse</b>: the Earth moves <b>between</b> the Sun and the Moon; light heading for the Moon is blocked "
    "and the Moon enters the Earth&#39;s shadow.<br>"
    "Drag the timeline below to see how the positions of Sun, Earth and Moon decide each phase.'},\n"
)
s = rep(s,
        "'v.line.shadow.tag': {zh:'光沿直线传播'",
        LINE_ECL_KEYS + "'v.line.shadow.tag': {zh:'光沿直线传播'",
        label="i18n v.line.eclipse")


# ===========================================================================
# 4. 结构：模式按钮 + 3D 演示内嵌容器 + 数据面板提示
# ===========================================================================
s = rep(s,
        '        <button class="sec" data-m="pinhole" data-i18n="line.m.pinhole">小孔成像</button>',
        '        <button class="sec" data-m="pinhole" data-i18n="line.m.pinhole">小孔成像</button>\n'
        '        <button class="sec" data-m="eclipse" data-i18n="line.m.eclipse">日食与月食</button>',
        label="第三个模式按钮")

CV_LINE = '<canvas id="cv-line" width="920" height="420" role="img" aria-label="光的直线传播实验示意图：影子形成与小孔成像两种模式，结论见右侧判定卡片"></canvas>'
ECL_HOST = CV_LINE + """
    <!-- V5.2.0：日食与月食 3D 演示（独立 iframe，首次进入本模式时才注入源码） -->
    <div class="ecl-host" id="line-eclHost" hidden>
      <div class="ecl-head">
        <b class="ecl-title" data-i18n="ecl.title">日食与月食 · 3D 立体演示</b>
        <span class="ecl-badge" data-i18n="ecl.badge">独立 3D 场景</span>
      </div>
      <div class="ecl-frame" id="line-eclFrame">
        <div class="ecl-fsbar">
          <button type="button" class="sec" id="line-eclExit" data-i18n="ecl.exit">← 退出全屏</button>
          <span class="ecl-tip" data-i18n="ecl.tipFs">按 Esc 或点左侧按钮退出全屏</span>
        </div>
        <iframe id="line-eclIfr" title="日食与月食 3D 演示"></iframe>
      </div>
      <div class="ecl-bar">
        <button type="button" class="sec" id="line-eclFs" data-i18n="ecl.fs">全屏演示</button>
        <span class="ecl-tip" data-i18n="ecl.tip">拖动底部时间轴看日食 / 月食的全过程；可全屏放大观察</span>
      </div>
    </div>"""
s = rep(s, CV_LINE, ECL_HOST, label="内嵌 3D 演示容器")

s = rep(s,
        '<div class="data-head"><b data-i18n="data.title">数据记录</b><label class="rec-auto" title="停止操作 1 秒后自动记录一行"><input type="checkbox" id="line-recAuto" checked>',
        '<div class="data-head"><b data-i18n="data.title">数据记录</b><span class="ecl-note" id="line-eclNote" hidden data-i18n="ecl.note">3D 演示不参与数据记录</span><label class="rec-auto" title="停止操作 1 秒后自动记录一行"><input type="checkbox" id="line-recAuto" checked>',
        label="数据面板 3D 提示")


# ===========================================================================
# 5. MODULES.line：模式分流 + 阶段同步 + 不落表
# ===========================================================================
OLD_OBJ_H = "  let uCm = 30, vCm = 30, hole = 2, objLvl = 0;\n  const OBJ_H = 64;\n"
NEW_HELPERS = OLD_OBJ_H + """
  /* V5.2.0：第三个模式「日食与月食」----------------------------------------
     把独立的 3D 立体演示（单文件，内联 three.js）以 iframe/srcdoc 内嵌到本实验：
       · 画布与 3D 演示互斥显示，靠 window.ECL.setActive() 通知 ECL 模块挂载 / 收起；
       · 3D 演示是自带文档边界的外部场景（跨文档取不到内部读数），
         因此本模式下 getRow() 返回 null → 不落表，数据面板同时给出提示。  */
  function eclOn(){ return mode === 'eclipse'; }
  function syncStage(){
    const on = eclOn();
    cv.style.display = on ? 'none' : '';
    const rs = $('line-reset'); if (rs) rs.style.display = on ? 'none' : '';
    if (window.ECL && window.ECL.setActive) window.ECL.setActive(on);
  }
  function renderEclipse(){
    P = PAL[THEME];
    syncStage();
    $('verdict-line').innerHTML =
      '<span class="tag" style="background:#8ea6d8;color:#06202b">' + T('v.line.eclipse.tag') + '</span><br>' +
      T('v.line.eclipse');
  }
"""
s = rep(s, OLD_OBJ_H, NEW_HELPERS, label="line 模块新增 syncStage/renderEclipse")

OLD_RENDER_HEAD = """  function render(){
    P = PAL[THEME];
    ctx.fillStyle = P.bg; ctx.fillRect(0, 0, W, H);
    ctx.save();
    ctx.strokeStyle = P.mark; ctx.lineWidth = 1.5; ctx.setLineDash([8, 6]);"""
NEW_RENDER_HEAD = """  function render(){
    // V5.2.0：3D 演示模式不画画布，改为同步「画布 / 3D 演示」的显隐并刷新结论卡
    if (eclOn()){ renderEclipse(); return; }
    P = PAL[THEME];
    ctx.fillStyle = P.bg; ctx.fillRect(0, 0, W, H);
    ctx.save();
    ctx.strokeStyle = P.mark; ctx.lineWidth = 1.5; ctx.setLineDash([8, 6]);"""
s = rep(s, OLD_RENDER_HEAD, NEW_RENDER_HEAD, label="render() 增加 3D 模式分流")

OLD_MODE_SWITCH = """    document.querySelectorAll('#tab-line .slider-g').forEach(g => {
      g.style.display = g.dataset.g === mode ? '' : 'none';
    });
    render();
  }));"""
NEW_MODE_SWITCH = """    document.querySelectorAll('#tab-line .slider-g').forEach(g => {
      g.style.display = g.dataset.g === mode ? '' : 'none';
    });
    syncStage();
    render();
  }));"""
s = rep(s, OLD_MODE_SWITCH, NEW_MODE_SWITCH, label="模式切换同步舞台")

OLD_GETROW = """    () => {
      if (mode === 'pinhole'){"""
NEW_GETROW = """    () => {
      // V5.2.0：3D 演示为独立场景，不参与数据记录（返回 null → REC.commit 直接跳过）
      if (mode === 'eclipse') return null;
      if (mode === 'pinhole'){"""
s = rep(s, OLD_GETROW, NEW_GETROW, label="getRow 在 3D 模式返回 null")


# ===========================================================================
# 6. 追加：演示源码 + 样式 + ECL 逻辑（放在文档末尾 </body> 之前）
# ===========================================================================
ECL_CSS = """
<style>
/* ==========================================================================
   V5.2.0 · 直线传播 · 日食与月食 3D 演示（内嵌 iframe）
   深色"影院"容器：演示自带深空配色，浅色（纸黄）主题下也用深底衬托，
   靠圆角 + 描边 + 阴影与页面其余部分区分。
   ========================================================================== */
.ecl-host{width:100%;display:flex;flex-direction:column;gap:8px;}
.ecl-host[hidden]{display:none !important;}
.ecl-head{display:flex;align-items:center;gap:8px;flex-wrap:wrap;}
.ecl-head .ecl-title{font-size:15px;}
.ecl-badge{font-size:11px;font-weight:700;letter-spacing:.5px;color:#cfe0ff;background:#1d2b46;
  border:1px solid rgba(122,156,220,.4);border-radius:99px;padding:2px 9px;}
.ecl-frame{position:relative;width:100%;height:58vh;min-height:340px;max-height:620px;
  border-radius:10px;overflow:hidden;background:#04060e;border:var(--hard-border);
  box-shadow:var(--shadow-lg);}
.ecl-frame > iframe{display:block;width:100%;height:100%;border:0;background:#04060e;}
.ecl-fsbar{display:none;align-items:center;gap:10px;padding:8px 12px;background:#070c18;
  border-bottom:1px solid rgba(122,156,220,.28);color:#e7eefc;font-size:13px;flex:0 0 auto;}
.ecl-fsbar .ecl-tip{color:#93a7ca;font-size:12px;}
.ecl-frame.ecl-live{display:flex;flex-direction:column;}
.ecl-frame.ecl-live .ecl-fsbar{display:flex;}
.ecl-frame.ecl-live > iframe{flex:1 1 auto;height:auto;min-height:0;}
/* 降级全屏（浏览器不支持对 div 调用 requestFullscreen 时使用） */
.ecl-frame.ecl-fs{position:fixed;inset:0;z-index:900;width:auto;height:auto;max-height:none;
  min-height:0;border-radius:0;border:0;box-shadow:none;}
body.ecl-lock{overflow:hidden;}
.ecl-bar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.ecl-bar .ecl-tip{color:var(--muted);font-size:12px;line-height:1.5;}
.ecl-note{margin-left:auto;font-size:12px;color:var(--muted);white-space:nowrap;}
.ecl-note[hidden]{display:none !important;}
/* 三个模式按钮在窄屏 / 放大字号（A＋）下靠 .seg 自带的 flex-wrap 换行；
   这里只禁止按钮内部的标签被折成两行（模式标签折行比整体换行更难看） */
#line-mode .sec{white-space:nowrap;}
</style>
"""

ECL_LOGIC = """
<script>
/* ==========================================================================
   V5.2.0 · 直线传播 · 日食与月食 3D 演示的挂载与全屏
   --------------------------------------------------------------------------
   · 上方的 <script> 只保存演示的单文件源码（window.__ECL_HTML__）；
   · 本脚本负责：懒挂载（首次进入该模式才 setAttribute('srcdoc')）、
     全屏进出（原生 Fullscreen API，失败降级为页面内固定覆盖层）。
   · 演示与主页面各自独立文档，样式 / 脚本零污染，既有 10 个实验行为不变。
   ========================================================================== */
(function(){
  'use strict';
  var SRC = window.__ECL_HTML__ || '';
  var host    = document.getElementById('line-eclHost');
  var frame   = document.getElementById('line-eclFrame');
  var ifr     = document.getElementById('line-eclIfr');
  var fsBtn   = document.getElementById('line-eclFs');
  var exitBtn = document.getElementById('line-eclExit');
  var note    = document.getElementById('line-eclNote');
  if (!host || !frame || !ifr) return;      // 结构被改动时静默退出，不影响其它功能

  var mounted = false, fallbackFs = false;

  function tt(k){
    try { return (typeof T === 'function') ? T(k) : k; } catch(e){ return k; }
  }

  /* ---------- 懒挂载 ---------- */
  function mount(){
    if (mounted) return true;
    if (!SRC){ console.warn('[ECL] 演示源码缺失，3D 演示无法挂载'); return false; }
    try { ifr.setAttribute('srcdoc', SRC); }
    catch(e){ console.warn('[ECL] srcdoc 注入失败:', e && e.message); return false; }
    mounted = true;
    return true;
  }

  /* ---------- 全屏 ---------- */
  function fsElement(){
    return document.fullscreenElement || document.webkitFullscreenElement || null;
  }
  function live(){ return !!fsElement() || fallbackFs; }
  function syncFsUI(){
    var on = live();
    frame.classList.toggle('ecl-live', on);
    document.body.classList.toggle('ecl-lock', on);
    if (fsBtn) fsBtn.textContent = tt(on ? 'ecl.exit' : 'ecl.fs');
  }
  function fallbackEnter(err){
    if (err) console.warn('[ECL] 原生全屏不可用，改用页面内全屏:', (err && err.message) || err);
    fallbackFs = true;
    frame.classList.add('ecl-fs');
    syncFsUI();
  }
  function enterFs(){
    var req = frame.requestFullscreen || frame.webkitRequestFullscreen;
    if (req){
      try {
        var p = req.call(frame);
        /* 必须接住 reject：否则会被页面顶部的「未处理 Promise 拒绝」看门狗记成一次错误 */
        if (p && p['catch']) p['catch'](function(e){ fallbackEnter(e); });
      } catch(e){ fallbackEnter(e); }
    } else {
      fallbackEnter(null);
    }
    syncFsUI();
  }
  function exitFs(){
    var native = !!(document.fullscreenElement || document.webkitFullscreenElement);
    fallbackFs = false;
    frame.classList.remove('ecl-fs');
    /* 只在确实处于原生全屏时才调 exitFullscreen：非全屏状态下调用会返回
       「Document not active」的 rejected promise（V5.2.0 首轮 e2e 实测到）。 */
    if (native){
      try {
        var p = document.exitFullscreen ? document.exitFullscreen()
              : (document.webkitExitFullscreen ? document.webkitExitFullscreen() : null);
        if (p && p['catch']) p['catch'](function(){});
      } catch(e){}
    }
    syncFsUI();
  }
  function toggleFs(){ if (live()) exitFs(); else enterFs(); }
  if (fsBtn)   fsBtn.addEventListener('click', toggleFs);
  if (exitBtn) exitBtn.addEventListener('click', exitFs);
  document.addEventListener('fullscreenchange', syncFsUI);
  document.addEventListener('webkitfullscreenchange', syncFsUI);
  /* 焦点回到主文档时 Esc 才收得到；焦点在 iframe 内时靠左侧「退出全屏」按钮 */
  document.addEventListener('keydown', function(e){
    if (e.key === 'Escape' && fallbackFs) exitFs();
  });
  /* 点到别的实验页就退出全屏，避免"全屏罩着却已经换了实验" */
  document.addEventListener('click', function(e){
    var tb = (e.target && e.target.closest) ? e.target.closest('.tab-btn') : null;
    if (tb && tb.dataset && tb.dataset.tab !== 'line' && live()) exitFs();
  }, true);
  /* 切语言后 applyLang 会把按钮文案重置，这里按当前全屏状态刷回来 */
  var lb = document.getElementById('langBtn');
  if (lb) lb.addEventListener('click', function(){ setTimeout(syncFsUI, 0); });

  /* ---------- 对外接口（由 MODULES.line 的模式切换调用） ---------- */
  window.ECL = {
    mount: mount,
    exitFs: exitFs,
    isMounted: function(){ return mounted; },
    setActive: function(on){
      on = !!on;
      if (!on && live()) exitFs();
      host.hidden = !on;
      if (note) note.hidden = !on;
      if (on) mount();
    }
  };
  syncFsUI();
})();
</script>
"""

NEW_TAIL = (
    "\n<script>\n"
    "/* ==========================================================================\n"
    "   V5.2.0 · 直线传播实验内嵌的「日食与月食 3D 演示」单文件源码（原样保存）\n"
    "   来源：日食与月食 3D演示.html（自包含：内联 three.js + OrbitControls + 演示逻辑，\n"
    "        无任何外链、无网络请求、无本地存储依赖，离线可用）\n"
    "   仅一处改写：源码里所有脚本收尾标签都插入了反斜杠转义（写成反斜杠 + /script），\n"
    "        避免提前闭合本页的脚本标签 —— 本注释也刻意不写出该字面量，同一个坑只踩一次。\n"
    "   ========================================================================== */\n"
    "window.__ECL_HTML__ = " + esc + ";\n"
    "</script>\n" + ECL_CSS + ECL_LOGIC + "\n"
)

s = rep(s, "\n</body>\n</html>\n", NEW_TAIL + "</body>\n</html>\n", label="追加演示源码 + 样式 + ECL 逻辑")


# ===========================================================================
# 7. 收尾自检 + 落盘
# ===========================================================================
left = s.count("v5.1.3")
assert left == 0, "[FAIL] 仍残留 %d 处 v5.1.3 版本引用" % left
LOG.append("OK   %-42s x%d" % ("版本号三处全部同步", 3))

# 🔥 硬校验：脚本收尾标签的字面量个数必须等于真实 script 元素个数。
#    浏览器在 script data 状态遇到「< / s c r i p t」+（空白 | / | >）就会闭合标签，
#    因此注释 / 字符串里出现该字面量 = 整页脚本链断裂（V5.2.0 首轮实测踩到）。
#    注意别用 r"</script>" 做检查：它漏掉「</script 」这种带空格的写法。
closes = re.findall(r"</script(?=[\s>/])", s)
opens = re.findall(r"<script(?=[\s>])", s)
LOG.append("OK   %-42s 收尾标签 %d 个 / 开标签 %d 个（含内嵌源码里的 3 个开标签）"
           % ("脚本标签字面量校验", len(closes), len(opens)))
assert len(closes) == 11, "[FAIL] 正文里出现 %d 处脚本收尾标签字面量，应为 11" % len(closes)

# 源文件是 CRLF；文本模式读入已归一为 \n，这里写回 CRLF 保持与历史版本一致
open(DST, "w", encoding="utf-8", newline="\r\n").write(s)
n1 = os.path.getsize(DST)

print("\n".join(LOG))
print("-" * 70)
print("源 %s (%d B)" % (os.path.basename(SRC), n0))
print("产物 %s (%d B, %+d B)" % (os.path.basename(DST), n1, n1 - n0))
