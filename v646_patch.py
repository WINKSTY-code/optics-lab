# -*- coding: utf-8 -*-
"""
V6.4.5 -> V6.4.6
① 小孔成像 2D 实验新增「物距 u」的调节 + 扫描（物距组两个模式共用，data-g 支持空格分隔）
② 字体调节 / 语言调节 / AI 设置 / 背景颜色调节 四个入口合并进顶栏「设置」下拉，功能不变
③ 版本号四处同步（BUILD / 报告兜底常量 / 版本角标 / 更新日志），日志 19 字

关键设计约束（踩坑记录）：
  · .set-wrap 必须放在 .topbar-right 之外。.topbar-right 是 overflow-x:auto 的滚动容器，
    按 CSS Overflow 规范，一轴非 visible 时另一轴的 visible 会计算成 auto —— 绝对定位的
    下拉层会被它整个裁掉（菜单在下沿之外 → 完全看不见）。
  · 两个 injectXXX() 原来以 #aiCfgBtn 为锚点。该按钮已移进下拉，若仍以它为锚，注入的
    「学生 / 朗读 / 问AI / 诊断」按钮会掉进下拉里 → 锚点改到 topbar-right 内的 #fsBtn。
  · 五个按钮的 id / 事件监听 / 文案全部原样保留，因此既有 JS 一行都不用改。

每处替换都断言命中次数，任一处不符立即中止。
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "光学交互实验室_AI_v6.4.5.html")
DST = os.path.join(BASE, "光学交互实验室_AI_v6.4.6.html")

LOG = []


def rep(s, old, new, n=1, label=""):
    c = s.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    LOG.append("OK  %-46s x%d" % (label, c))
    return s.replace(old, new)


LOG_VER = "小孔成像加物距调节，顶栏按钮并入设置。"   # 19 字
assert len(LOG_VER) <= 20, "更新日志超过 20 字"

# ============================================================ A. 顶栏：抽出四个入口
TOPBAR_OLD = """      <button id="aiCfgBtn" class="theme-btn" data-i18n="btn.aiCfg">AI 设置</button>
      <button id="zoomOut" class="theme-btn" data-i18n-title="zoom.title.out" title="缩小字号" aria-label="缩小字号">A\u2212</button>
      <button id="zoomIn" class="theme-btn" data-i18n-title="zoom.title.in" title="放大字号" aria-label="放大字号">A\uff0b</button>
      <button id="langBtn" class="theme-btn">\u4e2d\u6587</button>
      <button id="themeBtn" class="theme-btn">\u9ed1\u677f</button>
"""

TOPBAR_NEW = """      <!-- V6.4.6：字体 / 语言 / AI 设置 / 背景色 四个入口移入「设置」下拉（见 .set-wrap） -->
"""

# 「设置」下拉：挂在 .topbar-right 之外（它是 overflow-x:auto 的滚动容器，会把下拉层裁掉）
SET_WRAP_OLD = """      <button id="signBtn" class="sign-btn" data-i18n="btn.about" title="\u5173\u4e8e\u672c\u9875">\u5173\u4e8e</button>
    </div>
  </div>
"""

SET_WRAP_NEW = """      <button id="signBtn" class="sign-btn" data-i18n="btn.about" title="\u5173\u4e8e\u672c\u9875">\u5173\u4e8e</button>
    </div>
    <!-- V6.4.6 · 「设置」下拉：字体调节 / 语言调节 / AI 设置 / 背景色调节 四入口合并。
         ★ 必须放在 .topbar-right 之外：它是 overflow-x:auto 的滚动容器，绝对定位的下拉层
           会被它裁掉（overflow-x 非 visible 时 overflow-y 计算为 auto）。五个按钮的
           id / 事件监听 / 文案全部原样保留，因此既有 JS 一行都不用改。 -->
    <div class="set-wrap" id="setWrap">
      <button id="setBtn" class="theme-btn" data-i18n="btn.settings" aria-haspopup="true" aria-expanded="false" aria-controls="setMenu">\u8bbe\u7f6e</button>
      <div class="set-menu" id="setMenu" role="menu" hidden>
        <button id="aiCfgBtn" class="set-item" data-i18n="btn.aiCfg" role="menuitem">AI \u8bbe\u7f6e</button>
        <div class="set-row">
          <button id="zoomOut" class="set-item" data-i18n-title="zoom.title.out" title="\u7f29\u5c0f\u5b57\u53f7" aria-label="\u7f29\u5c0f\u5b57\u53f7" role="menuitem">A\u2212</button>
          <button id="zoomIn" class="set-item" data-i18n-title="zoom.title.in" title="\u653e\u5927\u5b57\u53f7" aria-label="\u653e\u5927\u5b57\u53f7" role="menuitem">A\uff0b</button>
        </div>
        <button id="langBtn" class="set-item" role="menuitem">\u4e2d\u6587</button>
        <button id="themeBtn" class="set-item" role="menuitem">\u9ed1\u677f</button>
      </div>
    </div>
  </div>
"""

# ============================================================ B. 样式
CSS_OLD = """  .theme-btn:hover{transform:translate(2px,2px);box-shadow:1px 1px 0 var(--line);}
  .tab-nav{display:flex;flex-wrap:wrap;gap:5px;margin:10px 0 6px;}
"""

CSS_NEW = """  .theme-btn:hover{transform:translate(2px,2px);box-shadow:1px 1px 0 var(--line);}
  /* V6.4.6 · 「设置」下拉（字体 / 语言 / AI 设置 / 背景色 合并入口）
     z-index 45 —— 低于 .modal-mask 的 50，A 配置弹窗不会被菜单压住 */
  .set-wrap{position:relative;display:inline-flex;align-items:center;flex:0 0 auto;}
  .set-menu{position:absolute;top:calc(100% + 6px);right:0;z-index:45;
    display:flex;flex-direction:column;gap:4px;min-width:118px;padding:6px;
    background:var(--panel);border:var(--hard-border);border-radius:10px;box-shadow:var(--shadow);}
  .set-menu[hidden]{display:none !important;}
  .set-menu .set-row{display:flex;gap:4px;}
  .set-menu .set-item{display:block;width:100%;text-align:left;cursor:pointer;white-space:nowrap;
    background:var(--panel);color:var(--txt);border:var(--hard-border);border-radius:6px;
    padding:5px 9px;font-size:12px;font-weight:700;box-shadow:none;}
  .set-menu .set-row .set-item{flex:1;text-align:center;}
  .set-menu .set-item:hover,.set-menu .set-item:focus-visible{
    background:var(--accent);color:var(--accent-ink);box-shadow:none;}
  #setBtn[aria-expanded="true"]{background:var(--accent);color:var(--accent-ink);}
  /* 菜单一律 right:0 —— 配合下面两条把 .set-wrap 推到行尾的规则，下拉层不会溢出视口。
     实测：曾在窄屏改 left:0，390px 视口下菜单右边缘掉到 458px（溢出 68px）；
     而 700px 时 .set-wrap 被换行到第二行且左对齐，right:0 又会让左边缘跑到 −66px。
     结论：不要按断点改边，只保证 .set-wrap 永远贴着行尾。 */
  /* ≤880px：顶栏必然换行（移动端闸门就在 880px），把「设置」推到本行行尾 */
  @media (max-width:880px){
    .set-wrap{margin-left:auto;}
  }
  /* 极窄桌面窗口兜底（<=640px 且未触发移动端闸门）：顶栏换行，
     保证「设置」不会被 flex-shrink:0 的 .topbar-right 挤出视口 */
  @media (max-width:640px){
    .topbar{flex-wrap:wrap;}
    .topbar-right{max-width:100%;flex-wrap:wrap;overflow-x:visible;justify-content:flex-start;}
  }
  html[data-mode="mobile"] #setBtn{padding:4px 7px;font-size:11px;}
  .tab-nav{display:flex;flex-wrap:wrap;gap:5px;margin:10px 0 6px;}
"""

# ============================================================ C. 设置下拉行为
JS_OLD = """$('themeBtn').addEventListener('click', () => { THEME = THEME === 'dark' ? 'light' : 'dark'; try{ localStorage.setItem(K+'_theme', THEME); }catch(e){} applyTheme(); });
"""

JS_NEW = """$('themeBtn').addEventListener('click', () => { THEME = THEME === 'dark' ? 'light' : 'dark'; try{ localStorage.setItem(K+'_theme', THEME); }catch(e){} applyTheme(); });

// ---- V6.4.6 · 「设置」下拉开合 ----
// 五个按钮的 click 监听全部在别处，这里只负责显隐，不动任何一个功能。
(function(){
  const wrap = $('setWrap'), btn = $('setBtn'), menu = $('setMenu');
  if(!wrap || !btn || !menu) return;
  function setOpen(on){
    menu.hidden = !on;
    btn.setAttribute('aria-expanded', on ? 'true' : 'false');
  }
  // stopPropagation：避免同一次点击又冒到 document 上把刚打开的菜单立刻关掉
  btn.addEventListener('click', function(e){ e.stopPropagation(); setOpen(menu.hidden); });
  // AI 设置会弹出配置窗，顺手收起菜单；
  // A±／语言／背景色 保持展开 —— 字号与主题常要连点几次，收起来反而碍事
  const cfgB = $('aiCfgBtn');
  if(cfgB) cfgB.addEventListener('click', function(){ setOpen(false); });
  document.addEventListener('click', function(e){ if(!wrap.contains(e.target)) setOpen(false); });
  document.addEventListener('keydown', function(e){ if(e.key === 'Escape') setOpen(false); });
  setOpen(false);
})();
"""

# ============================================================ D. 注入锚点（#aiCfgBtn 已入下拉）
INJ1_OLD = """  (function injectIdentityButtons(){
    const cfgBtn = $('aiCfgBtn');
    if(!cfgBtn || !cfgBtn.parentNode) return;
    const wrap = document.createElement('div');
    wrap.style.cssText = 'display:inline-flex;gap:6px;align-items:center;';
    wrap.innerHTML =
      '<button id="studentBtn" class="theme-btn" style="padding:5px 10px;font-size:12px;">'+T('btn.student')+'</button>';
    cfgBtn.parentNode.insertBefore(wrap, cfgBtn);
"""

INJ1_NEW = """  (function injectIdentityButtons(){
    /* V6.4.6：锚点由 #aiCfgBtn 改为 topbar-right 内的 #fsBtn —— #aiCfgBtn 已移入
       「设置」下拉，若仍以它为锚，学生按钮会被插进下拉里 */
    const anchor = $('fsBtn') || $('aiCfgBtn');
    if(!anchor || !anchor.parentNode) return;
    const wrap = document.createElement('div');
    wrap.style.cssText = 'display:inline-flex;gap:6px;align-items:center;';
    wrap.innerHTML =
      '<button id="studentBtn" class="theme-btn" style="padding:5px 10px;font-size:12px;">'+T('btn.student')+'</button>';
    anchor.parentNode.insertBefore(wrap, anchor);
"""

INJ2_OLD = """  (function injectTopbarAi(){
    const topbar = document.querySelector('.topbar-right');
    const cfgBtn = $('aiCfgBtn');
    if(!topbar || !cfgBtn) return;
"""

INJ2_NEW = """  (function injectTopbarAi(){
    const topbar = document.querySelector('.topbar-right');
    /* V6.4.6：同 injectIdentityButtons，锚点改到 #fsBtn（#aiCfgBtn 已入下拉） */
    const anchor = $('fsBtn') || $('aiCfgBtn');
    if(!topbar || !anchor) return;
"""

INJ2B_OLD = """    cfgBtn.parentNode.insertBefore(wrap, cfgBtn);
    $('topTts').onclick  = ()=>topbarAiClick('tts');
"""

INJ2B_NEW = """    anchor.parentNode.insertBefore(wrap, anchor);
    $('topTts').onclick  = ()=>topbarAiClick('tts');
"""

# ============================================================ E. 小孔成像：物距 u
PIN_HTML_OLD = """      <span class="slider-g" data-g="shadow">
        <label><span data-i18n="line.lbl.u">\u7269\u8ddd u</span> = <b id="line-uVal">30</b> cm</label>
        <input type="range" id="line-uSlider" min="10" max="50" step="0.1" value="30" aria-label="object distance">
        <button id="line-uPlay" class="play-btn" data-i18n="btn.scanU">\u25b6 \u64ad\u653e\uff1a\u7269\u8ddd\u626b\u63cf</button>
      </span>
"""

PIN_HTML_NEW = """      <!-- V6.4.6：物距组改为「影子形成 + 小孔成像」共用（data-g 空格分隔）。
           小孔成像里物距 u 直接决定像高比 v/u，是新增的可调 + 可扫描量。 -->
      <span class="slider-g" data-g="shadow pinhole">
        <label><span data-i18n="line.lbl.u">\u7269\u8ddd u</span> = <b id="line-uVal">30</b> cm</label>
        <input type="range" id="line-uSlider" min="10" max="50" step="0.1" value="30" aria-label="object distance">
        <button id="line-uPlay" class="play-btn" data-i18n="btn.scanU">\u25b6 \u64ad\u653e\uff1a\u7269\u8ddd\u626b\u63cf</button>
      </span>
"""

PIN_JS_OLD = """    // \u6309\u6a21\u5f0f\u5206\u7ec4\u663e\u793a\u6ed1\u5757\uff1a\u5f71\u5b50=\u7269\u8ddd+\u7269\u4f53\u4f4d\u7f6e\uff0c\u5c0f\u5b54=\u50cf\u8ddd+\u5b54\u5927\u5c0f
    document.querySelectorAll('#tab-line .slider-g').forEach(g => {
      g.style.display = g.dataset.g === mode ? '' : 'none';
    });
"""

PIN_JS_NEW = """    // 按模式分组显示滑块：影子=物距+物体位置，小孔=物距+像距+孔大小
    // V6.4.6：data-g 支持空格分隔的多模式（物距组是 "shadow pinhole" 两个模式共用）
    document.querySelectorAll('#tab-line .slider-g').forEach(g => {
      var gs = (g.dataset.g || '').split(/\\s+/);
      g.style.display = gs.indexOf(mode) >= 0 ? '' : 'none';
    });
"""

# ============================================================ F. i18n 词条
I18N_OLD = "'btn.aiCfg':      {zh:'AI \u8bbe\u7f6e', zht:'AI \u8a2d\u5b9a', en:'AI Settings'},\n"
I18N_NEW = I18N_OLD + "'btn.settings':   {zh:'\u8bbe\u7f6e', zht:'\u8a2d\u5b9a', en:'Settings'},\n"

# ============================================================ G. 版本号
V_BUILD_OLD = "  var BUILD = 'v6.4.5', MAX_SHOW = 3, shown = 0, dismissed = false, reported = 0;"
V_BUILD_NEW = "  var BUILD = 'v6.4.6', MAX_SHOW = 3, shown = 0, dismissed = false, reported = 0;"

V_RPT_OLD = "    return 'v6.4.5';"
V_RPT_NEW = "    return 'v6.4.6';"

V_BADGE_OLD = '<div class="ver-badge" title="\u5149\u5b66\u4ea4\u4e92\u5b9e\u9a8c\u5ba4 V6.4.5 \u00b7 \u5f71\u5b50\u5f62\u6210\u65b0\u589e\u8def\u706f\u5f71\u5b50\u95f4\u8ddd3D\u6848\u4f8b">v6.4.5</div>'
V_BADGE_NEW = '<div class="ver-badge" title="\u5149\u5b66\u4ea4\u4e92\u5b9e\u9a8c\u5ba4 V6.4.6 \u00b7 ' + LOG_VER + '">v6.4.6</div>'

LOG_OLD = """      <div class="log-item cur">
        <div class="log-head"><span class="log-ver">V6.4.5</span><span class="log-date">2026-09-18</span></div>
        <p>\u5f71\u5b50\u5f62\u6210\u65b0\u589e\u8def\u706f\u5f71\u5b50\u95f4\u8ddd3D\u6848\u4f8b\u3002</p>
      </div>
"""

LOG_NEW = """      <div class="log-item cur">
        <div class="log-head"><span class="log-ver">V6.4.6</span><span class="log-date">2026-09-18</span></div>
        <p>""" + LOG_VER + """</p>
      </div>
      <div class="log-item">
        <div class="log-head"><span class="log-ver">V6.4.5</span><span class="log-date">2026-09-18</span></div>
        <p>\u5f71\u5b50\u5f62\u6210\u65b0\u589e\u8def\u706f\u5f71\u5b50\u95f4\u8ddd3D\u6848\u4f8b\u3002</p>
      </div>
"""

# ============================================================ run
s = open(SRC, encoding="utf-8").read()
n0 = os.path.getsize(SRC)

s = rep(s, TOPBAR_OLD, TOPBAR_NEW, 1, "顶栏抽出四个入口按钮")
s = rep(s, SET_WRAP_OLD, SET_WRAP_NEW, 1, "插入「设置」下拉（topbar-right 之外）")
s = rep(s, CSS_OLD, CSS_NEW, 1, "下拉样式")
s = rep(s, JS_OLD, JS_NEW, 1, "下拉开合逻辑")
s = rep(s, INJ1_OLD, INJ1_NEW, 1, "学生按钮注入锚点")
s = rep(s, INJ2_OLD, INJ2_NEW, 1, "AI 按钮组注入锚点")
s = rep(s, INJ2B_OLD, INJ2B_NEW, 1, "AI 按钮组插入位置")
s = rep(s, PIN_HTML_OLD, PIN_HTML_NEW, 1, "物距组改为两模式共用")
s = rep(s, PIN_JS_OLD, PIN_JS_NEW, 1, "data-g 多模式匹配")
s = rep(s, I18N_OLD, I18N_NEW, 1, "i18n: btn.settings")
s = rep(s, V_BUILD_OLD, V_BUILD_NEW, 1, "BUILD 版本号")
s = rep(s, V_RPT_OLD, V_RPT_NEW, 1, "报告版本兜底常量")
s = rep(s, V_BADGE_OLD, V_BADGE_NEW, 1, "版本角标")
s = rep(s, LOG_OLD, LOG_NEW, 1, "更新日志首条")

# 脚本收尾标签字面量计数：改动前后必须不变（见 skill §12）
import re
closes = len(re.findall(r"</script(?=[\s>/])", s))
LOG.append("脚本收尾标签计数 %d（源 %d）" % (
    closes, len(re.findall(r"</script(?=[\s>/])", open(SRC, encoding="utf-8").read()))))
assert closes == len(re.findall(r"</script(?=[\s>/])", open(SRC, encoding="utf-8").read())), \
    "脚本收尾标签计数变化，可能引入了会提前闭合脚本的字面量"

open(DST, "w", encoding="utf-8", newline="\n").write(s)
n1 = os.path.getsize(DST)

print("\n".join(LOG))
print("-" * 66)
print("更新日志：%s（%d 字）" % (LOG_VER, len(LOG_VER)))
print("源 %s (%d B)  ->  产物 %s (%d B, %+d B)" % (
    os.path.basename(SRC), n0, os.path.basename(DST), n1, n1 - n0))
