# -*- coding: utf-8 -*-
"""由 v600_patch.py 生成 v610_patch.py（v6.1.0：切换条挪右下角、修 tab 退全屏、加状态回写）"""
src = open('v600_patch.py', encoding='utf-8').read()
DONE = []


def rep(old, new, tag, cnt=1):
    global src
    assert src.count(old) == cnt, ('MISS ' + tag, src.count(old))
    src = src.replace(old, new)
    DONE.append(tag)


rep('V5.2.0 -> V6.0.0', 'V6.1.0：由 v5.2.0 全量重建（= V6.0.0 三场景 + 本轮修订）', 'doc')
rep('DST = os.path.join(BASE, "..", "光学交互实验室_AI_v6.0.0.html")',
    'DST = os.path.join(BASE, "..", "光学交互实验室_AI_v6.1.0.html")', 'dst')

# 1) 三个面板的 2D/3D 块套一层 .s3d-stage（切换条才能定位到"画布右下角"）
rep('    return (CANVAS[key] + "\\n"', '    return (\'<div class="s3d-stage">\' + "\\n" + CANVAS[key] + "\\n"', 'wrap head')
rep("""            '          <iframe class="s3d-ifr" title="%s" aria-label="%s"></iframe>\\n'
            '        </div>') % (key, key, title, title)""",
    """            '          <iframe class="s3d-ifr" title="%s" aria-label="%s"></iframe>\\n'
            '        </div>\\n        </div>') % (key, key, title, title)""", 'wrap tail')
rep('        <!-- V6.0.0：2D / 3D 视图切换（悬浮在画布右上角）+ 独立 3D 场景 -->',
    '        <!-- V6.1.0：2D / 3D 视图切换（悬浮在画布右下角）+ 独立 3D 场景 -->', 'comment')

# 2) CSS
rep(""".left{position:relative;}
.s3d-bar{position:absolute;top:10px;right:12px;z-index:4;display:inline-flex;""",
    """.s3d-stage{position:relative;}
.s3d-bar{position:absolute;bottom:10px;right:12px;z-index:4;display:inline-flex;""", 'css bar')
rep("""@media (max-width:880px){
  .s3d-bar{top:8px;right:8px;}""",
    """@media (max-width:880px){
  .s3d-bar{bottom:8px;right:8px;}""", 'css media')

# 3) setMode：舞台结构下的显隐
rep("""    var col = frame.parentNode, i;
    for (i = 0; i < col.children.length; i++){
      var el = col.children[i];
      if (el === frame || el === bar) continue;
      el.style.display = on ? 'none' : '';
    }""",
    """    var stage = frame.parentNode, col = stage.parentNode, i, el;
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
    }""", 'setMode hide')

# 4) 🔥 全屏归属判定：只认自己的 3D 框
rep("""  var fsKey = null, fb = false;
  function live(){ return !!fsKey; }""",
    """  var fsKey = null, fb = false;
  /* 🔥 实验室顶部自带一个「全屏」按钮（全屏的是 documentElement）。
     只有【自己的 3D 框】处于全屏才算"我们在全屏"，否则点实验名会把网页全屏一起退掉。 */
  function myFsEl(){
    var f = document.fullscreenElement || document.webkitFullscreenElement || null;
    return (f && f.classList && f.classList.contains('s3d-frame')) ? f : null;
  }
  function live(){ return !!myFsEl() || (!!fsKey && fb); }""", 'myFsEl')
rep("""  function exitFs(k){
    var target = fsKey || k;
    var native = !!(document.fullscreenElement || document.webkitFullscreenElement);
    fsKey = null; fb = false;""",
    """  function exitFs(k){
    var target = fsKey || k;
    var native = !!myFsEl();
    fsKey = null; fb = false;""", 'exitFs guard')
rep("""  document.addEventListener('fullscreenchange', function(){ if (!(document.fullscreenElement || document.webkitFullscreenElement)){ fsKey = null; syncFsUI(); } });
  document.addEventListener('webkitfullscreenchange', function(){ if (!(document.fullscreenElement || document.webkitFullscreenElement)){ fsKey = null; syncFsUI(); } });""",
    """  function onFsChange(){ if (!myFsEl()){ fsKey = null; fb = false; syncFsUI(); } }
  document.addEventListener('fullscreenchange', onFsChange);
  document.addEventListener('webkitfullscreenchange', onFsChange);""", 'fschange')

# 5) 点实验名：绝不调用全屏 API
rep("""  /* 切到别的实验页：全部 3D 暂停（省电），并退出全屏 */
  document.addEventListener('click', function(e){
    var tb = e.target && e.target.closest ? e.target.closest('.tab-btn') : null;
    if (!tb) return;
    for (var k in CFG){ if (isOn(k)) post(k, { t:'s3d:active', on:false }); }
    exitFs(k);
  }, true);""",
    """  /* 切到别的实验页：全部 3D 暂停（省电）。
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
  }, true);""", 'tab click')

# 6) 子场景回写 → 父页滑块（带 echo 保护）
rep("""  window.addEventListener('message', function(e){
    var m = e && e.data;
    if (!m || typeof m !== 'object' || typeof m.t !== 'string') return;
    if (m.t === 's3d:error'){""",
    """  /* 子场景里动过的滑杆 → 回写父页控件，保证 2D 视图与数据记录始终和 3D 一致。
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
    if (m.t === 's3d:error'){""", 'state back')
rep("""  function onAnyEvent(e){
    var t = e.target, p, k;
    if (!t || !t.closest) return;""",
    """  function onAnyEvent(e){
    if (echoing) return;
    var t = e.target, p, k;
    if (!t || !t.closest) return;""", 'echo guard')

# 7) 版本号 / 角标 / 更新日志
rep("""s = rep(s, "var BUILD = 'v5.2.0', MAX_SHOW = 3", "var BUILD = 'v6.0.0', MAX_SHOW = 3", label="BUILD 常量")
s = rep(s, "    return 'v5.2.0';\\n  })();", "    return 'v6.0.0';\\n  })();", label="RPT_BUILD 兜底常量")""",
    """s = rep(s, "var BUILD = 'v5.2.0', MAX_SHOW = 3", "var BUILD = 'v6.1.0', MAX_SHOW = 3", label="BUILD 常量")
s = rep(s, "    return 'v5.2.0';\\n  })();", "    return 'v6.1.0';\\n  })();", label="RPT_BUILD 兜底常量")""", 'ver consts')
rep("""'<div class="ver-badge" title="光学交互实验室 V6.0.0 · 反射 / 凸透镜成像 / 平面镜成像 三个实验各内嵌 3D 立体场景（画布右上角切换 2D｜3D）">v6.0.0</div>',""",
    """'<div class="ver-badge" title="光学交互实验室 V6.1.0 · 3D 场景修订：切换条移到画布右下角、点实验名不再退掉网页全屏、棋子可拖动、入射角可在 3D 内调节、光锥改为立体">v6.1.0</div>',""", 'badge')
# v6.1.0 只改 NEW_LOG 的开头（把带 cur 的位置换成 V6.1.0，V6.0.0 降级为普通条目）；
# OLD_LOG（源文件里 V5.2.0 的 cur 行）保持不动，否则锚点对不上源文件。
rep("""NEW_LOG = (
    '      <div class="log-item cur">\\n'
    '        <div class="log-head"><span class="log-ver">V6.0.0</span><span class="log-date">2026-09-16</span></div>\\n'""",
    """NEW_LOG = (
    '      <div class="log-item cur">\\n'
    '        <div class="log-head"><span class="log-ver">V6.1.0</span><span class="log-date">2026-09-16</span></div>\\n'
    '        <p>三个 3D 场景集中修订：<strong>2D ｜ 3D 切换条移到实验区右下角</strong>；'
    '<strong>修掉「点实验名会退掉网页全屏」</strong>（顶部自带的「全屏」按钮全屏的是整个页面，'
    '之前被误认成 3D 全屏一起退掉了）；平面镜成像的<strong>棋子可直接在 3D 里拖动</strong>'
    '（左右移动时虚像跟着一起动，前后移动会同步回 2D 的物距滑块）；光的反射把<strong>入射角也放进 3D 控制条</strong>；'
    '凸透镜的<strong>光锥改成真正的立体光锥</strong>（此前取样点只落在同一个竖直平面里，看着像一个扇面）；'
    '另修掉长时间动画每帧重建光路未释放显存的隐患。</p>\\n'
    '      </div>\\n'
    '      <div class="log-item">\\n'
    '        <div class="log-head"><span class="log-ver">V6.0.0</span><span class="log-date">2026-09-16</span></div>\\n'""", 'new log')

open('v610_patch.py', 'w', encoding='utf-8', newline='\n').write(src)
print('v610_patch.py generated:', len(DONE), 'edits ->', DONE)
