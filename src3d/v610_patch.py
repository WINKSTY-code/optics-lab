# -*- coding: utf-8 -*-
"""
V6.1.0：由 v5.2.0 全量重建（= V6.0.0 三场景 + 本轮修订）
「光的反射 / 凸透镜成像 / 平面镜成像」三个实验各自内嵌一份独立的 3D 立体场景，
并在 2D 画布角落加一个悬浮的「2D ｜ 3D」切换按钮。2D 视图与既有功能完全不变。

每个 3D 场景都是自包含单文件（自带 three.js r147 + OrbitControls + 外壳），
经 JSON 转义后作为 JS 字符串塞进本页，首次切到 3D 时才注入 iframe 的 srcdoc。
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "..", "光学交互实验室_AI_v5.2.0.html")
DST = os.path.join(BASE, "..", "光学交互实验室_AI_v6.1.0.html")
S3D = os.path.join(BASE, "..", "src3d")

LOG = []


def rep(s, old, new, n=1, label=""):
    c = s.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    LOG.append("OK   %-46s x%d" % (label, c))
    return s.replace(old, new)


# ===========================================================================
# 0. 读入三个 3D 场景并转义
# ===========================================================================
SCENES = [
    ("refl", "3D_光的反射_可折转纸板.html", "__S3D_REFL__", "光的反射 · 3D 立体模型"),
    ("lens", "3D_凸透镜成像.html", "__S3D_LENS__", "凸透镜成像 · 3D 立体光锥"),
    ("mirror", "3D_平面镜像_棋子.html", "__S3D_MIRROR__", "平面镜成像 · 3D 立体模型"),
]
SCENES[2] = ("mirror", "3D_平面镜成像_棋子.html", "__S3D_MIRROR__", "平面镜成像 · 3D 立体模型")

ESC = {}
for key, fn, var, title in SCENES:
    p = os.path.join(S3D, fn)
    raw = open(p, encoding="utf-8").read()
    assert "<!--" not in raw, "%s 含 <!--" % fn
    e = json.dumps(raw, ensure_ascii=False).replace("</script", "<\\/script")
    assert json.loads(e) == raw, "%s 转义无法无损还原" % fn
    ESC[key] = (e, os.path.getsize(p), title)
    LOG.append("OK   %-46s %d B -> %d B" % ("转义 " + fn, os.path.getsize(p), len(e.encode())))

s = open(SRC, encoding="utf-8").read()
n0 = os.path.getsize(SRC)


# ===========================================================================
# 1. 三个面板各插入「2D｜3D」悬浮切换条 + 3D 框
# ===========================================================================
CANVAS = {
    "refl": '<canvas id="cv-refl" width="920" height="520" role="img" aria-label="光的反射实验示意图：可拖动改变入射角，入射角与反射角数值见右侧读数卡片"></canvas>',
    "mirror": '<canvas id="cv-mirr" width="920" height="520" role="img" aria-label="平面镜成像实验示意图：物距与像距相等，成正立等大的虚像，数值见右侧读数卡片"></canvas>',
    "lens": '<canvas id="cv-lens" width="920" height="520" role="img" aria-label="凸透镜成像实验示意图：可调节物距与焦距，像距、放大率与成像性质见右侧读数卡片"></canvas>',
}


def block(key):
    title = ESC[key][2]
    return ('<div class="s3d-stage">' + "\n" + CANVAS[key] + "\n"
            '        <!-- V6.1.0：2D / 3D 视图切换（悬浮在画布右下角）+ 独立 3D 场景 -->\n'
            '        <div class="s3d-bar" data-s3d="%s" role="group" aria-label="视图切换">\n'
            '          <button type="button" class="s3d-b is-on" data-m="2d" aria-pressed="true" data-i18n="s3d.2d">2D</button>\n'
            '          <button type="button" class="s3d-b" data-m="3d" aria-pressed="false" data-i18n="s3d.3d">3D</button>\n'
            '          <button type="button" class="s3d-b s3d-only3 s3d-fsb" data-i18n-title="s3d.fs" title="\u5168\u5c4f\u6f14\u793a" aria-label="\u5168\u5c4f\u6f14\u793a">'
            '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true">'
            '<path d="M4 9V4h5M20 15v5h-5M15 4h5v5M9 20H4v-5"/></svg></button>\n'
            '        </div>\n'
            '        <div class="s3d-frame" data-s3d="%s" hidden>\n'
            '          <div class="s3d-fsbar">\n'
            '            <button type="button" class="sec s3d-exit" data-i18n="s3d.exit">← 退出全屏</button>\n'
            '            <span class="s3d-fstip" data-i18n="s3d.fstip">按 Esc 或点左侧按钮退出全屏</span>\n'
            '          </div>\n'
            '          <iframe class="s3d-ifr" title="%s" aria-label="%s"></iframe>\n'
            '        </div>\n        </div>') % (key, key, title, title)


for key in ("refl", "mirror", "lens"):
    s = rep(s, CANVAS[key], block(key), label="插入 3D 切换条与 3D 框 · " + key)


# ===========================================================================
# 2. i18n 词条
# ===========================================================================
KEYS = (
    "\n/* ---- V6.0.0 2D / 3D 视图切换 ---- */\n"
    "'s3d.2d':   {zh:'2D', zht:'2D', en:'2D'},\n"
    "'s3d.3d':   {zh:'3D', zht:'3D', en:'3D'},\n"
    "'s3d.fs':   {zh:'全屏演示', zht:'全螢幕演示', en:'Full screen'},\n"
    "'s3d.exit': {zh:'← 退出全屏', zht:'← 退出全螢幕', en:'← Exit full screen'},\n"
    "'s3d.fstip':{zh:'按 Esc 或点左侧按钮退出全屏', zht:'按 Esc 或點左側按鈕退出全螢幕', en:'Press Esc or the left button to exit full screen'},\n"
    "'s3d.enter':{zh:'3D 立体演示', zht:'3D 立體演示', en:'3D view'},\n"
    "'s3d.fail': {zh:'3D 场景加载失败，已自动切回 2D 视图', zht:'3D 場景載入失敗，已自動切回 2D 視圖', en:'3D failed to load; switched back to 2D'},"
)
s = rep(s, "'line.m.pinhole': {zh:'小孔成像'", KEYS + "\n'line.m.pinhole': {zh:'小孔成像'", label="i18n s3d.* 词条")


# ===========================================================================
# 3. 版本号 + 更新日志
# ===========================================================================
s = rep(s, "var BUILD = 'v5.2.0', MAX_SHOW = 3", "var BUILD = 'v6.1.0', MAX_SHOW = 3", label="BUILD 常量")
s = rep(s, "    return 'v5.2.0';\n  })();", "    return 'v6.1.0';\n  })();", label="RPT_BUILD 兜底常量")
s = rep(s,
        '<div class="ver-badge" title="光学交互实验室 V5.2.0 · 直线传播新增「日食与月食」3D 立体演示（可全屏）">v5.2.0</div>',
        '<div class="ver-badge" title="光学交互实验室 V6.1.0 · 3D 场景修订：切换条移到画布右下角、点实验名不再退掉网页全屏、棋子可拖动、入射角可在 3D 内调节、光锥改为立体">v6.1.0</div>',
        label="版本角标")

OLD_LOG = '      <div class="log-item cur">\n        <div class="log-head"><span class="log-ver">V5.2.0</span>'
NEW_LOG = (
    '      <div class="log-item cur">\n'
    '        <div class="log-head"><span class="log-ver">V6.1.0</span><span class="log-date">2026-09-16</span></div>\n'
    '        <p>三个 3D 场景集中修订：<strong>2D ｜ 3D 切换条移到实验区右下角</strong>；'
    '<strong>修掉「点实验名会退掉网页全屏」</strong>（顶部自带的「全屏」按钮全屏的是整个页面，'
    '之前被误认成 3D 全屏一起退掉了）；平面镜成像的<strong>棋子可直接在 3D 里拖动</strong>'
    '（左右移动时虚像跟着一起动，前后移动会同步回 2D 的物距滑块）；光的反射把<strong>入射角也放进 3D 控制条</strong>；'
    '凸透镜的<strong>光锥改成真正的立体光锥</strong>（此前取样点只落在同一个竖直平面里，看着像一个扇面）；'
    '另修掉长时间动画每帧重建光路未释放显存的隐患。</p>\n'
    '      </div>\n'
    '      <div class="log-item">\n'
    '        <div class="log-head"><span class="log-ver">V6.0.0</span><span class="log-date">2026-09-16</span></div>\n'
    '        <p><strong>「光的反射 / 凸透镜成像 / 平面镜成像」三个实验各新增一个独立的 3D 立体场景</strong>，'
    '画布右上角悬浮 <strong>2D ｜ 3D</strong> 按钮一键切换（2D 视图与原有全部功能不变）。三个场景都按苏科版教材装置建模：'
    '<strong>可绕法线折转的纸板</strong>（折转后 F 板接不到反射光线 → 三线共面）、'
    '<strong>凸透镜的立体光锥</strong>（从烛焰发出的整束光会聚成倒立实像）、'
    '<strong>玻璃板与棋子找像</strong>（拖动棋子 B 与像重合，量出像距 = 物距）。'
    '三个场景各自内嵌一份 three.js，离线可用；切到 3D 时自动继承当前 2D 的物距 / 焦距 / 入射角，'
    '拖动任一滑块两边同步；支持全屏观察。</p>\n'
    '      </div>\n'
    '      <div class="log-item">\n'
    '        <div class="log-head"><span class="log-ver">V5.2.0</span>'
)
s = rep(s, OLD_LOG, NEW_LOG, label="更新日志新增 V6.0.0")


# ===========================================================================
# 4. 样式
# ===========================================================================
CSS = """
<style>
/* ==========================================================================
   V6.0.0 · 2D / 3D 视图切换
   切换按钮悬浮在 2D 画布右上角（不占布局、不改 2D 视图）；切到 3D 时
   画布与本列其它元素整体隐藏，同一块位置换成独立文档的 3D 场景框。
   ========================================================================== */
.s3d-stage{position:relative;}
.s3d-bar{position:absolute;bottom:10px;right:12px;z-index:4;display:inline-flex;
  border-radius:99px;overflow:hidden;background:var(--panel);border:var(--hard-border);
  box-shadow:0 2px 10px rgba(0,0,0,.20);}
.s3d-bar .s3d-b{font:inherit;font-size:12px;font-weight:700;letter-spacing:.04em;
  padding:5px 12px;cursor:pointer;color:var(--muted);background:none;border:none;
  transition:background .18s ease,color .18s ease;}
.s3d-bar .s3d-b.is-on{background:var(--accent);color:var(--accent-ink);}
.s3d-bar .s3d-b.s3d-only3{display:none;align-items:center;}
.s3d-bar.is-3d .s3d-b.s3d-only3{display:inline-flex;}
.s3d-frame{position:relative;width:100%;height:min(58vh,560px);min-height:330px;
  border-radius:10px;overflow:hidden;background:#04060e;border:var(--hard-border);
  box-shadow:var(--shadow-lg);display:flex;flex-direction:column;}
.s3d-frame[hidden]{display:none !important;}
.s3d-frame .s3d-ifr{flex:1 1 auto;width:100%;border:0;background:#04060e;}
.s3d-fsbar{display:none;align-items:center;gap:10px;padding:8px 12px;background:#070c18;
  border-bottom:1px solid rgba(122,156,220,.28);color:#e7eefc;font-size:13px;flex:0 0 auto;}
.s3d-fsbar .s3d-fstip{color:#93a7ca;font-size:12px;}
.s3d-frame.is-live .s3d-fsbar{display:flex;}
.s3d-frame.is-fs{position:fixed;inset:0;z-index:900;width:auto;height:auto;min-height:0;
  border-radius:0;border:0;box-shadow:none;}
body.s3d-lock{overflow:hidden;}
@media (max-width:880px){
  .s3d-bar{bottom:8px;right:8px;}
  .s3d-bar .s3d-b{padding:5px 10px;}
  .s3d-frame{height:min(52vh,440px);min-height:280px;}
}
</style>
"""


# ===========================================================================
# 5. 挂载层脚本
# ===========================================================================
HOST_JS = """
<script>
/* ==========================================================================
   V6.0.0 · 2D / 3D 视图切换的挂载层
   --------------------------------------------------------------------------
   · 三个 3D 场景各自是【自包含单文件】（自带的 three.js r147 + OrbitControls +
     场景外壳），这里只负责：懒挂载（首次切到 3D 才注入 srcdoc）、把父页参数
     通过 postMessage 推给子场景、全屏进出、切页时暂停渲染省电。
   · 为什么用 iframe：3D 场景各自带 :root 配色、html/body 布局与自己的 canvas
     尺寸逻辑，内联会与主页面正面冲突；iframe 自带文档边界，样式与脚本零污染，
     既有 11 个实验一行都不用改。
   · 单向读、单向写：父页只 postMessage（不读子文档，跨文档读在 file:// 下会被
     同源策略挡住）；子场景通过 {t:'s3d:state'} 回报，父页按形状与范围严格校验。
   ========================================================================== */
(function(){
  'use strict';
  var SRC = { refl: window.__S3D_REFL__, lens: window.__S3D_LENS__, mirror: window.__S3D_MIRROR__ };
  /* 每个场景：所在面板 id + 需要同步给 3D 的父页控件（name → 选择器 + 取值口径） */
  var CFG = {
    refl:   { panel:'tab-reflect', src:{ i:'#refl-iSlider' } },
    lens:   { panel:'tab-lens',    src:{ u:'#lens-uSlider', f:'#lens-fInput' } },
    mirror: { panel:'tab-mirror',  src:{ u:'#mirr-uSlider', h:'#mirr-hSlider' } }
  };
  var st = {};                       // key -> { on:bool, mounted:bool }

  function frameOf(k){ return document.querySelector('.s3d-frame[data-s3d="' + k + '"]'); }
  function barOf(k){ return document.querySelector('.s3d-bar[data-s3d="' + k + '"]'); }
  function ifrOf(k){ var f = frameOf(k); return f ? f.querySelector('.s3d-ifr') : null; }

  function mount(k){
    var it = st[k];
    if (!it || it.mounted) return true;
    var src = SRC[k];
    if (!src){ console.warn('[S3D] 缺少 3D 场景源码:', k); return false; }
    try {
      ifrOf(k).setAttribute('srcdoc', src);
      it.mounted = true;
    } catch(e){ console.warn('[S3D] srcdoc 注入失败:', k, e && e.message); return false; }
    return true;
  }

  /* 从父页控件读当前参数（用 DOM 现值，不依赖各实验的内部变量） */
  function readParams(k){
    var cfg = CFG[k], out = {}, name, el, v;
    for (name in cfg.src){
      el = document.querySelector(cfg.src[name]);
      if (!el) continue;
      v = parseFloat(el.value);
      if (isFinite(v)) out[name] = v;
    }
    return out;
  }
  function post(k, msg){
    var f = ifrOf(k);
    if (!f || !f.contentWindow) return;
    try { f.contentWindow.postMessage(msg, '*'); } catch(e){}
  }
  function sync(k){ post(k, { t:'s3d:init', params: readParams(k) }); }

  /* 切 2D / 3D：画布与同列其它元素整体让位给 3D 框（恢复时置回空串，不写死 display） */
  function setMode(k, mode){
    var it = st[k] || (st[k] = { on:false, mounted:false });
    var on = (mode === '3d');
    var frame = frameOf(k), bar = barOf(k);
    if (!frame || !bar) return;
    var stage = frame.parentNode, col = stage.parentNode, i, el;
    /* 舞台内：只有画布要让位（切换条与 3D 框各自按需显示） */
    for (i = 0; i < stage.children.length; i++){
      el = stage.children[i];
      if (el === frame || el === bar) continue;
      el.style.display = on ? 'none' : '';
    }
    /* 舞台外（画布下方的图例等）：3D 态一并收起，免得 2D 的说明留在 3D 界面里 */
    for (i = 0; i < col.children.length; i++){
      el = col.children[i];
      if (el === stage) continue;
      el.style.display = on ? 'none' : '';
    }
    frame.hidden = !on;
    var bs = bar.querySelectorAll('.s3d-b');
    for (i = 0; i < bs.length; i++){
      var isOn = bs[i].getAttribute('data-m') === (on ? '3d' : '2d');
      bs[i].classList.toggle('is-on', isOn);
      bs[i].setAttribute('aria-pressed', isOn ? 'true' : 'false');
    }
    bar.classList.toggle('is-3d', on);
    it.on = on;
    if (on){ mount(k); sync(k); post(k, { t:'s3d:active', on:true }); }
    else { post(k, { t:'s3d:active', on:false }); exitFs(k); }
  }
  function isOn(k){ return !!(st[k] && st[k].on); }

  /* 点切换按钮 */
  document.addEventListener('click', function(e){
    var b = e.target && e.target.closest ? e.target.closest('.s3d-bar .s3d-b') : null;
    if (!b) return;
    var bar = b.closest('.s3d-bar');
    var m = b.getAttribute('data-m');
    if (m !== '2d' && m !== '3d') return;      // 全屏按钮等非切换键不参与模式切换
    setMode(bar.getAttribute('data-s3d'), m);
  });

  /* 点全屏按钮 */
  document.addEventListener('click', function(e){
    var b = e.target && e.target.closest ? e.target.closest('.s3d-bar .s3d-fsb') : null;
    if (!b) return;
    var bar = b.closest('.s3d-bar');
    if (bar && st[bar.getAttribute('data-s3d')] && st[bar.getAttribute('data-s3d')].on)
      enterFs(bar.getAttribute('data-s3d'));
  });

  /* 父页滑块变化 → 推给 3D（捕获阶段全局委托，零侵入各实验的既有监听） */
  function onAnyEvent(e){
    if (echoing) return;
    var t = e.target, p, k;
    if (!t || !t.closest) return;
    p = t.closest('.panel.active');
    if (!p || !p.id || p.id.indexOf('tab-') !== 0) return;
    for (k in CFG){ if (CFG[k].panel === p.id && isOn(k)) sync(k); }
  }
  document.addEventListener('input', onAnyEvent, true);
  document.addEventListener('change', onAnyEvent, true);

  /* 切到别的实验页：全部 3D 暂停（省电）。
     ⚠️ 这里【绝不调用 document.exitFullscreen()】—— 实验室顶部自带的「全屏」按钮
     全屏的是 documentElement；早先一视同仁地退出，就出现了"点实验名把网页全屏退掉"。
     只收起「页面内回退全屏」这一层 CSS（它本来就盖着整个页面）。 */
  document.addEventListener('click', function(e){
    var tb = e.target && e.target.closest ? e.target.closest('.tab-btn') : null;
    if (!tb) return;
    for (var k in CFG){ if (isOn(k)) post(k, { t:'s3d:active', on:false }); }
    if (fb){
      fb = false; fsKey = null;
      for (var k2 in CFG){ var f2 = frameOf(k2); if (f2) f2.classList.remove('is-fs'); }
      syncFsUI();
    }
  }, true);

  /* ---------- 全屏 ---------- */
  var fsKey = null, fb = false;
  /* 🔥 实验室顶部自带一个「全屏」按钮（全屏的是 documentElement）。
     只有【自己的 3D 框】处于全屏才算"我们在全屏"，否则点实验名会把网页全屏一起退掉。 */
  function myFsEl(){
    var f = document.fullscreenElement || document.webkitFullscreenElement || null;
    return (f && f.classList && f.classList.contains('s3d-frame')) ? f : null;
  }
  function live(){ return !!myFsEl() || (!!fsKey && fb); }
  function syncFsUI(){
    for (var k in CFG){
      var f = frameOf(k);
      if (f) f.classList.toggle('is-live', fsKey === k);
    }
    document.body.classList.toggle('s3d-lock', live());
  }
  function fallbackEnter(k, err){
    if (err) console.warn('[S3D] 原生全屏不可用，改用页面内全屏:', (err && err.message) || err);
    fsKey = k; fb = true;
    frameOf(k).classList.add('is-fs');
    syncFsUI();
  }
  function enterFs(k){
    var f = frameOf(k);
    if (!f) return;
    if (f.requestFullscreen || f.webkitRequestFullscreen){
      fsKey = k; fb = false;
      try {
        var p = (f.requestFullscreen || f.webkitRequestFullscreen).call(f);
        if (p && p['catch']) p['catch'](function(e){ fallbackEnter(k, e); });
      } catch(e){ fallbackEnter(k, e); }
    } else fallbackEnter(k, null);
    syncFsUI();
  }
  function exitFs(k){
    var target = fsKey || k;
    var native = !!myFsEl();
    fsKey = null; fb = false;
    for (var key in CFG){ var f = frameOf(key); if (f) f.classList.remove('is-fs'); }
    if (native){
      try {
        var p = document.exitFullscreen ? document.exitFullscreen()
              : (document.webkitExitFullscreen ? document.webkitExitFullscreen() : null);
        if (p && p['catch']) p['catch'](function(){});
      } catch(e){}
    }
    syncFsUI();
    return target;
  }
  document.addEventListener('click', function(e){
    var b = e.target && e.target.closest ? e.target.closest('.s3d-fsbar .s3d-exit') : null;
    if (!b) return;
    var f = b.closest('.s3d-frame');
    if (f) exitFs(f.getAttribute('data-s3d'));
  });
  function onFsChange(){ if (!myFsEl()){ fsKey = null; fb = false; syncFsUI(); } }
  document.addEventListener('fullscreenchange', onFsChange);
  document.addEventListener('webkitfullscreenchange', onFsChange);
  document.addEventListener('keydown', function(e){ if (e.key === 'Escape' && fb) exitFs(fsKey); });

  /* 双击 3D 画面也可全屏 / 退出（iframe 内部的双击收不到，故走子场景回报） */
  /* 子场景里动过的滑杆 → 回写父页控件，保证 2D 视图与数据记录始终和 3D 一致。
     带 echo 保护：回写时派发的事件不再触发下一轮同步，避免来回对打。 */
  var echoing = false;
  function applyBack(k, params){
    var cfg = CFG[k]; if (!cfg || !params) return;
    echoing = true;
    try {
      for (var name in params){
        var sel = cfg.src[name]; if (!sel) continue;   /* beta / b / z 等 3D 独有量没有父页控件 */
        var el = document.querySelector(sel); if (!el) continue;
        var v = params[name]; if (typeof v !== 'number' || !isFinite(v)) continue;
        if (String(el.value) === String(v)) continue;
        el.value = v;
        try { el.dispatchEvent(new Event('input', { bubbles: true })); } catch (err) {}
        try { el.dispatchEvent(new Event('change', { bubbles: true })); } catch (err) {}
      }
    } finally { setTimeout(function(){ echoing = false; }, 0); }
  }

  window.addEventListener('message', function(e){
    var m = e && e.data;
    if (!m || typeof m !== 'object' || typeof m.t !== 'string') return;
    if (m.t === 's3d:state'){ if (!echoing && CFG[m.key]) applyBack(m.key, m.params); return; }
    if (m.t === 's3d:error'){
      console.warn('[S3D] 3D 场景报告错误:', m.key, m.msg);
      if (m.key && CFG[m.key] && isOn(m.key)){
        setMode(m.key, '2d');
        if (window.T) try { console.warn('[S3D] ' + T('s3d.fail')); } catch(err){}
      }
    }
  });

  window.S3D = { setMode: setMode, sync: sync, enterFs: enterFs, exitFs: exitFs,
                 isOn: isOn, snapshot: function(){ return readParams('refl'); } };
})();
</script>
"""

TAIL = (
    "\n<script>\n"
    "/* ==========================================================================\n"
    "   V6.0.0 · 三个 3D 立体场景的完整源码（各自自包含：内联 three.js r147 +\n"
    "   OrbitControls + 场景外壳 + 场景脚本；无任何外链、无网络请求、离线可用）\n"
    "   装载顺序：三个源码块 → 样式 → 挂载层脚本。\n"
    "   源码里所有脚本收尾标签都插入了反斜杠转义，避免提前闭合本页的脚本标签\n"
    "   （本注释也刻意不写出该字面量）。\n"
    "   ========================================================================== */\n"
    "window.__S3D_REFL__ = " + ESC["refl"][0] + ";\n"
    "</script>\n\n<script>\n"
    "window.__S3D_LENS__ = " + ESC["lens"][0] + ";\n"
    "</script>\n\n<script>\n"
    "window.__S3D_MIRROR__ = " + ESC["mirror"][0] + ";\n"
    "</script>\n" + CSS + HOST_JS + "\n"
)
s = rep(s, "\n</body>\n</html>\n", TAIL + "</body>\n</html>\n", label="追加 3D 源码 + 样式 + 挂载层")


# ===========================================================================
# 5b. 🔥 日食演示宿主（V5.2.0 写入的 ECL 模块）里也有一模一样的判断：
#     "document 有全屏元素" 就被当成"我在全屏"，于是点实验名会把
#     实验室顶部「全屏」按钮的网页全屏一起退掉。同样改成只认自己的 3D 框。
# ===========================================================================
s = rep(s,
        """  function fsElement(){
    return document.fullscreenElement || document.webkitFullscreenElement || null;
  }""",
        """  function fsElement(){
    /* 🔥 只认【自己的】全屏框：实验室顶部自带的「全屏」按钮全屏的是 documentElement，
       早先把"document 有全屏元素"一律当成自己在全屏，于是点实验名会把网页全屏退掉。 */
    var f = document.fullscreenElement || document.webkitFullscreenElement || null;
    return (f && f === frame) ? f : null;
  }""",
        label="日食宿主：全屏归属判定")

s = rep(s,
        """  function exitFs(){
    var native = !!(document.fullscreenElement || document.webkitFullscreenElement);
    fallbackFs = false;""",
        """  function exitFs(){
    var native = !!fsElement();
    fallbackFs = false;""",
        label="日食宿主：exitFs 守卫")


# ===========================================================================
# 6. 落地硬校验
# ===========================================================================
left = s.count("v5.2.0")
assert left == 0, "[FAIL] 仍残留 %d 处 v5.2.0 引用" % left
LOG.append("OK   %-46s x%d" % ("版本号三处同步", 3))
closes = re.findall(r"</script(?=[\s>/])", s)
opens = re.findall(r"<script(?=[\s>])", s)
assert len(closes) == 15, "[FAIL] 脚本收尾标签字面量 %d 处，应为 15（既有 11 + 3 份场景源码 + 1 挂载层）" % len(closes)
LOG.append("OK   %-46s 收尾 %d / 开 %d（含 3 份场景源码里的 12 个开标签）"
           % ("脚本标签字面量硬校验", len(closes), len(opens)))
blocks = re.findall(r"<script[^>]*>(.*?)</script(?=[\s>/])", s, re.S)
assert len(blocks) == 15, "[FAIL] 脚本块 %d 个，应为 15" % len(blocks)
for k, _, var, _t in [(k, f, v, t) for k, f, v, t in SCENES]:
    lit = "window.%s = " % var
    assert lit in s, "[FAIL] 找不到 %s" % lit
LOG.append("OK   %-46s x3" % ("三份场景源码均已就位"))

open(DST, "w", encoding="utf-8", newline="\r\n").write(s)
n1 = os.path.getsize(DST)
print("\n".join(LOG))
print("-" * 72)
print("源 %s (%d B)" % (os.path.basename(SRC), n0))
print("产物 %s (%d B, %+d B / %+.2f%%)" % (os.path.basename(DST), n1, n1 - n0, (n1 - n0) * 100.0 / n0))
