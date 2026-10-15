# -*- coding: utf-8 -*-
"""
V5.1.3 补丁
  1) 每个实验的数据记录按钮行末新增「实验报告」按钮（浅蓝底色 .rpj），点击跳到该实验的报告页
  2) 报告页「← 返回实验」按钮同步改为浅蓝底色
  3) 数据记录行的「导出CSV」精简为「导出」（新增独立 i18n 键，教师端的同名按钮不受影响）
  4) 版本号 → 5.1.3
基线：光学交互实验室_AI_v5.1.2.html
产物：光学交互实验室_AI_v5.1.3.html
所有替换均带命中数断言，任一处不符立即中止。
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "光学交互实验室_AI_v5.1.2.html")
DST = os.path.join(BASE, "光学交互实验室_AI_v5.1.3.html")
LOG = []


def rep(s, old, new, n=1, label=""):
    c = s.count(old)
    assert c == n, "[FAIL] %s: 期望 %d 处，实际 %d 处" % (label, n, c)
    LOG.append("OK  %-52s x%d" % (label, c))
    return s.replace(old, new)


with open(SRC, "r", encoding="utf-8") as f:
    s = f.read()
n0 = os.path.getsize(SRC)   # 体积一律取磁盘字节（文本模式 read 会做 CRLF→LF 归一）

# ============================================ C1 浅色（纸黄）主题：浅蓝按钮变量
s = rep(s,
        "    --tts-bg:#dbeafe; --tts-ink:#17150e;\n"
        "    --diag-bg:#c8331f; --diag-ink:#ffffff;",
        "    --tts-bg:#dbeafe; --tts-ink:#17150e;\n"
        "    --diag-bg:#c8331f; --diag-ink:#ffffff;\n"
        "    /* V5.1.3：「实验报告」跳转按钮 · 浅蓝底色（字色成对，避免 V4.9 那类「白底白字」） */\n"
        "    --rpj-bg:#cfe6ff; --rpj-ink:#0a2d55;",
        1, "C1 :root 浅蓝按钮变量")

# ============================================ C2 暗色（黑板）主题：浅蓝按钮变量
s = rep(s,
        "    --tts-bg:#1e3a5f; --tts-ink:#e8f2ff;   /* 10.2:1 */\n"
        "    --diag-bg:#ff8a70; --diag-ink:#2a0808; /* 8.0:1 */",
        "    --tts-bg:#1e3a5f; --tts-ink:#e8f2ff;   /* 10.2:1 */\n"
        "    --diag-bg:#ff8a70; --diag-ink:#2a0808; /* 8.0:1 */\n"
        "    /* V5.1.3：暗色下仍保持「浅蓝底 + 深蓝字」，对比度 > 10:1 */\n"
        "    --rpj-bg:#bcd9ff; --rpj-ink:#082444;",
        1, "C2 body.light 浅蓝按钮变量")

# ============================================ C3 .rpj 规则（放最后一块 style 末尾）
s = rep(s,
        "@keyframes spin{to{transform:rotate(360deg)}}\n</style>",
        "@keyframes spin{to{transform:rotate(360deg)}}\n"
        "/* ==========================================================================\n"
        "   V5.1.3 · 浅蓝「实验报告」按钮\n"
        "   放在最后一块 <style> 的末尾：与 button.sec 同为 (0,1,1) 优先级，靠后即胜出，\n"
        "   不必用 !important；hover 只改位移/阴影（见全局 button:hover），底色不受影响。\n"
        "   ========================================================================== */\n"
        "button.rpj{background:var(--rpj-bg);color:var(--rpj-ink);white-space:nowrap;}\n"
        "button.rpj:hover{background:var(--rpj-bg);}\n"
        "</style>",
        1, "C3 .rpj 浅蓝按钮样式")

# ============================================ C4 报告页「← 返回实验」改浅蓝
s = rep(s,
        '<button id="rpt-back" class="sec" data-i18n="rpt.back">← 返回实验</button>',
        '<button id="rpt-back" class="sec rpj" data-i18n="rpt.back">← 返回实验</button>',
        1, "C4 返回实验按钮浅蓝")

# ============================================ C5 数据行「导出CSV」→「导出」（10 处）
s = rep(s,
        'data-i18n="btn.export">导出CSV</button>',
        'data-i18n="btn.exportShort">导出</button>',
        10, "C5 导出CSV → 导出（10 个实验）")

# ============================================ C6 i18n 新增两个键
s = rep(s,
        "'btn.copy':       {zh:'复制', zht:'複製', en:'Copy'},",
        "/* V5.1.3：数据记录行的「导出」短标签 + 「实验报告」跳转按钮 */\n"
        "'btn.exportShort':{zh:'导出', zht:'匯出', en:'Export'},\n"
        "'btn.rpt':        {zh:'实验报告', zht:'實驗報告', en:'Lab report'},\n"
        "'btn.copy':       {zh:'复制', zht:'複製', en:'Copy'},",
        1, "C6 i18n btn.exportShort / btn.rpt")

# ============================================ C7 数据记录行注入「实验报告」按钮
s = rep(s,
        "  $(key + '-clearBtn').addEventListener('click', () => {\n"
        "    if(!recIdx) return;\n"
        "    clearAction = () => { recIdx = 0; tbody.innerHTML = ''; };\n"
        "    $('clearMask').classList.add('show');\n"
        "  });",
        "  $(key + '-clearBtn').addEventListener('click', () => {\n"
        "    if(!recIdx) return;\n"
        "    clearAction = () => { recIdx = 0; tbody.innerHTML = ''; };\n"
        "    $('clearMask').classList.add('show');\n"
        "  });\n"
        "  /* V5.1.3：数据记录行末新增「📝 实验报告」跳转按钮（浅蓝底色 .rpj），\n"
        "     点一下直接跳到本实验的实验报告页。带 data-i18n，切语言时由 applyLang() 同步刷新。 */\n"
        "  (function(){\n"
        "    var rec = $(key + '-recBtn');\n"
        "    var rowBox = rec ? rec.parentNode : null;\n"
        "    if(!rowBox || rowBox.querySelector('button.rpj')) return;\n"
        "    var rb = document.createElement('button');\n"
        "    rb.type = 'button';\n"
        "    rb.id = key + '-rptBtn';\n"
        "    rb.className = 'sec rpj';\n"
        "    rb.setAttribute('data-i18n', 'btn.rpt');\n"
        "    rb.textContent = T('btn.rpt');\n"
        "    rb.addEventListener('click', function(){\n"
        "      // 先让报告页选中本实验（借 REPORT 自己的 change 钩子把 pickedExp 置真），再切页；\n"
        "      // 此时报告面板尚未激活，REC 的归属判定取不到激活面板，不会被误记一行数据。\n"
        "      var sel = document.getElementById('rpt-exp');\n"
        "      if(sel){ sel.value = key; sel.dispatchEvent(new Event('change', { bubbles:true })); }\n"
        "      switchTab('report');\n"
        "      try{ window.scrollTo({ top:0, behavior:'smooth' }); }catch(e){ window.scrollTo(0, 0); }\n"
        "    });\n"
        "    rowBox.appendChild(rb);\n"
        "  })();",
        1, "C7 数据行注入实验报告按钮")

# ============================================ C8 构建常量
s = rep(s,
        "  var BUILD = 'v5.1.2', MAX_SHOW = 3",
        "  var BUILD = 'v5.1.3', MAX_SHOW = 3",
        1, "C8 BUILD 常量")

# ============================================ C9 报告模块版本兜底
s = rep(s,
        "    return 'v5.1.2';",
        "    return 'v5.1.3';",
        1, "C9 RPT_BUILD 兜底")

# ============================================ C10 版本角标
s = rep(s,
        '<div class="ver-badge" title="光学交互实验室 V5.1.2 · 实验报告入口移入 AI 诊断弹窗 · 更新日志精简">v5.1.2</div>',
        '<div class="ver-badge" title="光学交互实验室 V5.1.3 · 数据记录行新增实验报告跳转按钮 · 导出按钮精简">v5.1.3</div>',
        1, "C10 ver-badge")

# ============================================ C11 更新日志新增 V5.1.3
s = rep(s,
        '      <div class="log-item cur">\n'
        '        <div class="log-head"><span class="log-ver">V5.1.2</span><span class="log-date">2026-09-15</span></div>',
        '      <div class="log-item cur">\n'
        '        <div class="log-head"><span class="log-ver">V5.1.3</span><span class="log-date">2026-09-15</span></div>\n'
        '        <p>每个实验的数据记录行末新增<strong>「实验报告」按钮</strong>（浅蓝底色），点一下直接跳到该实验的实验报告；报告页的「← 返回实验」按钮同步改为浅蓝底色；数据记录行的「导出CSV」精简为「导出」。</p>\n'
        '      </div>\n'
        '      <div class="log-item">\n'
        '        <div class="log-head"><span class="log-ver">V5.1.2</span><span class="log-date">2026-09-15</span></div>',
        1, "C11 更新日志新增 V5.1.3")

# ============================================ 产物复检
assert s.count('data-i18n="btn.exportShort">导出</button>') == 10, "[FAIL] 导出按钮未改全"
assert s.count('data-i18n="btn.export"') == 0, "[FAIL] 数据行不应再引用 btn.export"
assert s.count("T('btn.export')") == 1, "[FAIL] 教师端 T('btn.export') 应保留 1 处"
assert s.count('id="rpt-back" class="sec rpj"') == 1, "[FAIL] 返回按钮未改浅蓝"
assert s.count("button.rpj{background:var(--rpj-bg)") == 1, "[FAIL] .rpj 规则缺失"
assert s.count("white-space:nowrap;}\nbutton.rpj:hover") == 1, "[FAIL] nowrap 兜底缺失"
assert s.count("--rpj-bg") == 4, "[FAIL] 浅蓝变量应有 2 组定义 + 2 处使用"
assert s.count("rb.className = 'sec rpj'") == 1, "[FAIL] 注入按钮类名缺失"
assert s.count("'btn.rpt'") == 3, "[FAIL] btn.rpt 键或调用缺失（字典 + data-i18n + T()）"
assert s.count("v5.1.3") >= 3, "[FAIL] 版本号未同步"
assert s.count("</script>") >= 9, "[FAIL] script 块数量异常"

with open(DST, "w", encoding="utf-8") as f:
    f.write(s)
n1 = os.path.getsize(DST)

print("\n".join(LOG))
print("-" * 70)
print("基线 %s (%d B)" % (os.path.basename(SRC), n0))
print("产物 %s (%d B)" % (os.path.basename(DST), n1))
print("体积变化 %+d B (%.3f%%)" % (n1 - n0, (n1 - n0) * 100.0 / n0))
