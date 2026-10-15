# -*- coding: utf-8 -*-
"""V6.4.6 产物自检：
   1. 按浏览器口径拆 <script> 块，逐块喂 node --check
   2. 结构断言：设置下拉（四入口已入菜单、锚点在 topbar-right 之外）、五个 id 原样保留
   3. 小孔成像物距：data-g 双模式 + data-g 多模式匹配逻辑
   4. 版本号四处同步 + 更新日志 ≤ 20 字
"""
import os
import re
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(BASE, "光学交互实验室_AI_v6.4.6.html")
CHK = os.path.join(BASE, "_chk646")
NODE = r"C:\Users\Administrator\.workbuddy\binaries\node\versions\22.12.0\node.exe"

s = open(DST, encoding="utf-8").read()
os.makedirs(CHK, exist_ok=True)

# ---- 1. 拆块 + node --check
blocks = re.findall(r"<script[^>]*>(.*?)</script(?=[\s>/])", s, re.S)
print("脚本块数：%d" % len(blocks))
bad = 0
for i, b in enumerate(blocks):
    if len(b.strip()) < 20:
        continue
    p = os.path.join(CHK, "_chk646_%02d.js" % i)
    open(p, "w", encoding="utf-8", newline="\n").write(b)
    r = subprocess.run([NODE, "--check", p], capture_output=True, text=True)
    if r.returncode != 0:
        bad += 1
        print("[JS FAIL] block %d: %s" % (i, r.stderr[:500]))
    else:
        print("  OK  block %-2d  %8d chars" % (i, len(b)))
assert bad == 0, "%d 个脚本块语法错误" % bad

# ---- 2. 结构断言
CHECKS = [
    # 设置下拉
    ('<div class="set-wrap" id="setWrap">', 1, "设置下拉容器"),
    ('<div class="set-menu" id="setMenu" role="menu" hidden>', 1, "下拉菜单本体（默认收起）"),
    ('id="setBtn" class="theme-btn" data-i18n="btn.settings"', 1, "设置按钮"),
    ("'btn.settings':", 1, "i18n 词条"),
    (".set-menu[hidden]{display:none !important;}", 1, "收起态样式"),
    # 五个入口 id 全部保留（事件监听挂在 id 上，改 id 会静默失效）
    ('<button id="aiCfgBtn" class="set-item"', 1, "AI 设置按钮保留原 id"),
    ('<button id="zoomOut" class="set-item"', 1, "缩小字号按钮保留原 id"),
    ('<button id="zoomIn" class="set-item"', 1, "放大字号按钮保留原 id"),
    ('<button id="langBtn" class="set-item"', 1, "语言按钮保留原 id"),
    ('<button id="themeBtn" class="set-item"', 1, "背景色按钮保留原 id"),
    ('<button id="setBtn"', 1, "设置按钮唯一"),
    # 设置下拉必须在 topbar-right 之外
    ('  </div>\n    <!-- V6.4.6 · 「设置」下拉', 1, "下拉紧跟在 topbar-right 之后（未被滚动容器包裹）"),
    # 注入锚点已改（否则学生/AI 按钮会掉进下拉）
    ("$('fsBtn') || $('aiCfgBtn')", 2, "两处注入锚点改到 #fsBtn"),
    ("// ---- V6.4.6 · 「设置」下拉开合 ----", 1, "下拉开合逻辑"),
    ("if(!wrap.contains(e.target)) setOpen(false);", 1, "点外部关闭"),
    # 小孔成像物距
    ('<span class="slider-g" data-g="shadow pinhole">', 1, "物距组两模式共用"),
    ('<button id="line-uPlay" class="play-btn" data-i18n="btn.scanU">', 1, "物距扫描按钮仍在"),
    ("var gs = (g.dataset.g || '').split(/\\s+/);", 1, "data-g 空格分隔匹配"),
    ("g.style.display = gs.indexOf(mode) >= 0 ? '' : 'none';", 1, "多模式显隐"),
    # 版本号四处
    ("var BUILD = 'v6.4.6'", 1, "BUILD"),
    ("    return 'v6.4.6';", 1, "报告版本兜底"),
    ('title="光学交互实验室 V6.4.6 · ', 1, "角标 title"),
    (">v6.4.6</div>", 1, "角标正文"),
    ('<span class="log-ver">V6.4.6</span>', 1, "更新日志条目"),
    ('<div class="log-item cur">\n        <div class="log-head"><span class="log-ver">V6.4.6</span>', 1, "新条目为 cur"),
    ('<span class="log-ver">V6.4.5</span>', 1, "旧条目降级保留"),
    # 旧版残留不该再有
    ('<button id="aiCfgBtn" class="theme-btn"', 0, "旧顶栏 AI 设置按钮已移除"),
    ('html[data-mode="mobile"] .set-menu', 0, "窄屏改边规则已移除（会导致 390px 下溢出右侧）"),
    ('.set-menu{position:absolute;top:calc(100% + 6px);right:0;', 1, "菜单统一 right:0 定位"),
    ('.set-wrap{margin-left:auto;}', 1, "窄屏把设置推到行尾（下拉不会溢出）"),
    # 分组保有量：物距组已并入 pinhole；「物体位置」仍只属影子；像距/孔大小仍只属小孔
    ('data-g="shadow pinhole">', 1, "共用组 1 个"),
    ('data-g="shadow">', 1, "影子专属组 1 个（物体位置）"),
    ('data-g="pinhole"', 2, "小孔专属组 2 个（像距 / 孔大小）"),
]
for t, n, name in CHECKS:
    c = s.count(t)
    assert c == n, "[FAIL] %s：%r 出现 %d 次，应为 %d" % (name, t, c, n)
print("结构断言 %d 项全部命中" % len(CHECKS))

# 更新日志字数
m = re.search(r'<span class="log-ver">V6\.4\.6</span>.*?<p>(.*?)</p>', s, re.S)
assert m, "未找到 V6.4.6 日志正文"
txt = m.group(1)
assert len(txt) <= 20, "更新日志 %d 字，超过 20" % len(txt)
print("更新日志：%s（%d 字）" % (txt, len(txt)))

# 脚本收尾标签字面量：与源文件同口径
src = open(os.path.join(BASE, "光学交互实验室_AI_v6.4.5.html"), encoding="utf-8").read()
assert len(re.findall(r"</script(?=[\s>/])", s)) == len(re.findall(r"</script(?=[\s>/])", src)), \
    "脚本收尾标签计数变化"
print("脚本收尾标签计数与源一致：%d" % len(re.findall(r"</script(?=[\s>/])", s)))
print("\n全部静态自检通过。")
