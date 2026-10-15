
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
    /* 🔥 只认【自己的】全屏框：实验室顶部自带的「全屏」按钮全屏的是 documentElement，
       早先把"document 有全屏元素"一律当成自己在全屏，于是点实验名会把网页全屏退掉。 */
    var f = document.fullscreenElement || document.webkitFullscreenElement || null;
    return (f && f === frame) ? f : null;
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
    var native = !!fsElement();
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
