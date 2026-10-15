
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
  var SRC = { refl: window.__S3D_REFL__, lens: window.__S3D_LENS__, mirror: window.__S3D_MIRROR__, pinhole: window.__S3D_PINHOLE__ };
  /* 每个场景：所在面板 id + 需要同步给 3D 的父页控件（name → 选择器 + 取值口径） */
  var CFG = {
    refl:   { panel:'tab-reflect', src:{ i:'#refl-iSlider' } },
    lens:   { panel:'tab-lens',    src:{ u:'#lens-uSlider', f:'#lens-fInput' } },
    mirror: { panel:'tab-mirror',  src:{ u:'#mirr-uSlider', h:'#mirr-hSlider' } },
    pinhole:{ panel:'tab-line',    src:{} }
  };
  var st = {};                       // key -> { on:bool, mounted:bool }

  /* ★ V6.3.0：3D 场景的上下文回收策略
     ----------------------------------------------------------------------
     旧实现只在「上下文丢失 / 报错」时 unmount，正常切换一律保留 srcdoc，
     于是依次进过四个 3D（三个场景 + 日食）之后最多 4 份 WebGL 上下文同时活着，
     显存与浏览器上下文额度双重承压。现在的口径：
       · view（'2d'/'3d'）是【持久的视图选择】，on 是【此刻是否在渲染】，两者分开；
       · 互斥 —— 进入任一 3D 时立即回收其它所有 3D 的挂载，同屏只留一份；
       · 静置回收 —— 离开 3D（切回 2D、或切到别的实验页）后 IDLE_MS 内没回来就卸掉；
       · 唤醒 —— 切回该实验页时，凡 view 仍是 3D 的场景重新挂载并恢复渲染（见 resumeFor）。 */
  var IDLE_MS = 30000, _idle = {};

  function cancelIdle(k){ if (_idle[k]){ clearTimeout(_idle[k]); _idle[k] = 0; } }
  function onTabOf(k){
    var p = document.getElementById(CFG[k].panel);
    return !!(p && p.classList.contains('active'));
  }
  function scheduleIdle(k){
    cancelIdle(k);
    _idle[k] = setTimeout(function(){
      _idle[k] = 0;
      if (!onTabOf(k) || !(st[k] && st[k].view === '3d')) unmount(k);
    }, IDLE_MS);
  }
  function reclaimAll(){ for (var k in CFG){ if (st[k] && st[k].mounted) unmount(k); } }
  function reclaimOthers(except){
    for (var k in CFG){ if (k !== except && st[k] && st[k].mounted) unmount(k); }
    try { if (window.ECL && window.ECL.reclaim) window.ECL.reclaim(); } catch(e){}
  }

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

  /* ★ V6.2.1：把挂载退回去，让"下一次进入 3D"变成一次全新的初始化。
     旧实现 mount() 有 it.mounted 一次性守卫，srcdoc 只注入一次；一旦场景内部的
     WebGL 渲染上下文丢失（弱机 / 显存紧张时很常见），子文档就永久停在"画面不动"，
     而父页再怎么切 3D 都只是往一个已经死掉的文档里发消息 ——
     用户感受就是"用一段时间就卡死、3D 点不进去"。清掉 srcdoc 等于把 iframe 连同
     它那份 WebGL 上下文一起丢弃，下次进入就是干净的新场景。 */
  function unmount(k){
    var it = st[k]; if (!it) return;
    cancelIdle(k);
    it.on = false;
    it.mounted = false;
    var f = ifrOf(k);
    if (f){ try { f.removeAttribute('srcdoc'); f.setAttribute('srcdoc', ''); } catch(e){} }
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
    var it = st[k] || (st[k] = { on:false, mounted:false, view:'2d' });
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
    /* view 记住用户选的 2D/3D，与"此刻是否在渲染"分开：
       被互斥回收、或静置回收之后切回来，仍按 view 恢复成 3D。 */
    it.view = on ? '3d' : '2d';
    if (on){
      cancelIdle(k);
      reclaimOthers(k);                       /* 同屏只留这一份 3D 挂载 */
      mount(k); sync(k); post(k, { t:'s3d:active', on:true });
    } else {
      post(k, { t:'s3d:active', on:false }); exitFs(k);
      scheduleIdle(k);                        /* 静置 IDLE_MS 后把这枚上下文还回去 */
    }
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
    /* ★ V6.3.0：点的是【当前】这个实验（此刻 class 仍是 active）→ 不碰 3D。
       旧实现无条件暂停，于是在 3D 模式里点一下实验名，画面就冻住且再也醒不过来。 */
    if (tb.classList.contains('active')) return;
    for (var k in CFG){ if (isOn(k)) { post(k, { t:'s3d:active', on:false }); scheduleIdle(k); } }
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
    if (m.t === 's3d:lost'){
      /* ★ V6.2.1：渲染上下文丢了 → 先退回 2D（别让用户盯着不动的画面），
         再把挂载重置掉。这样他再点一次 3D 就是重新初始化，而不是往死文档里发消息。 */
      console.warn('[S3D] 3D 场景渲染中断:', m.key, '（已重置挂载，下次进入 3D 会重新初始化）');
      if (m.key && CFG[m.key]){ if (isOn(m.key)) setMode(m.key, '2d'); unmount(m.key); }
      return;
    }
    if (m.t === 's3d:error'){
      console.warn('[S3D] 3D 场景报告错误:', m.key, m.msg);
      if (m.key && CFG[m.key] && isOn(m.key)){
        setMode(m.key, '2d');
        if (window.T) try { console.warn('[S3D] ' + T('s3d.fail')); } catch(err){}
      }
      /* ★ V6.2.1：失败也要重置挂载，否则用户再点 3D 只会看到一个死掉的画面 */
      if (m.key && CFG[m.key]) unmount(m.key);
    }
  });

  /* ★ V6.3.0：切回某个实验页时，把该页处于 3D 态的场景重新唤醒。
     旧实现 on:true 只在点 3D 按钮那一处发过，而切页会无条件暂停，
     于是「切到别的实验再切回来」必然看到一帧死图（拖不动、缩放无反应）。 */
  function resumeFor(panelId){
    for (var k in CFG){
      if (CFG[k].panel !== panelId || !(st[k] && st[k].view === '3d')) continue;
      cancelIdle(k);
      reclaimOthers(k);
      mount(k);                                 /* 静置期间被回收过就重新初始化 */
      sync(k);                                  /* 把父页当前参数推回场景 */
      post(k, { t:'s3d:active', on:true });
    }
    if (window.ECL && window.ECL.onTab){ try { window.ECL.onTab(panelId === 'tab-line'); } catch(e){} }
  }

  window.S3D = { setMode: setMode, sync: sync, enterFs: enterFs, exitFs: exitFs,
                 isOn: isOn, resumeFor: resumeFor, reclaimAll: reclaimAll,
                 snapshot: function(){ return readParams('refl'); } };
})();
