# -*- coding: utf-8 -*-
"""
V5.1.2 补丁
  1) 实验报告入口从 tab-nav（第 12 个并列 tab）移入「AI 诊断」弹窗
  2) 报告页新增「← 返回实验」快捷出口
  3) 精简 V5.0 及以后的更新日志
  4) 版本号 → 5.1.2
基线：光学交互实验室_AI_v5.1.1.html
产物：光学交互实验室_AI_v5.1.2.html
所有替换均带命中数断言，任一处不符立即中止。
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "光学交互实验室_AI_v5.1.1.html")
DST = os.path.join(BASE, "光学交互实验室_AI_v5.1.2.html")
LOG = []


def rep(s, old, new, n=1, label=""):
    c = s.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    LOG.append("OK  %-52s x%d" % (label, c))
    return s.replace(old, new)


with open(SRC, "r", encoding="utf-8") as f:
    s = f.read()
# 注意：文本模式会做 CRLF→LF 归一，len(s.encode()) 会少报「行数」个字节，
# 体积统计必须直接取磁盘文件字节数。
n0 = os.path.getsize(SRC)

# =============================================================== C1 版本号 BUILD
s = rep(s,
        "  var BUILD = 'v5.1.1', MAX_SHOW = 3",
        "  var BUILD = 'v5.1.2', MAX_SHOW = 3",
        1, "C1 BUILD 常量")

# ================================================ C2 报告模块版本兜底字面量
s = rep(s,
        "    return 'v5.1.1';",
        "    return 'v5.1.2';",
        1, "C2 RPT_BUILD 兜底")

# ====================================================== C3 右下角版本角标
s = rep(s,
        '<div class="ver-badge" title="光学交互实验室 V5.1.1 · 实验报告自动生成（探究六要素）+ 一键导出">v5.1.1</div>',
        '<div class="ver-badge" title="光学交互实验室 V5.1.2 · 实验报告入口移入 AI 诊断弹窗 · 更新日志精简">v5.1.2</div>',
        1, "C3 ver-badge")

# ========================================== C4 从 tab-nav 移除报告按钮
s = rep(s,
        '    <button class="tab-btn" data-tab="report" data-i18n="tab.report">12 · 实验报告 📝</button>\n',
        '',
        1, "C4 移除 nav 报告按钮")

# ===================================== C5 i18n：新增诊断弹窗入口 & 返回按钮
s = rep(s,
        "'diag.map':       {zh:'🧭 知识地图', zht:'🧭 知識地圖', en:'🧭 Knowledge map'},",
        "'diag.map':       {zh:'🧭 知识地图', zht:'🧭 知識地圖', en:'🧭 Knowledge map'},\n"
        "/* ---- V5.1.2：实验报告入口移入诊断弹窗 ---- */\n"
        "'diag.rpt':       {zh:'📝 实验报告', zht:'📝 實驗報告', en:'📝 Lab report'},\n"
        "'rpt.back':       {zh:'← 返回实验', zht:'← 返回實驗', en:'← Back to lab'},",
        1, "C5 i18n diag.rpt / rpt.back")

# ========================================= C6 报告面板：注释 + 返回按钮
s = rep(s,
        '  <section id="tab-report" class="panel">\n    <div class="rpt-head">',
        '  <!-- V5.1.2：实验报告不再与实验并列；入口在「AI 诊断」弹窗内（见 showAiDiagModal） -->\n'
        '  <section id="tab-report" class="panel">\n    <div class="rpt-head">',
        1, "C6a 报告面板注释")

s = rep(s,
        '        <button id="rpt-refresh" class="sec" data-i18n="rpt.refresh">↻ 重新取值</button>',
        '        <button id="rpt-refresh" class="sec" data-i18n="rpt.refresh">↻ 重新取值</button>\n'
        '        <button id="rpt-back" class="sec" data-i18n="rpt.back">← 返回实验</button>',
        1, "C6b 返回实验按钮")

# ================================== C7 注册逻辑注释 + 返回按钮事件绑定
s = rep(s,
        "/* 注册为第 12 个模块：switchTab('report') 与语言切换都会触发 render() */\n"
        "MODULES.report = { render: function(){ if(window.REPORT) REPORT.render(); } };",
        "/* V5.1.2：报告页不再作为并列 tab，入口在「AI 诊断」弹窗内；\n"
        "   switchTab('report') 与语言切换仍会触发 render() */\n"
        "MODULES.report = { render: function(){ if(window.REPORT) REPORT.render(); } };\n"
        "/* V5.1.2：「← 返回实验」快捷出口——按当前报告所选实验回到对应画布页 */\n"
        "(function(){\n"
        "  var b = document.getElementById('rpt-back'); if(!b) return;\n"
        "  b.addEventListener('click', function(){\n"
        "    var sel = document.getElementById('rpt-exp');\n"
        "    var key = sel ? sel.value : '';\n"
        "    var t2k = (window.REPORT && REPORT.TAB2KEY) || {};\n"
        "    var tab = '';\n"
        "    for(var t in t2k){ if(t2k[t] === key){ tab = t; break; } }\n"
        "    switchTab(tab || 'reflect');\n"
        "    try{ window.scrollTo({ top:0, behavior:'smooth' }); }catch(e){ window.scrollTo(0, 0); }\n"
        "  });\n"
        "})();",
        1, "C7 返回按钮绑定")

# ==================================== C8 诊断弹窗：新增「实验报告」按钮
s = rep(s,
        "'<div class=\"row\" style=\"display:flex;gap:6px;flex-wrap:wrap;\"><button id=\"aiDiagGo\">'+T('diag.go')+'</button><button id=\"aiDiagMap\" class=\"sec\">'+T('diag.map')+'</button><button id=\"aiDiagClose\" class=\"sec\">'+T('btn.close')+'</button></div>'+",
        "'<div class=\"row\" style=\"display:flex;gap:6px;flex-wrap:wrap;\"><button id=\"aiDiagGo\">'+T('diag.go')+'</button><button id=\"aiDiagMap\" class=\"sec\">'+T('diag.map')+'</button><button id=\"aiDiagReport\" class=\"sec\">'+T('diag.rpt')+'</button><button id=\"aiDiagClose\" class=\"sec\">'+T('btn.close')+'</button></div>'+",
        1, "C8 诊断弹窗按钮")

# ==================================== C9 诊断弹窗按钮事件绑定
s = rep(s,
        "    $('aiDiagMap').onclick = function(){ closeModal(); showKmap(); };   // V4.9.3：从诊断弹窗进知识地图",
        "    $('aiDiagMap').onclick = function(){ closeModal(); showKmap(); };   // V4.9.3：从诊断弹窗进知识地图\n"
        "    $('aiDiagReport').onclick = function(){ closeModal(); switchTab('report'); try{ window.scrollTo({ top:0, behavior:'smooth' }); }catch(e){ window.scrollTo(0, 0); } };   // V5.1.2：实验报告入口",
        1, "C9 诊断弹窗绑定")

# ============ C12 修复 V5.1.0~V5.1.1 的静默数据污染：记录归属按事件源面板
s = rep(s,
        "  // 捕获阶段全局委托：无需改动任何既有监听，桌面端/移动端一致生效\n"
        "  document.addEventListener('input',     function(){ touch(activeTab()); }, true);\n"
        "  document.addEventListener('change',    function(){ touch(activeTab()); }, true);\n"
        "  document.addEventListener('pointerup', function(){ touch(activeTab()); }, true);",
        "  // V5.1.2 修复（V5.1.0~V5.1.1 的静默数据污染）：\n"
        "  //   记录归属改为「事件源所在的那个【激活】面板」，而不是「全局当前激活面板」。\n"
        "  //   原因：点顶部 tab 按钮切页时 pointerup 早于 click 到达，此刻全局 activeTab()\n"
        "  //   仍指向上一个实验，照旧排队就会在 1 秒后给那个实验凭空补记一行当前画布读数\n"
        "  //   （表现为：只是切了下标签，上一张数据表里就多出一行）。\n"
        "  //   非画布内交互（tab 按钮、弹窗、报告页控件）以及隐藏面板上的交互一律不计。\n"
        "  function tabOfTarget(t){\n"
        "    if (!t || !t.closest) return null;\n"
        "    var p = t.closest('.panel.active');\n"
        "    return (p && p.id && p.id.indexOf('tab-') === 0) ? p.id.slice(4) : null;\n"
        "  }\n"
        "  // 捕获阶段全局委托：无需改动任何既有监听，桌面端/移动端一致生效\n"
        "  document.addEventListener('input',     function(e){ touch(tabOfTarget(e.target)); }, true);\n"
        "  document.addEventListener('change',    function(e){ touch(tabOfTarget(e.target)); }, true);\n"
        "  document.addEventListener('pointerup', function(e){ touch(tabOfTarget(e.target)); }, true);",
        1, "C12 记录归属按事件源面板（修数据污染）")

# ============ C11 报告页激活时，顶栏 AI 按钮回退到报告所选实验
s = rep(s,
        "    const sec = document.querySelector('.panel.active');\n"
        "    if(!sec){ alert('请先切换到任意实验 tab'); return; }\n"
        "    const expKey = sec.id.replace('tab-','');",
        "    const sec = document.querySelector('.panel.active');\n"
        "    if(!sec){ alert('请先切换到任意实验 tab'); return; }\n"
        "    let expKey = sec.id.replace('tab-','');\n"
        "    // V5.1.2：实验报告页没有自己的实验上下文；此时回退到报告当前所选实验，\n"
        "    // 避免诊断 / 问 AI / 朗读 出现「错题诊断 · report」这类无效标题。\n"
        "    if(!EXP_TTS[expKey]){\n"
        "      try{\n"
        "        const sel = document.getElementById('rpt-exp');\n"
        "        const k = sel ? sel.value : '';\n"
        "        const m = (window.REPORT && REPORT.TAB2KEY) || {};\n"
        "        let t = '';\n"
        "        for(const x in m){ if(m[x] === k){ t = x; break; } }\n"
        "        expKey = t || 'reflect';\n"
        "      }catch(e){ expKey = 'reflect'; }\n"
        "    }",
        1, "C11 报告页 AI 上下文回退")

# ================================ C10 更新日志：精简 V5.0+ 并新增 V5.1.2
NEW_LOG = """      <div class="log-item cur">
        <div class="log-head"><span class="log-ver">V5.1.2</span><span class="log-date">2026-09-15</span></div>
        <p>「实验报告」不再与 10 个实验并列成第 12 个标签页，改为从「AI 诊断」弹窗进入，报告页内新增「← 返回实验」快捷出口；同步精简 V5.0 及之后的更新日志篇幅。</p>
      </div>
      <div class="log-item">
        <div class="log-head"><span class="log-ver">V5.1.1</span><span class="log-date">2026-09-15</span></div>
        <p>新增「实验报告」：按<strong>问题 → 猜想 → 方案（含变量控制）→ 数据表 → 结论 → 反思</strong>六要素组织，其中问题、方案、数据与结论均由各实验<strong>画布的真实参数</strong>自动取值；另含自评 / 互评与完成度进度条。支持一键导出自包含 HTML、纯文本、数据 CSV 与打印 / 存 PDF，全部离线可用。</p>
      </div>
      <div class="log-item">
        <div class="log-head"><span class="log-ver">V5.1.0</span><span class="log-date">2026-09-14</span></div>
        <p>新增通用数据记录器：有数据可记的实验在用户<strong>停止操作 1 秒后自动落表</strong>（拖动滑块、切换模式、画布拖拽均可触发），数据自动去重并可导出 CSV；为原先缺表的 6 个实验补齐表格。AI 判卷升级为<strong>错因归因</strong>，并自动生成同知识点的变式题。</p>
      </div>
      <div class="log-item">
        <div class="log-head"><span class="log-ver">V5.0.2</span><span class="log-date">2026-09-14</span></div>
        <p>挑战模式新增「暂停计时」按钮。</p>
      </div>
      <div class="log-item">
        <div class="log-head"><span class="log-ver">V5.0.1</span><span class="log-date">2026-09-14</span></div>
        <p>兼容性紧急修复：部分手机浏览器缺少 <code>window.matchMedia</code>，导致 JS 链中断后误显示「JS 已关闭」兜底页；现加外层 try-catch 与安全封装，并增强 noscript 兜底页的排查指引。</p>
      </div>
      <div class="log-item">
        <div class="log-head"><span class="log-ver">V5.0.0</span><span class="log-date">2026-09-14</span></div>
        <p>首发移动端：自动识别手机 / 桌面，手机竖屏四档断点排版、弹窗全屏化与安全区避让，canvas 启用高分屏适配，并补齐触屏交互；桌面端零侵入。</p>
      </div>
"""

i0 = s.index('      <div class="log-item cur">\n        <div class="log-head"><span class="log-ver">V5.1.1</span>')
i1 = s.index('      <div class="log-item">\n        <div class="log-head"><span class="log-ver">V4.10.4</span>')
assert i0 < i1, "[FAIL] C10 更新日志定位异常"
s = s[:i0] + NEW_LOG + s[i1:]
LOG.append("OK  %-52s (V5.1.1~V5.0.0 精简 + 新增 V5.1.2)" % "C10 更新日志")

# ============================================================== 断言复检
assert s.count('data-tab="report"') == 0, "[FAIL] 仍存在 report 导航按钮"
assert s.count("'tab.report'") == 1, "[FAIL] tab.report 字典异常"   # 字典保留、按钮已删
assert s.count("id=\"aiDiagReport\"") == 1, "[FAIL] 诊断弹窗报告按钮缺失"
assert s.count("$('aiDiagReport').onclick") == 1, "[FAIL] 诊断弹窗报告绑定缺失"
assert s.count("id=\"rpt-back\"") == 1, "[FAIL] 返回实验按钮缺失"
assert s.count("v5.1.2") >= 3, "[FAIL] 版本号未同步"
assert s.count("</script>") >= 9, "[FAIL] script 块数量异常"

with open(DST, "w", encoding="utf-8") as f:
    f.write(s)
n1 = os.path.getsize(DST)

print("\n".join(LOG))
print("-" * 70)
print("基线 %s (%d B)" % (os.path.basename(SRC), n0))
print("产物 %s (%d B)" % (os.path.basename(DST), n1))
print("体积变化 %+d B (%.2f%%)" % (n1 - n0, (n1 - n0) * 100.0 / n0))
